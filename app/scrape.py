from datetime import datetime, timezone

def _parse_ts(ts):
    try:
        return datetime.utcfromtimestamp(int(ts)).replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return None

def fetch_profile_via_api(ctx, username: str):
    if not username:
        return {}
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {"x-ig-app-id": "936619743392459"}
    resp = ctx.request.get(url, headers=headers, timeout=30000)
    status = getattr(resp, "status", None) or getattr(resp, "status_code", None)
    if status != 200:
        return {}
    data = resp.json()
    user = data.get("data", {}).get("user")
    if not user:
        return {}
    out = {
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "bio": (user.get("biography") or "").strip(),
        "external_url": user.get("external_url"),
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
        "followers": user.get("edge_followed_by", {}).get("count"),
        "following": user.get("edge_follow", {}).get("count"),
        "posts": [],
    }
    edges = user.get("edge_owner_to_timeline_media", {}).get("edges", []) or []
    for edge in edges[:3]:
        node = edge.get("node", {})
        caption = ""
        cap_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        if cap_edges:
            caption = cap_edges[0].get("node", {}).get("text", "") or ""
        media_urls = []
        if node.get("display_url"):
            media_urls.append(node["display_url"])
        if node.get("video_url"):
            media_urls.append(node["video_url"])
        if node.get("__typename") == "GraphSidecar":
            sc = node.get("edge_sidecar_to_children", {}).get("edges", []) or []
            for e in sc:
                n = e.get("node", {})
                if n.get("display_url"):
                    media_urls.append(n["display_url"])
                if n.get("video_url"):
                    media_urls.append(n["video_url"])
        out["posts"].append({
            "shortcode": node.get("shortcode"),
            "caption": caption,
            "media_urls": media_urls,
            "posted_at": _parse_ts(node.get("taken_at_timestamp")),
        })
    return out
