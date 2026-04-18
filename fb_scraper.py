"""
FB Marketplace 撿漏爬蟲
- 每次執行掃描所有 config.json 中的目標
- 找出低於行情 60% 的標的，寫入 deals.json，並發 Line 通知
- 設計在 GitHub Actions (ubuntu-latest headless) 環境執行
- 本機也可執行，會嘗試載入 fb_cookies.json 維持登入狀態

使用方式：
  python fb_scraper.py
"""

import json
import os
import random
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# ─── 設定 ────────────────────────────────────────────────────────────────────

CONFIG_FILE = Path("config.json")
DEALS_FILE = Path("deals.json")
COOKIES_FILE = Path("fb_cookies.json")

EXCLUDE_KEYWORDS = [
    # 通用排除
    "故障", "零件", "求收", "徵收", "求購", "收購", "損壞", "故障品", "拆機",
    "誠徵", "配件", "保護套", "矽膠套", "收納包", "遙控模組", "冷靴", "轉接",
    # 吉他配件（非本體）
    "吉他弦", "琴弦", "琴袋", "琴架", "背帶", "效果器", "踏板", "拾音器",
    "琴頸", "指板", "琴橋", "顫音", "弦鈕", "民謠吉他", "古典吉他", "木吉他",
    "烏克麗麗", "Bass", "貝斯", "教學", "課程",
    # 相機配件（非本體）
    "電池", "充電器", "記憶卡", "相機包", "鏡頭蓋", "UV鏡", "快門線",
]
MIN_PRICE = 1000       # 低於此值視為無效價格（釣魚/免費）
MAX_PRICE = 200000     # 高於此值可能是誤抓到非價格數字
# 每個 item 最多回報幾筆（避免 Line 訊息爆炸）
MAX_DEALS_PER_ITEM = 5
PAGE_WAIT_MS = 5000    # 等待頁面渲染毫秒數

# 台灣時區
TZ_TW = timezone(timedelta(hours=8))


