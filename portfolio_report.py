#!/usr/bin/env python3
"""
每日投資組合分析報告
自動整合：派網 + Firstrade + 國泰複委託 + 國泰台股
每天早上 9:00 自動執行
"""

import hmac, hashlib, time, urllib.request, urllib.parse, json
import subprocess, glob, os
from datetime import datetime
import openpyxl

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "portfolio_history.csv")

def log_history(total_twd: float):
    now_hour = datetime.now().strftime("%Y-%m-%d %H:00")
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            f.write("時間,總市值(TWD)\n")
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    if lines and lines[-1].startswith(now_hour):
        return
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{now_hour},{total_twd:.0f}\n")

# ── 設定 ──────────────────────────────────────────────
PIONEX_KEY    = "7spnSfdT5zFwADvjT8bNfXrqMoFgyEzZedSM95oGSYECHeB5kqLUToawuPZMMYbrPS"
PIONEX_SECRET = "KstZhblHWw3ErU1exq46qGVNHHWYo9Rnij50pzZzExzUP4x3NHtCY8QAIe3jdxSv"
FIRSTRADE_DIR = os.path.expanduser("~/Downloads")
REPORT_DIR    = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-jay0916746661@gmail.com/My Drive/Claude筆記/股票")
NTD_RATE      = 32.5  # USDT → 台幣匯率，可手動調整

# 派網代幣化股票對應原股
PIONEX_MAP = {
    "ORCLX": "ORCL", "OKLOX": "OKLO", "ADBEX": "ADBE",
    "INTCX": "INTC", "APLDX": "APLD", "METAX": "META",
    "MSFTX": "MSFT",
    "SMCIX": "SMCI",
}

# 派網加密貨幣（用 CoinGecko）
CRYPTO_IDS = {
    "ETH":  "ethereum",
    "ADA":  "cardano",
    "ARKM": "arkham",
}

# 國泰台股零股（代號, 名稱, 零股數, 成本均價TWD）
CATHAY_TW = [
    {"code": "00763U", "name": "街口道瓊", "qty": 6,   "cost": 29.83},
    {"code": "1303",   "name": "南亞",     "qty": 3,   "cost": 81.00},
    {"code": "1326",   "name": "台化",     "qty": 6,   "cost": 48.50},
    {"code": "2027",   "name": "大成鋼",   "qty": 7,   "cost": 38.43},
    {"code": "2317",   "name": "鴻海",     "qty": 1,   "cost": 205.22},
    {"code": "2344",   "name": "華邦電",   "qty": 1,   "cost": 95.80},
    {"code": "3481",   "name": "群創",     "qty": 100, "cost": 25.45},
    {"code": "6148",   "name": "正文科技", "qty": 34,  "cost": 33.63},
]

# 國泰複委託持倉（手動維護）
CATHAY_HOLDINGS = [
    {"sym": "JOBY", "qty": 11,       "cost": 8.570909},
    {"sym": "LULU", "qty": 0.60693,  "cost": 164.895457},
    {"sym": "MSFT", "qty": 0.25639,  "cost": 390.342837},
    {"sym": "NKE",  "qty": 1,        "cost": 43.320000},
    {"sym": "ONDS", "qty": 3,        "cost": 9.296667},
    {"sym": "RXRX", "qty": 30,       "cost": 3.351667},
    {"sym": "TSLA", "qty": 0.28417,  "cost": 352.183552},
]


