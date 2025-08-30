# app/scrape.py
from __future__ import annotations

import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

_NUM_RE = re.compile(r"([\d\.,]+)\s*([kKmMbB]?)")
_WS_RE = re.compile(r"\s+")


def _strip_ws(s: Optional[str]) -> str:
    if not s:
        return ""
    return _WS_RE.sub(" ", s).strip()


def _to_int_approx(s: Optional[str]) -> Optional[int]:
    """
    Convert '12,345' or '1.2m' into an int. Returns None on failure.
    """
    if not s:
        return None
    s = s.lower().replace(",", "").strip()
    m = _NUM_RE.match(s)
    if not m:
        return None
    num, suffix = m.groups()
    try:
        val = float(num)
    except Exception:
        return None
    mult = 1
    if suffix == "k":
        mult = 1_000
    elif suffix == "m":
        mult = 1_000_000
    elif suffix == "b":
        mult = 1_000_000_000
    return int(val * mult)


def _username_from_url(url: str) -> Optional[str]:
    try:
        p = urlparse(url or "")
        parts = [x for x in p.path.split("/") if x]
        if parts and parts[0] not in {"p", "reel", "explore", "accounts", "stories"}:
            return parts[0]
    except Exception:
        pass
    return None


def _parse_ld_json(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Try to parse application/ld+json block which sometimes includes name, description, etc.
    """
    out: Dict[str, Any] = {}
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        with suppress(Exception):
            data = json.loads(tag.get_text() or "{}")
            # If it's a list, pick first dict-looking entry
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        data = item
                        break
            if isinstance(data, dict):
                if "name" in data and not out.get("full_name"):
                    out["full_name"] = _strip_ws(str(data.get("name")))
                if "description" in data and not out.get("bio"):
                    out["bio"] = _strip_ws(str(data.get("description")))
                if "url" in data and not out.get("external_url"):
                    out["external_url"] = _strip_ws(str(data.get("url")))
    return out


class suppress:
    def __init__(self, *exc):
        self.exc = exc or (Exception,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        return exc_type is not None and issubclass(exc_type, self.exc)


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------
def scrape_profile_basics(html: str, url: str) -> Dict[str, Any]:
    """
    Parse basic profile info from a profile HTML page.
    Returns dict with keys: username, full_name, bio, external_url, followers, following, profile_pic_url, url
    """
    soup = BeautifulSoup(html or "", "lxml")
    out: Dict[str, Any] = {
        "username": _username_from_url(url or "") or "",
        "full_name": None,
        "bio": None,
        "external_url": None,
        "followers": None,
        "following": None,
        "profile_pic_url": None,
        "url": url,
    }

    # Try ld+json first
    with suppress(Exception):
        meta = _parse_ld_json(soup)
        out.update({k: v for k, v in meta.items() if v})

    # Meta tags fallbacks
    # <meta property="og:title" content="Full Name (@username) â€¢ Instagram photos and videos">
    with suppress(Exception):
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title and og_title.get("content"):
            c = og_title["content"]
            # Try to split "Full Name (@username)"
            if "(@" in c:
                fn = c.split("(@", 1)[0].strip()
                if fn and not out.get("full_name"):
                    out["full_name"] = fn

    # Description sometimes contains follower counts
    # <meta property="og:description" content="X Followers, Y Following, Z Posts - ...">
    with suppress(Exception):
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and og_desc.get("content"):
            desc = og_desc["content"]
            # naive parse
            m = re.search(r"([\d\.,kKmMbB]+)\s+Followers", desc)
            if m and not out.get("followers"):
                out["followers"] = _to_int_approx(m.group(1))
            m = re.search(r"([\d\.,kKmMbB]+)\s+Following", desc)
            if m and not out.get("following"):
                out["following"] = _to_int_approx(m.group(1))

    # Profile image
    with suppress(Exception):
        og_img = soup.select_one('meta[property="og:image"]')
        if og_img and og_img.get("content"):
            out["profile_pic_url"] = og_img["content"]

    # Bio: look for <meta name="description"> or a bio container
    with suppress(Exception):
        mdesc = soup.select_one('meta[name="description"]')
        if mdesc and mdesc.get("content") and not out.get("bio"):
            out["bio"] = _strip_ws(mdesc["content"])

    # External URL: try anchors with rel/me or same host
    if not out.get("external_url"):
        with suppress(Exception):
            a = soup.select_one("header a[href^='http']")
            if a and a.get("href"):
                out["external_url"] = a["href"]

    # Normalize empties
    for k in ("full_name", "bio", "external_url", "profile_pic_url"):
        if out.get(k) is not None:
            out[k] = _strip_ws(out[k])

    return out


def collect_post_links(page, max_posts: int = 3) -> List[str]:
    """
    Use Playwright page to grab latest post/reel permalinks from the profile grid.
    Returns a list of hrefs like /p/SHORTCODE/ or /reel/SHORTCODE/
    """
    # Common selectors for grid items
    candidates = []
    try:
        # All anchors that look like posts or reels
        anchors = page.query_selector_all("a[href*='/p/'], a[href*='/reel/']")
        for a in anchors:
            with suppress(Exception):
                href = a.get_attribute("href") or ""
                if href and ("/p/" in href or "/reel/" in href):
                    candidates.append(href)
    except Exception:
        pass

    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for h in candidates:
        if h not in seen:
            seen.add(h)
            out.append(h)
            if len(out) >= max_posts:
                break
    return out


def scrape_post_page(page) -> Dict[str, Any]:
    """
    Extract caption, media URLs, timestamp from a single post/reel page (currently loaded).
    """
    data: Dict[str, Any] = {
        "caption": None,
        "media_urls": [],
        "posted_at": None,
        "shortcode": None,
    }

    # Try meta tags / JSON first
    html = ""
    with suppress(Exception):
        html = page.content() or ""
    soup = BeautifulSoup(html, "lxml")

    # Caption: try og:description or meta description
    with suppress(Exception):
        og = soup.select_one('meta[property="og:description"]')
        if og and og.get("content"):
            data["caption"] = _strip_ws(og["content"])
    if not data["caption"]:
        with suppress(Exception):
            md = soup.select_one('meta[name="description"]')
            if md and md.get("content"):
                data["caption"] = _strip_ws(md["content"])

    # Media: images and video
    # Prefer og:image
    with suppress(Exception):
        ogi = soup.select_one('meta[property="og:image"]')
        if ogi and ogi.get("content"):
            data["media_urls"].append(ogi["content"])
    # Also pick up any <img> with src
    with suppress(Exception):
        for im in soup.select("img[src]"):
            src = im.get("src")
            if src and src.startswith("http") and src not in data["media_urls"]:
                data["media_urls"].append(src)
    # Videos
    with suppress(Exception):
        ogv = soup.select_one('meta[property="og:video"]')
        if ogv and ogv.get("content"):
            url = ogv["content"]
            if url not in data["media_urls"]:
                data["media_urls"].append(url)
    with suppress(Exception):
        for v in soup.select("video[src]"):
            src = v.get("src")
            if src and src.startswith("http") and src not in data["media_urls"]:
                data["media_urls"].append(src)

    # Time: <time datetime="...">
    with suppress(Exception):
        t = soup.select_one("time[datetime]")
        if t and t.get("datetime"):
            data["posted_at"] = t["datetime"]

    # Shortcode from URL
    with suppress(Exception):
        u = page.url or ""
        parts = [x for x in urlparse(u).path.split("/") if x]
        if len(parts) >= 2 and parts[0] in {"p", "reel"}:
            data["shortcode"] = parts[1]

    # Normalize caption
    if data["caption"]:
        data["caption"] = _strip_ws(data["caption"])

    return data
