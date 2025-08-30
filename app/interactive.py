# app/interactive.py
import re, time, json, datetime
from pathlib import Path
import argparse
from typing import Optional, Dict, Any, List
from playwright.sync_api import TimeoutError as PWTimeout
from .browser import open_browser
from .scrape import fetch_profile_via_api

RESERVED = {
    "p","reel","explore","direct","accounts","stories",
    "about","developer","legal","privacy","help","ads"
}

def _username_from_url(url: str) -> Optional[str]:
    m = re.match(r"^https?://(?:www\.)?instagram\.com/([^/?#]+)/?", url or "")
    if not m:
        return None
    u = m.group(1)
    return None if u in RESERVED else u

def _wait_for_profile(page, prev_username: Optional[str], timeout_s: int) -> str:
    deadline = time.time() + timeout_s
    seen = None
    while time.time() < deadline:
        try:
            url = page.url or ""
        except Exception:
            url = ""
        u = _username_from_url(url)
        if u and u != prev_username and u != seen:
            # give DOM a sec
            try: page.wait_for_load_state("domcontentloaded", timeout=3000)
            except Exception: pass
            return u
        seen = u
        try:
            page.wait_for_event("framenavigated", timeout=1000)
        except Exception:
            time.sleep(0.25)
    raise PWTimeout("Timed out waiting for a profile URL.")

def _save_txt(profile: Dict[str, Any]) -> str:
    def c(x): return "-" if (x is None or str(x).strip()=="") else str(x).strip()
    lines = [
        f"Username      : {c(profile.get('username'))}",
        f"Full name     : {c(profile.get('full_name'))}",
        f"Bio           : {c(profile.get('bio'))}",
        f"External URL  : {c(profile.get('external_url'))}",
        f"Followers     : {c(profile.get('followers'))}",
        f"Following     : {c(profile.get('following'))}",
        f"Profile Photo : {c(profile.get('profile_pic_url'))}",
        "",
        "Latest posts:"
    ]
    posts = profile.get("posts") or []
    if not posts:
        lines.append("  (none)")
    else:
        for i, p in enumerate(posts, 1):
            caption = (p.get("caption") or "").replace("\n"," ").strip()
            if len(caption) > 180: caption = caption[:177]+"..."
            lines += [
                f"  {i}. Shortcode : {c(p.get('shortcode'))}",
                f"     Date      : {c(p.get('posted_at'))}",
                f"     Caption   : {caption}",
            ]
            mus = p.get("media_urls") or []
            if mus:
                lines.append(f"     Media URLs ({len(mus)}):")
                for mu in mus[:5]: lines.append(f"       - {mu}")
                if len(mus)>5: lines.append(f"       ... +{len(mus)-5} more")
            if p.get('screenshot_path'):
                lines.append(f"     Screenshot: {p['screenshot_path']}")
            lines.append("")
    return "\n".join(lines).rstrip()+"\n"

def _screenshot_posts(ctx, username: str, posts: List[Dict[str,Any]], max_posts: int, shots_dir: Path):
    shots_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for p in posts:
        if done >= max_posts: break
        sc = p.get("shortcode")
        if not sc: continue
        url = f"https://www.instagram.com/p/{sc}/"
        try:
            newp = ctx.new_page()
            newp.goto(url, wait_until="domcontentloaded", timeout=60_000)
            # small settle wait
            try: newp.wait_for_load_state("networkidle", timeout=5000)
            except Exception: pass
            out = shots_dir / f"{username}_{sc}.png"
            newp.screenshot(path=str(out), full_page=True)
            p["screenshot_path"] = str(out)
            newp.close()
            done += 1
        except Exception:
            try: newp.close()
            except Exception: pass

