#!/usr/bin/env python3
"""
價格警報 + 每小時報價腳本

功能：
  - ETH 跌破 $2,000 即時通知
  - 每小時整點推播 TSLA PLTR RKLB JOBY OKLO RUN + ETH ADA 報價

用法：
  python3 price_alert.py          # 持續執行
  python3 price_alert.py --once   # 只執行一次（含小時報價）
"""

import sys
import time
import subprocess
import urllib.request
import json
from datetime import datetime

import yfinance as yf

# === 設定（在這裡新增/修改標的）===
STOCKS = ["TSLA", "PLTR", "RKLB", "JOBY", "OKLO", "RUN"]   # 美股，直接加代碼即可
PIONEX_STOCKS = [                                            # 派網代幣化美股（追蹤原股）
    {"name": "ORCLX", "symbol": "ORCL"},   # Oracle
    {"name": "OKLOX", "symbol": "OKLO"},   # 核能
    {"name": "ADBEX", "symbol": "ADBE"},   # Adobe
    {"name": "INTCX", "symbol": "INTC"},   # Intel
    {"name": "Visa",  "symbol": "V"},      # Visa
]
CRYPTO_ALERTS = [
    {"name": "ETH", "coin_id": "ethereum", "below": 2000},  # 跌破 $2,000 發出警報
    {"name": "ADA", "coin_id": "cardano"},                   # 只報價，無警報
    # {"name": "BTC", "coin_id": "bitcoin", "below": 80000}, # 範例：加 BTC 並設警報
]
CHECK_INTERVAL = 60   # 每分鐘跑一次主迴圈
triggered = set()


# ── 資料抓取 ──────────────────────────────────────────

def get_crypto_prices() -> dict:
    ids = ",".join(a["coin_id"] for a in CRYPTO_ALERTS)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "price-alert/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[錯誤] 加密貨幣價格失敗：{e}")
        return {}


def get_stock_prices() -> dict:
    """批次下載所有股票（單次請求，避免 rate-limit）。"""
    result = {}
    for attempt in range(3):
        try:
            data = yf.download(
                STOCKS, period="2d", interval="1d",
                group_by="ticker", auto_adjust=True,
                progress=False, threads=False,
            )
            for sym in STOCKS:
                try:
                    df = data[sym] if len(STOCKS) > 1 else data
                    price = float(df["Close"].dropna().iloc[-1])
                    prev  = float(df["Close"].dropna().iloc[-2])
                    result[sym] = {
                        "price": price,
                        "change_pct": (price - prev) / prev * 100,
                    }
                except Exception as e:
                    print(f"[錯誤] {sym}：{e}")
            return result
        except Exception as e:
            wait = 2 ** attempt
            print(f"[錯誤] 批次下載失敗（第 {attempt+1} 次）：{e}，{wait}s 後重試")
            time.sleep(wait)
    return result


# ── 通知 ─────────────────────────────────────────────

def notify(title: str, message: str):
    script = f'display notification "{message}" with title "{title}" sound name "Ping"'
    subprocess.run(["osascript", "-e", script])


# ── 每小時報價 ────────────────────────────────────────

def get_pionex_prices() -> dict:
    """抓派網代幣化美股（用原股代碼查詢）。"""
    symbols = [p["symbol"] for p in PIONEX_STOCKS]
    result = {}
    for attempt in range(3):
        try:
            data = yf.download(
                symbols, period="2d", interval="1d",
                group_by="ticker", auto_adjust=True,
                progress=False, threads=False,
            )
            for p in PIONEX_STOCKS:
                sym = p["symbol"]
                try:
                    df = data[sym] if len(symbols) > 1 else data
                    price = float(df["Close"].dropna().iloc[-1])
                    prev  = float(df["Close"].dropna().iloc[-2])
                    result[sym] = {
                        "price": price,
                        "change_pct": (price - prev) / prev * 100,
                    }
                except Exception as e:
                    print(f"[錯誤] {sym}：{e}")
            return result
        except Exception as e:
            wait = 2 ** attempt
            print(f"[錯誤] 派網批次下載失敗（第 {attempt+1} 次）：{e}，{wait}s 後重試")
            time.sleep(wait)
    return result


def hourly_report():
    now = datetime.now().strftime("%m/%d %H:%M")
    crypto = get_crypto_prices()
    stocks = get_stock_prices()
    pionex = get_pionex_prices()

    lines = []

    # 加密貨幣
    for a in CRYPTO_ALERTS:
        data = crypto.get(a["coin_id"], {})
        price = data.get("usd")
        chg = data.get("usd_24h_change")
        if price is not None:
            chg_str = f"{chg:+.1f}%" if chg is not None else ""
            lines.append(f"{a['name']} ${price:,.2f} {chg_str}")

    # 美股
    for sym in STOCKS:
        data = stocks.get(sym, {})
        price = data.get("price")
        chg = data.get("change_pct")
        if price is not None:
            chg_str = f"{chg:+.1f}%" if chg is not None else ""
            lines.append(f"{sym} ${price:.2f} {chg_str}")

    # 派網代幣化美股
    if any(pionex.values()):
        print(f"\n--- 派網持倉 ---")
        for p in PIONEX_STOCKS:
            data = pionex.get(p["symbol"], {})
            price = data.get("price")
            chg = data.get("change_pct")
            if price is not None:
                chg_str = f"{chg:+.1f}%" if chg is not None else ""
                print(f"  {p['name']} ({p['symbol']}) ${price:.2f} {chg_str}")

    if lines:
        body = "\n".join(lines)
        print(f"\n=== 整點報價 {now} ===")
        print(body)
        notify(f"整點報價 {now}", "  |  ".join(lines))


# ── ETH 警報 ──────────────────────────────────────────

def check_alerts():
    crypto = get_crypto_prices()
    now = datetime.now().strftime("%H:%M:%S")

    for alert in CRYPTO_ALERTS:
        cid = alert["coin_id"]
        name = alert["name"]
        data = crypto.get(cid, {})
        price = data.get("usd")
        if price is None:
            continue

        print(f"[{now}] {name}: ${price:,.2f}")

        if "below" in alert:
            key = f"{cid}_below_{alert['below']}"
            if price < alert["below"]:
                if key not in triggered:
                    triggered.add(key)
                    notify(f"{name} 價格警報 ⚠", f"{name} 跌破 ${alert['below']:,}，目前 ${price:,.2f}")
                    print(f"  ⚠ 通知已發送")
            else:
                triggered.discard(key)


# ── 主程式 ────────────────────────────────────────────

def main():
    once = "--once" in sys.argv
    print("ETH 跌破 $2,000 即時警報")
    print(f"每小時整點推播：{'、'.join(STOCKS)} + ETH ADA")
    print(f"{'單次執行' if once else '持續監控中...'}\n")

    last_hour = -1

    def run():
        nonlocal last_hour
        now = datetime.now()
        check_alerts()
        if now.hour != last_hour:
            last_hour = now.hour
            hourly_report()

    run()
    if once:
        return

    while True:
        time.sleep(CHECK_INTERVAL)
        run()


if __name__ == "__main__":
    main()