# ── 派網 API ──────────────────────────────────────────
def pionex_get(path, params={}):
    ts = str(int(time.time() * 1000))
    p = {**params, "timestamp": ts}
    q = urllib.parse.urlencode(sorted(p.items()))
    sig = hmac.new(PIONEX_SECRET.encode(), f"GET{path}?{q}".encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        f"https://api.pionex.com{path}?{q}",
        headers={"PIONEX-KEY": PIONEX_KEY, "PIONEX-SIGNATURE": sig,
                 "PIONEX-TIMESTAMP": ts, "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {}

def get_pionex_positions():
    data = pionex_get("/api/v1/account/balances")
    balances = data.get("data", {}).get("balances", [])
    result = []
    for b in balances:
        coin = b["coin"]
        qty = float(b.get("free", 0)) + float(b.get("frozen", 0))
        if qty < 0.0001: continue
        result.append({"coin": coin, "qty": qty})
    return result


# ── Yahoo Finance v8 API（避免 yfinance rate limit）────
def get_stock_quote(sym):
    """回傳 {price, prev_close, change_pct}"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        valid = [c for c in closes if c is not None]
        price = valid[-1] if valid else 0.0
        prev  = valid[-2] if len(valid) >= 2 else price
        chg   = (price - prev) / prev * 100 if prev else 0.0
        return {"price": float(price), "prev": float(prev), "change_pct": chg}
    except Exception:
        return {"price": 0.0, "prev": 0.0, "change_pct": 0.0}

def get_prices(symbols):
    result = {}
    for sym in symbols:
        result[sym] = get_stock_quote(sym)
        time.sleep(0.3)
    return result


# ── CoinGecko 加密貨幣現價 ────────────────────────────
def get_crypto_prices():
    ids = ",".join(CRYPTO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "portfolio/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result = {}
        for coin, cid in CRYPTO_IDS.items():
            result[coin] = data.get(cid, {}).get("usd", 0.0)
        return result
    except Exception:
        return {coin: 0.0 for coin in CRYPTO_IDS}


# ── Firstrade Excel（只讀持倉量和成本，價格用即時 API）─
def get_firstrade_holdings():
    files = sorted(glob.glob(f"{FIRSTRADE_DIR}/*positions*.xlsx"), key=os.path.getmtime, reverse=True)
    if not files:
        print("[警告] 找不到 Firstrade xlsx 檔案")
        return []
    wb = openpyxl.load_workbook(files[0])
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows: return []
    header = rows[0]
    idx = {h: i for i, h in enumerate(header) if h}
    result = []
    for row in rows[1:]:
        if not row[0]: continue
        try:
            qty  = float(row[idx.get("股數", 1)] or 0)
            cost = float(row[idx.get("成本", 18)] or 0)
            if qty < 0.0001: continue
            result.append({
                "symbol": str(row[idx.get("代號", 0)]).strip(),
                "qty": qty,
                "cost": cost,
            })
        except: continue
    return result


# ── 通知 ─────────────────────────────────────────────
def notify(title, msg):
    subprocess.run(["osascript", "-e",
        f'display notification "{msg}" with title "{title}" sound name "Glass"'])


# ── 主報告 ────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 投資組合日報  {now}", "=" * 55]

    # ── 抓所有需要的股票現價（批次，含今日漲跌）──
    firstrade_holdings = get_firstrade_holdings()
    ft_syms     = [h["symbol"] for h in firstrade_holdings]
    cathay_syms = [h["sym"] for h in CATHAY_HOLDINGS]
    pionex_raw  = get_pionex_positions()
    pionex_stock_syms = list(set(PIONEX_MAP[p["coin"]] for p in pionex_raw if p["coin"] in PIONEX_MAP))
    all_stock_syms = list(set(ft_syms + cathay_syms + pionex_stock_syms))
    quotes = get_prices(all_stock_syms)

    # 加密貨幣現價
    crypto_prices = get_crypto_prices()

    # ── 派網 ──
    lines.append("\n【派網現貨】")
    pionex_total = 0.0
    for p in sorted(pionex_raw, key=lambda x: x["coin"]):
        coin, qty = p["coin"], p["qty"]
        if coin == "USDT":
            val_usd = qty
            chg_str = ""
        elif coin in PIONEX_MAP:
            q = quotes.get(PIONEX_MAP[coin], {})
            price = q.get("price", 0)
            val_usd = qty * price
            chg = q.get("change_pct", 0)
            chg_str = f" ({chg:+.1f}%)" if price else ""
        elif coin in crypto_prices:
            val_usd = qty * crypto_prices[coin]
            chg_str = ""
        else:
            val_usd = 0
            chg_str = ""
        val_ntd = val_usd * NTD_RATE
        pionex_total += val_ntd
        if val_ntd > 1:
            lines.append(f"  {coin:<10} {qty:>10.4f}   NT${val_ntd:>8.0f}{chg_str}")

    lines.append(f"  {'派網小計':<10}              NT${pionex_total:>8.0f}")

    # ── Firstrade（即時價格）──
    lines.append(f"\n【Firstrade 美股】")
    ft_rows = []
    for h in firstrade_holdings:
        q = quotes.get(h["symbol"], {})
        price    = q.get("price", 0.0)
        chg_pct  = q.get("change_pct", 0.0)
        value    = h["qty"] * price
        cost     = h["cost"]
        gain     = value - cost
        gain_pct = (gain / cost * 100) if cost > 0 else 0
        today_gain = h["qty"] * (price - q.get("prev", price))
        ft_rows.append({**h, "price": price, "value": value, "gain": gain,
                        "gain_pct": gain_pct, "today_gain": today_gain, "chg_pct": chg_pct})

    ft_total_value = sum(r["value"] for r in ft_rows)
    ft_total_cost  = sum(r["cost"]  for r in ft_rows)
    ft_total_gain  = sum(r["gain"]  for r in ft_rows)
    ft_today_gain  = sum(r["today_gain"] for r in ft_rows)

    for r in sorted(ft_rows, key=lambda x: -abs(x["today_gain"])):
        if r["value"] < 0.5: continue
        g    = f"{r['gain']:+.2f}"
        pct  = f"{r['gain_pct']:+.1f}%"
        td   = f"今日{r['today_gain']:+.2f}({r['chg_pct']:+.1f}%)"
        lines.append(f"  {r['symbol']:<6} ${r['value']:>7.2f}  損益{g}({pct})  {td}")

    lines.append(f"  {'Firstrade小計':<10} ${ft_total_value:.2f}  損益${ft_total_gain:+.2f}  今日${ft_today_gain:+.2f}")

    # ── 國泰複委託（即時價格）──
    lines.append(f"\n【國泰複委託】")
    cath_rows = []
    for h in CATHAY_HOLDINGS:
        q = quotes.get(h["sym"], {})
        price    = q.get("price", 0.0)
        chg_pct  = q.get("change_pct", 0.0)
        value    = h["qty"] * price
        cost     = h["qty"] * h["cost"]
        gain     = value - cost
        gain_pct = (gain / cost * 100) if cost > 0 else 0
        today_gain = h["qty"] * (price - q.get("prev", price))
        cath_rows.append({**h, "price": price, "value": value, "cost": cost,
                          "gain": gain, "gain_pct": gain_pct, "today_gain": today_gain, "chg_pct": chg_pct})

    cathay_total_value = sum(r["value"] for r in cath_rows)
    cathay_total_cost  = sum(r["cost"]  for r in cath_rows)
    cathay_total_gain  = cathay_total_value - cathay_total_cost
    cathay_today_gain  = sum(r["today_gain"] for r in cath_rows)

    for r in sorted(cath_rows, key=lambda x: -abs(x["today_gain"])):
        if r["value"] < 0.01: continue
        g   = f"{r['gain']:+.2f}"
        pct = f"{r['gain_pct']:+.1f}%"
        td  = f"今日{r['today_gain']:+.2f}({r['chg_pct']:+.1f}%)"
        lines.append(f"  {r['sym']:<6} ${r['value']:>7.2f}  損益{g}({pct})  {td}")

    cathay_gain_pct = (cathay_total_gain / cathay_total_cost * 100) if cathay_total_cost > 0 else 0
    lines.append(f"  {'國泰小計':<10} ${cathay_total_value:.2f}  損益${cathay_total_gain:+.2f}({cathay_gain_pct:+.1f}%)  今日${cathay_today_gain:+.2f}")

    # ── 國泰台股 ──
    tw_syms = [h["code"] + ".TW" for h in CATHAY_TW]
    tw_prices = get_prices(tw_syms)  # 台股用 .TW 查詢

    lines.append(f"\n【國泰台股零股】")
    tw_total_value = 0.0
    tw_total_cost  = 0.0
    tw_today       = 0.0
    for h in CATHAY_TW:
        sym = h["code"] + ".TW"
        q = tw_prices.get(sym, {})
        price = q.get("price", 0.0)
        chg_pct = q.get("change_pct", 0.0)
        value = h["qty"] * price
        cost  = h["qty"] * h["cost"]
        gain  = value - cost
        gain_pct = gain / cost * 100 if cost > 0 else 0
        today = h["qty"] * (price - q.get("prev", price))
        tw_total_value += value
        tw_total_cost  += cost
        tw_today       += today
        if value > 0:
            lines.append(f"  {h['code']} {h['name']:<6} {h['qty']:>4}股  "
                         f"NT${value:>6.0f}  損益{gain:+.0f}({gain_pct:+.1f}%)  今日NT${today:+.0f}({chg_pct:+.1f}%)")
    tw_gain = tw_total_value - tw_total_cost
    tw_gain_pct = tw_gain / tw_total_cost * 100 if tw_total_cost > 0 else 0
    lines.append(f"  {'台股小計':<10} NT${tw_total_value:.0f}  "
                 f"損益NT${tw_gain:+.0f}({tw_gain_pct:+.1f}%)  今日NT${tw_today:+.0f}")

    # ── 總計 ──
    ft_ntd      = ft_total_value * NTD_RATE
    cathay_ntd  = cathay_total_value * NTD_RATE
    total_ntd   = pionex_total + ft_ntd + cathay_ntd + tw_total_value

    lines.append("\n" + "=" * 55)
    lines.append(f"  派網         NT${pionex_total:>9.0f}")
    lines.append(f"  Firstrade    NT${ft_ntd:>9.0f}  損益${ft_total_gain:+.2f}")
    lines.append(f"  國泰複委託   NT${cathay_ntd:>9.0f}  損益${cathay_total_gain:+.2f}")
    lines.append(f"  國泰台股     NT${tw_total_value:>9.0f}  損益NT${tw_gain:+.0f}")
    lines.append(f"  ──────────────────────────────")
    lines.append(f"  總資產       NT${total_ntd:>9.0f}")
    total_today = ft_today_gain + cathay_today_gain
    lines.append(f"  Firstrade今日  ${ft_today_gain:+.2f} (NT${ft_today_gain*NTD_RATE:+.0f})")
    lines.append(f"  國泰今日       ${cathay_today_gain:+.2f} (NT${cathay_today_gain*NTD_RATE:+.0f})")
    lines.append(f"  台股今日       NT${tw_today:+.0f}")
    lines.append(f"  美股今日合計   ${total_today:+.2f} (NT${total_today*NTD_RATE:+.0f})")
    lines.append("=" * 55)

    # ── 今日主要漲跌排行 ──
    all_today = []
    for r in ft_rows:
        if r["value"] >= 0.5:
            all_today.append({"sym": r["symbol"], "today_ntd": r["today_gain"]*NTD_RATE,
                               "chg_pct": r["chg_pct"], "broker": "FT"})
    for r in cath_rows:
        if r["value"] >= 0.5:
            all_today.append({"sym": r["sym"], "today_ntd": r["today_gain"]*NTD_RATE,
                               "chg_pct": r["chg_pct"], "broker": "國泰"})
    # 加台股
    for h in CATHAY_TW:
        sym = h["code"] + ".TW"
        q = tw_prices.get(sym, {})
        price = q.get("price", 0.0)
        chg_pct = q.get("change_pct", 0.0)
        today_ntd = h["qty"] * (price - q.get("prev", price))
        if price > 0:
            all_today.append({"sym": f"{h['code']} {h['name']}", "today_ntd": today_ntd,
                               "chg_pct": chg_pct, "broker": "台股"})
    all_today.sort(key=lambda x: -x["today_ntd"])
    lines.append("\n📈 今日漲最多（NT$）")
    for r in all_today[:3]:
        lines.append(f"  {r['sym']:<12} {r['chg_pct']:+.1f}%  今日NT${r['today_ntd']:+.0f}  [{r['broker']}]")
    lines.append("📉 今日跌最多（NT$）")
    for r in all_today[-3:][::-1]:
        lines.append(f"  {r['sym']:<12} {r['chg_pct']:+.1f}%  今日NT${r['today_ntd']:+.0f}  [{r['broker']}]")

    report = "\n".join(lines)
    print(report)

    # ── 記錄走勢 ──
    log_history(total_ntd)

    # ── 存到 Google Drive ──
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = f"{REPORT_DIR}/{date_str}_日報.md"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n✅ 報告已存至 Google Drive：{date_str}_日報.md")
    except Exception as e:
        print(f"[警告] 無法存至 Google Drive：{e}")

    # ── Mac 通知 ──
    all_today_ntd = ft_today_gain*NTD_RATE + cathay_today_gain*NTD_RATE + tw_today
    notify(
        f"投資日報 {datetime.now().strftime('%m/%d')}",
        f"總資產 NT${total_ntd:,.0f}  今日合計NT${all_today_ntd:+,.0f}"
    )


if __name__ == "__main__":
    main()
