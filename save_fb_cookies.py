"""
儲存 FB 登入 Cookies
執行後會開啟瀏覽器，登入 FB 後按 Enter，自動儲存 cookies
"""

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.facebook.com/")

    print("\n✅ 瀏覽器已開啟，請在瀏覽器中登入你的 Facebook 帳號")
    print("登入完成後回到這個視窗，按 Enter 繼續...\n")
    input()

    cookies = context.cookies()
    with open("fb_cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)

    print(f"✅ 已儲存 {len(cookies)} 個 cookies 到 fb_cookies.json")
    browser.close()
