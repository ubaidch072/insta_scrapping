from playwright.sync_api import sync_playwright
STATE = "storage_state.json"
def main():
    print("[login] starting playwright...")
    with sync_playwright() as p:
        print("[login] launching chromium (headed, safe flags)...")
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-features=IsolateOrigins,site-per-process,RendererCodeIntegrity",
                "--no-sandbox",
            ],
        )
        print("[login] creating fresh context...")
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.set_default_timeout(45000)
        page.set_default_navigation_timeout(60000)
        print("\n[login] A blank tab is open.")
        print("[login] Click the address bar, paste this URL, press Enter:")
        print("[login]   https://www.instagram.com/accounts/login/\n")
        input("[login] After the login page appears, press ENTER here to continue... ")
        print("[login] Log in fully (username/password + any 2FA/challenges).")
        print("[login] Dismiss 'Save info' / 'Turn on notifications' with 'Not now'.")
        input("[login] When your HOME FEED or PROFILE is visible, press ENTER to save... ")
        print(f"[login] saving state to {STATE} ...")
        ctx.storage_state(path=STATE)
        print("[login] saved. You can close the browser window.")
        browser.close()
        print("[login] done.")
if __name__ == "__main__":
    main()
