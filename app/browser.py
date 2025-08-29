# app/browser.py
from playwright.async_api import async_playwright

LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--single-process",
]

async def open_browser(storage_state_path: str, headless: bool = True):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless, args=LAUNCH_ARGS)
    context = await browser.new_context(storage_state=storage_state_path)
    page = await context.new_page()
    return pw, browser, context, page
