from typing import Optional
from .browser import open_browser
from .scrape import fetch_profile_via_api

def run(query: Optional[str], username: Optional[str], headless: bool = True):
    p, b, ctx, page = open_browser("storage_state.json", headless=headless)
    try:
        handle = username or query
        data = fetch_profile_via_api(ctx, handle)
        return data or {}
    finally:
        b.close()
        p.stop()
