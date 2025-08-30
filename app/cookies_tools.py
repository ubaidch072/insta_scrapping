
import json, argparse, os, sys
from loguru import logger

def cookie_editor_to_storage_state(src_path: str, dst_path: str):
    with open(src_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    # Cookie-Editor format is a list of dicts
    storage = {"cookies": [], "origins": []}
    for c in cookies:
        # map fields
        storage['cookies'].append({
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain").lstrip("."),
            "path": c.get("path", "/"),
            "expires": c.get("expirationDate", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True),
            "sameSite": c.get("sameSite", "Lax")
        })
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(storage, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote Playwright storage to {dst_path} with {len(storage['cookies'])} cookies.")

def main():
    ap = argparse.ArgumentParser(description="Convert Cookie-Editor JSON to Playwright storage_state.json")
    ap.add_argument("--from", dest="src", required=True, help="Path to Cookie-Editor export JSON")
    ap.add_argument("--to", dest="dst", required=True, help="Path to write storage_state.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.dst) or ".", exist_ok=True)
    cookie_editor_to_storage_state(args.src, args.dst)

if __name__ == "__main__":
    main()