# ─── 工具函式 ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_deals(deals: list, scan_time: str):
    data = {"last_scan": scan_time, "deals": deals}
    with open(DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[deals.json] 寫入 {len(deals)} 筆標的")


def load_cookies() -> list | None:
    # 優先從環境變數讀取（GitHub Actions 注入）
    env_cookies = os.getenv("FB_COOKIES", "").strip()
    if env_cookies:
        try:
            return json.loads(env_cookies)
        except Exception:
            pass
    # 其次讀本機檔案
    if COOKIES_FILE.exists():
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def extract_price(text: str) -> int | None:
    """從文字中提取價格數字，例如 'NT$12,500' → 12500"""
    # 移除常見符號後取純數字
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    price = int(digits)
    if MIN_PRICE <= price <= MAX_PRICE:
        return price
    return None


def is_excluded(title: str) -> bool:
    """標題包含排除關鍵字時回傳 True"""
    return any(kw in title for kw in EXCLUDE_KEYWORDS)


# ─── 爬蟲核心 ─────────────────────────────────────────────────────────────────

def scrape_fb_marketplace(page, keyword: str, target_price: float, market_price: float = 0) -> list[dict]:
    """
    搜尋 FB Marketplace 台北地區，回傳符合條件的標的清單
    每筆格式：{"title": str, "price": int, "link": str}
    market_price 用於過濾明顯異常的假價格（低於行情 10% 的直接跳過）
    """
    min_price = market_price * 0.10 if market_price else MIN_PRICE
    found = []
    url = f"https://www.facebook.com/marketplace/taipei/search?query={keyword}&sortBy=creation_time_descend"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(PAGE_WAIT_MS)

        # 嘗試滾動以載入更多結果
        page.evaluate("window.scrollBy(0, 600)")
        page.wait_for_timeout(2000)

        # 抓取所有商品卡片（FB 的商品容器通常是 a[href*="/marketplace/item/"]）
        items = page.query_selector_all('a[href*="/marketplace/item/"]')
        print(f"  找到 {len(items)} 個商品卡片")

        seen_links = set()
        for item in items:
            try:
                # 取得連結
                href = item.get_attribute("href") or ""
                link = f"https://www.facebook.com{href}" if href.startswith("/") else href

                # 去重：同一個商品只處理一次
                link_id = href.split("?")[0]
                if link_id in seen_links:
                    continue
                seen_links.add(link_id)

                # 取得整塊文字（包含標題和價格）
                text = item.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                # FB 卡片結構：通常 價格在前，標題在後
                # 策略：找第一個含 $ 的行為價格，第一個不含 $ 且非純數字的行為標題
                title = ""
                price = None
                for line in lines:
                    has_price_symbol = "$" in line
                    if has_price_symbol and not price:
                        price = extract_price(line)
                    elif not title and not has_price_symbol and not re.match(r"^\d+$", line):
                        title = line

                # fallback：若以上方法沒取到標題，用第一行
                if not title:
                    title = lines[0]

                # 排除黑名單關鍵字
                if is_excluded(title):
                    continue

                # 若還沒找到價格，從所有行補找
                if not price:
                    for line in lines:
                        price = extract_price(line)
                        if price:
                            break

                if not price:
                    continue

                # 價格合理性：至少是行情的 10%，排除 $1/$100 等釣魚促銷
                if price < min_price:
                    continue

                # 撿漏判斷
                if price <= target_price:
                    found.append({
                        "title": title,
                        "price": price,
                        "link": link
                    })
                    print(f"  🔥 撿漏！{title[:25]} NT${price:,}（觸發價 NT${int(target_price):,}）")

            except Exception:
                continue

    except PWTimeout:
        print(f"  ⚠️ 頁面載入超時：{keyword}")
    except Exception as e:
        print(f"  ❌ 爬蟲錯誤：{e}")

    return found


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def run_scan() -> list[dict]:
    """執行完整掃描，回傳所有發現的標的"""
    config = load_config()
    threshold_ratio = config.get("threshold_ratio", 0.6)
    all_deals = []

    print(f"\n{'='*50}")
    print(f"FB Marketplace 撿漏掃描 — {datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M')}")
    print(f"觸發門檻：行情 × {threshold_ratio:.0%}")
    print(f"{'='*50}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
        )

        # 載入已儲存的 FB 登入 cookies（若存在）
        cookies = load_cookies()
        if cookies:
            context.add_cookies(cookies)
            print("✅ 已載入 FB 登入 cookies\n")
        else:
            print("⚠️ 未找到 fb_cookies.json，以訪客模式嘗試（部分功能受限）\n")

        page = context.new_page()

        for target in config["targets"]:
            name = target["name"]
            market_price = target["market_price"]
            trigger_price = market_price * threshold_ratio
            keywords = target.get("keywords", [name])

            print(f"🔍 掃描：{name}（行情 NT${market_price:,}，觸發價 NT${int(trigger_price):,}）")

            item_deals = []
            seen_item_links = set()
            for kw in keywords:
                hits = scrape_fb_marketplace(page, kw, trigger_price, market_price)
                for h in hits:
                    link_id = h["link"].split("?")[0]
                    if link_id in seen_item_links:
                        continue
                    seen_item_links.add(link_id)
                    h["item"] = name
                    h["market_price"] = market_price
                    h["discount_pct"] = round((1 - h["price"] / market_price) * 100, 1)
                    item_deals.append(h)

                # 隨機延遲避免被封鎖
                time.sleep(random.uniform(3, 6))

            # 去重後按價格排序，只保留最便宜的幾筆
            item_deals.sort(key=lambda x: x["price"])
            item_deals = item_deals[:MAX_DEALS_PER_ITEM]

            if item_deals:
                print(f"  → 過濾後保留 {len(item_deals)} 筆最低價標的\n")
                all_deals.extend(item_deals)
            else:
                print(f"  沒有發現低價標的\n")

        page.close()
        browser.close()

    return all_deals


def notify_deals(deals: list, config: dict):
    """Line Notify 通知（無 token 時靜默跳過）"""
    token = os.getenv("LINE_NOTIFY_TOKEN", "").strip()
    if not token:
        try:
            from line_notify import get_token
            token = get_token() or ""
        except Exception:
            pass
    if not token or token.startswith("PASTE_YOUR"):
        print("\n[Line Notify] Token 未設定，跳過通知")
        return

    msg = f"\n🚨 Jim 撿漏警報！發現 {len(deals)} 個好物"
    for d in deals[:5]:
        msg += (
            f"\n\n📦 {d['item']}"
            f"\n💰 NT${d['price']:,}（省 {d['discount_pct']}%）"
            f"\n📝 {d['title'][:30]}"
            f"\n🔗 {d['link']}"
        )

    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({"message": msg}).encode()
        req  = urllib.request.Request(
            "https://notify-api.line.me/api/notify", data=data,
            headers={"Authorization": f"Bearer {token}"}
        )
        urllib.request.urlopen(req, timeout=10)
        print("✅ Line 通知已發送")
    except Exception as e:
        print(f"⚠️  Line 通知失敗: {e}")


if __name__ == "__main__":
    scan_time = datetime.now(TZ_TW).isoformat()
    deals = run_scan()

    # 寫入結果
    save_deals(deals, scan_time)

    if deals:
        config = load_config()
        notify_deals(deals, config)
        print(f"\n✅ 本次掃描發現 {len(deals)} 個低於行情 60% 的標的！")
    else:
        print("\n✅ 掃描完成，目前市場價格正常，未發現撿漏標的。")
