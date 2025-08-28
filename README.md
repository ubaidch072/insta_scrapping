
# IG Scout (Starter)

A minimal, **working** Instagram profile scraper and query API built with Playwright.
**For educational use only.** Using this against Instagram may violate their Terms of Use.
Use it **only** on your own account / authorized data, at a low rate.

---

## What this starter gives you

- Playwright-based browser with saved auth (`storage_state.json`)
- Search by **display name** or direct **username**
- Extract: `username, full_name, bio, external_url, profile_pic_url, followers, following`
- Fetch **latest 3 posts**: `shortcode, caption, media_urls[], posted_at`
- CLI and optional FastAPI API

---

## Quickstart (Local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install
# Linux only:
playwright install-deps
```

### Get authenticated (choose one)

**Path A — Cookie Editor (manual export/import):**

1. In Chrome, install the extension **Cookie-Editor** (by `devpm`).  
2. Log in to Instagram at https://www.instagram.com/ and verify you are completely logged in (home feed visible).
3. Open Cookie-Editor while on instagram.com → **Export** cookies (include `.instagram.com`).
4. Save the JSON to `cookies/instagram_cookies.json` (create the folder if needed).
5. Convert to Playwright storage format:
   ```bash
   python -m app.cookies_tools --from cookies/instagram_cookies.json --to storage_state.json
   ```
6. Verify the file exists:
   ```bash
   ls -l storage_state.json
   ```

**Path B — One-time Login (recommended):**

1. Run the helper (a headed browser will open):
   ```bash
   python scripts/one_time_login.py
   ```
2. Manually log into Instagram, complete any 2FA or challenges.
3. Close the browser window. The script will save `storage_state.json` in project root.

> If auth expires later, simply re-run Path B to refresh **storage_state.json**.

---

## Try the CLI

- Search by name (it will pick the best match):
  ```bash
  python -m app.cli --query "zuck"
  ```
- Or go straight by username:
  ```bash
  python -m app.cli --username "zuck"
  ```
- Save output:
  ```bash
  python -m app.cli --username "zuck" --json out.json
  ```
- Optional debug screenshot:
  ```bash
  python -m app.cli --username "zuck" --screenshot debug.png
  ```

## Run the API (optional)

```bash
uvicorn app.webapi:app --host 0.0.0.0 --port 8080
# GET /profile?username=zuck
# GET /profile?query=mark zuckerberg
# GET /healthz
```

---

## VPS Deploy (Ubuntu 22.04)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv git
git clone <your-repo-or-scp-this-folder> /opt/ig-scout
cd /opt/ig-scout
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install
playwright install-deps
# copy storage_state.json to /opt/ig-scout (chmod 600)
uvicorn app.webapi:app --host 0.0.0.0 --port 8080
```

Optionally create a `systemd` service.

---

## Troubleshooting

- **Login wall / empty page** → Auth expired → run `scripts/one_time_login.py` again.
- **429 or Action blocked** → Slow down; wait 30–60 mins; reduce rate.
- **Selectors changed** → Update CSS fallbacks in `scrape.py`.
- **Private account** → You will get `PrivateAccountError` and no posts.

---

## Legal Notice

This code is provided for **educational purposes**. You are responsible for ensuring your use complies with platform terms and applicable laws.
