# app/cli.py
<<<<<<< HEAD
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
=======
# ------------------------------------------------------------
# Scraper entrypoint used by webapi.py
# - Loads cookies from storage_state.json if present
# - Extracts counts from OG meta (stable), then JSON-LD, then DOM
# - Pulls recent 3 posts (caption, media_urls, posted_at, shortcode, url)
# - Understands 1,234 / 987k / 1.2m / 3.4B formats
# - Optional: USE_SYSTEM_CHROME=1 to use installed Google Chrome
# ------------------------------------------------------------

from __future__ import annotations
import os
import re
import json
import pathlib
from typing import Optional, Dict, Any, List

from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

_NUM_RE = re.compile(r"([\d,.]+)\s*([kmbKMB])?$")
POST_CODE_RE = re.compile(r"/(p|reel)/([^/]+)/")

def _parse_compact_num(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    s = s.strip()
    m = _NUM_RE.search(s.replace(" ", ""))
    if not m:
        return None
    num, suf = m.group(1), (m.group(2) or "").lower()
    num = num.replace(",", "")
    try:
        val = float(num)
    except Exception:
        return None
    mult = 1
    if suf == "k": mult = 1_000
    elif suf == "m": mult = 1_000_000
    elif suf == "b": mult = 1_000_000_000
    return int(val * mult)

async def _extract_post(ctx, url: str) -> Dict[str, Any]:
    """
    Open a post/reel URL and extract caption, main media and timestamp.
    Note: IG carousels may contain multiple media; we reliably take the OG image/video.
    """
    page = await ctx.new_page()
    try:
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")

        og_desc  = await page.locator('meta[property="og:description"]').get_attribute("content")
        og_img   = await page.locator('meta[property="og:image"]').get_attribute("content")
        try:
            og_vid = await page.locator('meta[property="og:video"]').get_attribute("content")
        except Exception:
            og_vid = None

        # Caption: try the quoted text in the og:description, else take leading piece
        caption = None
        if og_desc:
            m = re.search(r"“(.+?)”", og_desc)  # smart quotes variant
            if not m:
                m = re.search(r'"(.+?)"', og_desc)  # straight quotes
            if m:
                caption = m.group(1).strip()
            else:
                caption = og_desc.split("•")[0].strip()

        try:
            posted_at = await page.locator("time").get_attribute("datetime")
        except Exception:
            posted_at = None

        m = POST_CODE_RE.search(url)
        shortcode = m.group(2) if m else None

        media_urls = [u for u in [og_vid, og_img] if u]
        return {
            "shortcode": shortcode,
            "caption": caption or "",
            "media_urls": media_urls,
            "posted_at": posted_at,
            "url": url,
        }
    finally:
        await page.close()

async def run(
    username: str,
    query: Optional[str] = None,
    headless: bool = True,
) -> Dict[str, Any]:
    url = f"https://www.instagram.com/{username}/"

    name = None
    bio = None
    followers = following = posts = None
    posts_data: List[Dict[str, Any]] = []

    try:
        async with async_playwright() as p:
            launch_kwargs = {"headless": headless}
            if os.getenv("USE_SYSTEM_CHROME") == "1":
                launch_kwargs["channel"] = "chrome"  # or "msedge"
            browser = await p.chromium.launch(**launch_kwargs)

            ctx_kwargs: Dict[str, Any] = {}
            if pathlib.Path("storage_state.json").exists():
                ctx_kwargs["storage_state"] = "storage_state.json"
            ctx_kwargs["user_agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            ctx = await browser.new_context(**ctx_kwargs)
            page = await ctx.new_page()

            # Load profile
            await page.goto(url, timeout=120_000, wait_until="domcontentloaded")

            # ---------- LAYER 1: OG meta ----------
            try:
                og_desc  = await page.locator('meta[property="og:description"]').get_attribute("content")
            except Exception:
                og_desc = None
            try:
                og_title = await page.locator('meta[property="og:title"]').get_attribute("content")
            except Exception:
                og_title = None

            if og_desc:
                try:
                    leading = og_desc.split("-")[0]
                    parts = [x.strip() for x in leading.split(",")]
                    for part in parts:
                        low = part.lower()
                        token = part.split()[0]
                        if "follower" in low:
                            followers = _parse_compact_num(token)
                        elif "following" in low:
                            following = _parse_compact_num(token)
                        elif "post" in low:
                            posts = _parse_compact_num(token)
                except Exception:
                    pass

            if og_title:
                try:
                    name = og_title.split("•")[0].strip()
                except Exception:
                    pass

            # ---------- LAYER 2: JSON-LD fallback ----------
            if not name or name == "":
                try:
                    ld = await page.locator('script[type="application/ld+json"]').first.text_content(timeout=3_000)
                    if ld:
                        j = json.loads(ld)
                        if isinstance(j, dict):
                            name = j.get("name") or name
                            bio  = j.get("description") or bio
                except Exception:
                    pass

            # ---------- LAYER 3: DOM fallbacks (counts) ----------
            try:
                if followers is None:
                    txt = await page.locator(
                        "a[href$='/followers/'] span, a:has-text('followers') span"
                    ).first.inner_text(timeout=3_000)
                    followers = _parse_compact_num(txt)
            except Exception:
                pass
            try:
                if following is None:
                    txt = await page.locator(
                        "a[href$='/following/'] span, a:has-text('following') span"
                    ).first.inner_text(timeout=3_000)
                    following = _parse_compact_num(txt)
            except Exception:
                pass
            try:
                if posts is None:
                    header_txt = await page.locator("header").first.inner_text(timeout=3_000)
                    m = re.search(r"(\d[\d,\.]*\s*[kmbKMB]?)\s+posts?", header_txt, flags=re.I)
                    if m:
                        posts = _parse_compact_num(m.group(1))
            except Exception:
                pass

            # ---------- Bio fallback ----------
            if bio is None:
                try:
                    meta_desc = await page.locator('meta[name="description"]').get_attribute("content")
                    bio = meta_desc or ""
                except Exception:
                    bio = ""

            # ---------- Recent 3 posts ----------
            try:
                hrefs = await page.locator('article a[href*="/p/"], article a[href*="/reel/"]').evaluate_all(
                    "els => Array.from(new Set(els.map(e => e.getAttribute('href'))))"
                )
                abs_urls: List[str] = []
                seen = set()
                for h in hrefs:
                    if not h:
                        continue
                    full = "https://www.instagram.com" + h if h.startswith("/") else h
                    m = POST_CODE_RE.search(full)
                    if not m:
                        continue
                    code = m.group(2)
                    if code in seen:
                        continue
                    seen.add(code)
                    abs_urls.append(full)
                abs_urls = abs_urls[:3]
                for pu in abs_urls:
                    posts_data.append(await _extract_post(ctx, pu))
            except Exception:
                pass

            await ctx.close()
            await browser.close()

        return {
            "ok": True,
            "username": username,
            "name": name or username,
            "bio": bio or "",
            "profile_url": url,
            "followers": followers,
            "following": following,
            "posts": posts,
            "posts_data": posts_data,
        }

    except PWTimeoutError as e:
        return {"ok": False, "error": f"timeout: {e}", "username": username, "profile_url": url}
    except Exception as e:
        return {"ok": False, "error": str(e) or e.__class__.__name__, "username": username, "profile_url": url}
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
