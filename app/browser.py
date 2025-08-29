# app/browser.py
from pathlib import Path
import random
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def human_sleep(a: float = 0.8, b: float = 1.6) -> None:
    """Small random delay to look less botty."""
    time.sleep(random.uniform(min(a, b), max(a, b)))


def clear_interstitials(page) -> None:
    """
    Close/accept common popups on Instagram (cookie, login, allow-notifications, etc).
    All actions are best-effort and fully guarded.
    """
    selectors = [
        # Cookie banners (various locales/variants)
        "button:has-text('Only allow essential cookies')",
        "button:has-text('Allow essential and optional cookies')",
        "button:has-text('Allow all cookies')",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Accept')",
        "[role=dialog] button:has-text('OK')",

        # “Not now” login/save dialogs
        "button:has-text('Not Now')",
        "text=Not now",
        "button:has-text('Maybe later')",

        # Generic close buttons on dialogs
        "[role=dialog] [aria-label='Close']",
        "[role=dialog] svg[aria-label='Close']",
    ]

    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.click(timeout=500)
                human_sleep(0.2, 0.6)
        except Exception:
            pass

    # If a blocking dialog remained, try pressing Escape once
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def open_browser(storage_state_path: str = "storage_state.json", headless: bool = True):
    """
    Start Playwright Chromium in a way that works locally and on Render.
    Returns (playwright, browser, context, page).
    """
    p = sync_playwright().start()

    # Arguments that make headless Chromium stable in containers like Render
    launch_args = [
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-software-rasterizer",
        "--disable-extensions",
        "--disable-features=IsolateOrigins,site-per-process,RendererCodeIntegrity",
        "--no-sandbox",
    ]

    browser = p.chromium.launch(headless=headless, args=launch_args)

    storage_path = Path(storage_state_path)
    context_kwargs = {
        "viewport": {"width": 1280, "height": 900},
        "ignore_https_errors": True,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        # Keep default locale English to simplify selectors
        "locale": "en-US",
    }

    if storage_path.exists():
        context_kwargs["storage_state"] = str(storage_path)

    ctx = browser.new_context(**context_kwargs)
    page = ctx.new_page()

    # Be a bit generous for slow networks
    page.set_default_timeout(45000)
    page.set_default_navigation_timeout(60000)

    try:
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
        clear_interstitials(page)
    except PWTimeout:
        # continue; the caller may still navigate to what they need
        pass
    except Exception:
        pass

    return p, browser, ctx, page
