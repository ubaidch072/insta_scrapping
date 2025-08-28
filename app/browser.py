from pathlib import Path
from playwright.sync_api import sync_playwright

def open_browser(storage_state_path: str, headless: bool = True):
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=headless,
        args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-features=IsolateOrigins,site-per-process,RendererCodeIntegrity",
            "--no-sandbox",
        ],
    )
    storage = storage_state_path if Path(storage_state_path).exists() else None
    ctx = browser.new_context(
        storage_state=storage,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        viewport={"width": 1280, "height": 900},
    )
    page = ctx.new_page()
    page.set_default_timeout(30000)
    page.set_default_navigation_timeout(45000)
    try:
        cookies = ctx.cookies()
        has_session = any(c.get("name") == "sessionid" for c in cookies)
        print(f"[auth] sessionid present: {has_session} | cookies={len(cookies)}")
    except Exception:
        pass
    return p, browser, ctx, page
