#!/usr/bin/env python3
"""Jim 投資全視界 Dashboard — streamlit run dashboard.py"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import urllib.request, json, time, hmac, hashlib, urllib.parse, os, csv
from datetime import datetime, date, timedelta

HOLDINGS_FILE  = os.path.join(os.path.dirname(__file__), "holdings.json")
HISTORY_FILE   = os.path.join(os.path.dirname(__file__), "portfolio_history.csv")
REVIEW_FILE    = os.path.join(os.path.dirname(__file__), "data", "review_history.csv")

st.set_page_config(page_title="Jim 投資全視界", layout="wide",
                   page_icon="📊", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;600;700&display=swap');
:root{--bg:#0b0b0d;--surface:#131317;--surface-2:#1a1a20;--border:#24242c;--border-2:#2e2e38;
  --fg:#e9e9ec;--fg-2:#a8a8b2;--fg-3:#6c6c78;--fg-4:#3f3f48;
  --danger:#ef4444;--warn:#f59e0b;--ok:#22c55e;
  --mono:"JetBrains Mono",ui-monospace,monospace;--sans:"Inter","Noto Sans TC",system-ui,sans-serif}

/* ── Streamlit overrides ───────────────────────── */
.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
.block-container{padding:1rem 2rem!important;max-width:1440px}
body,.stMarkdown,p{font-family:var(--sans)!important}
h1,h2,h3,h4{font-family:var(--sans)!important;letter-spacing:-.01em}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid var(--border)!important;gap:0!important}
.stTabs [data-baseweb="tab"]{font-family:var(--sans)!important;font-size:13px!important;font-weight:500!important;
  color:var(--fg-3)!important;padding:12px 20px!important;background:transparent!important;letter-spacing:.02em}
.stTabs [aria-selected="true"]{color:var(--fg)!important;background:transparent!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--fg)!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:20px!important}

/* Metrics */
[data-testid="metric-container"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:8px!important;padding:14px 16px!important}
[data-testid="stMetricValue"]{font-family:var(--mono)!important;font-weight:600!important}
[data-testid="stMetricLabel"]{font-family:var(--mono)!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:.1em!important;color:var(--fg-3)!important}

/* Buttons */
.stButton button{background:transparent!important;border:1px solid var(--border-2)!important;color:var(--fg-2)!important;
  font-family:var(--mono)!important;font-size:11px!important;letter-spacing:.05em!important;border-radius:4px!important}
.stButton button:hover{border-color:var(--fg-3)!important;color:var(--fg)!important}
.stButton [data-testid="baseButton-primary"]{background:var(--fg)!important;color:#000!important}

/* Inputs */
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox select{
  background:var(--bg)!important;border:1px solid var(--border)!important;color:var(--fg)!important;
  font-family:var(--sans)!important;border-radius:4px!important}

/* Expanders */
.streamlit-expanderHeader{background:var(--surface-2)!important;border:1px solid var(--border)!important;border-radius:6px!important;font-family:var(--sans)!important;color:var(--fg-2)!important}
details[open] .streamlit-expanderHeader{border-radius:6px 6px 0 0!important}
.streamlit-expanderContent{background:var(--surface)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 6px 6px!important}

/* Dividers */
hr{border-color:var(--border)!important}

/* ── Design system ─────────────────────────────── */
/* Topbar */
.topbar-inner{display:flex;justify-content:space-between;align-items:center;padding:12px 0 16px;border-bottom:1px solid var(--border);flex-wrap:wrap;gap:16px;margin-bottom:20px}
.brand{display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px;font-family:var(--sans)}
.brand-dot{width:8px;height:8px;background:var(--fg);border-radius:50%}
.brand small{color:var(--fg-3);font-weight:400;font-size:12px;margin-left:8px}
.meta{display:flex;gap:20px;color:var(--fg-3);font-size:12px;font-family:var(--mono);flex-wrap:wrap}
.meta b{color:var(--fg);font-weight:500}
.pulse{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--ok);margin-right:6px;animation:pulse-anim 2s infinite}
@keyframes pulse-anim{0%,100%{opacity:1}50%{opacity:.3}}

/* Section headers */
.sec-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;margin-top:22px}
.sec-title{font-size:10px;font-weight:600;letter-spacing:.12em;color:var(--fg-3);text-transform:uppercase;font-family:var(--mono)}
.sec-sub{font-size:11px;color:var(--fg-4);font-family:var(--mono)}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px 18px}

/* Hero */
.hero-big{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:22px 24px;margin-bottom:16px}
.hero-big .label{font-size:10px;color:var(--fg-3);letter-spacing:.1em;font-family:var(--mono);text-transform:uppercase}
.hero-big .value{font-size:38px;font-weight:600;font-family:var(--mono);letter-spacing:-.02em;margin:6px 0 10px;line-height:1}
.hero-big .sub{display:flex;gap:20px;font-family:var(--mono);font-size:12px;color:var(--fg-2);flex-wrap:wrap}
.hero-big .sub b{color:var(--fg);font-weight:500}

/* Account mini cards */
.acct-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.acct{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
.acct .name{font-size:10px;color:var(--fg-3);letter-spacing:.1em;font-family:var(--mono);text-transform:uppercase;margin-bottom:8px}
.acct .val{font-size:20px;font-weight:600;font-family:var(--mono);letter-spacing:-.01em;color:var(--fg)}
.acct .row{display:flex;gap:12px;margin-top:6px;font-family:var(--mono);font-size:11px;color:var(--fg-3)}
.acct .bar{height:2px;background:var(--border-2);border-radius:2px;margin-top:10px;overflow:hidden}
.acct .bar span{display:block;height:100%;background:var(--fg-2)}

/* Alerts */
.alert-stack{display:flex;flex-direction:column;gap:6px;margin-bottom:20px}
.alert{display:flex;gap:12px;align-items:center;padding:10px 14px;border-radius:6px;font-size:13px;border:1px solid transparent;font-family:var(--sans)}
.alert-danger{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.3);color:#fca5a5}
.alert-entry {background:rgba(34,197,94,.08); border-color:rgba(34,197,94,.3); color:#86efac}
.alert-warn  {background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.3);color:#fcd34d}
.alert-icon{font-family:var(--mono);font-size:10px;font-weight:700;padding:3px 7px;border-radius:3px;flex-shrink:0;letter-spacing:.05em}
.alert-danger .alert-icon{background:var(--danger);color:#fff}
.alert-entry  .alert-icon{background:var(--ok);color:#000}
.alert-warn   .alert-icon{background:var(--warn);color:#000}
.alert b{color:#fff;font-weight:600}
.alert-meta{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--fg-3)}

/* Rank rows */
.rank-list{display:flex;flex-direction:column}
.rank-row{display:grid;grid-template-columns:26px 72px 1fr auto auto;gap:12px;align-items:center;padding:11px 0;border-bottom:1px solid var(--border);font-size:13px}
.rank-row:last-child{border-bottom:none}
.rank-n{font-family:var(--mono);color:var(--fg-4);font-size:12px;font-weight:500}
.rank-sym{font-weight:600;font-family:var(--mono);font-size:14px;letter-spacing:.02em;color:var(--fg)}
.rank-reason{color:var(--fg-3);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rank-tag{font-family:var(--mono);font-size:10px;padding:2px 6px;border-radius:3px;letter-spacing:.05em;white-space:nowrap}
.rank-tag.sell{background:rgba(239,68,68,.12);color:var(--danger)}
.rank-tag.buy {background:rgba(34,197,94,.12); color:var(--ok)}
.rank-tag.wait{background:var(--surface-2);color:var(--fg-3)}
.rank-tag.hold{background:rgba(245,158,11,.12);color:var(--warn)}
.rank-price{font-family:var(--mono);color:var(--fg-2);font-size:12px;text-align:right;white-space:nowrap}
.rank-price b{color:var(--fg);font-weight:500}

/* Status cells */
.status-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.status-cell{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
.status-cell .lbl{font-size:10px;color:var(--fg-3);letter-spacing:.08em;font-family:var(--mono);text-transform:uppercase}
.status-cell .val{font-size:22px;font-weight:600;font-family:var(--mono);margin:6px 0 4px;color:var(--fg)}
.progress{height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-top:8px}
.progress span{display:block;height:100%;background:var(--fg-2)}
.hint{color:var(--fg-4);font-size:11px;font-family:var(--mono);margin-top:6px}
.up{color:var(--ok)}.down{color:var(--danger)}.muted{color:var(--fg-3)}

/* Status pills */
.status-pill{font-size:10px;padding:2px 8px;border-radius:10px;font-family:var(--mono);letter-spacing:.05em;font-weight:500;display:inline-block}
.sp-zone{background:rgba(34,197,94,.12);color:var(--ok)}
.sp-near{background:rgba(245,158,11,.12);color:var(--warn)}
.sp-wait{background:var(--surface-2);color:var(--fg-3)}

/* Watchlist table */
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px 14px;font-family:var(--mono);font-size:12px}
thead th{color:var(--fg-3);font-weight:500;border-bottom:1px solid var(--border);font-size:10px;letter-spacing:.1em;text-transform:uppercase}
tbody tr{border-bottom:1px solid var(--border)}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:var(--surface-2)}
td.num{text-align:right}

/* Resale */
.resale-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;position:relative;margin-bottom:10px}
.resale-card .rs-status{position:absolute;top:12px;right:14px;font-size:10px;font-family:var(--mono);padding:2px 8px;border-radius:10px;letter-spacing:.05em}
.rs-listed{background:rgba(59,130,246,.12);color:#93c5fd}
.rs-wait  {background:rgba(245,158,11,.12);color:var(--warn)}
.rs-sold  {background:rgba(34,197,94,.12); color:var(--ok)}
.rs-keep  {background:var(--surface-2);color:var(--fg-3)}
.resale-card .rn{font-size:14px;font-weight:600;margin-bottom:4px;padding-right:60px;color:var(--fg)}
.resale-card .rb{font-size:11px;color:var(--fg-3);font-family:var(--mono);letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}
.price-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-family:var(--mono);font-size:11px}
.price-grid div{padding:6px 8px;background:var(--surface-2);border-radius:4px}
.price-grid .pl{color:var(--fg-4);font-size:10px;text-transform:uppercase;letter-spacing:.05em}
.price-grid .pv{font-size:13px;font-weight:500;margin-top:2px;color:var(--fg)}
.profit-val{color:var(--ok)}

/* Journal */
.journal-row{display:grid;grid-template-columns:70px 60px 1fr 80px;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--border);font-size:12px}
.journal-row:last-child{border-bottom:none}
.journal-date{color:var(--fg-3);font-family:var(--mono);font-size:11px}
.journal-sym{font-family:var(--mono);font-weight:600;font-size:13px;color:var(--fg)}
.journal-reason{color:var(--fg-2);line-height:1.4;font-size:12px}
.journal-conf{font-family:var(--mono);font-size:11px;color:var(--fg-3);text-align:right}

/* Insider (kept) */
.insider-buy {background:rgba(34,197,94,.08);border-left:3px solid var(--ok);    padding:8px 12px;border-radius:4px;margin:3px 0;font-size:13px}
.insider-sell{background:rgba(239,68,68,.08);border-left:3px solid var(--danger);padding:8px 12px;border-radius:4px;margin:3px 0;font-size:13px}

/* AI card */
.ai-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px;margin-bottom:16px}
.ai-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.ai-head .t{font-size:13px;font-weight:600;display:flex;align-items:center;gap:8px;font-family:var(--sans)}
.ai-dot{width:6px;height:6px;background:var(--fg);border-radius:50%;animation:pulse-anim 2s infinite}
.ai-head .time{font-size:11px;color:var(--fg-4);font-family:var(--mono)}

/* Responsive */
@media(max-width:900px){
  .acct-grid{grid-template-columns:repeat(2,1fr)}
  .status-grid{grid-template-columns:repeat(2,1fr)}
  .rank-row{grid-template-columns:20px 60px 1fr auto;gap:10px}
  .rank-row .rank-reason{display:none}
  .block-container{padding:0.5rem 0.75rem!important}
  h1{font-size:1.3rem!important}h2{font-size:1rem!important}
}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# 持倉資料
# ════════════════════════════════════════════════════
EXCHANGE_RATE = 32.5

# 國泰美股複委託 (成本USD, 股數)
CATHAY_US = {
    'HIMS': (27.660000,   3.0),      # 新增 2026-04-18
    'JOBY': (8.570909,   11.0),
    'LULU': (164.895457,  0.60693),
    'MSFT': (390.342837,  0.25639),
    'NKE':  (45.469707,   1.0),      # 成本更新
    'ONDS': (9.296667,    3.0),
    'ORCL': (172.201383,  0.58118),  # 新增 2026-04-18
    'RXRX': (3.484783,   46.0),      # 加碼至 46 股
    'TSLA': (352.183552,  0.28417),
}

# 國泰台股零股 (名稱, 股數, 成本TWD)
CATHAY_TW = {
    "00763U": ("街口道瓊", 6,   29.83),
    "1303":   ("南亞",     3,   81.00),
    "1326":   ("台化",     6,   48.50),
    "2027":   ("大成鋼",   7,   38.43),
    "2317":   ("鴻海",     1,   205.22),
    "2344":   ("華邦電",   1,   95.80),
    "3481":   ("群創",     100, 25.45),
    "6148":   ("正文科技", 34,  33.63),
}

# 派網代幣化股票 (成本USD, 預設股數) — 更新：2026-04-20
PIONEX_STOCKS = {
    'ADBE': (239.70, 0.247),
    'HIMS': (24.29,  1.23),
    'IONQ': (25.00,  0.507),
    'META': (560.00, 0.0458),
    'MSFT': (390.00, 0.112),
    'MSTR': (320.00, 0.2048),  # MicroStrategy — Beta ~3.5x ⚠️
    'NVO':  (40.81,  1.25),
    'ORCL': (135.25, 0.25),
    'SMCI': (22.16,  2.07),
    'SMR':  (5.50,   3.0),     # NuScale Power（小型核能）
    'TSLA': (240.00, 0.138),
}
COIN_MAP = {"ADBE":"ADBEX","HIMS":"HIMSX","IONQ":"IONQX",
            "META":"METAX","MSFT":"MSFTX","MSTR":"MSTRX",
            "NVO":"NVOX","ORCL":"ORCLX","SMCI":"SMCIX",
            "SMR":"SMRX","TSLA":"TSLAX"}

# 派網加密貨幣 (coingecko_id, 預設數量, 成本USD) — 更新：2026-04-18
PIONEX_CRYPTO = {
    'ETH':  ('ethereum', 0.00927,  2200.0),
    'SOL':  ('solana',   0.2799,   90.0),
    'ADA':  ('cardano',  54.21,    0.35),
    'ARKM': ('arkham',   321.634,  0.097),
}
PIONEX_USDT = 24.51  # 更新：2026-04-18

# Firstrade (成本USD, 股數)
FIRSTRADE = {
    'DXYZ': (22.06235, 0.02085),
    'GOOG': (153.00,   0.01779),
    'JOBY': (8.39,     3.57568),
    'META': (579.71,   0.01725),
    'NBIS': (98.12,    0.10192),
    'NVDL': (68.96,    0.14502),
    'NVO':  (38.92,    0.01079),
    'OKLO': (49.06,    0.40766),
    'ORCL': (138.91,   0.14398),
    'PYPL': (44.42,    0.00968),
    'RUN':  (12.53,    0.00878),
    'TSLA': (388.89,   0.00144),
    'URA':  (47.94,    0.21817),
}

PIONEX_KEY    = "7spnSfdT5zFwADvjT8bNfXrqMoFgyEzZedSM95oGSYECHeB5kqLUToawuPZMMYbrPS"
PIONEX_SECRET = "KstZhblHWw3ErU1exq46qGVNHHWYo9Rnij50pzZzExzUP4x3NHtCY8QAIe3jdxSv"

# ════════════════════════════════════════════════════
# Firstrade Excel 讀取（動態更新持倉）
# ════════════════════════════════════════════════════
def load_firstrade_from_excel() -> dict:
    """從 Firstrade 匯出的 Excel 讀取持倉，找不到時 fallback 到 hardcode dict。"""
    import glob
    patterns = [
        os.path.expanduser("~/Downloads/*-positions*.xlsx"),
        os.path.expanduser("~/Downloads/*positions*.xlsx"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    if not files:
        return FIRSTRADE
    latest = max(files, key=os.path.getmtime)
    try:
        df_xl = pd.read_excel(latest, sheet_name=0)
        result = {}
        for _, row in df_xl.iterrows():
            sym  = str(row.get("代號", "")).strip().upper()
            qty  = float(row.get("股數", 0) or 0)
            cost = float(row.get("單位成本", 0) or 0)
            if sym and qty > 0 and cost > 0:
                result[sym] = (cost, qty)
        return result if result else FIRSTRADE
    except Exception:
        return FIRSTRADE

# ════════════════════════════════════════════════════
# 派網 API helper（需在 sidebar 前定義）
# ════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def _pionex_get(path: str, params: dict = {}) -> dict:
    """Pionex HMAC-SHA256 GET helper, returns raw JSON dict"""
    ts = str(int(time.time() * 1000))
    p  = {**params, "timestamp": ts}
    q  = urllib.parse.urlencode(sorted(p.items()))
    sig = hmac.new(PIONEX_SECRET.encode("utf-8"),
                   f"GET{path}?{q}".encode("utf-8"),
                   hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        f"https://api.pionex.com{path}?{q}",
        headers={"PIONEX-KEY": PIONEX_KEY,
                 "PIONEX-SIGNATURE": sig,
                 "PIONEX-TIMESTAMP": ts,
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


@st.cache_data(ttl=30)
def fetch_pionex_bal() -> dict:
    """Returns coin→qty dict + "_ok" bool + "_error" str + "_prices" coin→USD price"""
    try:
        data = _pionex_get("/api/v1/account/balances")
        if not data.get("result"):
            return {"_ok": False, "_error": data.get("message", "API 回傳 result=false")}
        bals = data.get("data", {}).get("balances", [])
        result = {b["coin"]: float(b.get("free", 0)) + float(b.get("frozen", 0))
                  for b in bals
                  if float(b.get("free", 0)) + float(b.get("frozen", 0)) > 0.0001}
        result["_ok"] = True
        prices = {}
        for coin in list(result.keys()):
            if coin.startswith("_") or coin == "USDT" or coin.endswith("X"):
                continue
            try:
                td = _pionex_get("/api/v1/market/tickers", {"symbol": f"{coin}_USDT"})
                px = float(td["data"]["tickers"][0]["close"])
                if px > 0:
                    prices[coin] = px
            except:
                pass
        result["_prices"] = prices
        return result
    except Exception as e:
        return {"_ok": False, "_error": str(e), "_prices": {}}

# ════════════════════════════════════════════════════
# 即時匯率（需在 sidebar 前定義）
# ════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_usdtwd_rate() -> float:
    """抓即時 USD/TWD 匯率，失敗 fallback 到預設值"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDTWD=X?interval=1d&range=5d"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        valid = [c for c in closes if c is not None]
        return round(valid[-1], 2) if valid else EXCHANGE_RATE
    except:
        return EXCHANGE_RATE

# ════════════════════════════════════════════════════
# VIX + Insider Trading API
# ════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_vix() -> dict:
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=5d"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        valid = [c for c in closes if c is not None]
        vix  = round(valid[-1], 2) if valid else 20.0
        prev = valid[-2] if len(valid) >= 2 else vix
        return {"vix": vix, "chg": round(vix - prev, 2)}
    except:
        return {"vix": 20.0, "chg": 0.0}


@st.cache_data(ttl=1800)
def fetch_insider_trades(symbols: tuple) -> list:
    """SEC EDGAR Form 4 近 60 天內部人交易"""
    from datetime import timedelta
    start = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    end   = datetime.now().strftime("%Y-%m-%d")
    results = []
    for sym in symbols[:8]:
        try:
            url = (f"https://efts.sec.gov/LATEST/search-index?q=%22{sym}%22"
                   f"&forms=4&dateRange=custom&startdt={start}&enddt={end}")
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 portfolio-dashboard"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for hit in data.get("hits", {}).get("hits", [])[:4]:
                s = hit.get("_source", {})
                names = s.get("display_names") or ["—"]
                results.append({
                    "標的": sym,
                    "申報人": names[0][:25],
                    "日期": s.get("file_date", "")[:10],
                    "公司": (s.get("entity_name") or "")[:20],
                    "連結": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={sym}&type=4&dateb=&owner=include&count=5",
                })
        except:
            pass
        time.sleep(0.3)
    return results


# ════════════════════════════════════════════════════
# 持倉 JSON 讀寫
# ════════════════════════════════════════════════════
def _defaults():
    return {
        "cathay_us":       {k: list(v) for k,v in CATHAY_US.items()},
        "cathay_tw":       {k: list(v) for k,v in CATHAY_TW.items()},
        "pionex_stocks":   {k: list(v) for k,v in PIONEX_STOCKS.items()},
        "pionex_crypto":   {k: list(v) for k,v in PIONEX_CRYPTO.items()},
        "pionex_usdt":     PIONEX_USDT,
        "firstrade":       {k: list(v) for k,v in FIRSTRADE.items()},
        "savings_current": 0,
        "savings_target":  150000,
        "savings_deadline": "2026-05-31",
    }

