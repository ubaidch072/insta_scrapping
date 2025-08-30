# app/browser.py
import os
from playwright.async_api import async_playwright

LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

async def open_browser(storage_state_path: str | None = "storage_state.json", headless: bool = True):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless, args=LAUNCH_ARGS)

    # Make storage state OPTIONAL: only pass if file actually exists
    storage_arg = None
    if storage_state_path and os.path.exists(storage_state_path):
        storage_arg = storage_state_path

    context = await browser.new_context(storage_state=storage_arg)
    page = await context.new_page()
    return pw, browser, context, page

async def close_browser(pw, browser, ctx):
    try:
        await ctx.close()
    except Exception:
        pass
    try:
        await browser.close()
    except Exception:
        pass
    try:
        await pw.stop()
    except Exception:
        pass