def main():
    ap = argparse.ArgumentParser("Interactive IG scraper (search any public profile and it will auto-save).")
    ap.add_argument("--max-posts", type=int, default=3)
    ap.add_argument("--save-dir", default="out")
    ap.add_argument("--save-txt", action="store_true")
    ap.add_argument("--screenshot", action="store_true", help="profile full-page screenshot")
    ap.add_argument("--post-screenshots", action="store_true")
    ap.add_argument("--profile-wait", type=int, default=300)
    ap.add_argument("--username", required=False, help="Optional: start directly on this username")
    args = ap.parse_args()

    out_dir = Path(args.save_dir); out_dir.mkdir(parents=True, exist_ok=True)

    print("[interactive] Launching browser (headed). Use it like normal Instagram.")
    p, b, ctx, page = open_browser("storage_state.json", headless=False)

    try:
        start_url = f"https://www.instagram.com/{args.username}/" if args.username else "https://www.instagram.com/"
        page.goto(start_url, wait_until="domcontentloaded", timeout=60_000)

        print(
            "\n=== Interactive Mode ===\n"
            "â€¢ IG window open hai. Search bar se koi bhi PUBLIC profile open karo.\n"
            "â€¢ Jaise hi profile load hogi, yeh tool details + last posts ki screenshots save kar dega.\n"
            "â€¢ Phir next profile open karoâ€”yeh loop chalta rahega. (CTRL+C to exit)\n"
        )

        last = None
        while True:
            user = _wait_for_profile(page, last, args.profile_wait)
            print(f"[interactive] Detected profile: @{user}. Fetching details...")
            # Ensure canonical URL (sometimes search opens modal/redirect)
            try:
                page.goto(f"https://www.instagram.com/{user}/", wait_until="domcontentloaded", timeout=60_000)
            except Exception:
                pass

            # 1) Profile JSON via web API (stable)
            prof = fetch_profile_via_api(ctx, user) or {"username": user, "posts": []}

            # 2) Save JSON/TXT
            ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            base = out_dir / f"{user}_{ts}"
            (base.with_suffix(".json")).write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
            if args.save_txt:
                (base.with_suffix(".txt")).write_text(_screenshot_friendly_txt(prof := prof.copy()), encoding="utf-8")

            # 3) Profile screenshot (optional)
            if args.screenshot:
                shot = out_dir / f"{user}_{ts}_profile.png"
                try:
                    page.screenshot(path=str(shot), full_page=True)
                except Exception: pass

            # 4) Post screenshots (optional)
            if args.post_screenshots and prof.get("posts"):
                shots_dir = out_dir / f"{user}_{ts}_posts"
                _screenshot_posts(ctx, user, prof["posts"], args.max_posts, shots_dir)
                # update JSON with screenshot paths
                (base.with_suffix(".json")).write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")

            print(f"[interactive] Saved to: {out_dir}  (profile: {user})")
            print("[interactive] Open next profile in the IG windowâ€¦")
            last = user

    except KeyboardInterrupt:
        print("\n[interactive] Exiting. Bye!")
    finally:
        try: ctx.close()
        except Exception: pass
        try: b.close()
        except Exception: pass
        try: p.stop()
        except Exception: pass

def _screenshot_friendly_txt(profile: Dict[str,Any]) -> str:
    # same as _save_txt but called below (kept separate to avoid forward-ref hassle)
    def c(x): return "-" if (x is None or str(x).strip()=="") else str(x).strip()
    lines = [
        f"Username      : {c(profile.get('username'))}",
        f"Full name     : {c(profile.get('full_name'))}",
        f"Bio           : {c(profile.get('bio'))}",
        f"External URL  : {c(profile.get('external_url'))}",
        f"Followers     : {c(profile.get('followers'))}",
        f"Following     : {c(profile.get('following'))}",
        f"Profile Photo : {c(profile.get('profile_pic_url'))}",
        "",
        "Latest posts:"
    ]
    posts = profile.get("posts") or []
    if not posts:
        lines.append("  (none)")
    else:
        for i, p in enumerate(posts, 1):
            cap = (p.get("caption") or "").replace("\n"," ").strip()
            if len(cap) > 180: cap = cap[:177]+"..."
            lines += [
                f"  {i}. Shortcode : {c(p.get('shortcode'))}",
                f"     Date      : {c(p.get('posted_at'))}",
                f"     Caption   : {cap}",
            ]
            if p.get("screenshot_path"):
                lines.append(f"     Screenshot: {p['screenshot_path']}")
            lines.append("")
    return "\n".join(lines).rstrip()+"\n"

if __name__ == "__main__":
    main()
