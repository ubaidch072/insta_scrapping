
from playwright.sync_api import TimeoutError as PWTimeout
from .browser import human_sleep
from loguru import logger
import urllib.parse

def goto_profile_by_search(page, query: str) -> str:
    page.goto("https://www.instagram.com/", wait_until="networkidle")
    human_sleep(0.8, 1.4)

    # Try internal API first (works only when logged in)
    try:
        url = f"https://www.instagram.com/web/search/topsearch/?context=blended&query={urllib.parse.quote(query)}"
        resp = page.request.get(url, timeout=15000)
        if resp.ok:
            data = resp.json()
            users = data.get("users", [])
            if users:
                # Prefer exact username match else first result
                best = None
                for u in users:
                    user = u.get("user", {})
                    if user.get("username","").lower() == query.lower():
                        best = user; break
                if not best:
                    best = users[0].get("user", {})
                username = best.get("username")
                if username:
                    page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded")
                    return username
    except Exception as e:
        logger.debug(f"Topsearch failed, fallback to UI search: {e}")

    # Fallback: UI search box
    try:
        page.keyboard.press("/")
    except:
        pass
    page.keyboard.type(query)
    page.wait_for_selector("a[href^='https://www.instagram.com/']", timeout=20000)
    links = page.query_selector_all("a[href^='https://www.instagram.com/']")
    for a in links:
        href = a.get_attribute("href")
        if href and href.rstrip("/").count("/") <= 4 and "explore" not in href:
            page.goto(href, wait_until="domcontentloaded")
            return href.rstrip("/").split("/")[-1]
    raise RuntimeError("No profile link found from search results")