def load_holdings():
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE) as f:
                return json.load(f)
        except:
            pass
    d = _defaults()
    with open(HOLDINGS_FILE, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d

def save_holdings(data):
    with open(HOLDINGS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_history(total_twd: float):
    """每小時記一筆總市值到 CSV"""
    now_hour = datetime.now().strftime("%Y-%m-%d %H:00")
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            f.write("時間,總市值(TWD)\n")
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    # 同一小時只記一次
    if lines and lines[-1].startswith(now_hour):
        return
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{now_hour},{total_twd:.0f}\n")

def load_history() -> pd.DataFrame:
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["時間","總市值(TWD)"])
    try:
        df = pd.read_csv(HISTORY_FILE, parse_dates=["時間"])
        df["總市值(TWD)"] = pd.to_numeric(df["總市值(TWD)"], errors="coerce")
        df = df.dropna().drop_duplicates(subset=["時間"]).sort_values("時間")
        return df.tail(30*24)  # 最多 30 天
    except:
        return pd.DataFrame(columns=["時間","總市值(TWD)"])

# 載入持倉（優先 JSON，fallback 預設值）
_h = load_holdings()
CATHAY_US     = {k: tuple(v) for k,v in _h.get("cathay_us",     {k:list(v) for k,v in CATHAY_US.items()}).items()}
CATHAY_TW     = {k: tuple(v) for k,v in _h.get("cathay_tw",     {k:list(v) for k,v in CATHAY_TW.items()}).items()}
PIONEX_STOCKS = {k: tuple(v) for k,v in _h.get("pionex_stocks", {k:list(v) for k,v in PIONEX_STOCKS.items()}).items()}
PIONEX_CRYPTO = {k: tuple(v) for k,v in _h.get("pionex_crypto", {k:list(v) for k,v in PIONEX_CRYPTO.items()}).items()}
PIONEX_USDT   = _h.get("pionex_usdt", PIONEX_USDT)
FIRSTRADE     = load_firstrade_from_excel()

# ════════════════════════════════════════════════════
# Sidebar 持倉編輯面板
# ════════════════════════════════════════════════════
with st.sidebar:
    st.header("✏️ 編輯持倉")

    def df_to_dict_us(edited_df, name_col="標的"):
        """把 data_editor 結果存回 dict"""
        result = {}
        for _, row in edited_df.iterrows():
            sym = row[name_col].strip().upper()
            if sym:
                result[sym] = [float(row["成本(USD)"]), float(row["股數"])]
        return result

    account = st.selectbox("選擇帳戶", ["國泰美股","國泰台股","派網股票","派網加密","Firstrade"])

    if account == "國泰美股":
        df_edit = pd.DataFrame([
            {"標的":k,"成本(USD)":v[0],"股數":v[1]} for k,v in CATHAY_US.items()
        ])
        edited = st.data_editor(df_edit, num_rows="dynamic",
                                column_config={"成本(USD)":st.column_config.NumberColumn(format="%.4f"),
                                               "股數":st.column_config.NumberColumn(format="%.5f")},
                                use_container_width=True, key="edit_cus")
        if st.button("💾 儲存 國泰美股"):
            _h["cathay_us"] = df_to_dict_us(edited)
            save_holdings(_h)
            st.cache_data.clear(); st.success("已儲存！"); st.rerun()

    elif account == "國泰台股":
        df_edit = pd.DataFrame([
            {"代號":k,"名稱":v[0],"股數":v[1],"成本(TWD)":v[2]} for k,v in CATHAY_TW.items()
        ])
        edited = st.data_editor(df_edit, num_rows="dynamic",
                                column_config={"成本(TWD)":st.column_config.NumberColumn(format="%.2f"),
                                               "股數":st.column_config.NumberColumn(format="%.0f")},
                                use_container_width=True, key="edit_ctw")
        if st.button("💾 儲存 國泰台股"):
            result = {}
            for _, row in edited.iterrows():
                code = str(row["代號"]).strip()
                if code:
                    result[code] = [str(row["名稱"]), int(row["股數"]), float(row["成本(TWD)"])]
            _h["cathay_tw"] = result
            save_holdings(_h)
            st.cache_data.clear(); st.success("已儲存！"); st.rerun()

    elif account == "派網股票":
        df_edit = pd.DataFrame([
            {"標的":k,"成本(USD)":v[0],"股數":v[1]} for k,v in PIONEX_STOCKS.items()
        ])
        edited = st.data_editor(df_edit, num_rows="dynamic",
                                column_config={"成本(USD)":st.column_config.NumberColumn(format="%.4f"),
                                               "股數":st.column_config.NumberColumn(format="%.4f")},
                                use_container_width=True, key="edit_pio")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("💾 儲存 派網股票"):
                _h["pionex_stocks"] = df_to_dict_us(edited)
                save_holdings(_h)
                st.cache_data.clear(); st.success("已儲存！"); st.rerun()
        with c2:
            new_usdt = st.number_input("USDT 餘額", value=float(PIONEX_USDT), step=1.0)
            if st.button("更新USDT"):
                _h["pionex_usdt"] = new_usdt
                save_holdings(_h)
                st.cache_data.clear(); st.success("USDT更新！"); st.rerun()

    elif account == "派網加密":
        df_edit = pd.DataFrame([
            {"幣種":k,"數量":v[1],"成本(USD)":v[2]} for k,v in PIONEX_CRYPTO.items()
        ])
        edited = st.data_editor(df_edit,
                                column_config={"數量":st.column_config.NumberColumn(format="%.4f"),
                                               "成本(USD)":st.column_config.NumberColumn(format="%.4f")},
                                use_container_width=True, key="edit_cry")
        if st.button("💾 儲存 加密貨幣"):
            cg_map = {"ETH":"ethereum","ADA":"cardano","ARKM":"arkham"}
            for _, row in edited.iterrows():
                coin = row["幣種"]
                if coin in _h.get("pionex_crypto",{}):
                    _h["pionex_crypto"][coin][1] = float(row["數量"])
                    _h["pionex_crypto"][coin][2] = float(row["成本(USD)"])
            save_holdings(_h)
            st.cache_data.clear(); st.success("已儲存！"); st.rerun()

    elif account == "Firstrade":
        df_edit = pd.DataFrame([
            {"標的":k,"成本(USD)":v[0],"股數":v[1]} for k,v in FIRSTRADE.items()
        ])
        edited = st.data_editor(df_edit, num_rows="dynamic",
                                column_config={"成本(USD)":st.column_config.NumberColumn(format="%.4f"),
                                               "股數":st.column_config.NumberColumn(format="%.5f")},
                                use_container_width=True, key="edit_ft")
        if st.button("💾 儲存 Firstrade"):
            _h["firstrade"] = df_to_dict_us(edited)
            save_holdings(_h)
            st.cache_data.clear(); st.success("已儲存！"); st.rerun()

    st.divider()
    st.caption("💰 儲蓄目標設定")
    _sv_cur  = st.number_input("目前現金儲蓄 (TWD)", value=float(_h.get("savings_current", 0)), step=1000.0, format="%.0f")
    _sv_tgt  = st.number_input("目標金額 (TWD)",     value=float(_h.get("savings_target", 150000)), step=1000.0, format="%.0f")
    _sv_dead = st.text_input("截止日期",             value=_h.get("savings_deadline", "2026-05-31"))
    if st.button("💾 儲存目標"):
        _h["savings_current"]  = _sv_cur
        _h["savings_target"]   = _sv_tgt
        _h["savings_deadline"] = _sv_dead
        save_holdings(_h)
        st.cache_data.clear(); st.success("已儲存！"); st.rerun()

    st.divider()
    st.caption("修改後按💾，自動刷新畫面")

    st.divider()
    # ── Pionex 連線狀態 ──────────────────────────────
    st.caption("🔌 派網 API 狀態")
    _pio_test = fetch_pionex_bal()
    if _pio_test.get("_ok"):
        _pio_coins = [k for k in _pio_test if not k.startswith("_")]
        st.success(f"✅ 已連線　持倉 {len(_pio_coins)} 種　USDT: {_pio_test.get('USDT',0):.2f}")
    else:
        st.error(f"❌ 連線失敗：{_pio_test.get('_error','未知錯誤')}")

    st.divider()
    st.caption("⚙️ 匯率設定")
    _sidebar_live = fetch_usdtwd_rate()
    st.caption(f"即時匯率：**{_sidebar_live}**　（Yahoo Finance USDTWD=X）")
    if "exchange_rate" not in st.session_state:
        st.session_state["exchange_rate"] = _sidebar_live
    new_er = st.number_input("USD/TWD 匯率（可手動覆蓋）", min_value=28.0, max_value=40.0,
                              value=st.session_state["exchange_rate"], step=0.1, format="%.2f")
    if new_er != st.session_state["exchange_rate"]:
        st.session_state["exchange_rate"] = new_er
        st.cache_data.clear()
        st.rerun()

# ════════════════════════════════════════════════════
# 警報設定 (停損價, 危險跌幅%)
# ════════════════════════════════════════════════════
STOP_LOSS = {
    # 美股  (停損價USD, 最大容忍虧損%)
    'RXRX': (2.80,  -16),
    'LULU': (140.0, -15),
    'ONDS': (6.50,  -30),
    'JOBY': (6.00,  -30),
    'TSLA': (280.0, -20),
    'ARKM': (0.0,   -60),   # 加密貨幣，只看虧損%
    # 台股
    '2344': (75.0,  -20),
}

# ════════════════════════════════════════════════════
# 操作建議（含日期）
# ════════════════════════════════════════════════════
ANALYST = {
    "NBIS": {"action":"BUY",  "target":205.0, "stop":85.0,
             "reason":"Meta $270億+MS $170億合約，Goldman目標$205(+31%)", "date":"2026-04-14"},
    "ORCL": {"action":"BUY",  "target":261.0, "stop":130.0,
             "reason":"雲端+41% YoY，AI基建訂單爆炸，Oracle連兩天+19%", "date":"2026-04-14"},
    "MSFT": {"action":"BUY",  "target":520.0, "stop":340.0,
             "reason":"Azure 40%+，4/29財報前佈局，目標$520(+33%)", "date":"2026-04-14"},
    "META": {"action":"BUY",  "target":860.0, "stop":650.0,
             "reason":"AI廣告護城河強，法律案件壓力後反彈，$860目標", "date":"2026-04-09"},
    "GOOG": {"action":"BUY",  "target":220.0, "stop":140.0,
             "reason":"AI搜尋+廣告雙引擎，小倉可加", "date":"2026-04-10"},
    "SMCI": {"action":"BUY",  "target":60.0,  "stop":20.0,
             "reason":"AI伺服器需求爆炸，剛進場成本$22，目標$60(+170%)", "date":"2026-04-15"},
    "OKLO": {"action":"HOLD", "target":99.0,  "stop":35.0,
             "reason":"核能法規利多已反應，等回調$45再加", "date":"2026-04-13"},
    "APLD": {"action":"HOLD", "target":35.0,  "stop":25.0,
             "reason":"昨天+14.8%，今天觀察守不守$30，跌破$25停損", "date":"2026-04-15"},
    "ADBE": {"action":"HOLD", "target":265.0, "stop":224.0,
             "reason":"昨天剛建倉成本$239，守$224支撐，目標$265", "date":"2026-04-15"},
    "TSLA": {"action":"HOLD", "target":424.0, "stop":280.0,
             "reason":"2.5σ 大漲後目標看 $424 稀疏區（Arthur 分析），持有等爆發；跌破 $280 停損", "date":"2026-04-16"},
    "RXRX": {"action":"HOLD", "target":7.50,  "stop":2.80,
             "reason":"主流分析師Buy，$7.5目標，但燒錢生技高風險", "date":"2026-04-14"},
    "URA":  {"action":"HOLD", "target":40.0,  "stop":30.0,
             "reason":"鈾礦ETF，核能受益，持有", "date":"2026-04-10"},
    "NVDL": {"action":"SELL", "target":0.0,   "stop":70.0,
             "reason":"已獲利+26%，2倍槓桿高風險，趁漲鎖利出場換穩健標的", "date":"2026-04-15"},
    "LULU": {"action":"HOLD", "target":206.0, "stop":140.0,
             "reason":"分析師目標$200~206，現在已到位，不加碼等財報", "date":"2026-04-15"},
    "JOBY": {"action":"SELL", "target":0.0,   "stop":6.0,
             "reason":"內部人連續賣股，無獲利路徑，現價$8.69幾乎打平快出", "date":"2026-04-15"},
    "ARKM": {"action":"SELL", "target":0.0,   "stop":0.0,
             "reason":"小幣無題材，已腰斬，考慮認賠換ORCL/MSFT", "date":"2026-04-13"},
    "PYPL": {"action":"SELL", "target":0.0,   "stop":42.0,
             "reason":"現價$48小獲利+8%，無催化劑，倉位極小清掉換有動能標的", "date":"2026-04-15"},
    "RUN":  {"action":"SELL", "target":0.0,   "stop":0.0,
             "reason":"倉位極小，無動能，清掉", "date":"2026-04-15"},
    "NKE":  {"action":"HOLD", "target":55.0,  "stop":38.0,
             "reason":"基本面穩但成長放緩，小倉持有", "date":"2026-04-10"},
    "ONDS": {"action":"HOLD", "target":12.0,  "stop":6.50,
             "reason":"小倉觀望，成交量低", "date":"2026-04-10"},
    "HIMS": {"action":"HOLD", "target":35.0,  "stop":18.0,
             "reason":"GLP-1減重業務高速成長，今日+9.6%，守$18停損", "date":"2026-04-16"},
    "SOFI": {"action":"HOLD", "target":28.0,  "stop":14.0,
             "reason":"金融科技+AI整合，小倉持有，等突破$22再加", "date":"2026-04-16"},
    "SOUN": {"action":"BUY",  "target":18.0,  "stop":7.0,
             "reason":"已建倉$7.59，AI語音高波動高潛力，目標$18(+137%)", "date":"2026-04-16"},
}

# ════════════════════════════════════════════════════
# 觀察清單
# ════════════════════════════════════════════════════
WATCHLIST = {
    "PLTR": {"entry_zone":[95,110],  "target":180.0,"stop":85.0,
             "theme":"AI/數據","reason":"政府+企業AI合約雙引擎，回$95~110可買","date":"2026-04-14"},
    "RKLB": {"entry_zone":[22,28],   "target":50.0, "stop":18.0,
             "theme":"太空","reason":"商業火箭發射加速，NASA合約，不受SpaceX上市壓力；手頭14億現金，理想加倉價$75以下（Ace 2026-04-18）","date":"2026-04-18"},
    "NVDA": {"entry_zone":[90,105],  "target":160.0,"stop":80.0,
             "theme":"AI晶片","reason":"AI基建核心，等回$90~105支撐區","date":"2026-04-14"},
    "IONQ": {"entry_zone":[20,26],   "target":55.0, "stop":16.0,
             "theme":"量子","reason":"Microsoft合作，量子+AI題材，小倉","date":"2026-04-10"},
    "CRWD": {"entry_zone":[300,340], "target":450.0,"stop":270.0,
             "theme":"資安","reason":"AI驅動資安龍頭，等拉回$300~340","date":"2026-04-10"},
    "CEG":  {"entry_zone":[220,250], "target":320.0,"stop":200.0,
             "theme":"核能","reason":"微軟TMI核電廠合約，核能股龍頭","date":"2026-04-12"},
    "VRT":  {"entry_zone":[90,100],  "target":140.0,"stop":80.0,
             "theme":"AI基建","reason":"AI伺服器散熱龍頭，NVDA每賣一顆GPU就受益","date":"2026-04-15"},
    "MRVL": {"entry_zone":[60,70],   "target":110.0,"stop":55.0,
             "theme":"AI晶片","reason":"客製化ASIC晶片，Google/Amazon指定，財報前AI收入預期翻倍","date":"2026-04-15"},
    "SOUN": {"entry_zone":[8,10],    "target":18.0, "stop":7.0,
             "theme":"AI語音","reason":"AI語音投機股，小倉5%以內，高波動高潛力","date":"2026-04-15"},
    "IRDM": {"entry_zone":[29,35],   "target":60.0, "stop":25.0,
             "theme":"太空/衛星","reason":"Iridium 衛星通訊，從底部大幅反轉，上方阻力小；Ace 成本$29，目標$60+（Ace 2026-04-18）","date":"2026-04-18"},
    "INTC": {"entry_zone":[18,24],   "target":40.0, "stop":15.0,
             "theme":"半導體/AI晶片","reason":"Ace 由空轉多：馬斯克潛在晶片製造合作 + 18A 製程良率提升，財報下週，長期看好（Ace 2026-04-18）","date":"2026-04-18"},
    "MSTR": {"entry_zone":[150,220], "target":500.0,"stop":130.0,
             "theme":"比特幣代理","reason":"MicroStrategy 持續定額買BTC，Ace 平均成本$200，等BTC多頭確認再加；適合BTC替代倉位","date":"2026-04-18"},
    "ICHR": {"entry_zone":[25,35],   "target":55.0, "stop":20.0,
             "theme":"半導體設備","reason":"半導體設備上游供應商，AI帶動晶圓廠資本支出上升直接受益，低調但有潛力（Ace 2026-04-18）","date":"2026-04-18"},
    # ── 消費品牌（零售銷售數據觸發關鍵）──────────────────
    "DECK": {"entry_zone":[85, 120],  "target":185.0, "stop":75.0,
             "theme":"消費品牌/HOKA","reason":"基本面最強（淨利率19.4%），HOKA+UGG雙品牌，等零售銷售數據確認後再進場；ROE 53%，幾乎零債","date":"2026-04-20"},
    "ANF":  {"entry_zone":[65,  90],  "target":130.0, "stop":55.0,
             "theme":"消費品牌","reason":"穩健成長但消費信心承壓，等週二零售銷售數據後決定是否進場","date":"2026-04-20"},
    "FIGS": {"entry_zone":[5,   8],   "target":14.0,  "stop":4.0,
             "theme":"醫療服飾","reason":"YoY +13.6%成長，體量小波動大，小倉投機；等市場情緒穩定後進","date":"2026-04-20"},
}

# ════════════════════════════════════════════════════
# API 函數
# ════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def fetch_us_quotes(symbols: tuple) -> dict:
    result = {}
    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            valid = [c for c in closes if c is not None]
            price = valid[-1] if valid else 0.0
            prev  = valid[-2] if len(valid) >= 2 else price
            result[sym] = {"price":price, "prev":prev,
                           "chg_pct":(price-prev)/prev*100 if prev else 0.0}
        except:
            result[sym] = {"price":0.0,"prev":0.0,"chg_pct":0.0}
        time.sleep(0.2)
    return result

@st.cache_data(ttl=60)
def fetch_tw_quotes() -> dict:
    result = {}
    all_codes = list(dict.fromkeys(list(CATHAY_TW.keys()) + list(TW_WATCHLIST.keys())))
    for code in all_codes:
        sym = code + ".TW"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            valid = [c for c in closes if c is not None]
            price = valid[-1] if valid else 0.0
            prev  = valid[-2] if len(valid) >= 2 else price
            result[code] = {"price":price,"prev":prev,
                            "chg_pct":(price-prev)/prev*100 if prev else 0.0}
        except:
            result[code] = {"price":0.0,"prev":0.0,"chg_pct":0.0}
        time.sleep(0.15)
    return result

# CoinGecko ID 對照表（symbol → coingecko_id）
CG_ID_MAP = {
    "BTC":  "bitcoin",
    "ETH":  "ethereum",
    "BNB":  "binancecoin",
    "SOL":  "solana",
    "DOGE": "dogecoin",
    "ADA":  "cardano",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "DOT":  "polkadot",
    "MATIC":"matic-network",
    "UNI":  "uniswap",
    "ARKM": "arkham",
    "SUI":  "sui",
    "INJ":  "injective-protocol",
    "TIA":  "celestia",
    "SEI":  "sei-network",
}

# 加密貨幣觀察清單
CRYPTO_WATCHLIST = {
    # priority: 1=最優先 8=最低  rr=風險報酬比（以現價中間估算）
    "BTC":  {"entry_zone":[70000, 82000], "target":105000, "stop":63000,
             "theme":"數位黃金", "priority":1,
             "reason":"ETF 機構資金持續流入，減半後供應收緊；$70k~82k 是本輪修正關鍵支撐區，最安全分批建倉"},
    "SOL":  {"entry_zone":[75, 105],  "target":185,  "stop":60,
             "theme":"高速公鏈", "priority":2,
             "reason":"DEX 交易量超越以太坊，Firedancer 升級在即；$75~105 是歷史強支撐，基本面最強 L1"},
    "LINK": {"entry_zone":[8, 13],    "target":25,   "stop":6,
             "theme":"預言機", "priority":3,
             "reason":"DeFi+TradFi 基礎設施龍頭（Swift/DTCC）；相對其他 L1 跌最深、最被低估，R:R 極佳"},
    "AVAX": {"entry_zone":[8, 13],    "target":30,   "stop":6,
             "theme":"L1/企業鏈", "priority":4,
             "reason":"Avalanche9000 升級降低建鏈成本，機構與遊戲生態擴展；$8~13 為強支撐，中等風險"},
    "DOGE": {"entry_zone":[0.07, 0.13],"target":0.35, "stop":0.05,
             "theme":"迷因/馬斯克", "priority":5,
             "reason":"X 支付整合預期、馬斯克效應；純投機但流動性最高，嚴控倉位 ≤5%，適合短線"},
    "INJ":  {"entry_zone":[2.5, 5.0], "target":18,   "stop":1.8,
             "theme":"DeFi/衍生品", "priority":6,
             "reason":"鏈上衍生品龍頭，TVL 持續成長；跌幅大但基本面完整，高風險高報酬"},
    "SUI":  {"entry_zone":[0.75, 1.30],"target":4.5,  "stop":0.55,
             "theme":"新興L1", "priority":7,
             "reason":"Move 語言生態，三星 Galaxy 預裝錢包；高風險新興 L1，小倉試水"},
    "TIA":  {"entry_zone":[0.30, 0.60],"target":2.5,  "stop":0.20,
             "theme":"模組化區塊鏈", "priority":8,
             "reason":"DA 層龍頭，Rollup 擴展直接受益；超高風險小市值，最小倉位佈局"},
}

# 台股觀察清單（入場區間 TWD）
TW_WATCHLIST = {
    "2330": {"name":"台積電",   "entry_zone":[700,  870],  "target":1050, "stop":640,
             "theme":"AI晶片龍頭",   "priority":1,
             "reason":"AI算力需求爆炸，3nm/2nm 產能滿載；全球最先進製程護城河無可取代，逢跌首選建倉"},
    "2454": {"name":"聯發科",   "entry_zone":[900,  1100], "target":1500, "stop":780,
             "theme":"IC設計",       "priority":2,
             "reason":"天璣旗艦晶片持續升級，AI 手機週期啟動；本益比合理，受惠 AI 終端需求爆發"},
    "2317": {"name":"鴻海",     "entry_zone":[145,  185],  "target":250,  "stop":125,
             "theme":"AI伺服器EMS",  "priority":3,
             "reason":"GB200 NVL72 機架主要組裝商，AI 伺服器佔比快速提升；回踩支撐為布局良機"},
    "2382": {"name":"廣達",     "entry_zone":[220,  280],  "target":380,  "stop":190,
             "theme":"AI伺服器ODM",  "priority":4,
             "reason":"Google/Meta 雲端 AI 伺服器最大 ODM；液冷伺服器技術領先，AI 轉型進行式"},
    "3711": {"name":"日月光投控","entry_zone":[130,  165],  "target":220,  "stop":115,
             "theme":"先進封裝",     "priority":5,
             "reason":"CoWoS/SoIC 先進封裝受惠 AI 算力，與台積電深度合作；供不應求延續至 2026H2"},
    "2308": {"name":"台達電",   "entry_zone":[250,  320],  "target":420,  "stop":215,
             "theme":"電源/散熱",    "priority":6,
             "reason":"AI 資料中心電源與散熱方案龍頭，NVIDIA 指定供應商；長線穩健，防守兼進攻"},
    "6669": {"name":"緯穎",     "entry_zone":[1600, 2100], "target":2800, "stop":1350,
             "theme":"AI伺服器",     "priority":7,
             "reason":"Meta/Microsoft AI 伺服器直接設計代工；波動大，逢深回至支撐區再進，高 R:R"},
    "2412": {"name":"中華電",   "entry_zone":[115,  130],  "target":145,  "stop":108,
             "theme":"電信/防禦",    "priority":8,
             "reason":"高殖利率防禦股，市場動盪時避風港；6G 佈局啟動，適合保守型資金"},
}

def _cg_fetch(ids: list) -> dict:
    """CoinGecko simple/price，單次最多 10 個 ID，自動分批"""
    result = {}
    for i in range(0, len(ids), 10):
        batch = ids[i:i+10]
        url = ("https://api.coingecko.com/api/v3/simple/price?ids="
               + ",".join(batch)
               + "&vs_currencies=usd&include_24hr_change=true")
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"portfolio/1.0",
                                                        "Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                result.update(json.loads(r.read()))
        except:
            pass
        if i + 10 < len(ids):
            time.sleep(0.5)
    return result

@st.cache_data(ttl=60)
def fetch_crypto() -> dict:
    held_ids  = list(dict.fromkeys(v[0] for v in PIONEX_CRYPTO.values()))
    watch_ids = [CG_ID_MAP[s] for s in CRYPTO_WATCHLIST if s in CG_ID_MAP]
    extra_ids = [CG_ID_MAP["BTC"]]
    all_ids   = list(dict.fromkeys(held_ids + watch_ids + extra_ids))
    d = _cg_fetch(all_ids)
    result = {}
    # 持倉幣種
    for sym, (cg_id, _, _) in PIONEX_CRYPTO.items():
        rec   = d.get(cg_id, {})
        price = float(rec.get("usd", 0) or 0)
        chg   = float(rec.get("usd_24h_change", 0) or 0)
        prev  = price / (1 + chg / 100) if chg != -100 and price else price
        result[sym] = {"price": price, "prev": prev, "chg_pct": chg}
    # 所有 CG_ID_MAP 幣種（觀察清單用）
    for sym, cg_id in CG_ID_MAP.items():
        if sym in result:
            continue
        rec   = d.get(cg_id, {})
        price = float(rec.get("usd", 0) or 0)
        chg   = float(rec.get("usd_24h_change", 0) or 0)
        prev  = price / (1 + chg / 100) if chg != -100 and price else price
        result[sym] = {"price": price, "prev": prev, "chg_pct": chg}
    return result

@st.cache_data(ttl=300)
def fetch_technicals(sym: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=3mo"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        q = data["chart"]["result"][0]["indicators"]["quote"][0]
        closes = [c for c in q.get("close",[]) if c]
        highs  = [h for h in q.get("high",[])  if h]
        lows   = [l for l in q.get("low",[])   if l]
        if len(closes)<20: return {}
        ma20 = sum(closes[-20:])/20
        ma50 = sum(closes[-50:])/50 if len(closes)>=50 else ma20
        gains  = [max(closes[-i]-closes[-i-1],0) for i in range(1,15)]
        losses = [max(closes[-i-1]-closes[-i],0) for i in range(1,15)]
        ag,al = sum(gains)/14 or 0.001, sum(losses)/14 or 0.001
        rsi = round(100-100/(1+ag/al),1)
        price = closes[-1]
        score = sum([price>ma20, price>ma50, rsi>50, price>(min(lows[-20:])+max(highs[-20:]))/2])
        sent = "🟢 偏多" if score>=3 else ("🟡 中性" if score==2 else "🔴 偏空")
        return {"support":round(min(lows[-20:]),2),"resist":round(max(highs[-20:]),2),
                "ma20":round(ma20,2),"ma50":round(ma50,2),"rsi":rsi,"sentiment":sent}
    except:
        return {}

# ════════════════════════════════════════════════════
# 組合計算
# ════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def build_portfolio(exrate: float = 32.5):
    all_us = tuple(set(list(CATHAY_US)+list(PIONEX_STOCKS)+list(FIRSTRADE)+list(WATCHLIST)+["TSM","SPY","TSLA"]))
    us_q   = fetch_us_quotes(all_us)
    tw_q   = fetch_tw_quotes()
    cry_q  = fetch_crypto()
    pio_bal= fetch_pionex_bal()
    rows   = []

    def us_row(platform, sym, cost_usd, qty, price, prev):
        chg_pct  = (price-prev)/prev*100 if prev else 0
        value    = qty*price
        cost_tot = qty*cost_usd
        gain     = value-cost_tot
        today    = qty*(price-prev)
        return {
            "平台":platform,"標的":sym,
            "現價":price,"成本":cost_usd,"股數":qty,
            "現值(TWD)":  value*exrate,
            "損益(TWD)":  gain*exrate,
            "今日(TWD)":  today*exrate,
            "漲跌幅(%)":  round(chg_pct,2),
            "總損益(%)":  round(gain/cost_tot*100,2) if cost_tot else 0,
        }

    # ── 國泰美股
    for sym,(cost,qty) in CATHAY_US.items():
        q = us_q.get(sym,{})
        rows.append(us_row("國泰美股",sym,cost,qty,q.get("price",0),q.get("prev",0)))

    # ── 國泰台股（TWD 計價，不乘匯率）
    for code,(name,qty,cost_twd) in CATHAY_TW.items():
        q = tw_q.get(code,{})
        price = q.get("price",0.0)
        prev  = q.get("prev",price)
        chg   = (price-prev)/prev*100 if prev else 0
        value = qty*price
        cost_tot = qty*cost_twd
        gain  = value-cost_tot
        rows.append({
            "平台":"國泰台股","標的":f"{code} {name}",
            "現價":price,"成本":cost_twd,"股數":qty,
            "現值(TWD)":  value,
            "損益(TWD)":  gain,
            "今日(TWD)":  qty*(price-prev),   # 已是TWD
            "漲跌幅(%)":  round(chg,2),
            "總損益(%)":  round(gain/cost_tot*100,2) if cost_tot else 0,
        })

    _pio_prices = pio_bal.get("_prices", {})  # Pionex token 市場價（TSLAX→price）

    # ── 派網股票
    for sym,(cost,default_qty) in PIONEX_STOCKS.items():
        coin = COIN_MAP.get(sym,sym+"X")
        qty  = pio_bal.get(coin,default_qty)
        yq   = us_q.get(sym,{})
        # 優先用 Pionex token 市場價，fallback 到 Yahoo
        price = _pio_prices.get(coin, yq.get("price",0))
        prev  = yq.get("prev", price)
        rows.append(us_row("派網",f"{coin}→{sym}",cost,qty,price,prev))

    # ── 派網加密貨幣
    for coin,(cg_id,default_qty,cost) in PIONEX_CRYPTO.items():
        qty = pio_bal.get(coin,default_qty)
        q   = cry_q.get(coin,{})
        price= q.get("price",0.0)
        prev = q.get("prev",price)
        chg  = q.get("chg_pct",0.0)
        value= qty*price
        cost_tot = qty*cost
        gain = (value-cost_tot)*exrate if cost>0 else 0
        rows.append({
            "平台":"派網","標的":coin,
            "現價":price,"成本":cost,"股數":qty,
            "現值(TWD)":  value*exrate,
            "損益(TWD)":  int(gain),
            "今日(TWD)":  int(qty*(price-prev)*exrate),
            "漲跌幅(%)":  round(chg,2),
            "總損益(%)":  round((price-cost)/cost*100,2) if cost else 0,
        })

    # ── 派網 USDT
    usdt = pio_bal.get("USDT",PIONEX_USDT)
    rows.append({"平台":"派網","標的":"USDT","現價":1.0,"成本":1.0,"股數":usdt,
                 "現值(TWD)":usdt*exrate,"損益(TWD)":0,"今日(TWD)":0,
                 "漲跌幅(%)":0,"總損益(%)":0})

    # ── Firstrade
    for sym,(cost,qty) in FIRSTRADE.items():
        q = us_q.get(sym,{})
        rows.append(us_row("Firstrade",sym,cost,qty,q.get("price",0),q.get("prev",0)))

    df = pd.DataFrame(rows)
    df = df[df["現值(TWD)"]>1].copy()
    for col in ["現值(TWD)","損益(TWD)","今日(TWD)"]:
        df[col] = df[col].round(0).astype(int)
    return df, us_q, tw_q, cry_q

# ════════════════════════════════════════════════════
# 警報系統
# ════════════════════════════════════════════════════
def check_alerts(df, us_q, tw_q):
    danger, entry = [], []

    # 危險警報：停損觸發 or 今日跌幅 > 5%
    for sym,(stop_price, max_loss_pct) in STOP_LOSS.items():
        q = us_q.get(sym,{}) or tw_q.get(sym,{})
        price = q.get("price",0)
        if price==0: continue
        chg = q.get("chg_pct",0)
        # 今日跌幅警報
        if chg < -5:
            danger.append(f"⚠️ **{sym}** 今日跌 {chg:.1f}%  現價 ${price:.2f}")
        # 接近停損
        if stop_price>0 and price < stop_price*1.05:
            danger.append(f"🔴 **{sym}** 接近停損 ${stop_price}  現價 ${price:.2f}  ({(price-stop_price)/stop_price*100:+.1f}%)")
        # 超過最大虧損
        rows = df[(df["標的"].str.contains(sym,na=False))]
        if not rows.empty:
            pct = rows.iloc[0]["總損益(%)"]
            if pct < max_loss_pct:
                danger.append(f"🚨 **{sym}** 虧損 {pct:.1f}% 超過警戒線 {max_loss_pct}%  現價 ${price:.2f}")

    # 急需入場警報：觀察清單進入買入區
    wl_q = fetch_us_quotes(tuple(WATCHLIST.keys()))
    for sym, info in WATCHLIST.items():
        q = wl_q.get(sym,{})
        price = q.get("price",0)
        if price==0: continue
        lo,hi = info["entry_zone"]
        chg = q.get("chg_pct",0)
        if price <= hi:
            label = "🟢 已入進場區！" if price<=lo else "🟡 進入進場區"
            entry.append(f"{label} **{sym}** ${price:.2f}（進場區 ${lo}~${hi}）  今日{chg:+.1f}%  {info['date']}")

    return danger, entry

# ════════════════════════════════════════════════════
# Market Insights 區塊
# ════════════════════════════════════════════════════
def render_market_insights(us_q: dict):
    st.header("🚀 Jim's 24H Market Insights")

    # ── SPX 關鍵點位警示 ──────────────────────────────
    spy_q  = us_q.get("SPY", {})
    spy_px = spy_q.get("price", 0)
    spy_chg= spy_q.get("chg_pct", 0)
    spx_col, warn_col = st.columns([1, 2])
    with spx_col:
        st.metric("SPY（S&P 500 代理）",
                  f"${spy_px:.2f}" if spy_px else "N/A",
                  f"{spy_chg:+.2f}%")
        st.caption("SPX ≈ SPY×10　7000=真空　7025-7035=磁鐵　6965=地板")
    with warn_col:
        if spy_px:
            spx = spy_px * 10
            if spx >= 7025:
                st.error("🧲 **磁鐵區 7025-7035**　分批停利，不追高，利用逼空出場")
            elif spx >= 7000:
                st.warning("⚡ **突破 7000 真空區**　動能不足時主動減位，鎖定部分利潤")
            elif spx < 6965:
                st.error("🚨 **跌破 6965 地板**　無條件收縮風險，不硬扛，保本優先")
            else:
                st.info("📊 **觀察帶 6965-7000**　等方向確認再行動")

    st.divider()

    # ── 三套劇本 SOP ─────────────────────────────────
    st.subheader(f"📋 本週操作 SOP（3%財富覺醒 Arthur · {datetime.now().strftime('%Y-%m-%d')}）")
    sop_data = {
        "劇本":     ["🚀 劇本一：強力突破",           "⚡ 劇本二：高位震盪",                    "🚨 劇本三：有效跌破"],
        "觸發條件": ["SPX 突破 7000→7025-7035",       "7000 附近劇烈來回，動能不足",            "SPX 跌破 6965"],
        "操作 SOP": ["分批停利，不追高加碼，逼空出場", "主動減位至跌也不心痛水位，保護心智",     "無條件收縮風險，果斷砍底層部位"],
    }
    st.table(pd.DataFrame(sop_data))

    st.divider()

    # ── 個股即時報價 ──────────────────────────────────
    st.subheader("📡 關鍵標的即時行情")
    col1, col2, col3, col4 = st.columns(4)

    def _metric(col, sym, label, caption_text):
        q     = us_q.get(sym, {})
        price = q.get("price", 0)
        chg   = q.get("chg_pct", 0)
        col.metric(label=label,
                   value=f"${price:.2f}" if price else "N/A",
                   delta=f"{chg:+.2f}%")
        col.caption(caption_text)

    with col1:
        _metric(col1, "TSLA", "TSLA", "目標 $424 稀疏區｜2.5σ 大漲後留意回測")
    with col2:
        _metric(col2, "NVDA", "NVDA", "價值發現續抱｜跌 2σ 以上考慮停利")
    with col3:
        _metric(col3, "TSM",  "TSM",  "亞利桑那 Fab 4 滿載，定價權確立")
    with col4:
        _metric(col4, "ORCL", "ORCL", "雲端+41% YoY，AI 基建訂單爆炸")

    st.caption("來源：3%財富覺醒 Arthur · 期權結構 · 造市商 Gamma 環境監測")

# ════════════════════════════════════════════════════
# 24H 重啟系統（含每日表單）
# ════════════════════════════════════════════════════
def _append_review(row: dict):
    os.makedirs(os.path.dirname(REVIEW_FILE), exist_ok=True)
    exists = os.path.isfile(REVIEW_FILE) and os.path.getsize(REVIEW_FILE) > 0
    with open(REVIEW_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if not exists:
            w.writeheader()
        w.writerow(row)


@st.cache_data(ttl=60)
def _load_review_history() -> pd.DataFrame:
    if not os.path.isfile(REVIEW_FILE) or os.path.getsize(REVIEW_FILE) == 0:
        return pd.DataFrame()
    df = pd.read_csv(REVIEW_FILE, parse_dates=["date"])
    return df.sort_values("date", ascending=False)


@st.fragment
def render_daily_system():
    st.header("🔄 24H 人生重啟系統")
    st.caption("核心：改變人生不靠意志力，靠修復大腦「反饋迴路」，讓大腦重新體驗「我贏了」的感覺")

    with st.expander("📖 系統說明"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**🌙 前夜清障**")
            st.markdown("- 寫下明天第一任務\n- 清空桌面、備妥環境\n- 手機放客廳、封鎖社交軟體\n- 心理設定：明天只把系統跑起來")
        with c2:
            st.markdown("**☀️ 早晨 60 分鐘**")
            st.markdown("- 5 分鐘內起床\n- 自然光 + 飲水\n- 5 分鐘低強度運動\n- ❌ 不刷任何訊息流\n- 確立今日唯一 **MIT**")
        with c3:
            st.markdown("**🔥 深度執行**")
            st.markdown("- 90-120 分鐘專注區塊\n- 先求產出，再求完美\n- 卡住 → 降級動作\n- 中段重置：輕運動 + 低糖")
        with c4:
            st.markdown("**🌜 晚間復盤**")
            st.markdown("- 今天有效的動作？\n- 最大的阻力？\n- 明天保留 / 刪除哪些？\n- 寫下明天第一任務")
        st.error("**為什麼你以前會失敗？**　列了 20 件事只做完 3 件 → 大腦收到「輸了」信號 → 系統關機。設定**唯一必勝任務**，讓大腦對「贏的感覺」上癮。")

    # ── 表單（直接顯示）──────────────────────────────
    _entry_date = st.date_input("填寫日期", value=date.today(), key="rv_date")

    _fa, _fb, _fc, _fd, _fe = st.columns(5)
    with _fa:
        st.markdown("**🌙 前夜清障**")
        _p1_task  = st.text_input("明天第一任務", placeholder="幾點完成什麼", key="rv_p1t")
        _p1_rule  = st.text_input("啟動規則", placeholder="想拖延就先做5分鐘", key="rv_p1r")
        _p1_moti  = st.text_input("啟動動力", placeholder="明天只做一件事", key="rv_p1m")
        _p1_env   = st.checkbox("已清空桌面/備妥環境", key="rv_p1e")
        _p1_block = st.checkbox("已封鎖誘惑入口", key="rv_p1b")
    with _fb:
        st.markdown("**☀️ 主動開局**")
        _mit     = st.text_input("MIT（今日唯一必勝任務）", placeholder="可見交付是什麼", key="rv_mit")
        _p2_bed  = st.checkbox("5 分鐘內下床", key="rv_p2bed")
        _p2_lite = st.checkbox("自然光 + 喝水", key="rv_p2lt")
        _p2_ex   = st.checkbox("低強度運動 5 分鐘", key="rv_p2ex")
        _p2_nos  = st.checkbox("起床後未刷訊息", key="rv_p2ns")
    with _fc:
        st.markdown("**🔥 深度執行**")
        _p3_pomo = st.number_input("番茄鐘輪數", min_value=0, max_value=10, value=0, key="rv_pomo")
        _p3_out  = st.text_area("本日交付成果", placeholder="可見的輸出是什麼？", height=100, key="rv_p3o")
        _p3_of   = st.checkbox("先產出再修正", key="rv_p3of")
        _p3_ds   = st.checkbox("每輪前寫下交付標準", key="rv_p3ds")
        _p3_dg   = st.checkbox("卡住時使用降級動作", key="rv_p3dg")
    with _fd:
        st.markdown("**🔁 中段重置**")
        _p4_rst  = st.checkbox("已完成中段重置", key="rv_p4r")
        _p4_con  = st.checkbox("下午繼續推進同一任務", key="rv_p4c")
        _p4_note = st.text_area("復位卡", placeholder="上午完成了…\n下午幾點繼續…", height=100, key="rv_p4n")
    with _fe:
        st.markdown("**🌜 晚間復盤**")
        _q1 = st.text_input("① 最有效的動作？", key="rv_q1")
        _q2 = st.text_input("② 最大的阻力？", key="rv_q2")
        _q3 = st.text_input("③ 阻力因為我做了？", key="rv_q3")
        _q4 = st.text_input("④ 明天保留？", key="rv_q4")
        _q5 = st.text_input("⑤ 明天刪除？", key="rv_q5")

    _score = st.slider("今日整體評分", 1, 10, 7, key="rv_score")
    st.caption(f"{'⭐' * _score}  {_score} / 10")

    if st.button("✅ 儲存今日紀錄", type="primary", key="rv_submit"):
        _row = {
            "date": _entry_date.isoformat(), "mit": _mit,
            "phase1_task": _p1_task, "phase1_env": _p1_env, "phase1_block": _p1_block,
            "phase1_rule": _p1_rule, "phase1_motivation": _p1_moti,
            "phase2_bed": _p2_bed, "phase2_light": _p2_lite,
            "phase2_exercise": _p2_ex, "phase2_no_social": _p2_nos,
            "phase3_pomodoros": _p3_pomo, "phase3_output_first": _p3_of,
            "phase3_delivery_std": _p3_ds, "phase3_downgrade": _p3_dg,
            "phase3_deliverable": _p3_out,
            "phase4_reset": _p4_rst, "phase4_continue": _p4_con, "phase4_reset_note": _p4_note,
            "phase5_q1": _q1, "phase5_q2": _q2, "phase5_q3": _q3,
            "phase5_q4": _q4, "phase5_q5": _q5, "phase5_score": _score,
        }
        _append_review(_row)
        st.cache_data.clear()
        st.success(f"已儲存 {_entry_date} 的紀錄！評分 {_score}/10")
        st.balloons()

    # ── 歷史紀錄（收合）──────────────────────────────
    with st.expander("📊 歷史紀錄"):
        _df_rv = _load_review_history()
        if _df_rv.empty:
            st.info("尚無歷史紀錄，填寫第一份表單後就會出現在這裡。")
        else:
            _c1, _c2 = st.columns(2)
            with _c1:
                st.markdown("**每日評分趨勢**")
                st.line_chart(_df_rv.set_index("date")[["phase5_score"]].sort_index())
            with _c2:
                st.markdown("**番茄鐘完成數**")
                st.bar_chart(_df_rv.set_index("date")[["phase3_pomodoros"]].sort_index())
            _latest = _df_rv.iloc[0]
            _ldate  = _latest["date"].date() if hasattr(_latest["date"], "date") else _latest["date"]
            st.caption(f"最近：{_ldate}　評分 {int(_latest.get('phase5_score',0))}/10　番茄 {int(_latest.get('phase3_pomodoros',0))} 輪　MIT：{_latest.get('mit','—') or '—'}")
            _bool_cols = ["phase1_env","phase1_block","phase2_bed","phase2_light",
                          "phase2_exercise","phase2_no_social","phase3_output_first",
                          "phase3_delivery_std","phase3_downgrade","phase4_reset","phase4_continue"]
            _disp = _df_rv.copy()
            for _bc in _bool_cols:
                if _bc in _disp.columns:
                    _disp[_bc] = _disp[_bc].map(
                        lambda v: "✅" if str(v).lower() in ("true","1","yes") else "❌")
            st.dataframe(_disp, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════
# 每日升級計畫
# ════════════════════════════════════════════════════
_UPGRADE_FILE = os.path.join(os.path.dirname(__file__), "data", "upgrade_log.csv")

DAILY_THEMES = {
    0: {"icon":"📈", "name":"投資體能",  "color":"#3b82f6",
        "desc":"深挖一個持倉的基本面，讓你知道自己買的是什麼"},
    1: {"icon":"🎓", "name":"技術升級",  "color":"#8b5cf6",
        "desc":"學一個新概念或看研究影片，寫下 3 個可執行結論"},
    2: {"icon":"🛡️", "name":"風險管理",  "color":"#ef4444",
        "desc":"審查停損設定、部位大小，確保沒有不可承受的風險"},
    3: {"icon":"🔍", "name":"撿漏掃描",  "color":"#f59e0b",
        "desc":"主動找市場低估機會，更新觀察清單與轉賣追蹤"},
    4: {"icon":"📊", "name":"週複盤",    "color":"#22c55e",
        "desc":"計算本週 P&L，寫下一個下週要改變的決策"},
    5: {"icon":"💪", "name":"身體升級",  "color":"#06b6d4",
        "desc":"30 分鐘運動 + 冷水澡 + 閱讀 20 頁，遠離螢幕"},
    6: {"icon":"🗓️", "name":"計畫下週",  "color":"#a855f7",
        "desc":"設定下週 MIT，整理待辦，更新持倉成本"},
}

def _get_upgrade_tasks(weekday: int, df, cry_q: dict) -> list:
    """根據星期幾 + 實際持倉狀況，生成 3 個具體可執行任務"""
    tasks = []

    if weekday == 0:  # 投資體能
        # 找虧損最深的標的
        if df is not None and not df.empty:
            worst = df.nsmallest(1, "總損益(%)").iloc[0]
            sym = worst["標的"]; pct = worst["總損益(%)"]
            tasks.append(f"**{sym}** 目前虧損 {pct:.1f}%，花 15 分鐘搜尋最新季報或新聞，判斷是否停損或補倉")
        tasks.append("列出你持有這檔股票/幣的「3 個買入理由」，今天還成立幾個？")
        tasks.append("設定一個具體的「出場條件」：若發生 ___ 就賣出")

    elif weekday == 1:  # 技術升級
        tasks.append("從 YouTube 研究筆記區打開一支影片，邊看邊記下 3 個可執行結論")
        tasks.append("研究一個你不懂的投資術語，用自己的話寫一行解釋")
        tasks.append("在待辦清單新增一個「本週要研究」的標的或概念")

    elif weekday == 2:  # 風險管理
        # 找離停損最近的部位
        tasks.append("打開持倉卡片，逐一確認每個標的的「停損價」是否還合理")
        # Check crypto stop distances
        in_danger = []
        for sym, info in CRYPTO_WATCHLIST.items():
            q = cry_q.get(sym, {})
            price = q.get("price", 0)
            stop = info["stop"]
            if price > 0 and (price - stop) / price < 0.15:
                in_danger.append(f"{sym}（現價 ${price:.2f}，停損 ${stop}，距停損 {(price-stop)/price*100:.0f}%）")
        if in_danger:
            tasks.append(f"⚠️ 以下標的距停損不足 15%，今天決定要不要調整：{', '.join(in_danger)}")
        else:
            tasks.append("計算你目前所有部位的總風險：如果全部觸停損，最大虧損多少台幣？")
        tasks.append("檢查派網帳戶是否有設定止盈止損訂單，沒有的補上")

    elif weekday == 3:  # 撿漏掃描
        tasks.append("打開 FB Marketplace 撿漏區，看看今天有無新標的，手動搜尋一次")
        tasks.append("更新轉賣追蹤：有沒有已賣出的品項要記錄？有沒有新品要加入？")
        # 找觀察清單在進場區的幣
        in_zone = [s for s, info in CRYPTO_WATCHLIST.items()
                   if cry_q.get(s,{}).get("price",0) > 0 and
                      cry_q.get(s,{}).get("price",0) <= info["entry_zone"][1]]
        if in_zone:
            tasks.append(f"🟢 {', '.join(in_zone)} 在進場區，今天評估是否要小倉試單（10% 倉位）")
        else:
            tasks.append("翻一翻蝦皮/PTT 二手版，找有沒有比 FB 更好的轉賣機會")

    elif weekday == 4:  # 週複盤
        if df is not None and not df.empty:
            total_today = df["今日(TWD)"].sum()
            sign = "+" if total_today >= 0 else ""
            tasks.append(f"今日帳面損益 {sign}{total_today:,.0f} TWD，思考：這個結果是運氣還是判斷力？")
        tasks.append("寫下本週「做對的一件事」和「如果重來要改變的一件事」")
        tasks.append("下週是否有財報、Fed 發言、重要數據？先排入日曆，避免被突發消息嚇到")

    elif weekday == 5:  # 身體升級
        tasks.append("30 分鐘運動（慢跑/重訓/游泳任一），完成後在復盤表單打卡")
        tasks.append("今天完全不看盤，讓大腦休息；只有早上 09:30 看一次開盤")
        tasks.append("閱讀 20 頁實體書（非投資相關），在睡前寫一行最大收穫")

    else:  # 週日 計畫下週
        tasks.append("設定下週唯一 MIT（Most Important Task），寫進表單的「明天第一任務」")
        tasks.append("整理待辦清單：刪掉超過 2 週未動的任務，保持清單不超過 10 項")
        if df is not None and not df.empty:
            tasks.append(f"更新持倉成本：側欄「持倉編輯」確認 {len(df)} 個部位的成本是否正確")

    return tasks[:3]


def _log_upgrade_done(weekday: int):
    os.makedirs(os.path.dirname(_UPGRADE_FILE), exist_ok=True)
    today = date.today().isoformat()
    try:
        with open(_UPGRADE_FILE, "a", encoding="utf-8", newline="") as f:
            import csv as _csv
            w = _csv.writer(f)
            w.writerow([today, weekday, DAILY_THEMES[weekday]["name"]])
    except:
        pass


def _upgrade_done_today() -> bool:
    today = date.today().isoformat()
    try:
        with open(_UPGRADE_FILE, "r", encoding="utf-8") as f:
            return any(today in line for line in f)
    except:
        return False


@st.fragment
def render_daily_upgrade(df=None, cry_q: dict = {}):
    st.header("⚡ 每日升級計畫")

    today_wd = date.today().weekday()  # 0=Mon … 6=Sun
    theme    = DAILY_THEMES[today_wd]
    done     = _upgrade_done_today()

    # ── 7天週曆 ──────────────────────────────────────
    day_names = ["一","二","三","四","五","六","日"]
    cols7 = st.columns(7)
    for i, c in enumerate(cols7):
        t = DAILY_THEMES[i]
        is_today = (i == today_wd)
        bg = t["color"] if is_today else "#1e1e2e"
        border = f"border:2px solid {t['color']}" if is_today else "border:1px solid #334155"
        c.markdown(f"""
<div style="background:{bg};{border};border-radius:8px;padding:8px 4px;text-align:center">
  <div style="font-size:16px">{t['icon']}</div>
  <div style="font-size:11px;color:{'#fff' if is_today else '#94a3b8'}">週{day_names[i]}</div>
  <div style="font-size:10px;color:{'#fff' if is_today else '#64748b'}">{t['name']}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── 今日主題卡 ────────────────────────────────────
    done_badge = "✅ 今日已完成" if done else "⬜ 尚未完成"
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{theme['color']}22,#1e1e2e);
     border-left:5px solid {theme['color']};border-radius:10px;padding:16px 20px;margin:8px 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="font-size:28px">{theme['icon']}</span>
      <span style="font-size:20px;font-weight:bold;margin-left:10px">今日主題：{theme['name']}</span>
      <span style="background:{theme['color']}33;color:{theme['color']};
            padding:2px 10px;border-radius:12px;font-size:12px;margin-left:12px">{done_badge}</span>
    </div>
  </div>
  <div style="color:#94a3b8;margin-top:6px;font-size:14px">{theme['desc']}</div>
</div>""", unsafe_allow_html=True)

    # ── 今日任務清單 ──────────────────────────────────
    st.markdown("#### 📋 今日 3 項任務")
    tasks = _get_upgrade_tasks(today_wd, df, cry_q)
    for i, task in enumerate(tasks, 1):
        key = f"upgrade_task_{i}"
        checked = st.session_state.get(key, False)
        col_chk, col_txt = st.columns([0.5, 9.5])
        with col_chk:
            if st.checkbox("", key=key, value=checked):
                st.session_state[key] = True
        with col_txt:
            prefix = f"~~任務 {i}：~~" if st.session_state.get(key) else f"**任務 {i}：**"
            st.markdown(f"{prefix} {task}")

    # ── 完成按鈕 ──────────────────────────────────────
    if not done:
        if st.button(f"🏆 完成今日升級：{theme['name']}", type="primary", key="upgrade_done_btn"):
            _log_upgrade_done(today_wd)
            st.success(f"🎉 太棒了！今日「{theme['name']}」升級完成！")
            st.balloons()
            st.rerun()
    else:
        st.success(f"✅ 今日升級已完成！繼續保持連勝！")

    # ── 連續升級天數 ──────────────────────────────────
    try:
        with open(_UPGRADE_FILE, "r", encoding="utf-8") as f:
            import csv as _csv_r
            rows = list(_csv_r.reader(f))
        if rows:
            streak = 0
            check_date = date.today()
            dates_done = {r[0] for r in rows if r}
            while check_date.isoformat() in dates_done:
                streak += 1
                check_date -= timedelta(days=1)
            if streak > 0:
                st.metric("🔥 連續升級天數", f"{streak} 天",
                          delta="繼續保持！" if streak >= 3 else None)
    except:
        pass


# ════════════════════════════════════════════════════
# 今日狀態列（手癢指數 + VIX + 儲蓄目標）
# ════════════════════════════════════════════════════
def render_status_bar(df, exrate):
    st.subheader("📊 今日狀態")
    vix_d  = fetch_vix()
    vix    = vix_d["vix"]
    vix_chg= vix_d["chg"]

    # VIX 市場情緒
    if vix >= 30:
        mkt_label, mkt_color = "🔴 市場恐慌", "#ef4444"
        mkt_note = "極度恐慌，非理性拋售可能出現機會，嚴控部位"
    elif vix >= 22:
        mkt_label, mkt_color = "🟠 市場緊張", "#f97316"
        mkt_note = "波動升高，觀察方向確立再入場，避免追跌"
    elif vix <= 14:
        mkt_label, mkt_color = "🟠 市場自滿", "#f97316"
        mkt_note = "VIX 極低，市場過度樂觀，留意潛在反轉風險"
    else:
        mkt_label, mkt_color = "🟢 市場正常", "#22c55e"
        mkt_note = "正常波動區間，可按計劃執行"

    # 手癢指數
    total_val   = df["現值(TWD)"].sum()
    today_total = df["今日(TWD)"].sum()
    today_pct   = abs(today_total) / (total_val - today_total) * 100 if total_val > 0 else 0
    heat = min(int(
        (max(vix - 15, 0) / 20 * 40) +   # VIX 貢獻
        (min(today_pct / 5 * 40, 40)) +   # 今日波動貢獻
        (20 if vix >= 28 or vix <= 13 else 0)  # 極端值加成
    ), 100)
    if heat >= 70:
        hand_label = "🔴 高度警戒 — 先深呼吸再決策"
        hand_color = "#ef4444"
    elif heat >= 40:
        hand_label = "🟡 適度注意 — 避免衝動操作"
        hand_color = "#eab308"
    else:
        hand_label = "🟢 冷靜狀態 — 按計劃執行"
        hand_color = "#22c55e"

    # 儲蓄目標
    sv_cur  = float(_h.get("savings_current", 0))
    sv_tgt  = float(_h.get("savings_target", 150000))
    sv_dead = _h.get("savings_deadline", "2026-05-31")
    sv_pct  = min(sv_cur / sv_tgt, 1.0) if sv_tgt else 0
    try:
        days_left = (datetime.strptime(sv_dead, "%Y-%m-%d").date() - datetime.now().date()).days
    except:
        days_left = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("😱 VIX 恐慌指數", f"{vix:.1f}", f"{vix_chg:+.2f}")
        st.markdown(f'<span style="color:{mkt_color};font-size:13px">{mkt_label}</span>', unsafe_allow_html=True)
        st.caption(mkt_note)
    with c2:
        st.markdown(f"**🌡️ 手癢指數　{heat}/100**")
        st.progress(heat / 100)
        st.markdown(f'<span style="color:{hand_color};font-size:13px">{hand_label}</span>', unsafe_allow_html=True)
    with c3:
        st.markdown(f"**💰 儲蓄目標　{sv_pct*100:.0f}%**")
        st.progress(sv_pct)
        st.caption(f"NT${sv_cur:,.0f} / NT${sv_tgt:,.0f}　剩 {days_left} 天")
        if days_left > 0 and sv_cur < sv_tgt:
            need_per_day = (sv_tgt - sv_cur) / days_left
            st.caption(f"每天需存 NT${need_per_day:,.0f}")
    with c4:
        total_assets = total_val + sv_cur
        st.metric("📦 總資產（投資+現金）", f"NT${total_assets:,.0f}")
        st.caption(f"投資 {total_val:,.0f} + 現金 {sv_cur:,.0f}")


# ════════════════════════════════════════════════════
# 投資組合歷史走勢
# ════════════════════════════════════════════════════
def render_portfolio_history():
    df_h = load_history()
    if df_h.empty or len(df_h) < 2:
        return
    st.subheader("📈 總市值歷史走勢")
    fig = go.Figure(go.Scatter(
        x=df_h["時間"], y=df_h["總市值(TWD)"],
        mode="lines", fill="tozeroy",
        line=dict(color="#7c3aed", width=2),
        fillcolor="rgba(124,58,237,0.15)",
        hovertemplate="%{x|%m/%d %H:%M}<br>NT$%{y:,.0f}<extra></extra>",
    ))
    first, last = df_h["總市值(TWD)"].iloc[0], df_h["總市值(TWD)"].iloc[-1]
    chg = last - first
    fig.update_layout(
        height=220, margin=dict(l=0,r=0,t=30,b=0),
        title=f"近期走勢　{'▲' if chg>=0 else '▼'} NT${abs(chg):,.0f}　({chg/first*100:+.2f}%)",
        yaxis=dict(tickformat=",.0f"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════
# Insider Trading 監控
# ════════════════════════════════════════════════════
def render_insider_trading(held_syms):
    st.subheader("🕵️ Insider Trading 監控")
    st.caption("SEC EDGAR Form 4　近 60 天美股內部人交易申報（按需載入）")
    if st.button("🔍 載入最新內部人交易", key="btn_insider"):
        st.session_state["insider_loaded"] = True
    if not st.session_state.get("insider_loaded"):
        return
    us_syms = tuple(s for s in held_syms
                    if s not in ("USDT","ETH","ADA","ARKM","BTC","BNB") and "X" not in s)[:8]
    with st.spinner(f"查詢 {len(us_syms)} 支標的的 SEC Form 4..."):
        trades = fetch_insider_trades(us_syms)
    if not trades:
        st.info("近 60 天無查詢到 Form 4 申報，或 SEC 網路暫時無法連線。")
        return
    df_ins = pd.DataFrame(trades)
    st.dataframe(df_ins[["標的","申報人","日期","公司"]], use_container_width=True, hide_index=True)
    st.caption("點擊連結查看完整申報內容 → 搜尋對應標的的 Form 4")
    for _, row in df_ins.iterrows():
        st.markdown(
            f'[🔗 {row["標的"]} SEC EDGAR]({row["連結"]})', unsafe_allow_html=False
        )


# ════════════════════════════════════════════════════
# YouTube 研究筆記
# ════════════════════════════════════════════════════

# 頻道設定（channel_id 可在 config.json 的 "youtube_channels" 欄位覆蓋）
DEFAULT_YT_CHANNELS = [
    {"name": "Money or Life 美股頻道", "channel_id": "UCcd3BOzMqZR0AK1wMmMz81Q"},
    {"name": "3%財富覺醒 Arthur",      "channel_id": "UCxPdMPRixCXvdWLqf0EVBFQ"},
    {"name": "股癌 Gooaye",            "channel_id": "UCN0OPGTqgWFBDkDgyFbZ4IA"},
]

# 股票代碼正則（英文大寫2~5字母，排除常見縮寫）
import re as _re
_TICKER_SKIP = {"AI","US","CEO","CFO","EPS","IPO","ETF","GDP","FED","USA","NYSE","AND","THE","FOR","NOT","ARE","BUT","YOU","ALL","NEW","CAN","HAS","OR"}
_TICKER_RE   = _re.compile(r'\b([A-Z]{2,5})\b')

def _extract_tickers(text: str) -> list:
    found = _TICKER_RE.findall(text)
    return list(dict.fromkeys(t for t in found if t not in _TICKER_SKIP))[:12]


@st.cache_data(ttl=1800)
def fetch_yt_channel_videos(channel_id: str, max_items: int = 6) -> list:
    """YouTube RSS → 最新影片列表"""
    import xml.etree.ElementTree as _ET
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            root = _ET.fromstring(r.read())
        ns = {"atom":"http://www.w3.org/2005/Atom",
              "yt":  "http://www.youtube.com/xml/schemas/2015",
              "media":"http://search.yahoo.com/mrss/"}
        videos = []
        for entry in root.findall("atom:entry", ns)[:max_items]:
            vid_id = entry.findtext("yt:videoId", "", ns)
            title  = entry.findtext("atom:title", "", ns)
            pub    = (entry.findtext("atom:published", "", ns) or "")[:10]
            desc_el= entry.find(".//media:description", ns)
            desc   = (desc_el.text or "").strip()[:600] if desc_el is not None else ""
            videos.append({
                "id": vid_id, "title": title, "date": pub,
                "desc": desc,
                "url":  f"https://www.youtube.com/watch?v={vid_id}",
                "thumb":f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
            })
        return videos
    except:
        return []


@st.cache_data(ttl=3600)
def fetch_yt_transcript(video_id: str) -> str:
    """嘗試抓取 YouTube 自動字幕，回傳前 3000 字"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        segs = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["zh-TW","zh-CN","zh","en"])
        return " ".join(s["text"] for s in segs)[:3000]
    except:
        return ""


def _summarise_transcript(text: str, title: str) -> dict:
    """從逐字稿粗提要點：找股票代碼、百分比數字、關鍵句"""
    tickers = _extract_tickers(text + " " + title)
    # 找所有包含百分比的句子
    pct_sents = []
    for sent in _re.split(r'[。！？\n]', text):
        if _re.search(r'\d+\.?\d*%', sent) and len(sent) > 8:
            pct_sents.append(sent.strip()[:80])
    # 找包含關鍵投資詞的句子
    kw = ["目標","停損","加倉","減倉","看好","看空","買入","賣出","財報","利多","利空",
          "support","target","buy","sell","hold","earnings","breakout"]
    key_sents = []
    for sent in _re.split(r'[。！？\n]', text):
        if any(k in sent.lower() for k in kw) and 10 < len(sent) < 120:
            key_sents.append(sent.strip())
    return {
        "tickers":   tickers[:8],
        "pct_sents": pct_sents[:5],
        "key_sents": list(dict.fromkeys(key_sents))[:6],
    }

TODOS_FILE = os.path.join(os.path.dirname(__file__), "data", "todos.json")

def _load_todos() -> list:
    os.makedirs(os.path.dirname(TODOS_FILE), exist_ok=True)
    if os.path.isfile(TODOS_FILE):
        try:
            with open(TODOS_FILE) as f:
                return json.load(f)
        except:
            pass
    # 預設待辦清單
    defaults = [
        {"id":1,  "done":False, "tag":"🔴緊急", "text":"觀察 TSLA Q1 財報（下週一）"},
        {"id":2,  "done":False, "tag":"🔴緊急", "text":"觀察 INTC Q1 財報（下週）— Ace 由空轉多"},
        {"id":3,  "done":False, "tag":"🟡持倉",  "text":"JOBY 考慮出場 — 內部人連續賣股，無獲利路徑"},
        {"id":4,  "done":False, "tag":"🟡持倉",  "text":"NVDL 已獲利 +26%，趁漲鎖利出場換穩健標的"},
        {"id":5,  "done":False, "tag":"🟡持倉",  "text":"PYPL / RUN 倉位極小，清掉換有動能標的"},
        {"id":6,  "done":False, "tag":"🟡持倉",  "text":"ARKM 考慮認賠換 ORCL/MSFT"},
        {"id":7,  "done":False, "tag":"🟢研究",  "text":"評估 IRDM 進場 — Ace 成本$29，目標$60+"},
        {"id":8,  "done":False, "tag":"🟢研究",  "text":"評估 INTC 小倉佈局 — 等財報後確認方向"},
        {"id":9,  "done":False, "tag":"🟢研究",  "text":"研究 ICHR — 半導體設備上游，AI受益"},
        {"id":10, "done":False, "tag":"🟢研究",  "text":"考慮 MSTR 定額策略作為 BTC 替代倉位"},
        {"id":11, "done":False, "tag":"⚙️系統",  "text":"設定 GitHub Secrets：GMAIL_USER + GMAIL_APP_PASSWORD（讓掃描代理可發 Email）"},
        {"id":12, "done":False, "tag":"⚙️系統",  "text":"申請 Gmail App Password（二步驟驗證後在 Google 帳號設定）"},
        {"id":13, "done":False, "tag":"⚙️系統",  "text":"確認 market_agent.yml 已在 GitHub Actions 頁面可手動觸發測試"},
        {"id":14, "done":False, "tag":"🟡持倉",  "text":"HIMS — FDA 利好後評估是否加碼（現持倉：國泰3股 + 派網1.23股）"},
        {"id":15, "done":False, "tag":"🟢研究",  "text":"Circle 跌破 $100 考慮重新買入（Ace 已清倉）"},
    ]
    with open(TODOS_FILE, "w") as f:
        json.dump(defaults, f, ensure_ascii=False, indent=2)
    return defaults

def _save_todos(todos: list):
    os.makedirs(os.path.dirname(TODOS_FILE), exist_ok=True)
    with open(TODOS_FILE, "w") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

_config_file = os.path.join(os.path.dirname(__file__), "config.json")

def _load_scraper_config():
    try:
        with open(_config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@st.fragment
def render_research_notes():
    st.header("📺 YouTube 研究筆記")

    # ── 頻道設定（讀 config.json 覆蓋）──────────────────
    cfg_channels = _load_scraper_config().get("youtube_channels", DEFAULT_YT_CHANNELS)

    # ── 頻道影片卡牆 ──────────────────────────────────
    for ch in cfg_channels:
        ch_name = ch.get("name", "頻道")
        ch_id   = ch.get("channel_id", "")
        if not ch_id:
            continue
        with st.expander(f"📡 {ch_name}", expanded=(ch == cfg_channels[0])):
            with st.spinner(f"抓取 {ch_name} 最新影片..."):
                videos = fetch_yt_channel_videos(ch_id, max_items=5)
            if not videos:
                st.warning("無法連線或頻道 ID 錯誤，請至 config.json 確認 youtube_channels 設定")
                st.code(f'{{ "name": "{ch_name}", "channel_id": "UCxxxxxxx" }}')
                continue

            for v in videos:
                tickers_from_title = _extract_tickers(v["title"])
                v_col, btn_col = st.columns([8, 1])
                with v_col:
                    ticker_badges = " ".join(
                        f'<span style="background:#1e293b;color:#7c3aed;padding:1px 6px;border-radius:4px;font-size:11px">{t}</span>'
                        for t in tickers_from_title
                    )
                    st.markdown(f"""
<div style="background:#1e1e2e;border-radius:8px;padding:10px 14px;margin:4px 0">
  <div style="display:flex;gap:12px;align-items:flex-start">
    <img src="{v['thumb']}" style="width:120px;border-radius:6px;flex-shrink:0" onerror="this.style.display='none'">
    <div style="flex:1;min-width:0">
      <a href="{v['url']}" target="_blank"
         style="color:#e2e8f0;font-weight:bold;text-decoration:none;font-size:14px">{v['title']}</a>
      <div style="color:#64748b;font-size:12px;margin:3px 0">{v['date']}</div>
      <div style="margin:4px 0">{ticker_badges}</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:4px;white-space:pre-wrap">{v['desc'][:220] + ('…' if len(v['desc'])>220 else '')}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                with btn_col:
                    if st.button("分析", key=f"yt_analyse_{v['id']}"):
                        st.session_state[f"yt_show_{v['id']}"] = True

                # 逐字稿摘要（按需展開）
                if st.session_state.get(f"yt_show_{v['id']}"):
                    with st.spinner("抓取逐字稿並分析..."):
                        transcript = fetch_yt_transcript(v["id"])
                    if transcript:
                        summary = _summarise_transcript(transcript, v["title"])
                        st.markdown(f"**🎯 提到的標的：** " +
                            "".join(f'`{t}` ' for t in summary["tickers"]))
                        if summary["pct_sents"]:
                            st.markdown("**📊 重要數字：**")
                            for s in summary["pct_sents"]:
                                st.markdown(f"- {s}")
                        if summary["key_sents"]:
                            st.markdown("**💡 關鍵觀點：**")
                            for s in summary["key_sents"]:
                                st.markdown(f"- {s}")
                        with st.expander("📜 完整逐字稿"):
                            st.text(transcript)
                    else:
                        st.info("此影片沒有可用的字幕（需頻道開啟自動字幕）")

    # ── 手動輸入影片 URL 分析 ─────────────────────────
    st.divider()
    st.subheader("🔍 分析任意影片")
    manual_url = st.text_input("貼上 YouTube 影片連結",
                               placeholder="https://www.youtube.com/watch?v=...",
                               key="yt_manual_url")
    if st.button("📥 載入並分析", key="yt_manual_btn") and manual_url.strip():
        m = _re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_\-]{11})', manual_url)
        if m:
            vid_id = m.group(1)
            st.session_state["yt_manual_id"] = vid_id
        else:
            st.error("無法解析影片 ID，請確認連結格式")

    if st.session_state.get("yt_manual_id"):
        vid_id = st.session_state["yt_manual_id"]
        with st.spinner("抓取逐字稿..."):
            transcript = fetch_yt_transcript(vid_id)
        if transcript:
            summary = _summarise_transcript(transcript, "")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🎯 提到的標的**")
                st.write("  ".join(f"`{t}`" for t in summary["tickers"]) or "—")
                if summary["pct_sents"]:
                    st.markdown("**📊 重要數字**")
                    for s in summary["pct_sents"]: st.markdown(f"- {s}")
            with c2:
                if summary["key_sents"]:
                    st.markdown("**💡 關鍵觀點**")
                    for s in summary["key_sents"]: st.markdown(f"- {s}")
            with st.expander("📜 完整逐字稿"):
                st.text_area("", transcript, height=300, key="yt_manual_transcript")
        else:
            st.warning("無可用字幕。這支影片可能未開啟自動字幕，或為私人影片。")
        st.caption(f"影片 ID: {vid_id}　[在 YouTube 開啟](https://www.youtube.com/watch?v={vid_id})")

    st.divider()

    # ── 待辦事項 ──────────────────────────────────────
    st.subheader("✅ 待辦事項")
    todos = _load_todos()
    tag_order = {"🔴緊急":0,"🟡持倉":1,"🟢研究":2,"⚙️系統":3}
    todos_sorted = sorted(todos, key=lambda x: (x.get("done",False), tag_order.get(x.get("tag",""),9)))

    pending   = [t for t in todos_sorted if not t.get("done")]
    completed = [t for t in todos_sorted if t.get("done")]

    changed = False
    for t in pending:
        col_chk, col_txt, col_tag = st.columns([0.5, 7, 1.5])
        with col_chk:
            if st.checkbox("", key=f"todo_{t['id']}", value=False):
                t["done"] = True; changed = True
        with col_txt:
            st.markdown(f"{t['text']}")
        with col_tag:
            st.caption(t.get("tag",""))

    if completed:
        with st.expander(f"✓ 已完成 ({len(completed)})"):
            for t in completed:
                col_chk, col_txt = st.columns([0.5, 9])
                with col_chk:
                    if st.checkbox("", key=f"todo_done_{t['id']}", value=True):
                        pass
                    else:
                        t["done"] = False; changed = True
                with col_txt:
                    st.markdown(f"~~{t['text']}~~")

    # 新增待辦
    new_col, tag_col, btn_col = st.columns([5, 2, 1])
    with new_col:
        new_text = st.text_input("新增待辦", placeholder="輸入新任務...", key="todo_new_text", label_visibility="collapsed")
    with tag_col:
        new_tag = st.selectbox("", ["🔴緊急","🟡持倉","🟢研究","⚙️系統"], key="todo_new_tag", label_visibility="collapsed")
    with btn_col:
        if st.button("＋ 新增", key="todo_add"):
            if new_text.strip():
                new_id = max((t["id"] for t in todos), default=0) + 1
                todos.append({"id": new_id, "done": False, "tag": new_tag, "text": new_text.strip()})
                changed = True

    if changed:
        _save_todos(todos)
        st.rerun()

    st.caption(f"待辦 {len(pending)} 項 · 已完成 {len(completed)} 項")


# ════════════════════════════════════════════════════
# 台股觀察清單
# ════════════════════════════════════════════════════
@st.fragment
def render_tw_watchlist(tw_q: dict):
    st.header("🇹🇼 台股即時入場觀察")

    rows = []
    for code, info in TW_WATCHLIST.items():
        q     = tw_q.get(code, {})
        price = q.get("price", 0.0)
        chg   = q.get("chg_pct", 0.0)
        lo, hi = info["entry_zone"]

        if price <= 0:
            status = "⚪ 無資料"
            score  = 0
        elif price < lo * 0.8:
            status = "🔵 超跌觀察"
            score  = 5
        elif price <= hi:
            status = "🟢 進場區！"
            score  = 10
        elif price <= hi * 1.1:
            status = "🟡 靠近上緣"
            score  = 6
        else:
            status = "⚪ 待觀望"
            score  = 0

        if price > 0 and info["stop"] > 0:
            mid    = (lo + hi) / 2
            rr_num = (info["target"] - mid) / max(mid - info["stop"], 1)
        else:
            rr_num = 0

        rows.append({
            "優先": info["priority"],
            "代號": code,
            "名稱": info["name"],
            "主題": info["theme"],
            "現價": price,
            "今日%": chg,
            "入場區": f"{lo:,.0f}–{hi:,.0f}",
            "目標": info["target"],
            "停損": info["stop"],
            "R:R": f"1:{rr_num:.1f}",
            "狀態": status,
            "_score": score,
            "_rr": rr_num,
        })

    rows.sort(key=lambda r: (-r["_score"], r["優先"]))

    # ── 可進場標的提示卡 ──────────────────────────────
    in_zone = [r for r in rows if r["_score"] >= 6]
    if in_zone:
        medals = ["🥇","🥈","🥉"] + ["📌"] * 10
        st.subheader(f"✅ 目前可入場標的（{len(in_zone)} 檔）")
        cols = st.columns(min(len(in_zone), 3))
        for i, r in enumerate(in_zone[:3]):
            with cols[i]:
                chg_str = f"+{r['今日%']:.1f}%" if r['今日%'] >= 0 else f"{r['今日%']:.1f}%"
                chg_color = "#22c55e" if r['今日%'] >= 0 else "#ef4444"
                st.markdown(f"""
<div style='background:#1a2744;border:1px solid #334155;border-radius:12px;padding:16px'>
  <div style='font-size:22px'>{medals[i]} {r['名稱']} <span style='color:#94a3b8;font-size:14px'>{r['代號']}</span></div>
  <div style='font-size:26px;font-weight:bold;margin:6px 0'>NT${r['現價']:,.0f}
    <span style='font-size:14px;color:{chg_color}'>{chg_str}</span></div>
  <div style='color:#fbbf24'>🎯 目標 NT${r['目標']:,} &nbsp; 🛡️ 停損 NT${r['停損']:,}</div>
  <div style='color:#a78bfa;margin-top:4px'>⚖️ R:R {r["R:R"]} &nbsp; {r["狀態"]}</div>
  <div style='color:#64748b;font-size:12px;margin-top:6px'>{r["主題"]}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("目前無標的落在入場區，繼續等待回調機會 📡")

    # ── 完整觀察清單表格 ──────────────────────────────
    st.subheader("📋 完整觀察清單")
    df_show = []
    for r in rows:
        chg_str = f"+{r['今日%']:.1f}%" if r['今日%'] >= 0 else f"{r['今日%']:.1f}%"
        df_show.append({
            "P": r["優先"],
            "代號": r["代號"],
            "名稱": r["名稱"],
            "現價": f"NT${r['現價']:,.0f}" if r["現價"] > 0 else "—",
            "今日": chg_str,
            "入場區(TWD)": r["入場區"],
            "目標": f"NT${r['目標']:,}",
            "R:R": r["R:R"],
            "狀態": r["狀態"],
        })
    st.dataframe(pd.DataFrame(df_show), use_container_width=True, hide_index=True)

    # ── 理由展開 ──────────────────────────────────────
    with st.expander("📖 各標的分析理由"):
        for code, info in sorted(TW_WATCHLIST.items(), key=lambda x: x[1]["priority"]):
            q = tw_q.get(code, {})
            price = q.get("price", 0.0)
            price_str = f"NT${price:,.0f}" if price > 0 else "—"
            st.markdown(f"**{info['priority']}. {info['name']} ({code})** · 現價 {price_str} · 進場區 NT${info['entry_zone'][0]:,}–{info['entry_zone'][1]:,}")
            st.caption(info["reason"])


# ════════════════════════════════════════════════════
# 加密貨幣追蹤 + 觀察清單
# ════════════════════════════════════════════════════
@st.fragment
def render_crypto_dashboard(cry_q: dict, exrate: float):
    st.header("🪙 加密貨幣追蹤")

    # ── 持倉幣種即時行情 ──────────────────────────────
    st.subheader("📡 持倉幣種行情")
    held_coins = list(PIONEX_CRYPTO.keys()) + ["BTC"]
    n = len(held_coins)
    cols = st.columns(min(n, 4))
    for i, sym in enumerate(held_coins):
        q = cry_q.get(sym, {})
        price = q.get("price", 0)
        chg   = q.get("chg_pct", 0)
        mcap  = q.get("mcap", 0)
        c = cols[i % 4]
        c.metric(sym, f"${price:,.4f}" if price < 1 else f"${price:,.2f}", f"{chg:+.2f}%")
        if mcap:
            c.caption(f"市值 ${mcap/1e9:.1f}B")

    st.divider()

    # ── 優先排名 + 觀察清單 ──────────────────────────────
    st.subheader("🏆 入場優先排名")

    # 計算 R:R 和狀態
    wl_rows = []
    for sym, info in CRYPTO_WATCHLIST.items():
        q     = cry_q.get(sym, {})
        price = q.get("price", 0)
        chg   = q.get("chg_pct", 0)
        lo, hi = info["entry_zone"]
        target = info["target"]
        stop   = info["stop"]

        if price == 0:
            status = "❓"
        elif price < lo:
            # 已低於進場區下界：判斷超跌程度
            pct_below = (lo - price) / lo * 100
            if pct_below > 30:
                status = "🔵 超跌觀察"   # 跌太深，需等反彈確認
            else:
                status = "🟢 進場區！"
        elif price <= hi:
            status = "🟢 進場區！"
        elif (price - hi) / hi * 100 <= 20:
            status = "🟡 接近進場"
        else:
            status = "⚪ 等待"

        upside = (target - price) / price * 100 if price else 0
        downside = (price - stop) / price * 100 if price else 0
        rr = upside / downside if downside > 0 else 0

        pct_vs_lo = (price - lo) / lo * 100  # 正=高於進場區下界, 負=低於
        price_fmt  = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
        target_fmt = f"${target:,.4f}" if target < 1 else f"${target:,.0f}"
        lo_fmt = f"${lo:,.4f}" if lo < 1 else f"${lo:,.0f}"
        hi_fmt = f"${hi:,.4f}" if hi < 1 else f"${hi:,.0f}"
        stop_fmt   = f"${stop:,.0f}" if stop >= 1 else f"${stop:.4f}"

        wl_rows.append({
            "_priority": info.get("priority", 9),
            "_rr":       rr,
            "_price":    price,
            "_pct_vs_lo": pct_vs_lo,
            "優先": f"#{info.get('priority',9)}",
            "狀態":   status,
            "幣種":   sym,
            "主題":   info["theme"],
            "現價":   price_fmt,
            "今日":   f"{chg:+.1f}%",
            "進場區": f"{lo_fmt}~{hi_fmt}",
            "目標":   target_fmt,
            "潛力":   f"+{upside:.0f}%",
            "R:R":    f"{rr:.1f}x",
            "停損":   stop_fmt,
            "邏輯":   info["reason"],
        })

    wl_df = pd.DataFrame(wl_rows)
    wl_df_sorted = wl_df.sort_values("_priority")

    # ── 首選推薦卡片 ──────────────────────────────────
    top3 = wl_df_sorted.head(3)
    cols3 = st.columns(3)
    rank_labels = ["🥇 首選", "🥈 次選", "🥉 第三"]
    rank_colors = ["#f59e0b", "#94a3b8", "#cd7c2f"]
    for i, (_, r) in enumerate(top3.iterrows()):
        with cols3[i]:
            st.markdown(f"""
<div style="background:#1e1e2e;border-radius:10px;padding:14px;border:2px solid {rank_colors[i]};text-align:center">
  <div style="color:{rank_colors[i]};font-size:13px;font-weight:bold">{rank_labels[i]}</div>
  <div style="font-size:22px;font-weight:bold;margin:4px 0">{r['幣種']}</div>
  <div style="color:#94a3b8;font-size:12px">{r['主題']}</div>
  <div style="font-size:16px;margin:6px 0">{r['現價']} <span style="color:#64748b;font-size:12px">{r['今日']}</span></div>
  <div style="display:flex;justify-content:center;gap:12px;font-size:12px;margin-top:6px">
    <span>目標 <b style="color:#22c55e">{r['目標']}</b></span>
    <span>潛力 <b style="color:#22c55e">{r['潛力']}</b></span>
    <span>R:R <b style="color:#7c3aed">{r['R:R']}</b></span>
  </div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── 完整觀察清單表格（按優先排序）────────────────
    st.subheader("👀 完整觀察清單（優先排序）")

    in_zone = wl_df_sorted[wl_df_sorted["狀態"].str.contains("進場區！", na=False)]
    overshot = wl_df_sorted[wl_df_sorted["狀態"].str.contains("超跌", na=False)]
    near_df  = wl_df_sorted[wl_df_sorted["狀態"].str.contains("接近", na=False)]

    if not in_zone.empty:
        st.success(f"🟢 進場區內：{', '.join(in_zone['幣種'])}　← 可開始分批布局")
    if not overshot.empty:
        st.info(f"🔵 超跌觀察（等反彈確認再入）：{', '.join(overshot['幣種'])}")
    if not near_df.empty:
        st.warning(f"🟡 接近進場：{', '.join(near_df['幣種'])}")

    display_cols = ["優先","狀態","幣種","主題","現價","今日","進場區","目標","潛力","R:R","停損","邏輯"]
    show_df = wl_df_sorted[display_cols]

    def _color_crypto(val):
        if "進場區！" in str(val): return "background:#14532d;color:#86efac"
        if "超跌"    in str(val): return "background:#1e3a5f;color:#93c5fd"
        if "接近"    in str(val): return "background:#713f12;color:#fde68a"
        return ""

    st.dataframe(show_df.style.map(_color_crypto, subset=["狀態"]),
                 use_container_width=True, hide_index=True)

    # ── 詳細卡片（展開） ──────────────────────────────
    with st.expander("📋 觀察清單詳細分析（按優先排序）"):
        sorted_wl = sorted(CRYPTO_WATCHLIST.items(), key=lambda x: x[1].get("priority", 9))
        for sym, info in sorted_wl:
            q     = cry_q.get(sym, {})
            price = q.get("price", 0)
            chg   = q.get("chg_pct", 0)
            lo, hi = info["entry_zone"]
            target = info["target"]
            stop   = info["stop"]
            upside   = (target - price) / price * 100 if price else 0
            downside = (price - stop)  / price * 100 if price else 0
            rr = upside / downside if downside > 0 else 0
            tc = "#22c55e" if chg >= 0 else "#ef4444"
            price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"

            if price == 0:
                badge, border = "❓", "#334155"
            elif price < lo:
                pct_below = (lo - price) / lo * 100
                if pct_below > 30:
                    badge, border = "🔵 超跌觀察", "#3b82f6"
                else:
                    badge, border = "🟢 進場區！", "#22c55e"
            elif price <= hi:
                badge, border = "🟢 進場區！", "#22c55e"
            elif (price - hi) / hi * 100 <= 20:
                badge, border = "🟡 接近進場", "#f59e0b"
            else:
                badge, border = "⚪ 等待", "#334155"

            priority = info.get("priority", 9)
            rank_star = "★" * max(0, 5 - priority // 2)

            st.markdown(f"""
<div style="background:#1e1e2e;border-radius:8px;padding:14px;margin:6px 0;border-left:4px solid {border}">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
    <div>
      <span style="color:#64748b;font-size:12px">#{priority}</span>
      <span style="font-size:17px;font-weight:bold;margin-left:6px">{sym}</span>
      <span style="background:#1e293b;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:12px;margin-left:8px">{info['theme']}</span>
      <span style="margin-left:8px;font-size:12px">{badge}</span>
    </div>
    <div style="text-align:right">
      <span style="font-size:18px;font-weight:bold">{price_fmt}</span>
      <span style="color:{tc};margin-left:8px">{chg:+.2f}%</span>
    </div>
  </div>
  <div style="display:flex;gap:20px;margin-top:8px;font-size:13px;flex-wrap:wrap">
    <span>進場區 <b>${lo:g} ~ ${hi:g}</b></span>
    <span>目標 <b style="color:#22c55e">${target:g}</b></span>
    <span>潛力 <b style="color:#22c55e">+{upside:.0f}%</b></span>
    <span>R:R <b style="color:#7c3aed">{rr:.1f}x</b></span>
    <span>停損 <b style="color:#ef4444">${stop:g}</b></span>
  </div>
  <p style="color:#94a3b8;font-size:13px;margin:8px 0 0">{info['reason']}</p>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# 主畫面
# ════════════════════════════════════════════════════
_live_rate = fetch_usdtwd_rate()
_exrate = st.session_state.get("exchange_rate", _live_rate)

# 公開模式：網址帶 ?public=true 時隱藏金額，只顯示比例
_public_mode = st.query_params.get("public", "false").lower() == "true"
if _public_mode:
    st.info("👁️ 公開瀏覽模式：金額已隱藏，僅顯示比例與漲跌方向")

with st.spinner("抓取即時行情..."):
    df, us_q, tw_q, cry_q = build_portfolio(exrate=_exrate)

danger_list, entry_list = check_alerts(df, us_q, tw_q)

total_val   = df["現值(TWD)"].sum()
total_pnl   = df["損益(TWD)"].sum()
total_today = df["今日(TWD)"].sum()
_pnl_color  = "#22c55e" if total_pnl >= 0 else "#ef4444"
_td_color   = "#22c55e" if total_today >= 0 else "#ef4444"

_topbar_val = "****" if _public_mode else f"NT${total_val:,}"
_topbar_today = ("今日 🟢" if total_today >= 0 else "今日 🔴") if _public_mode else f"今日 NT${total_today:+,}"
_topbar_pnl   = (f"累積 {'🟢' if total_pnl >= 0 else '🔴'}{abs(total_pnl)/total_val*100:.1f}%") if _public_mode else f"累積 NT${total_pnl:+,}"

st.markdown(f"""
<div class="topbar-inner">
  <span class="brand">📊 Jim Finance</span>
  <span class="meta">
    {_topbar_val} &nbsp;
    <span style="color:{_td_color}">{_topbar_today}</span> &nbsp;
    <span style="color:{_pnl_color}">{_topbar_pnl}</span> &nbsp;
    USD/TWD {_exrate:.1f} &nbsp;
    {datetime.now().strftime('%H:%M')}
  </span>
</div>""", unsafe_allow_html=True)

# ── Helper functions (defined before tabs) ───────────

def _pnl_html(today, pnl):
    tc = "#22c55e" if today >= 0 else "#ef4444"
    pc = "#22c55e" if pnl   >= 0 else "#ef4444"
    return (f'<div style="font-size:13px;margin-top:4px">'
            f'<span style="color:{tc}">今日 NT${today:+,}</span>'
            f'<span style="color:#475569">　｜　</span>'
            f'<span style="color:{pc}">累積 NT${pnl:+,}</span>'
            f'</div>')

def build_rec_rows(df):
    buy_r, hold_r, sell_r = [], [], []
    seen = set()
    for _, row in df.iterrows():
        raw = row["標的"]; sym = raw.split("→")[-1] if "→" in raw else raw
        if sym in seen or sym in ("USDT","ETH","ADA","ARKM"): continue
        seen.add(sym)
        info = ANALYST.get(sym)
        if not info: continue
        price = row["現價"]; target = info["target"]
        upside = (target-price)/price*100 if target and price else 0
        plat = "/".join(set(df[df["標的"].str.contains(sym,na=False)]["平台"].tolist()))
        dist_stop = (price-info["stop"])/price*100 if info.get("stop") and price else 0
        rec_date = info.get("date","")
        try:
            days_old = (datetime.now() - datetime.strptime(rec_date, "%Y-%m-%d")).days
            date_label = f"{rec_date} ({'今日' if days_old==0 else f'{days_old}天前'}{'⚠️' if days_old>=7 else ''})"
        except:
            date_label = rec_date
        rec = {"標的":sym,"現價":f"${price:.2f}","目標":f"${target:.0f}" if target else "—",
               "距目標":f"+{upside:.0f}%" if upside>0 else "—",
               "距停損":f"-{dist_stop:.1f}%",
               "持倉損益":f"{row['總損益(%)']:+.1f}%",
               "停損":f"${info['stop']:.0f}" if info.get('stop') else "—",
               "平台":plat,"更新":date_label,"理由":info["reason"]}
        if info["action"] == "BUY":    buy_r.append(rec)
        elif info["action"] == "SELL": sell_r.append(rec)
        else:                          hold_r.append(rec)
    return buy_r, hold_r, sell_r

def _rec_card(rec, color):
    return (f'<div style="background:#1e1e2e;border-left:3px solid {color};padding:8px;'
            f'border-radius:4px;margin:4px 0;font-size:13px">'
            f'<b>{rec["標的"]}</b>　{rec["現價"]} → <b style="color:{color}">{rec["目標"]}</b>　{rec["距目標"]}<br>'
            f'損益 {rec["持倉損益"]}　停損 {rec["停損"]}<br>'
            f'<span style="color:#94a3b8">{rec["理由"]}</span></div>')

def render_platform_detail(df, platform):
    sub = df[df["平台"] == platform].copy()
    sub = sub.sort_values("今日(TWD)", ascending=False)
    v = sub["現值(TWD)"].sum(); p = sub["損益(TWD)"].sum(); t = sub["今日(TWD)"].sum()
    t_color = "🟢" if t >= 0 else "🔴"
    label = (f"{t_color} {platform}　市值 NT${v:,}　"
             f"今日 {'▲' if t>=0 else '▼'} NT${abs(t):,}　"
             f"累積 {'▲' if p>=0 else '▼'} NT${abs(p):,}")
    with st.expander(label):
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("總市值", f"NT${v:,}")
        mc2.metric("今日損益", f"NT${t:+,}", delta_color="normal" if t >= 0 else "inverse")
        mc3.metric("累積損益", f"NT${p:+,}", delta_color="normal" if p >= 0 else "inverse")
        st.divider()
        if not sub.empty:
            top_sym = sub.iloc[0]["標的"]; top_today = sub.iloc[0]["今日(TWD)"]
            if top_today > 0:   st.success(f"🏆 今日最強：**{top_sym}**　今日 NT${top_today:+,}")
            elif top_today < 0: st.error(f"📉 今日最弱：**{top_sym}**　今日 NT${top_today:+,}")
        max_abs = sub["今日(TWD)"].abs().max() or 1
        for rank_i, (_, row) in enumerate(sub.iterrows()):
            sym = row["標的"]; price = row["現價"]; value = row["現值(TWD)"]
            today_v = int(row["今日(TWD)"]); total_v = int(row["損益(TWD)"])
            today_pct = row["漲跌幅(%)"]; total_pct = row["總損益(%)"]
            bar_w = int(abs(today_v) / max_abs * 100)
            tc = "#22c55e" if today_v >= 0 else "#ef4444"
            pc = "#22c55e" if total_v >= 0 else "#ef4444"
            medal = ("🥇" if rank_i == 0 else "🥈" if rank_i == 1 else "🥉" if rank_i == 2 else f"&nbsp;&nbsp;{rank_i+1}.")
            st.markdown(f"""
<div style="background:#1e1e2e;border-radius:8px;padding:10px 14px;margin:5px 0;border-left:4px solid {tc}">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
    <span style="font-size:15px">{medal} <b>{sym}</b>
      <span style="color:#64748b;font-size:12px;margin-left:6px">${price:.2f}　NT${value:,}</span>
    </span>
    <div style="text-align:right;min-width:200px">
      <span style="color:{tc};font-weight:bold;font-size:15px">今日&nbsp;NT${today_v:+,}&nbsp;({today_pct:+.1f}%)</span><br>
      <span style="color:{pc};font-size:12px">累積&nbsp;NT${total_v:+,}&nbsp;({total_pct:+.1f}%)</span>
    </div>
  </div>
  <div style="background:#334155;border-radius:3px;height:5px;margin-top:8px">
    <div style="background:{tc};width:{bar_w}%;height:5px;border-radius:3px;transition:width 0.3s"></div>
  </div>
</div>""", unsafe_allow_html=True)

_RESALE_FILE = os.path.join(os.path.dirname(__file__), "data", "resale_items.json")

def _load_resale():
    try:
        with open(_RESALE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def _save_resale(items):
    os.makedirs(os.path.dirname(_RESALE_FILE), exist_ok=True)
    with open(_RESALE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

_deals_file = os.path.join(os.path.dirname(__file__), "deals.json")

def _load_deals():
    try:
        with open(_deals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_scan": None, "deals": []}

_DECISION_FILE = os.path.join(os.path.dirname(__file__), "data", "decisions.csv")
_DECISION_COLS = ["date","symbol","action","price","quantity","reasoning","confidence","market_condition"]

def _load_decisions() -> pd.DataFrame:
    if os.path.exists(_DECISION_FILE):
        try:
            return pd.read_csv(_DECISION_FILE, dtype=str)
        except:
            pass
    return pd.DataFrame(columns=_DECISION_COLS)

def _save_decision(row: dict):
    os.makedirs(os.path.dirname(_DECISION_FILE), exist_ok=True)
    exists = os.path.exists(_DECISION_FILE)
    with open(_DECISION_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_DECISION_COLS)
        if not exists:
            w.writeheader()
        w.writerow(row)

def _get_anthropic_key() -> str:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        pass
    try:
        with open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8") as f:
            return json.load(f).get("anthropic_api_key", "")
    except:
        return ""

def _build_portfolio_context(df: pd.DataFrame, tw_q: dict, cry_q: dict, exrate: float) -> str:
    today_str = date.today().strftime("%Y-%m-%d")
    total_val = df["現值(TWD)"].sum()
    total_gain = df["損益(TWD)"].sum()
    gain_pct = total_gain / (total_val - total_gain) * 100 if (total_val - total_gain) > 0 else 0
    lines = [
        f"今天日期：{today_str}，USD/TWD 匯率：{exrate:.1f}",
        f"總資產：NT${total_val:,.0f}，總損益：NT${total_gain:+,.0f}（{gain_pct:+.1f}%）",
        "", "== 持倉明細 ==",
    ]
    for _, row in df.sort_values("損益(TWD)", ascending=False).iterrows():
        lines.append(f"{row['平台']} | {row['標的']} | 現價 {row['現價']:.2f} | "
                     f"現值 NT${row['現值(TWD)']:,.0f} | 損益 NT${row['損益(TWD)']:+,.0f}")
    tw_in_zone = [f"{code} {info['name']} (現價 NT${tw_q.get(code,{}).get('price',0):,.0f}，入場區 {info['entry_zone'][0]}-{info['entry_zone'][1]})"
                  for code, info in TW_WATCHLIST.items()
                  if 0 < tw_q.get(code,{}).get("price",0) <= info["entry_zone"][1]]
    if tw_in_zone:
        lines += ["", "== 台股目前在入場區 =="] + tw_in_zone
    cry_in_zone = [f"{sym} (現價 ${cry_q.get(sym,{}).get('price',0):.4f}，入場區 {info['entry_zone'][0]}-{info['entry_zone'][1]})"
                   for sym, info in CRYPTO_WATCHLIST.items()
                   if 0 < cry_q.get(sym,{}).get("price",0) <= info["entry_zone"][1]]
    if cry_in_zone:
        lines += ["", "== 加密貨幣目前在入場區 =="] + cry_in_zone
    return "\n".join(lines)

@st.fragment
def render_decision_journal():
    st.header("📓 投資決策日誌")
    st.caption("記錄每次買賣理由 → 建立屬於你的投資記憶層")
    with st.expander("✍️ 新增決策記錄", expanded=False):
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            dj_date   = st.date_input("日期", value=date.today(), key="dj_date")
            dj_sym    = st.text_input("標的代號 / 名稱", placeholder="e.g. NKE, 2330", key="dj_sym").upper().strip()
            dj_action = st.selectbox("操作", ["買入","賣出","加碼","減碼","觀察","停損"], key="dj_action")
        with dc2:
            dj_price  = st.number_input("執行價格", min_value=0.0, step=0.01, key="dj_price")
            dj_qty    = st.number_input("數量（股/顆）", min_value=0.0, step=1.0, key="dj_qty")
            dj_mkt    = st.selectbox("市場情緒", ["多頭","空頭","震盪","不確定"], key="dj_mkt")
        with dc3:
            dj_conf   = st.slider("信心度 1–5", 1, 5, 3, key="dj_conf")
            dj_reason = st.text_area("決策理由（為什麼做這個決定？）", height=100, key="dj_reason",
                                     placeholder="e.g. NKE 跌到支撐區，RSI 超賣，基本面沒變，分批建倉")
        if st.button("💾 儲存這筆決策", key="dj_save"):
            if not dj_sym:
                st.warning("請填入標的代號")
            elif not dj_reason.strip():
                st.warning("請填入決策理由（這是最重要的部分！）")
            else:
                _save_decision({"date": str(dj_date), "symbol": dj_sym, "action": dj_action,
                                "price": dj_price, "quantity": dj_qty, "reasoning": dj_reason.strip(),
                                "confidence": dj_conf, "market_condition": dj_mkt})
                st.success("✅ 已記錄！")
                st.rerun()
    dj_df = _load_decisions()
    if not dj_df.empty:
        st.subheader(f"📋 歷史記錄（共 {len(dj_df)} 筆）")
        syms = ["全部"] + sorted(dj_df["symbol"].dropna().unique().tolist())
        filt = st.selectbox("篩選標的", syms, key="dj_filter")
        show = dj_df if filt == "全部" else dj_df[dj_df["symbol"] == filt]
        show = show.sort_values("date", ascending=False)
        ACTION_ICON = {"買入":"🟢","賣出":"🔴","加碼":"📈","減碼":"📉","觀察":"👁️","停損":"🛑"}
        CONF_STAR   = {1:"⭐",2:"⭐⭐",3:"⭐⭐⭐",4:"⭐⭐⭐⭐",5:"⭐⭐⭐⭐⭐"}
        for _, r in show.head(20).iterrows():
            icon  = ACTION_ICON.get(r.get("action",""), "📌")
            stars = CONF_STAR.get(int(r.get("confidence", 3)), "")
            st.markdown(f"""
<div style='background:#1e1e2e;border-radius:8px;padding:10px 14px;margin:5px 0;border-left:3px solid #7c3aed'>
  <div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px'>
    <span>{icon} <b>{r.get('action','')} {r.get('symbol','')}</b>
      <span style='color:#94a3b8;font-size:12px;margin-left:8px'>@{r.get('price','')}　×{r.get('quantity','')}</span>
    </span>
    <span style='color:#64748b;font-size:12px'>{r.get('date','')} &nbsp; {stars} &nbsp; {r.get('market_condition','')}</span>
  </div>
  <div style='color:#cbd5e1;font-size:13px;margin-top:6px'>{r.get('reasoning','')}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("還沒有任何記錄，開始記錄你的第一筆投資決策吧！")

@st.fragment
def render_ai_chat(df: pd.DataFrame, tw_q: dict, cry_q: dict, exrate: float):
    st.header("🤖 AI 投資助理")
    api_key = _get_anthropic_key()
    if not api_key:
        st.info("💡 要啟用 AI 助理，請在 Streamlit Secrets 加入 `ANTHROPIC_API_KEY`，或在 config.json 加入 `anthropic_api_key`。")
        with st.expander("如何設定？"):
            st.code("""# Streamlit Cloud → Settings → Secrets：\nANTHROPIC_API_KEY = "sk-ant-xxxx"\n\n# 或本機 config.json：\n{\n  "anthropic_api_key": "sk-ant-xxxx"\n}""")
        return
    try:
        import anthropic as _ant
    except ImportError:
        st.error("請先安裝：`pip install anthropic`")
        return
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    portfolio_ctx = _build_portfolio_context(df, tw_q, cry_q, exrate)
    SYSTEM_PROMPT = f"""你是 Jim 的專屬投資助理，叫做 Claude Finance。你說繁體中文，回答簡潔有力，每次不超過 200 字，除非被要求詳細說明。

以下是 Jim 目前的投資組合和市場狀況（即時資料）：

{portfolio_ctx}

Jim 的目標：2026年底存到 20 萬 TWD 可投資資金，目前專注美股、台股、加密貨幣三個市場。
回答時要結合上面的真實數據，不要說「我沒有數據」，數據就在上面。"""
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt := st.chat_input("問我任何關於你投資組合的問題…", key="ai_chat_input"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("思考中…"):
                try:
                    client = _ant.Anthropic(api_key=api_key)
                    resp   = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": m["role"], "content": m["content"]}
                                  for m in st.session_state.chat_history],
                    )
                    answer = resp.content[0].text
                except Exception as e:
                    answer = f"❌ API 錯誤：{e}"
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
    if st.session_state.chat_history:
        if st.button("🗑️ 清除對話", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# ════════════════════════════════════════════════════
# 4 個分頁
# ════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 投資", "🧠 生活系統", "🛍️ 撿漏轉賣", "🔬 研究", "🗺️ AI學習地圖", "📚 書庫"])

# ══════════════════════════════════════════
# TAB 1 — 投資
# ══════════════════════════════════════════
with tab1:
    # ── 警報區 ────────────────────────────
    if danger_list or entry_list:
        if entry_list:
            st.success("🚀 **急需入場警報**")
            for a in entry_list:
                st.markdown(f'<div class="alert-entry">{a}</div>', unsafe_allow_html=True)
        if danger_list:
            st.error("🚨 **個股危險警報**")
            for a in danger_list:
                st.markdown(f'<div class="alert-danger">{a}</div>', unsafe_allow_html=True)
        st.divider()

    # ── 今日狀態列 ────────────────────────
    render_status_bar(df, _exrate)
    st.divider()

    # ── 派網部位快照 ──────────────────────
    _px_file = os.path.join(os.path.dirname(__file__), "pionex_manual.json")
    if os.path.exists(_px_file):
        with open(_px_file, encoding="utf-8") as _pf:
            _px = json.load(_pf)
        with st.expander(f"📱 派網部位快照　更新：{_px.get('updated_at','—')}　總資產 ${_px.get('total_usd',0):,.2f}", expanded=True):
            _px_cols = st.columns(4)
            for _i, _pos in enumerate(_px.get("positions", [])):
                _sym = _pos["symbol"]
                _prc = _pos["price"]
                _chg = _pos["change"]
                _dir = _pos["direction"]
                _arrow = "🟢" if _dir == "up" else ("🔴" if _dir == "down" else "➡️")
                _chg_str = f"{_chg:+.2f}" if _chg != 0 else "持平"
                _display_price = "****" if _public_mode else f"${_prc:,.2f}"
                _display_chg   = _arrow if _public_mode else f"{_arrow} {_chg_str}"
                _px_cols[_i % 4].markdown(
                    f"<div style='background:#1e1e2e;border-radius:8px;padding:8px 12px;margin:4px 0'>"
                    f"<div style='font-size:12px;color:#94a3b8'>{_sym}</div>"
                    f"<div style='font-size:16px;font-weight:bold'>{_display_price}</div>"
                    f"<div style='font-size:12px'>{_display_chg}</div>"
                    f"</div>", unsafe_allow_html=True)
            if not _public_mode:
                with st.form("px_update"):
                    st.caption("更新快照（貼上新數據後送出）")
                    _pc1, _pc2, _pc3 = st.columns(3)
                    with _pc1:
                        _new_time  = st.text_input("更新時間", value=_px.get("updated_at",""), placeholder="2026-04-22 23:33")
                        _new_total = st.number_input("總資產 USD", value=float(_px.get("total_usd",0)), step=0.01)
                    with _pc2:
                        _new_raw = st.text_area("貼上數據（每行：標的 價格 變動，空白分隔）",
                            placeholder="MSFTX 431.93 1.29\nMETAX 674.92 0.30", height=150)
                    if st.form_submit_button("💾 更新"):
                        _new_positions = []
                        for _line in _new_raw.strip().split("\n"):
                            _parts = _line.strip().split()
                            if len(_parts) >= 3:
                                try:
                                    _s, _p, _c = _parts[0], float(_parts[1]), float(_parts[2])
                                    _new_positions.append({"symbol":_s,"price":_p,"change":_c,
                                        "direction":"up" if _c>0 else ("down" if _c<0 else "flat")})
                                except: pass
                        if _new_positions:
                            _px["updated_at"] = _new_time
                            _px["total_usd"]  = _new_total
                            _px["positions"]  = _new_positions
                            with open(_px_file, "w", encoding="utf-8") as _wf:
                                json.dump(_px, _wf, ensure_ascii=False, indent=2)
                            st.success("已更新！"); st.rerun()
    st.divider()

    # ── 市場 Insights ─────────────────────
    render_market_insights(us_q)
    st.divider()

    # ── 4 帳戶總覽 ────────────────────────
    _platforms = ["國泰美股","國泰台股","派網","Firstrade"]
    cols = st.columns(5)
    cols[0].metric("💰 總市值", f"NT$ {total_val:,}")
    cols[0].markdown(_pnl_html(total_today, total_pnl), unsafe_allow_html=True)
    for i, plat in enumerate(_platforms):
        sub   = df[df["平台"]==plat]
        val   = sub["現值(TWD)"].sum()
        today = sub["今日(TWD)"].sum()
        pnl   = sub["損益(TWD)"].sum()
        cols[i+1].metric(plat, f"NT$ {val:,}")
        cols[i+1].markdown(_pnl_html(today, pnl), unsafe_allow_html=True)
    st.divider()

    # ── Beta 壓力測試 ─────────────────────
    with st.expander("📉 Beta 壓力測試 — 市場下跌我損失多少？"):
        _BETA_MAP = {
            "MSTRX":2.8, "SMRX":3.0, "ARKM":2.5, "SOL":2.8, "IONQ":2.2,
            "IONQX":2.2, "SMCIX":2.2, "TSLAX":2.0, "NVOX":1.8, "HIMSX":1.2,
            "ORCLX":1.1, "METAX":1.3, "MSFTX":1.1,
            "TSLA":2.0, "RXRX":2.5, "JOBY":2.5, "HIMS":1.5, "LULU":1.2,
            "NKE":0.8, "ORCL":1.1, "MSFT":1.0,
            "00763U":0.7, "1303":0.9, "1326":0.9, "2027":0.9,
            "2317":1.1, "2344":1.2, "3481":1.2, "6148":1.0,
        }
        _DEFAULT_BETA = 1.2
        _beta_rows = []
        for _, row in df[~df["標的"].isin(["USDT"])].iterrows():
            sym  = row["標的"].split("→")[-1] if "→" in row["標的"] else row["標的"]
            val  = row["現值(TWD)"]
            beta = _BETA_MAP.get(sym, _DEFAULT_BETA)
            _beta_rows.append((sym, val, beta))
        total_v = sum(v for _, v, _ in _beta_rows)
        w_beta  = sum(v * b for _, v, b in _beta_rows) / total_v if total_v > 0 else _DEFAULT_BETA
        bc1, bc2, bc3, bc4 = st.columns(4)
        bc1.metric("加權 Beta", f"{w_beta:.2f}x", help="組合整體相對大盤波動倍數")
        for (label, pct), col in zip([("大盤 -5%",-5),("大盤 -10%",-10),("大盤 -20%",-20)], [bc2,bc3,bc4]):
            loss = total_v * (pct / 100) * w_beta
            col.metric(label, f"NT${loss:,.0f}", delta=f"{pct*w_beta:.1f}%", delta_color="inverse")
        high_beta = sorted([(s,v,b) for s,v,b in _beta_rows if b >= 2.0], key=lambda x: -x[2])[:5]
        if high_beta:
            st.caption("⚠️ 高 Beta 標的（Beta ≥ 2x）")
            _hb_df = pd.DataFrame([{"標的":s,"現值(TWD)":int(v),"Beta":b,"大盤-10%預估":f"NT${v*(-0.1)*b:,.0f}"} for s,v,b in high_beta])
            st.dataframe(_hb_df, hide_index=True, use_container_width=True)
    st.divider()

    # ── 出場 / 進場優先 ───────────────────
    col_exit, col_entry = st.columns(2)
    with col_exit:
        st.subheader("🚨 出場優先排名")
        exit_rows = []
        for _, row in df.iterrows():
            raw = row["標的"]; sym = raw.split("→")[-1] if "→" in raw else raw
            info = ANALYST.get(sym)
            if not info or info["action"] != "SELL": continue
            price = row["現價"]; pnl_pct = row["總損益(%)"]
            stop = info.get("stop", 0)
            dist_stop = (price - stop) / price * 100 if stop and price else 0
            urgency = -pnl_pct + (5 - dist_stop if dist_stop < 5 else 0)
            exit_rows.append({"_urgency":urgency,"標的":sym,"現價":f"${price:.2f}",
                               "損益":f"{pnl_pct:+.1f}%","停損":f"${stop:.0f}" if stop else "—",
                               "原因":info["reason"],"更新":info.get("date","")})
        exit_rows.sort(key=lambda x: x["_urgency"], reverse=True)
        for i, r in enumerate(exit_rows, 1):
            color = "#ef4444" if i == 1 else ("#f97316" if i == 2 else "#eab308")
            st.markdown(f"""
<div style="background:#1e1e2e;border-left:4px solid {color};padding:10px;border-radius:6px;margin:6px 0">
<b>#{i} {r['標的']}</b>　現價 {r['現價']}　損益 <span style="color:{color}">{r['損益']}</span>　停損 {r['停損']}<br>
<span style="font-size:13px;color:#94a3b8">{r['原因']}</span>
</div>""", unsafe_allow_html=True)
        if not exit_rows: st.info("目前無出場建議")

    with col_entry:
        st.subheader("🚀 進場優先排名")
        entry_rows = []; seen_syms = set()
        for _, row in df.iterrows():
            raw = row["標的"]; sym = raw.split("→")[-1] if "→" in raw else raw
            if sym in seen_syms: continue
            seen_syms.add(sym)
            info = ANALYST.get(sym)
            if not info or info["action"] != "BUY": continue
            price = row["現價"]; target = info.get("target", 0)
            upside = (target - price) / price * 100 if target and price else 0
            entry_rows.append({"_upside":upside,"標的":sym,"類型":"持倉加碼",
                                "現價":f"${price:.2f}","目標":f"${target:.0f}",
                                "潛力":f"+{upside:.0f}%","原因":info["reason"]})
        wl_q2 = fetch_us_quotes(tuple(WATCHLIST.keys()))
        for sym, info in WATCHLIST.items():
            q = wl_q2.get(sym, {}); price = q.get("price", 0)
            if not price: continue
            lo, hi = info["entry_zone"]
            if price > hi * 1.05: continue
            upside = (info["target"] - price) / price * 100 if price else 0
            status = "🟢 已進場區" if price <= hi else "🟡 接近進場"
            entry_rows.append({"_upside":upside+(20 if price<=hi else 0),"標的":sym,
                                "類型":status,"現價":f"${price:.2f}","目標":f"${info['target']:.0f}",
                                "潛力":f"+{upside:.0f}%","原因":info["reason"]})
        entry_rows.sort(key=lambda x: x["_upside"], reverse=True)
        for i, r in enumerate(entry_rows[:6], 1):
            color = "#22c55e" if "進場區" in r["類型"] else ("#0ea5e9" if i <= 2 else "#7c3aed")
            st.markdown(f"""
<div style="background:#1e1e2e;border-left:4px solid {color};padding:10px;border-radius:6px;margin:6px 0">
<b>#{i} {r['標的']}</b>　<span style="color:{color}">{r['類型']}</span>　{r['現價']} → {r['目標']}　<b style="color:{color}">{r['潛力']}</b><br>
<span style="font-size:13px;color:#94a3b8">{r['原因']}</span>
</div>""", unsafe_allow_html=True)
        if not entry_rows: st.info("目前無進場機會")
    st.divider()

    # ── 財報日曆 + 資金利用率 ─────────────
    EARNINGS_CAL = [
        {"sym":"MSFT", "date":"2026-04-29", "note":"Azure成長 + AI Copilot"},
        {"sym":"META", "date":"2026-04-30", "note":"AI廣告收入"},
        {"sym":"GOOG", "date":"2026-04-29", "note":"搜尋+廣告+Cloud"},
        {"sym":"ORCL", "date":"2026-06-10", "note":"雲端+AI訂單"},
        {"sym":"NVDL", "date":"2026-05-28", "note":"NVDA財報（槓桿ETF受影響）"},
    ]
    today_dt = datetime.now().date()
    cal_col, fund_col = st.columns([1.2, 1])
    with cal_col:
        st.subheader("📅 財報日曆")
        for e in sorted(EARNINGS_CAL, key=lambda x: x["date"]):
            edate = datetime.strptime(e["date"], "%Y-%m-%d").date()
            days_left = (edate - today_dt).days
            if days_left < 0: continue
            urgency = "🔴" if days_left <= 7 else ("🟡" if days_left <= 14 else "🟢")
            st.markdown(f"{urgency} **{e['sym']}**　{e['date']}　（{days_left}天後）　{e['note']}")
    with fund_col:
        st.subheader("💵 資金利用率")
        usdt_val  = df[df["標的"]=="USDT"]["現值(TWD)"].sum()
        total_all = df["現值(TWD)"].sum()
        invested  = total_all - usdt_val
        util_pct  = invested / total_all * 100 if total_all else 0
        idle_usd  = usdt_val / _exrate
        sell_syms = ["JOBY","NVDL","PYPL","RUN"]
        sell_val  = df[df["標的"].isin(sell_syms)]["現值(TWD)"].sum()
        sell_usd  = sell_val / _exrate
        st.metric("閒置 USDT", f"${idle_usd:.0f}　≈ NT${usdt_val:,.0f}")
        st.metric("投資部位", f"{util_pct:.1f}% 已投入", delta=f"閒置 {100-util_pct:.1f}%")
        if sell_val > 0:
            st.info(f"📤 出場候選（{', '.join(sell_syms)}）\n可釋放 **NT${sell_val:,.0f}**（≈ **${sell_usd:.0f}**）")
    st.divider()

    # ── 操作建議 ──────────────────────────
    st.subheader("🎯 操作建議")
    buy_r, hold_r, sell_r = build_rec_rows(df)
    _rb, _rh, _rs = st.columns(3)
    with _rb:
        st.markdown(f"**✅ 加碼 ({len(buy_r)})**")
        for r in buy_r: st.markdown(_rec_card(r,"#22c55e"), unsafe_allow_html=True)
    with _rh:
        st.markdown(f"**⏸️ 觀望 ({len(hold_r)})**")
        for r in hold_r: st.markdown(_rec_card(r,"#94a3b8"), unsafe_allow_html=True)
    with _rs:
        st.markdown(f"**🚨 出場 ({len(sell_r)})**")
        for r in sell_r: st.markdown(_rec_card(r,"#ef4444"), unsafe_allow_html=True)
    st.divider()

    # ── 圖表 + 新聞 ───────────────────────
    left, right = st.columns([1.2, 1])
    with left:
        pie = df.groupby("平台")["現值(TWD)"].sum().reset_index()
        fig_pie = px.pie(pie, names="平台", values="現值(TWD)", hole=0.4, title="帳戶分佈",
                         color_discrete_sequence=["#7c3aed","#f59e0b","#0ea5e9","#10b981"])
        st.plotly_chart(fig_pie, use_container_width=True)
        today_df = df[~df["標的"].isin(["USDT"])].sort_values("今日(TWD)").copy()
        plat_colors = {"國泰美股":"#0ea5e9","國泰台股":"#f59e0b","派網":"#7c3aed","Firstrade":"#10b981"}
        today_df["顏色"] = today_df.apply(
            lambda r: plat_colors.get(r["平台"],"#6b7280") if r["今日(TWD)"]>=0 else "#ef4444", axis=1)
        fig_today = go.Figure(go.Bar(
            x=today_df["今日(TWD)"], y=today_df["標的"], orientation='h',
            marker_color=today_df["顏色"],
            text=[f"NT${v:+,}" for v in today_df["今日(TWD)"]], textposition='outside',
            customdata=today_df["平台"],
            hovertemplate="%{y}  %{customdata}<br>今日 NT$%{x:+,}<extra></extra>"))
        fig_today.update_layout(title="今日損益排行(NT$)", height=520, margin=dict(l=0,r=80,t=40,b=0))
        st.plotly_chart(fig_today, use_container_width=True)
    with right:
        st.subheader("🎙️ FinancialJuice 即時新聞")
        components.iframe("https://www.financialjuice.com/feed", height=750, scrolling=True)
    st.divider()

    # ── 觀察清單 ──────────────────────────
    st.subheader("👀 觀察清單")
    wl_q = fetch_us_quotes(tuple(WATCHLIST.keys()))
    wl_rows = []
    for sym, info in WATCHLIST.items():
        q = wl_q.get(sym,{}); price = q.get("price",0); chg = q.get("chg_pct",0)
        lo, hi = info["entry_zone"]
        if price == 0: status = "❓"
        elif price <= lo: status = "🟢 進場！"
        elif price <= hi: status = "🟡 接近"
        elif (price-hi)/hi*100 <= 10: status = "🔵 觀察"
        else: status = "⚪ 等待"
        upside = (info["target"]-price)/price*100 if price else 0
        pct_away = f"+{(price-hi)/hi*100:.0f}%" if price > hi else "✓進場區"
        tech = fetch_technicals(sym)
        wl_rows.append({
            "狀態":status,"標的":sym,"主題":info["theme"],
            "現價":f"${price:.2f}","今日":f"{chg:+.1f}%",
            "多空":tech.get("sentiment","—"),"RSI":tech.get("rsi","—"),
            "支撐":f"${tech['support']}" if tech.get("support") else "—",
            "壓力":f"${tech['resist']}" if tech.get("resist") else "—",
            "進場區":f"${lo}~${hi}","距進場":pct_away,
            "目標":f"${info['target']:.0f}","潛在獲利":f"+{upside:.0f}%",
            "停損":f"${info['stop']:.0f}","更新":info["date"],"邏輯":info["reason"],
        })
    wl_df = pd.DataFrame(wl_rows)
    ready = wl_df[wl_df["狀態"].str.contains("進場！",na=False)]
    near  = wl_df[wl_df["狀態"].str.contains("接近",na=False)]
    if not ready.empty: st.success(f"🟢 已入進場區：{', '.join(ready['標的'])}")
    if not near.empty:  st.warning(f"🟡 接近進場：{', '.join(near['標的'])}")
    def color_wl(val):
        if "進場！" in str(val): return "background:#14532d;color:#86efac"
        if "接近"   in str(val): return "background:#713f12;color:#fde68a"
        return ""
    st.dataframe(wl_df.style.map(color_wl, subset=["狀態"]), use_container_width=True, hide_index=True)
    with st.expander("📈 個股深度分析"):
        pick = st.selectbox("選擇：", list(WATCHLIST.keys()), key="wl_pick")
        info = WATCHLIST[pick]; q = wl_q.get(pick,{}); price = q.get("price",0)
        tech = fetch_technicals(pick)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("現價", f"${price:.2f}", f"{q.get('chg_pct',0):+.2f}%")
        c2.metric("進場區", f"${info['entry_zone'][0]}~${info['entry_zone'][1]}")
        c3.metric("目標", f"${info['target']:.0f}", f"+{(info['target']-price)/price*100:.0f}%" if price else None)
        c4.metric("RSI", tech.get("rsi","—"))
        if tech:
            s,r = tech["support"], tech["resist"]
            pos = max(0,min(100,(price-s)/(r-s)*100)) if r != s else 50
            st.progress(int(pos), text=f"支撐 ${s}  ←  ${price:.2f}  →  壓力 ${r}")
        TV_WL = f"""
<div class="tradingview-widget-container" style="height:280px;width:100%">
  <div class="tradingview-widget-container__widget" style="height:280px;width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
  {{"symbol":"{pick}","width":"100%","height":280,"locale":"en",
    "dateRange":"3M","colorTheme":"dark","isTransparent":false,"autosize":true}}
  </script>
</div>"""
        components.html(TV_WL, height=300)
        st.caption(f"📌 {info['reason']}  （更新：{info['date']}）")
    st.divider()

    # ── 投資組合歷史走勢 ──────────────────
    render_portfolio_history()
    st.divider()

    # ── 持倉明細 ──────────────────────────
    st.subheader("📋 持倉明細")
    for plat in ["國泰美股","國泰台股","派網","Firstrade"]:
        render_platform_detail(df, plat)
    st.divider()

    # ── S&P 500 熱力圖 ────────────────────
    st.subheader("🌍 S&P 500 熱力圖")
    TV_HEATMAP = """
<div class="tradingview-widget-container" style="height:400px;width:100%">
  <div class="tradingview-widget-container__widget" style="height:400px;width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
  {
    "exchanges": [],
    "dataSource": "SPX500",
    "grouping": "sector",
    "blockSize": "market_cap_basic",
    "blockColor": "change",
    "colorTheme": "dark",
    "hasTopBar": false,
    "isZoomEnabled": true,
    "hasSymbolTooltip": true,
    "width": "100%",
    "height": 400
  }
  </script>
</div>"""
    components.html(TV_HEATMAP, height=420)
    st.divider()

    # ── Insider Trading ───────────────────
    _held_syms = list(set(df["標的"].str.split("→").str[-1].tolist()))
    render_insider_trading(_held_syms)
    st.divider()

    # ── 台股觀察清單 ──────────────────────
    render_tw_watchlist(tw_q)
    st.divider()

    # ── 加密貨幣追蹤 ──────────────────────
    render_crypto_dashboard(cry_q, _exrate)

# ══════════════════════════════════════════
# TAB 2 — 生活系統
# ══════════════════════════════════════════
with tab2:
    render_daily_upgrade(df, cry_q)
    st.divider()
    render_daily_system()

# ══════════════════════════════════════════
# TAB 3 — 撿漏轉賣
# ══════════════════════════════════════════
with tab3:
    _resale_items = _load_resale()
    st.header("🧴 撿漏轉賣追蹤")

    with st.expander("➕ 新增品項", expanded=(len(_resale_items) == 0)):
        _nc1, _nc2, _nc3 = st.columns(3)
        with _nc1:
            _n_name     = st.text_input("品名", placeholder="LOEWE 小黃瓜蠟燭 170g", key="rn_name")
            _n_brand    = st.text_input("品牌", placeholder="LOEWE / Diptyque...", key="rn_brand")
            _n_category = st.selectbox("類別", ["電吉他","木吉他/民謠吉他","貝斯","鍵盤/電鋼琴","其他樂器","單眼相機機身","鏡頭","攝影周邊","其他"], key="rn_cat")
        with _nc2:
            _n_cost     = st.number_input("入手成本 NT$", min_value=0, step=100, key="rn_cost")
            _n_market   = st.number_input("市場行情 NT$（專櫃/市價）", min_value=0, step=100, key="rn_market")
            _n_suggest  = st.number_input("建議售價 NT$", min_value=0, step=100, key="rn_suggest")
        with _nc3:
            _n_note     = st.text_area("備註", placeholder="限量款、全新有盒...", height=80, key="rn_note")
            _n_date     = st.date_input("入手日期", value=date.today(), key="rn_date")
            if st.button("✅ 新增", type="primary", key="rn_add"):
                if _n_name.strip():
                    _new_id = max((i["id"] for i in _resale_items), default=0) + 1
                    _resale_items.append({
                        "id": _new_id, "name": _n_name.strip(), "brand": _n_brand.strip(),
                        "category": _n_category, "cost": int(_n_cost),
                        "market_price": int(_n_market), "suggest_price": int(_n_suggest),
                        "status": "待售", "platform": "", "sold_price": 0,
                        "note": _n_note.strip(), "acquired_date": _n_date.isoformat(),
                    })
                    _save_resale(_resale_items)
                    st.success(f"✅ 已新增：{_n_name.strip()}")
                    st.rerun()
                else:
                    st.warning("請填寫品名")

    if _resale_items:
        _total_cost    = sum(i["cost"] for i in _resale_items)
        _total_market  = sum(i["market_price"] for i in _resale_items)
        _total_suggest = sum(i["suggest_price"] for i in _resale_items)
        _sold_items    = [i for i in _resale_items if i["status"] == "已售出"]
        _total_sold    = sum(i["sold_price"] for i in _sold_items)
        _total_profit_if_sold = _total_suggest - _total_cost
        _realized_profit = _total_sold - sum(i["cost"] for i in _sold_items)
        _mc1, _mc2, _mc3, _mc4, _mc5 = st.columns(5)
        _mc1.metric("總入手成本",   f"NT${_total_cost:,}")
        _mc2.metric("市場行情總值", f"NT${_total_market:,}", f"+{(_total_market/_total_cost-1)*100:.0f}%")
        _mc3.metric("建議售價總計", f"NT${_total_suggest:,}")
        _mc4.metric("預估利潤",     f"NT${_total_profit_if_sold:,}",
                    delta_color="normal" if _total_profit_if_sold > 0 else "inverse")
        _mc5.metric("已實現利潤",   f"NT${_realized_profit:,}" if _sold_items else "—")
        st.divider()

        STATUS_COLOR = {"待售":"#f59e0b","上架中":"#3b82f6","已售出":"#22c55e","自留":"#94a3b8"}
        _resale_changed = False
        for _ri in _resale_items:
            _margin_pct = (_ri["suggest_price"] - _ri["cost"]) / _ri["cost"] * 100
            _vs_market  = (1 - _ri["suggest_price"] / _ri["market_price"]) * 100
            _sc = STATUS_COLOR.get(_ri["status"], "#94a3b8")
            _card_col, _ctrl_col = st.columns([3, 2])
            with _card_col:
                st.markdown(f"""
<div style="background:#1e1e2e;border-radius:8px;padding:12px 16px;border-left:4px solid {_sc}">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
    <div>
      <span style="font-weight:bold;font-size:15px">{_ri['name']}</span>
      <span style="background:{_sc}22;color:{_sc};padding:2px 8px;border-radius:4px;font-size:12px;margin-left:8px">{_ri['status']}</span>
    </div>
    <span style="color:#22c55e;font-size:13px">利潤空間 +{_margin_pct:.0f}%</span>
  </div>
  <div style="display:flex;gap:20px;margin-top:8px;font-size:13px;flex-wrap:wrap">
    <span>入手 <b style="color:#ef4444">NT${_ri['cost']:,}</b></span>
    <span>行情 <b>NT${_ri['market_price']:,}</b></span>
    <span>建議售價 <b style="color:#22c55e">NT${_ri['suggest_price']:,}</b></span>
    <span style="color:#64748b">比行情低 {_vs_market:.0f}%</span>
  </div>
  <div style="color:#94a3b8;font-size:12px;margin-top:6px">{_ri['note']}</div>
</div>""", unsafe_allow_html=True)
            with _ctrl_col:
                _new_status = st.selectbox(
                    "狀態", ["待售","上架中","已售出","自留"],
                    index=["待售","上架中","已售出","自留"].index(_ri.get("status","待售")),
                    key=f"rs_status_{_ri['id']}")
                _new_platform = st.text_input("平台", value=_ri.get("platform",""),
                                              placeholder="蝦皮/社團...", key=f"rs_plat_{_ri['id']}")
                _ce1, _ce2 = st.columns(2)
                _new_cost    = _ce1.number_input("成本", value=int(_ri.get("cost",0)), step=100, key=f"rs_cost_{_ri['id']}")
                _new_market  = _ce2.number_input("行情", value=int(_ri.get("market_price",0)), step=100, key=f"rs_mkt_{_ri['id']}")
                _new_suggest = _ce1.number_input("售價", value=int(_ri.get("suggest_price",0)), step=100, key=f"rs_sug_{_ri['id']}")
                _new_sold    = _ce2.number_input("實售", value=int(_ri.get("sold_price",0)), step=100, key=f"rs_sold_{_ri['id']}")
                if st.button("🗑️ 刪除", key=f"rs_del_{_ri['id']}", type="secondary"):
                    _resale_items = [i for i in _resale_items if i["id"] != _ri["id"]]
                    _save_resale(_resale_items); st.rerun()
                if (_new_status != _ri["status"] or _new_platform != _ri.get("platform","") or
                    _new_cost != _ri.get("cost",0) or _new_market != _ri.get("market_price",0) or
                    _new_suggest != _ri.get("suggest_price",0) or _new_sold != _ri.get("sold_price",0)):
                    _ri["status"] = _new_status; _ri["platform"] = _new_platform
                    _ri["cost"] = int(_new_cost); _ri["market_price"] = int(_new_market)
                    _ri["suggest_price"] = int(_new_suggest); _ri["sold_price"] = int(_new_sold)
                    _resale_changed = True
        if _resale_changed:
            _save_resale(_resale_items); st.rerun()
        _pending = [i for i in _resale_items if i["status"] in ("待售","上架中")]
        if len(_pending) >= 2:
            _bundle_cost = sum(i["cost"] for i in _pending)
            _bundle_min  = int(sum(i["suggest_price"] for i in _pending) * 0.88)
            _bundle_max  = int(sum(i["suggest_price"] for i in _pending) * 0.95)
            st.info(f"💡 **打包銷售建議**：{len(_pending)} 件合售 NT${_bundle_min:,} ~ NT${_bundle_max:,}　"
                    f"（預估利潤 NT${_bundle_min-_bundle_cost:,}）")
    else:
        st.info("尚無轉賣追蹤項目")

    # ── FB Marketplace 撿漏監控 ──────────
    st.divider()
    st.header("🛒 FB Marketplace 撿漏監控")
    _deal_data = _load_deals()
    _scraper_cfg = _load_scraper_config()
    _threshold = _scraper_cfg.get("threshold_ratio", 0.6)
    _col_info1, _col_info2, _col_info3, _col_info4 = st.columns(4)
    _scan_time_str = _deal_data.get("last_scan")
    with _col_info1:
        if _scan_time_str:
            try:
                from datetime import timezone as _tz
                _st_dt = datetime.fromisoformat(_scan_time_str)
                _now_tz = datetime.now(_st_dt.tzinfo) if _st_dt.tzinfo else datetime.now()
                _hours_ago = (_now_tz - _st_dt).total_seconds() / 3600
                _freshness = "🟢 剛更新" if _hours_ago < 5 else ("🟡 稍舊" if _hours_ago < 24 else "🔴 已過期")
                st.metric("上次掃描", _scan_time_str[5:16].replace("T"," "))
                st.caption(f"{_freshness}　{_hours_ago:.0f} 小時前")
            except:
                st.metric("上次掃描", _scan_time_str[:16].replace("T"," "))
        else:
            st.metric("上次掃描", "尚未執行"); st.caption("🔴 需要設定 FB_COOKIES")
    with _col_info2:
        st.metric("監控標的數", len(_scraper_cfg.get("targets", [])))
        st.caption(f"門檻：行情 × {_threshold:.0%}")
    with _col_info3:
        st.metric("發現好物", len(_deal_data.get("deals", [])))
    with _col_info4:
        st.metric("自動掃描", "每 4 小時"); st.caption("GitHub Actions 執行")

    with st.expander("⚙️ 自動掃描設定說明（第一次設定必看）"):
        st.markdown("""
**Step 1** — `python save_fb_cookies.py`（本機，瀏覽器登入 FB）

**Step 2** — `cat fb_cookies.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))"`

**Step 3** — 存入 GitHub Secrets → `FB_COOKIES`

完成後 GitHub Actions 每 4 小時自動掃描，deals.json 更新後 Streamlit 即時顯示。
""")

    if st.button("🔍 立即執行掃描（本機用，需安裝 playwright）"):
        with st.spinner("爬蟲執行中，請稍候..."):
            try:
                import subprocess, sys as _sys
                _res = subprocess.run(
                    [_sys.executable, os.path.join(os.path.dirname(__file__), "fb_scraper.py")],
                    capture_output=True, text=True, timeout=300)
                if _res.returncode == 0:
                    st.success("掃描完成！")
                    st.text(_res.stdout[-2000:] if len(_res.stdout) > 2000 else _res.stdout)
                else:
                    st.error("掃描時發生錯誤"); st.text(_res.stderr[-1000:])
            except Exception as _e:
                st.error(f"無法啟動爬蟲：{_e}")
        st.rerun()

    _deals = _deal_data.get("deals", [])
    if _deals:
        st.subheader(f"🔥 發現 {len(_deals)} 個撿漏標的")
        from collections import defaultdict
        _grouped = defaultdict(list)
        for _d in _deals: _grouped[_d.get("item","其他")].append(_d)
        for _item, _items in _grouped.items():
            _best = _items[0]
            _disc = _best.get("discount_pct", 0); _price = _best.get("price", 0)
            _market = _best.get("market_price", 0); _title = _best.get("title","")[:35]
            _link = _best.get("link","")
            _color = "#ef4444" if _disc >= 50 else ("#f97316" if _disc >= 40 else "#eab308")
            _extra = f"　＋另 {len(_items)-1} 筆" if len(_items) > 1 else ""
            st.markdown(f"""
<div style="background:#1e1e2e;border-left:4px solid {_color};padding:8px 12px;border-radius:6px;margin:4px 0;display:flex;justify-content:space-between;align-items:center">
<div>
  <b style="color:{_color}">省 {_disc:.0f}%</b>　<b>{_item}</b>　NT${_price:,}
  <span style="color:#64748b">（行情 NT${_market:,}）{_extra}</span><br>
  <span style="font-size:12px;color:#94a3b8">{_title}</span>
</div>
<a href="{_link}" target="_blank" style="color:{_color};font-size:12px;white-space:nowrap;margin-left:12px">查看 →</a>
</div>""", unsafe_allow_html=True)
    else:
        st.info("目前尚未發現低於行情 60% 的標的，或還未執行過掃描。")

    with st.expander("📋 監控清單"):
        _targets = _scraper_cfg.get("targets", [])
        if _targets:
            _tdf = pd.DataFrame([{"器材":t["name"],"行情":f"NT${t['market_price']:,}",
                                   f"觸發 ({_threshold:.0%})":f"NT${int(t['market_price']*_threshold):,}"} for t in _targets])
            st.dataframe(_tdf, use_container_width=True, hide_index=True)
        else:
            st.write("config.json 未找到監控清單")

# ══════════════════════════════════════════
# TAB 4 — 研究
# ══════════════════════════════════════════
with tab4:
    render_ai_chat(df, tw_q, cry_q, _exrate)
    st.divider()
    render_decision_journal()
    st.divider()
    try:
        render_research_notes()
    except Exception as _rr_err:
        st.error(f"研究筆記載入失敗：{_rr_err}")

# ══════════════════════════════════════════
# TAB 5 — AI 學習地圖
# ══════════════════════════════════════════
with tab5:
    st.header("🗺️ Jim 的 AI 槓桿學習地圖")
    st.caption("目標：一年內透過 AI 開始盈利或槓桿 · 更新於 2026-04-22")

    # 進度概覽
    st.subheader("📍 你現在的位置")
    st.markdown("""
    ```
    完全新手 ──[2026-04-15]──▶ 能用 Claude 建 dashboard ──▶ 你在這裡 ▶ ???
    ```
    """)

    # 四個層級
    st.subheader("四個能力層級")

    lvl1, lvl2, lvl3, lvl4 = st.tabs(["🟢 L1 指揮官", "🔵 L2 建造者", "🟣 L3 整合者", "🔴 L4 產品化"])

    with lvl1:
        st.markdown("### 🟢 Level 1｜指揮官（現在 ～ 1個月）")
        st.markdown("**核心技能：精準描述你要什麼**")
        data = {
            "要學的": ["Prompt 工程", "讀懂程式碼", "用 NotebookLM 整理資料", "認識 AI 工具版圖"],
            "怎麼練": [
                "每次問問題前寫「背景+目標+限制」",
                "每次拿到程式碼問「這段在做什麼」",
                "每天丟一筆資料進去",
                "知道 Claude/Gemini/GPT 各自強在哪",
            ],
            "完成標誌": [
                "Claude 第一次就給你要的結果",
                "能說出每個函數的用途",
                "有一份自己整理的知識庫",
                "能選對工具用",
            ],
        }
        st.table(pd.DataFrame(data))
        st.success("💡 這層的槓桿：你的時間 × 10")

    with lvl2:
        st.markdown("### 🔵 Level 2｜建造者（1 ～ 3個月）")
        st.markdown("**核心技能：用 AI 自動化你的日常**")
        data = {
            "要學的": ["Python 基礎讀寫", "GitHub Actions", "API 串接", "CSV/JSON 資料處理"],
            "怎麼練": [
                "改 dashboard.py 的小地方，問 Claude 解釋",
                "讓面板每天自動更新、自動發通知",
                "接 LINE Notify / Discord / Email",
                "用 AI 寫腳本整理投資紀錄",
            ],
            "完成標誌": [
                "能自己加一個新欄位",
                "不需要手動跑程式",
                "重要訊號自動推播",
                "有自動化的損益追蹤",
            ],
        }
        st.table(pd.DataFrame(data))
        st.success("💡 這層的槓桿：你的時間 × 50（自動化睡覺也在跑）")

    with lvl3:
        st.markdown("### 🟣 Level 3｜整合者（3 ～ 6個月）")
        st.markdown("**核心技能：把多個 AI 串成工作流**")
        data = {
            "要學的": ["n8n / Make 自動化平台", "Claude API 直接呼叫", "RAG 知識庫", "自動報告生成"],
            "怎麼練": [
                "建一條「新聞→分析→通知」的流程",
                "讓面板內建 AI 分析",
                "把投資筆記變成 AI 可查的知識庫",
                "每週自動生成投資週報",
            ],
            "完成標誌": [
                "有一條完全自動的情報流",
                "面板能自動解讀財報",
                "AI 能回答「我過去買TSLA的理由」",
                "不需要手動整理",
            ],
        }
        st.table(pd.DataFrame(data))
        st.success("💡 這層的槓桿：你的決策品質 × 10")

    with lvl4:
        st.markdown("### 🔴 Level 4｜產品化（6 ～ 12個月）")
        st.markdown("**核心技能：把你的系統變成可以賺錢的產品**")
        data = {
            "要學的": ["把面板變成付費工具", "AI Agent 設計", "樂器生意 × AI", "內容變現"],
            "怎麼練": [
                "包裝投資面板給其他人用",
                "建一個自動執行研究+整理+通知的 Agent",
                "用 AI 自動生成開發信、市場研究",
                "把 AI 使用過程分享出去",
            ],
            "完成標誌": [
                "第一個付費用戶",
                "Agent 每天替你工作8小時",
                "業績可量化提升",
                "建立個人品牌",
            ],
        }
        st.table(pd.DataFrame(data))
        st.success("💡 這層的槓桿：你的系統 × N 個人付費")

    st.divider()

    # 專屬路線
    st.subheader("🚀 你的專屬里程碑")
    milestones = [
        {"時間": "本週",    "目標": "把面板改到「看一眼就懂」",              "狀態": "🔄 進行中"},
        {"時間": "下週",    "目標": "設定 LINE 自動通知 + GitHub 自動排程",  "狀態": "⬜ 待開始"},
        {"時間": "第2週",   "目標": "用 NotebookLM 建立投資知識庫",          "狀態": "✅ 已建立"},
        {"時間": "第1個月", "目標": "能自己改面板小功能，不需要完全靠 Claude","狀態": "⬜ 待開始"},
        {"時間": "第3個月", "目標": "有一條自動情報流（新聞→分析→推播）",    "狀態": "⬜ 待開始"},
        {"時間": "第6個月", "目標": "面板可以給朋友用 / 開始樂器 AI 自動化", "狀態": "⬜ 待開始"},
        {"時間": "第12個月","目標": "有可量化的 AI 帶來的收入或節省",        "狀態": "⬜ 待開始"},
    ]
    st.table(pd.DataFrame(milestones))

    st.divider()
    st.info("💡 **每天最重要的一件事**：帶著一個具體問題來，完成它，明天再來一個。\n\n不要「今天想學 AI」——要「今天要讓面板的停損警示更顯眼」。")

    st.divider()
    st.subheader("🛠️ AI 工具推播")
    st.caption("Claude 幫你篩選的開源工具，你決定要不要裝")

    _tools_file = os.path.join(os.path.dirname(__file__), "data", "ai_tools_feed.json")
    try:
        with open(_tools_file, encoding="utf-8") as _tf:
            _tools = json.load(_tf)
    except:
        _tools = []

    _cat_colors = {"研究":"#8b5cf6","知識庫":"#3b82f6","自動化":"#f59e0b","Agent":"#ef4444","寫作":"#22c55e"}
    for _tool in _tools:
        _cat   = _tool.get("category","其他")
        _color = _cat_colors.get(_cat, "#64748b")
        _installed = _tool.get("status") == "installed"
        _badge = "✅ 已安裝" if _installed else "⬜ 待評估"
        _tc1, _tc2 = st.columns([4, 1])
        with _tc1:
            st.markdown(f"""
<div style='background:#131317;border:1px solid #24242c;border-radius:8px;padding:12px 16px;margin:6px 0;border-left:3px solid {_color}'>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px'>
    <span style='background:{_color}18;color:{_color};font-size:10px;padding:2px 8px;border-radius:4px;
         font-family:"JetBrains Mono",monospace;letter-spacing:.04em'>{_cat}</span>
    <b style='color:#e9e9ec;font-size:13px'>{_tool['name']}</b>
    <span style='color:#3f3f48;font-size:11px;font-family:"JetBrains Mono",monospace'>— {_tool['repo']}</span>
  </div>
  <div style='color:#a8a8b2;font-size:12px;line-height:1.55'>{_tool['desc']}</div>
  <div style='color:#3f3f48;font-size:10px;margin-top:7px;font-family:"JetBrains Mono",monospace'>
    安裝：<code style='color:#6c6c78'>{_tool['install']}</code></div>
</div>""", unsafe_allow_html=True)
        with _tc2:
            st.markdown(f"<div style='padding-top:20px;text-align:center'>{_badge}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 6 — 書庫
# ══════════════════════════════════════════
with tab6:
    _books_file   = os.path.join(os.path.dirname(__file__), "data", "books.json")
    _local_file   = os.path.join(os.path.dirname(__file__), "data", "local_books.json")
    _covers_dir   = os.path.join(os.path.dirname(__file__), "data", "covers")
    _data_dir     = os.path.dirname(_books_file)
    os.makedirs(_covers_dir, exist_ok=True)

    # ── 載入書單（Drive + 本機合併）────────
    import hashlib as _hl
    def _stable_key(b):
        """從 title 產生穩定 8 碼 hex，作為 Streamlit widget key"""
        return _hl.md5(b.get("title","").encode()).hexdigest()[:8]

    def _normalize_book(b, source="drive"):
        """統一 books.json / local_books.json 的欄位格式"""
        title = b.get("title","")
        return {
            "id":          b.get("id") or _stable_key(b),
            "title":       title,
            "author":      b.get("author",""),
            "category":    b.get("category","其他"),
            "drive_id":    b.get("drive_id",""),
            "local_path":  b.get("local_path",""),
            "cover_path":  b.get("cover_path",""),
            "status":      b.get("status","待讀"),
            "tags":        b.get("tags",[]),
            "added_date":  b.get("added_date",""),
            "folder":      b.get("folder") or b.get("shelf",""),
            "_source":     source,
        }

    def _load_all_books():
        drive_books, local_books = [], []
        try:
            raw = json.load(open(_books_file, encoding="utf-8"))
            drive_books = [_normalize_book(b, "drive") for b in raw]
        except Exception:
            pass
        try:
            raw = json.load(open(_local_file, encoding="utf-8"))
            local_books = [_normalize_book(b, "local") for b in raw]
        except Exception:
            pass
        # 合併：以書名去重，Drive 版優先
        seen = {b["title"]: b for b in drive_books}
        for b in local_books:
            if b["title"] not in seen:
                seen[b["title"]] = b
        merged = list(seen.values())
        merged.sort(key=lambda b: b.get("added_date",""), reverse=True)
        return merged, drive_books, local_books

    _books, _drive_books, _local_books_list = _load_all_books()

    _CAT_C = {
        "投資/財富":"#f59e0b","AI/科技":"#8b5cf6","人性/心理":"#3b82f6",
        "生活/心智":"#22c55e","關係/情緒":"#ec4899","商業":"#f97316",
        "攝影":"#06b6d4","塔羅/靈性":"#a855f7","其他":"#64748b"
    }
    _CAT_EM = {
        "投資/財富":"📈","AI/科技":"🤖","人性/心理":"🧠","生活/心智":"🌱",
        "關係/情緒":"💝","商業":"💼","攝影":"📷","塔羅/靈性":"🔮","其他":"📖"
    }
    _ST_C = {"待讀":"#f59e0b","讀中":"#3b82f6","已讀":"#22c55e"}

    # ── 頂部統計 ─────────────────────────
    _total    = len(_books)
    _reading  = sum(1 for b in _books if b.get("status") == "讀中")
    _done     = sum(1 for b in _books if b.get("status") == "已讀")
    _pending  = _total - _done - _reading
    _n_drive  = len(_drive_books)
    _n_local  = len(_local_books_list)

    st.markdown(f"""
<style>
.lib-stat-row{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
.lib-stat{{background:#131317;border:1px solid #24242c;border-radius:10px;
           padding:16px 20px;flex:1;min-width:110px}}
.lib-stat .lbl{{font-size:10px;color:#6c6c78;letter-spacing:.1em;
                font-family:"JetBrains Mono",monospace;text-transform:uppercase;margin-bottom:6px}}
.lib-stat .val{{font-size:30px;font-weight:900;font-family:"Noto Sans TC","JetBrains Mono",monospace;
                letter-spacing:-.02em;line-height:1}}
.lib-stat .sub{{font-size:10px;color:#3f3f48;font-family:"JetBrains Mono",monospace;margin-top:4px}}
.bk-card{{background:#131317;border:1px solid #24242c;border-radius:12px;overflow:hidden;
          margin-bottom:4px;transition:transform .18s,box-shadow .18s;cursor:default}}
.bk-card:hover{{transform:translateY(-3px);box-shadow:0 10px 32px rgba(0,0,0,.5)}}
.bk-cover{{width:100%;height:260px;object-fit:cover;display:block}}
.bk-body{{padding:12px 14px 10px}}
.bk-title{{font-size:14px;font-weight:900;font-family:"Noto Sans TC",sans-serif;
           letter-spacing:-.01em;color:#e9e9ec;line-height:1.4;margin-bottom:4px;
           display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.bk-author{{font-size:11px;color:#6c6c78;font-family:"JetBrains Mono",monospace;
            margin-bottom:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bk-footer{{display:flex;justify-content:space-between;align-items:center;gap:8px}}
.bk-badge{{font-size:9px;padding:2px 8px;border-radius:99px;
           font-family:"JetBrains Mono",monospace;letter-spacing:.04em;white-space:nowrap}}
.bk-src{{font-size:10px;color:#3f3f48;font-family:"JetBrains Mono",monospace}}
.bk-open{{font-size:11px;color:#a78bfa;text-decoration:none;
          font-family:"JetBrains Mono",monospace;letter-spacing:.02em;white-space:nowrap}}
</style>
<div class="lib-stat-row">
  <div class="lib-stat"><div class="lbl">總收藏</div><div class="val" style="color:#e9e9ec">{_total}</div>
    <div class="sub">☁️ {_n_drive} Drive　💻 {_n_local} 本機</div></div>
  <div class="lib-stat"><div class="lbl">待讀</div><div class="val" style="color:#f59e0b">{_pending}</div></div>
  <div class="lib-stat"><div class="lbl">讀中</div><div class="val" style="color:#3b82f6">{_reading}</div></div>
  <div class="lib-stat"><div class="lbl">已讀</div><div class="val" style="color:#22c55e">{_done}</div></div>
</div>""", unsafe_allow_html=True)

    # ── 控制列 ───────────────────────────
    _has_client = os.path.exists(os.path.join(_data_dir, "google_client.json"))
    _has_token  = os.path.exists(os.path.join(_data_dir, "google_token.json"))

    _lc0, _lc1, _lc2, _lc3, _lc4 = st.columns([1.2, 1, 2, 2, 1.5])
    with _lc0:
        if st.button("📁 掃描本機", key="book_local_scan", use_container_width=True,
                     help="掃描 ~/Desktop/電子書/ 並自動抽取封面"):
            with st.spinner("掃描中，抽取封面..."):
                try:
                    import subprocess as _ssp2, sys as _ssys2
                    _sr2 = _ssp2.run(
                        [_ssys2.executable,
                         os.path.join(os.path.dirname(__file__), "extract_covers.py")],
                        capture_output=True, text=True, timeout=300)
                    import re as _re3
                    _m2 = _re3.search(r"新增 (\d+) 本.*共 (\d+) 本", _sr2.stdout)
                    if _m2:
                        st.success(f"✓ 新增 {_m2.group(1)} 本，共 {_m2.group(2)} 本")
                    else:
                        st.success("✓ 掃描完成")
                    st.rerun()
                except Exception as _se2:
                    st.error(str(_se2))
    with _lc1:
        _sync_tip = None if _has_client else "請先在 ⚙️ Google Drive 設定中上傳憑證"
        if st.button("☁️ Drive同步", key="book_sync", use_container_width=True,
                     disabled=not _has_client, help=_sync_tip):
            with st.spinner("同步中..."):
                try:
                    import subprocess as _ssp, sys as _ssys, re as _re2
                    _sr = _ssp.run(
                        [_ssys.executable, os.path.join(os.path.dirname(__file__), "sync_books.py")],
                        capture_output=True, text=True, timeout=120)
                    if _sr.returncode == 0:
                        _m = _re2.search(r"共 (\d+) 本", _sr.stdout)
                        st.success(f"✓ 同步完成（共 {_m.group(1)} 本）" if _m else "✓ 同步完成")
                        st.rerun()
                    else:
                        st.error(_sr.stderr.strip() or "同步失敗，請查看 ⚙️ 設定")
                except Exception as _se:
                    st.error(str(_se))
    with _lc2:
        _sf = st.segmented_control("", ["全部","待讀","讀中","已讀"], default="全部", key="book_sf")
    with _lc3:
        _cf = st.selectbox("", ["全部分類"]+list(_CAT_C.keys()), key="book_cf", label_visibility="collapsed")
    with _lc4:
        _sq = st.text_input("", placeholder="搜尋書名...", key="book_sq", label_visibility="collapsed")

    # ── Google Drive 設定 ────────────────
    _gset_label = "⚙️ Google Drive 設定  ✅" if _has_token else (
                  "⚙️ Google Drive 設定  ⚠️ 需首次授權" if _has_client else
                  "⚙️ Google Drive 設定  — 未設定")
    with st.expander(_gset_label, expanded=not _has_client):
        if _has_token:
            st.success("已連接 Google Drive，可直接使用 ☁️ Drive同步")
        elif _has_client:
            st.info("憑證已上傳。點 ☁️ Drive同步後瀏覽器會開啟 Google 授權頁，完成一次即可。")
        else:
            st.markdown("""**第一次設定步驟：**
1. 前往 [Google Cloud Console](https://console.cloud.google.com/) → 建立（或選擇）專案
2. 搜尋並啟用 **Google Drive API**
3. 左側 **憑證** → 建立憑證 → **OAuth 2.0 用戶端 ID**（選「桌面應用程式」）
4. 下載 JSON → 上傳到下方""")
        _uploaded_cred = st.file_uploader("上傳 google_client.json", type="json", key="goog_cred_up",
                                           label_visibility="collapsed")
        if _uploaded_cred:
            _cred_dest = os.path.join(_data_dir, "google_client.json")
            with open(_cred_dest, "wb") as _cw:
                _cw.write(_uploaded_cred.read())
            st.success("✓ 憑證已儲存。請點 ☁️ Drive同步（首次會開啟瀏覽器授權）")
            st.rerun()

    # ── 選書推薦 ─────────────────────────
    with st.expander("🤖 幫我選書"):
        _mood = st.text_area("", placeholder="你現在的狀態，例：想學決策、今天很焦慮、想了解 AI 趨勢",
                              height=60, key="book_mood", label_visibility="collapsed")
        if st.button("推薦", key="book_rec", type="primary"):
            if _mood.strip():
                _unread = [b for b in _books if b.get("status") != "已讀"]
                _blist  = "\n".join(f"- 《{b['title']}》({b['category']})" for b in _unread[:60])
                with st.spinner("選書中..."):
                    try:
                        _ak = _get_anthropic_key()
                        if _ak:
                            import anthropic as _ant
                            _r = _ant.Anthropic(api_key=_ak).messages.create(
                                model="claude-sonnet-4-6", max_tokens=400,
                                messages=[{"role":"user","content":f"用戶狀態：{_mood}\n未讀書單：\n{_blist}\n\n推薦1-2本，說明理由。繁體中文。"}])
                            st.markdown(_r.content[0].text)
                        else:
                            st.warning("請先設定 Anthropic API Key")
                    except Exception as _re:
                        st.error(str(_re))
            else:
                st.warning("請描述你的狀態")

    st.divider()

    # ── 現代雜誌網格（2欄大卡片）────────────
    import base64 as _b64

    _sq_v   = _sq.strip().lower() if _sq else ""
    _sf_val = _sf if _sf else "全部"
    _fbooks = [b for b in _books
               if (_sf_val == "全部" or b.get("status","待讀") == _sf_val)
               and (_cf == "全部分類" or b.get("category","其他") == _cf)
               and (not _sq_v or _sq_v in b.get("title","").lower()
                    or _sq_v in (b.get("author","") or "").lower())]

    if not _fbooks:
        st.info("沒有符合條件的書籍")
    else:
        _NCOLS = 2
        for _ri in range(0, len(_fbooks), _NCOLS):
            _row   = _fbooks[_ri:_ri+_NCOLS]
            _rcols = st.columns(_NCOLS)
            for _ci, _b in enumerate(_row):
                _cc   = _CAT_C.get(_b.get("category","其他"), "#64748b")
                _em   = _CAT_EM.get(_b.get("category","其他"), "📖")
                _bst  = _b.get("status","待讀")
                _stc  = _ST_C.get(_bst, "#64748b")
                _auth = _b.get("author","") or "─"
                _is_drive = bool(_b.get("drive_id"))
                _src_icon = "☁️" if _is_drive else "💻"

                # 開啟連結
                if _is_drive:
                    _open_url = f"https://drive.google.com/file/d/{_b['drive_id']}/view"
                    _open_lbl = "Drive →"
                elif _b.get("local_path"):
                    _open_url = ""
                    _open_lbl = "本機"
                else:
                    _open_url = ""
                    _open_lbl = ""

                # 封面圖（優先順序：本機 cover_path → Drive cover → 佔位）
                _cov_html = ""
                _cover_found = False

                # 本機封面
                _lcp = _b.get("cover_path","")
                if _lcp and os.path.exists(_lcp):
                    try:
                        with open(_lcp,"rb") as _cf2:
                            _idata = _b64.b64encode(_cf2.read()).decode()
                        _cov_html = f'<img class="bk-cover" src="data:image/jpeg;base64,{_idata}">'
                        _cover_found = True
                    except Exception:
                        pass

                # Drive 封面
                if not _cover_found and _is_drive:
                    _dcp = os.path.join(_covers_dir, f"{_b['drive_id']}.jpg")
                    if os.path.exists(_dcp):
                        try:
                            with open(_dcp,"rb") as _cf2:
                                _idata = _b64.b64encode(_cf2.read()).decode()
                            _cov_html = f'<img class="bk-cover" src="data:image/jpeg;base64,{_idata}">'
                            _cover_found = True
                        except Exception:
                            pass

                # 無封面佔位
                if not _cover_found:
                    _atit = _b['title'][:28]+("…" if len(_b['title'])>28 else "")
                    _cov_html = f"""
<div style='height:260px;background:linear-gradient(155deg,{_cc}28 0%,{_cc}08 100%);
     display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;
     position:relative;border-bottom:1px solid {_cc}30'>
  <div style='position:absolute;top:10px;right:12px;background:{_stc}22;color:{_stc};
       font-size:9px;padding:2px 8px;border-radius:99px;
       font-family:"JetBrains Mono",monospace;letter-spacing:.05em'>{_bst}</div>
  <div style='font-size:52px;margin-bottom:14px;opacity:.85'>{_em}</div>
  <div style='font-size:13px;font-weight:900;font-family:"Noto Sans TC",sans-serif;
       text-align:center;line-height:1.5;color:{_cc};letter-spacing:-.01em;
       max-height:80px;overflow:hidden'>{_atit}</div>
</div>"""

                _open_a = (f'<a class="bk-open" href="{_open_url}" target="_blank">{_open_lbl}</a>'
                           if _open_url else
                           f'<span class="bk-src">{_open_lbl}</span>')

                with _rcols[_ci]:
                    _bid_key = _stable_key(_b)   # 穩定 8碼 hex，不會重複
                    st.markdown(f"""
<div class="bk-card">
  {_cov_html}
  <div class="bk-body">
    <div class="bk-title">{_b['title']}</div>
    <div class="bk-author">{_auth}</div>
    <div class="bk-footer">
      <span class="bk-badge" style="background:{_cc}18;color:{_cc}">{_b.get("category","")}</span>
      <span class="bk-src">{_src_icon}</span>
      {_open_a}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                    # 狀態切換
                    _opts = ["待讀","讀中","已讀"]
                    _cur  = _opts.index(_bst) if _bst in _opts else 0
                    _nst  = st.selectbox("", _opts, index=_cur,
                                         key=f"bst_{_bid_key}", label_visibility="collapsed")
                    if _nst != _bst:
                        _b["status"] = _nst
                        # 更新對應的 json（用 title 比對，因 Drive 書可能無 id）
                        if _b.get("_source") == "drive":
                            _tgt_file = _books_file
                            _tgt_list = _drive_books
                        else:
                            _tgt_file = _local_file
                            _tgt_list = _local_books_list
                        for _tb in _tgt_list:
                            if _tb.get("title") == _b["title"]:
                                _tb["status"] = _nst
                                break
                        with open(_tgt_file,"w",encoding="utf-8") as _bw:
                            json.dump(_tgt_list, _bw, ensure_ascii=False, indent=2)
                        st.rerun()

    st.divider()

    # ── NotebookLM ────────────────────────
    st.markdown("""
<div style='font-size:10px;letter-spacing:.12em;color:#6c6c78;font-family:"JetBrains Mono",monospace;
     text-transform:uppercase;margin-bottom:14px'>NOTEBOOK 重點整理</div>""", unsafe_allow_html=True)

    _drive_only = [b for b in _books if b.get("drive_id")]
    if _drive_only:
        _nlm_c1, _nlm_c2 = st.columns([3,1])
        with _nlm_c1:
            _sel_b = st.selectbox("", [b['title'] for b in _drive_only], key="book_nlm_sel", label_visibility="collapsed")
        with _nlm_c2:
            _gen_btn = st.button("生成摘要 →", key="book_nlm_btn", type="primary", use_container_width=True)
        if _gen_btn:
            _sb = next((b for b in _drive_only if b['title'] == _sel_b), None)
            if _sb:
                _nlm_url = f"https://drive.google.com/file/d/{_sb['drive_id']}/view"
                with st.spinner(f"上傳《{_sb['title']}》到 NotebookLM..."):
                    try:
                        import subprocess as _sp
                        _nb_id = "785be3cc-a70e-4642-b1eb-9953c79bed1f"
                        _sp.run(["notebooklm","use",_nb_id], capture_output=True)
                        _src = _sp.run(["notebooklm","source","add",_nlm_url,"--json"],
                                       capture_output=True, text=True)
                        _sd = json.loads(_src.stdout) if _src.stdout.strip().startswith("{") else {}
                        _sid = _sd.get("source",{}).get("id","")
                        if _sid:
                            _sp.run(["notebooklm","source","wait",_sid,"--timeout","120"], capture_output=True)
                        _rep = _sp.run(["notebooklm","generate","report","--format","study-guide",
                                        "--append",f"書名：《{_sb['title']}》，用繁體中文整理重點","--json"],
                                       capture_output=True, text=True)
                        _rd = json.loads(_rep.stdout) if _rep.stdout.strip().startswith("{") else {}
                        if _rd.get("task_id"):
                            st.info(f"✅ 生成中（約5-10分鐘）\n\n```\nnotebooklm download report ~/Downloads/{_sb['title']}.md\n```")
                        else:
                            st.warning("已上傳來源，請到 NotebookLM 手動生成報告")
                    except Exception as _be:
                        st.error(str(_be))

# ── 刷新 ─────────────────────────────────
st.divider()
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("🔄 立即刷新"):
        st.cache_data.clear(); st.rerun()
with c2:
    st.caption(f"更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}　每60秒自動刷新")
components.html("""<script>
let hasInput = false;
document.addEventListener('focusin', e => {
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') hasInput = true;
});
document.addEventListener('focusout', e => {
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')
    setTimeout(()=>{ hasInput = false; }, 3000);
});
setTimeout(()=>{
  if(!hasInput) window.parent.location.reload();
}, 60000);
</script>""", height=0)
