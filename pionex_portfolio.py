#!/usr/bin/env python3
"""
派網持倉分析器
用法：python3 pionex_portfolio.py
"""

import hmac
import hashlib
import time
import urllib.request
import urllib.parse
import json

# === API 設定 ===
API_KEY    = "7spnSfdT5zFwADvjT8bNfXrqMoFgyEzZedSM95oGSYECHeB5kqLUToawuPZMMYbrPS"
API_SECRET = "KstZhblHWw3ErU1exq46qGVNHHWYo9Rnij50pzZzExzUP4x3NHtCY8QAIe3jdxSv"
BASE_URL   = "https://api.pionex.com"

# === 派網代幣對應原股（用來查現價）===
PIONEX_MAP = {
    "ORCLX": "ORCL",
    "OKLOX": "OKLO",
    "ADBEX": "ADBE",
    "INTCX": "INTC",
    "VISA":  "V",
}


def api_get(path: str, params: dict = {}) -> dict:
    timestamp = str(int(time.time() * 1000))
    p = params.copy()
    p["timestamp"] = timestamp
    query = urllib.parse.urlencode(sorted(p.items()))
    message = "GET" + path + "?" + query
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    url = f"{BASE_URL}{path}?{query}"
    req = urllib.request.Request(url, headers={
        "PIONEX-KEY":       API_KEY,
        "PIONEX-SIGNATURE": signature,
        "PIONEX-TIMESTAMP": timestamp,
        "User-Agent":       "Mozilla/5.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[錯誤] HTTP {e.code}：{body}")
        return {}
    except Exception as e:
        print(f"[錯誤] {e}")
        return {}


def get_balances() -> list:
    """取得帳戶所有幣種餘額（過濾掉零值）"""
    data = api_get("/api/v1/account/balances")
    if not data.get("result"):
        print(f"[錯誤] {data}")
        return []
    balances = data.get("data", {}).get("balances", [])
    return [b for b in balances if float(b.get("free", 0)) + float(b.get("frozen", 0)) > 0.0001]


def get_ticker_price(symbol: str) -> float:
    """取得派網某交易對現價，例如 ORCL/USDT"""
    data = api_get("/api/v1/market/tickers", {"symbol": f"{symbol}_USDT"})
    try:
        return float(data["data"]["tickers"][0]["close"])
    except Exception:
        return 0.0


def main():
    print("=" * 45)
    print("  派網帳戶持倉分析")
    print("=" * 45)

    balances = get_balances()
    if not balances:
        print("無法取得持倉或帳戶是空的")
        return

    total_usdt = 0.0
    rows = []

    for b in balances:
        coin  = b["coin"]
        free  = float(b.get("free", 0))
        frozen = float(b.get("frozen", 0))
        amount = free + frozen

        if coin == "USDT":
            rows.append({"coin": "USDT", "amount": amount, "price": 1.0, "value": amount})
            total_usdt += amount
            continue

        # 嘗試取現價
        price = get_ticker_price(coin)
        value = amount * price if price else 0.0
        total_usdt += value

        # 對應原股名稱
        display = f"{coin}"
        if coin.upper() in PIONEX_MAP:
            display = f"{coin} ({PIONEX_MAP[coin.upper()]})"

        rows.append({"coin": display, "amount": amount, "price": price, "value": value})

    # 顯示
    print(f"{'標的':<20} {'數量':>12} {'現價(USDT)':>12} {'估值(USDT)':>12}")
    print("-" * 58)
    for r in sorted(rows, key=lambda x: -x["value"]):
        print(f"{r['coin']:<20} {r['amount']:>12.4f} {r['price']:>12.4f} {r['value']:>12.2f}")
    print("-" * 58)
    print(f"{'總估值':<20} {'':>12} {'':>12} {total_usdt:>12.2f} USDT")

    # 換算台幣（USDT ≈ 32.5 NTD，可自行調整）
    ntd_rate = 32.5
    print(f"{'約合台幣':<20} {'':>12} {'':>12} {total_usdt * ntd_rate:>11.0f} NTD")
    print("=" * 45)


if __name__ == "__main__":
    main()
