# app/cli.py
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger

from .browser import open_browser, clear_interstitials, human_sleep
from .scrape import scrape_profile_basics, collect_post_links, scrape_post_page


def _abs_url(href: str) -> str:
    href = (href or "").strip()
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("/"):
        return f"https://www.instagram.com{href}"
    return f"https://www.instagram.com/{href.lstrip('./')}"


def _scrape_current_profile(
    ctx,
    page,
    username: str,
    max_posts: int = 3,
    capture_post_shots: bool = False,
    shots_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Scrape the currently open profile page using existing parsers in app.scrape.
    Optionally capture per-post screenshots to shots_dir.
    """
    # Stabilize and parse basics
    clear_interstitials(page)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass

    profile = scrape_profile_basics(page.content(), page.url)

    # Try to collect recent post links
    try:
        hrefs = collect_post_links(page, max_posts=max_posts)
    except Exception:
        hrefs = []

    if not hrefs:
        logger.warning("No posts found yet; scrolling and retrying.")
        for _ in range(6):
            try:
                page.mouse.wheel(0, 1600)
            except Exception:
                pass
            human_sleep(0.6, 0.9)
            try:
                hrefs = collect_post_links(page, max_posts=max_posts)
            except Exception:
                hrefs = []
            if hrefs:
                break

    posts: List[Dict[str, Any]] = []
    for idx, href in enumerate(hrefs, start=1):
        url = _abs_url(href)
        short = url.rstrip("/").split("/")[-1]
        data: Optional[Dict[str, Any]] = None
        shot_path: Optional[Path] = None

        # Prefer a separate tab so we don't lose the profile page state
        try:
            newp = ctx.new_page()
            newp.goto(url, wait_until="domcontentloaded", timeout=60_000)
            clear_interstitials(newp)
            data = scrape_post_page(newp)

            if capture_post_shots and shots_dir:
                shots_dir.mkdir(parents=True, exist_ok=True)
                shot_path = shots_dir / f"{username}_{short}_{idx}.png"
                newp.screenshot(path=str(shot_path), full_page=True)

            newp.close()
        except Exception as e:
            logger.warning(f"New tab failed for {url}: {e} — fallback to same tab.")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                clear_interstitials(page)
                data = scrape_post_page(page)
                if capture_post_shots and shots_dir:
                    shots_dir.mkdir(parents=True, exist_ok=True)
                    shot_path = shots_dir / f"{username}_{short}_{idx}.png"
                    page.screenshot(path=str(shot_path), full_page=True)
                # go back to profile
                page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle", timeout=60_000)
                clear_interstitials(page)
            except Exception as e2:
                logger.error(f"Could not fetch post {url}: {e2}")

        if data:
            data["shortcode"] = short
            if shot_path:
                data["screenshot_path"] = str(shot_path)
            posts.append(data)
            human_sleep(1.0, 1.8)

    profile["latest_posts"] = posts
    return profile


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
        # go to canonical profile URL
        url = f"https://www.instagram.com/{username}/"
        page.goto(url, wait_until="networkidle", timeout=60_000)
        clear_interstitials(page)

        shots_dir = Path("/tmp/shots")
        if capture_post_shots:
            shots_dir.mkdir(parents=True, exist_ok=True)

        result = _scrape_current_profile(
            ctx=ctx,
            page=page,
            username=username,
            max_posts=max_posts,
            capture_post_shots=capture_post_shots,
            shots_dir=shots_dir if capture_post_shots else None,
        )
        return result
    finally:
        # graceful cleanup
        for closer in (lambda: ctx.close(), lambda: b.close(), lambda: p.stop()):
            try:
                closer()
            except Exception:
                pass
