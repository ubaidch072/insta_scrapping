# app/cli.py
from typing import Optional, Dict, Any
from .browser import open_browser

async def run(query: Optional[str], username: Optional[str], headless: bool = True) -> Dict[str, Any]:
    pw, browser, ctx, page = await open_browser("storage_state.json", headless=headless)
    try:
        # ===== Replace this with your real logic =====
        # Example flow: visit a page and collect something
        target = f"https://www.instagram.com/{username}/" if username else "https://example.com"
        await page.goto(target, wait_until="networkidle", timeout=90_000)

        # sample data to prove end-to-end works
        title = await page.title()
        content = await page.text_content("body")

        return {
            "ok": True,
            "target": target,
            "title": title,
            "snippet": (content[:300] if content else None),
        }
        # =============================================

    finally:
        await ctx.close()
        await browser.close()
        await pw.stop()
