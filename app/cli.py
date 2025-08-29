from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from .browser import open_browser, clear_interstitials
from .interactive import scrape_current_profile  # uses your robust post-scraper

def run(
    query: Optional[str],
    username: str,
    headless: bool = True,
    capture_post_shots: bool = False,
    max_posts: int = 3,
) -> Dict[str, Any]:
    """
    Open browser with saved session (storage_state.json), go to profile,
    scrape basics + recent posts, optionally capture per-post screenshots.
    """
    p, b, ctx, page = open_browser("storage_state.json", headless=headless)
    try:
        url = f"https://www.instagram.com/{username}/"
        page.goto(url, wait_until="networkidle", timeout=60_000)
        clear_interstitials(page)

        shots_dir = Path("/tmp/shots")
        if capture_post_shots:
            shots_dir.mkdir(parents=True, exist_ok=True)

        result = scrape_current_profile(
            ctx=ctx,
            page=page,
            username=username,
            max_posts=max_posts,
            capture_post_shots=capture_post_shots,
            shots_dir=shots_dir if capture_post_shots else None,
        )
        return result
    finally:
        for closer in (lambda: ctx.close(), lambda: b.close(), lambda: p.stop()):
            try:
                closer()
            except Exception:
                pass
