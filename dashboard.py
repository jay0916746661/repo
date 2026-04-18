#!/usr/bin/env python3
"""Jim 投資全視界 Dashboard — streamlit run dashboard.py"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import urllib.request, json, time, hmac, hashlib, urllib.parse, os, csv
from datetime import datetime, date

HOLDINGS_FILE  = os.path.join(os.path.dirname(__file__), "holdings.json")
HISTORY_FILE   = os.path.join(os.path.dirname(__file__), "portfolio_history.csv")
REVIEW_FILE    = os.path.join(os.path.dirname(__file__), "data", "review_history.csv")

st.set_page_config(page_title="Jim 投資全視界", layout="wide",
                   page_icon="📊", initial_sidebar_state="expanded")
st.markdown("""
<style>
[data-testid="metric-container"]{background:#1e1e2e;border-radius:10px;padding:12px}
.stTabs [data-baseweb="tab"]{font-size:15px}
.alert-danger{background:#3b0000;border-left:4px solid #ef4444;padding:10px;border-radius:6px;margin:4px 0}
.alert-entry{background:#0f2c0f;border-left:4px solid #22c55e;padding:10px;border-radius:6px;margin:4px 0}
.insider-buy{background:#0f2c0f;border-left:3px solid #22c55e;padding:8px;border-radius:4px;margin:3px 0;font-size:13px}
.insider-sell{background:#3b0000;border-left:3px solid #ef4444;padding:8px;border-radius:4px;margin:3px 0;font-size:13px}
@media(max-width:768px){
  [data-testid="metric-container"]{padding:8px}
  .block-container{padding:0.5rem 0.5rem}
  h1{font-size:1.4rem!important}
  h2{font-size:1.1rem!important}
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

# 派網代幣化股票 (成本USD, 預設股數) — 更新：2026-04-18
PIONEX_STOCKS = {
    'ADBE': (239.70, 0.247),
    'HIMS': (24.29,  1.23),
    'IONQ': (25.00,  0.507),   # 新增
    'META': (560.00, 0.0458),
    'MSFT': (390.00, 0.112),
    'NVO':  (40.81,  1.25),
    'ORCL': (135.25, 0.25),
    'SMCI': (22.16,  2.07),    # 加碼
    'TSLA': (240.00, 0.138),   # 新增
}
COIN_MAP = {"ADBE":"ADBEX","HIMS":"HIMSX","IONQ":"IONQX",
            "META":"METAX","MSFT":"MSFTX","NVO":"NVOX",
            "ORCL":"ORCLX","SMCI":"SMCIX","TSLA":"TSLAX"}

# 派網加密貨幣 (coingecko_id, 預設數量, 成本USD) — 更新：2026-04-18
PIONEX_CRYPTO = {
    'ETH':  ('ethereum', 0.00927,  2200.0),
    'ADA':  ('cardano',  54.21,    0.35),   # 大幅增加
    'ARKM': ('arkham',   48.77,    0.097),  # 減少
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
    for code in CATHAY_TW:
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
        time.sleep(0.2)
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
    "BTC":  {"entry_zone":[78000, 92000], "target":130000, "stop":72000,
             "theme":"數位黃金", "reason":"ETF 機構資金持續流入，減半後供應收緊，長期多頭結構，回 $78k~92k 可分批建倉"},
    "SOL":  {"entry_zone":[120, 155],  "target":280,  "stop":100,
             "theme":"高速公鏈", "reason":"DEX 交易量超越以太坊，手續費收入爆炸，Firedancer 升級在即，是以太坊最強挑戰者"},
    "LINK": {"entry_zone":[12, 16],    "target":32,   "stop":10,
             "theme":"預言機", "reason":"DeFi 基礎設施龍頭，與傳統金融（Swift、DTCC）合作，跨鏈互操作需求持續增長"},
    "AVAX": {"entry_zone":[22, 30],    "target":55,   "stop":18,
             "theme":"L1/企業鏈", "reason":"Avalanche9000 升級大幅降低 L1 建鏈成本，機構與遊戲生態快速擴展"},
    "INJ":  {"entry_zone":[15, 22],    "target":50,   "stop":12,
             "theme":"DeFi/衍生品", "reason":"鏈上衍生品龍頭，TVL 持續成長，機構級 DeFi 首選，回調到 $15~22 可布局"},
    "SUI":  {"entry_zone":[2.5, 3.5],  "target":8,    "stop":2.0,
             "theme":"新興L1", "reason":"Move 語言生態，三星 Galaxy 預裝錢包，用戶增速最快的 L1 之一，高風險高潛力"},
    "DOGE": {"entry_zone":[0.15, 0.22],"target":0.45, "stop":0.12,
             "theme":"迷因/馬斯克", "reason":"X 支付整合預期，馬斯克效應，迷因幣龍頭；純投機，嚴控倉位 5% 以內"},
    "TIA":  {"entry_zone":[3.5, 5.0],  "target":12,   "stop":2.8,
             "theme":"模組化區塊鏈", "reason":"資料可用層（DA）龍頭，Rollup 擴展需求直接受益，低市值高潛力小倉"},
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
def fetch_pionex_bal() -> dict:
    ts = str(int(time.time()*1000))
    path = "/api/v1/account/balances"
    q = urllib.parse.urlencode(sorted({"timestamp":ts}.items()))
    sig = hmac.new(PIONEX_SECRET.encode(), f"GET{path}?{q}".encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request(f"https://api.pionex.com{path}?{q}",
        headers={"PIONEX-KEY":PIONEX_KEY,"PIONEX-SIGNATURE":sig,
                 "PIONEX-TIMESTAMP":ts,"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        bals = data.get("data",{}).get("balances",[])
        return {b["coin"]:float(b.get("free",0))+float(b.get("frozen",0))
                for b in bals if float(b.get("free",0))+float(b.get("frozen",0))>0.0001}
    except:
        return {}

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

    # ── 派網股票
    for sym,(cost,default_qty) in PIONEX_STOCKS.items():
        coin = COIN_MAP.get(sym,sym+"X")
        qty  = pio_bal.get(coin,default_qty)
        q    = us_q.get(sym,{})
        rows.append(us_row("派網",f"{coin}→{sym}",cost,qty,q.get("price",0),q.get("prev",0)))

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
RESEARCH_NOTES = [
    {
        "date": "2026-04-18",
        "channel": "Money or Life 美股頻道",
        "author": "Ace (AS)",
        "title": "本周赚够，下周减仓！週六複盤",
        "url": "https://www.youtube.com/watch?v=ja-8fLQjTDI",
        "perf": "本月回報 +36.4%　YTD +30%　融資倉位 -11% 現金",
        "highlights": [
            {"sym":"TSLA",  "action":"HOLD",  "note":"週五重回 $400+，等下週Q1財報，長期信心維持"},
            {"sym":"RKLB",  "action":"WATCH", "note":"不受SpaceX上市壓力，關注14億現金用途，理想加倉 $75以下"},
            {"sym":"IRDM",  "action":"BUY",   "note":"成本$29從底部大幅反轉，上方阻力小，目標$60+"},
            {"sym":"HIMS",  "action":"BUY",   "note":"FDA對多肽小分子限制放寬，本週暴漲，GLP-1概念強勢"},
            {"sym":"INTC",  "action":"WATCH", "note":"由空轉多！馬斯克潛在晶片製造合作 + 18A良率提升，財報下週"},
            {"sym":"ICHR",  "action":"WATCH", "note":"半導體設備上游，AI帶動資本支出受益，低調潛力股"},
            {"sym":"MSTR",  "action":"HOLD",  "note":"持續定額投資，平均成本$200，比特幣代理倉位"},
            {"sym":"SATS",  "action":"HOLD",  "note":"趨於穩定創新高，Ace $132加倉，維持約10%倉位"},
            {"sym":"EOSC",  "action":"WATCH", "note":"數據中心儲能概念，但需注意管理層誠信，不適長期"},
        ],
        "key_actions": [
            "下週 TSLA Q1 財報 — 重要觀察點",
            "下週 INTC Q1 財報 — 轉多後第一個觀察機會",
            "Circle 已全數清倉，跌破 $100 或趨近 $90 考慮重新買入",
            "建議保持平常心，適時調整融資水位確保安全",
        ],
    },
]

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


def render_research_notes():
    st.header("📺 YouTube 研究筆記")

    for note in RESEARCH_NOTES:
        tc = "#7c3aed"
        st.markdown(f"""
<div style="background:#1e1e2e;border-radius:10px;padding:16px;margin-bottom:12px;border-left:4px solid {tc}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
    <div>
      <span style="color:#7c3aed;font-weight:bold;font-size:16px">{note['title']}</span><br>
      <span style="color:#64748b;font-size:13px">📅 {note['date']}　✍️ {note['author']} @ {note['channel']}</span>
    </div>
    <a href="{note['url']}" target="_blank"
       style="background:#7c3aed;color:#fff;padding:4px 12px;border-radius:6px;font-size:13px;text-decoration:none">
       ▶ 看影片
    </a>
  </div>
  <div style="background:#0f172a;border-radius:6px;padding:8px 12px;margin-top:10px;font-size:13px;color:#94a3b8">
    💹 {note['perf']}
  </div>
</div>""", unsafe_allow_html=True)

        # 個股重點
        st.markdown("**📌 個股重點**")
        cols = st.columns(3)
        action_color = {"BUY":"#22c55e","HOLD":"#94a3b8","WATCH":"#f59e0b","SELL":"#ef4444"}
        for i, h in enumerate(note["highlights"]):
            c = cols[i % 3]
            ac = action_color.get(h["action"], "#94a3b8")
            c.markdown(f"""
<div style="background:#1e293b;border-radius:6px;padding:8px;margin:3px 0;border-left:3px solid {ac}">
  <b>{h['sym']}</b> <span style="color:{ac};font-size:12px">[{h['action']}]</span><br>
  <span style="color:#94a3b8;font-size:12px">{h['note']}</span>
</div>""", unsafe_allow_html=True)

        # 關鍵行動
        st.markdown("**⚡ 關鍵行動**")
        for ka in note["key_actions"]:
            st.markdown(f"- {ka}")

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
# 加密貨幣追蹤 + 觀察清單
# ════════════════════════════════════════════════════
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

    # ── 觀察清單 ──────────────────────────────────────
    st.subheader("👀 幣種觀察清單")
    wl_rows = []
    for sym, info in CRYPTO_WATCHLIST.items():
        q     = cry_q.get(sym, {})
        price = q.get("price", 0)
        chg   = q.get("chg_pct", 0)
        lo, hi = info["entry_zone"]
        target = info["target"]

        if price == 0:    status = "❓"
        elif price <= lo: status = "🟢 進場！"
        elif price <= hi: status = "🟡 接近"
        elif (price - hi) / hi * 100 <= 15: status = "🔵 觀察"
        else:             status = "⚪ 等待"

        upside = (target - price) / price * 100 if price else 0
        pct_away = f"+{(price-hi)/hi*100:.0f}%" if price > hi else "✓進場區"
        price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
        target_fmt = f"${target:,.4f}" if target < 1 else f"${target:,.0f}"
        lo_fmt = f"${lo:,.4f}" if lo < 1 else f"${lo:,.0f}"
        hi_fmt = f"${hi:,.4f}" if hi < 1 else f"${hi:,.0f}"

        wl_rows.append({
            "狀態":   status,
            "幣種":   sym,
            "主題":   info["theme"],
            "現價":   price_fmt,
            "今日":   f"{chg:+.1f}%",
            "進場區": f"{lo_fmt}~{hi_fmt}",
            "距進場": pct_away,
            "目標":   target_fmt,
            "潛力":   f"+{upside:.0f}%",
            "停損":   f"${info['stop']:,.0f}" if info['stop'] >= 1 else f"${info['stop']:.4f}",
            "邏輯":   info["reason"],
        })

    wl_df = pd.DataFrame(wl_rows)
    ready = wl_df[wl_df["狀態"].str.contains("進場！", na=False)]
    near  = wl_df[wl_df["狀態"].str.contains("接近",  na=False)]
    if not ready.empty: st.success(f"🟢 已進場區：{', '.join(ready['幣種'])}")
    if not near.empty:  st.warning(f"🟡 接近進場：{', '.join(near['幣種'])}")

    def _color_crypto(val):
        if "進場！" in str(val): return "background:#14532d;color:#86efac"
        if "接近"   in str(val): return "background:#713f12;color:#fde68a"
        return ""

    st.dataframe(wl_df.style.map(_color_crypto, subset=["狀態"]),
                 use_container_width=True, hide_index=True)

    # ── 詳細卡片（展開） ──────────────────────────────
    with st.expander("📋 觀察清單詳細分析"):
        for sym, info in CRYPTO_WATCHLIST.items():
            q     = cry_q.get(sym, {})
            price = q.get("price", 0)
            chg   = q.get("chg_pct", 0)
            lo, hi = info["entry_zone"]
            target = info["target"]
            upside = (target - price) / price * 100 if price else 0
            tc = "#22c55e" if chg >= 0 else "#ef4444"
            price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"

            in_zone = price <= hi
            border = "#22c55e" if price <= lo else ("#f59e0b" if price <= hi else "#334155")
            badge = "🟢 已進場區" if price <= lo else ("🟡 接近進場" if price <= hi else "⚪ 等待")
            st.markdown(f"""
<div style="background:#1e1e2e;border-radius:8px;padding:14px;margin:6px 0;border-left:4px solid {border}">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
    <div>
      <span style="font-size:17px;font-weight:bold">{sym}</span>
      <span style="background:#1e293b;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:12px;margin-left:8px">{info['theme']}</span>
      <span style="margin-left:8px;font-size:12px">{badge}</span>
    </div>
    <div style="text-align:right">
      <span style="font-size:18px;font-weight:bold">{price_fmt}</span>
      <span style="color:{tc};margin-left:8px">{chg:+.2f}%</span>
    </div>
  </div>
  <div style="display:flex;gap:24px;margin-top:8px;font-size:13px;flex-wrap:wrap">
    <span>進場區 <b>${lo:g} ~ ${hi:g}</b></span>
    <span>目標 <b style="color:#22c55e">${target:g}</b></span>
    <span>潛力 <b style="color:#22c55e">+{upside:.0f}%</b></span>
    <span>停損 <b style="color:#ef4444">${info['stop']:g}</b></span>
  </div>
  <p style="color:#94a3b8;font-size:13px;margin:8px 0 0">{info['reason']}</p>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# 主畫面
# ════════════════════════════════════════════════════
st.title("📊 Jim 投資全視界")

_live_rate = fetch_usdtwd_rate()
_exrate = st.session_state.get("exchange_rate", _live_rate)

with st.spinner("抓取即時行情..."):
    df, us_q, tw_q, cry_q = build_portfolio(exrate=_exrate)

# ── 警報區（最上方）──────────────────────────────────
danger_list, entry_list = check_alerts(df, us_q, tw_q)

if danger_list or entry_list:
    with st.container():
        if entry_list:
            st.success("🚀 **急需入場警報**")
            for a in entry_list:
                st.markdown(f'<div class="alert-entry">{a}</div>', unsafe_allow_html=True)
        if danger_list:
            st.error("🚨 **個股危險警報**")
            for a in danger_list:
                st.markdown(f'<div class="alert-danger">{a}</div>', unsafe_allow_html=True)
    st.divider()

# ── 今日狀態列 ───────────────────────────────────────
render_status_bar(df, _exrate)
st.divider()

# ── Market Insights ───────────────────────────────────
render_market_insights(us_q)
render_daily_system()
st.divider()

# ── 頂部 4 帳戶數據看板 ───────────────────────────────
platforms = ["國泰美股","國泰台股","派網","Firstrade"]

total_val  = df["現值(TWD)"].sum()
total_pnl  = df["損益(TWD)"].sum()
total_today= df["今日(TWD)"].sum()

def _pnl_html(today, pnl):
    tc = "#22c55e" if today >= 0 else "#ef4444"
    pc = "#22c55e" if pnl   >= 0 else "#ef4444"
    return (f'<div style="font-size:13px;margin-top:4px">'
            f'<span style="color:{tc}">今日 NT${today:+,}</span>'
            f'<span style="color:#475569">　｜　</span>'
            f'<span style="color:{pc}">累積 NT${pnl:+,}</span>'
            f'</div>')

cols = st.columns(5)
cols[0].metric("💰 總市值", f"NT$ {total_val:,}")
cols[0].markdown(_pnl_html(total_today, total_pnl), unsafe_allow_html=True)
for i,plat in enumerate(platforms):
    sub   = df[df["平台"]==plat]
    val   = sub["現值(TWD)"].sum()
    today = sub["今日(TWD)"].sum()
    pnl   = sub["損益(TWD)"].sum()
    cols[i+1].metric(plat, f"NT$ {val:,}")
    cols[i+1].markdown(_pnl_html(today, pnl), unsafe_allow_html=True)

st.divider()

# ── 出場優先 / 進場優先 ───────────────────────────────
col_exit, col_entry = st.columns(2)

with col_exit:
    st.subheader("🚨 出場優先排名")
    exit_rows = []
    for _, row in df.iterrows():
        raw = row["標的"]
        sym = raw.split("→")[-1] if "→" in raw else raw
        info = ANALYST.get(sym)
        if not info or info["action"] != "SELL":
            continue
        price = row["現價"]
        pnl_pct = row["總損益(%)"]
        stop = info.get("stop", 0)
        dist_stop = (price - stop) / price * 100 if stop and price else 0
        # 緊迫度：虧損越多 or 距停損越近 越優先
        urgency = -pnl_pct + (5 - dist_stop if dist_stop < 5 else 0)
        exit_rows.append({
            "_urgency": urgency,
            "標的": sym,
            "現價": f"${price:.2f}",
            "損益": f"{pnl_pct:+.1f}%",
            "停損": f"${stop:.0f}" if stop else "—",
            "原因": info["reason"],
            "更新": info.get("date",""),
        })
    exit_rows.sort(key=lambda x: x["_urgency"], reverse=True)
    for i, r in enumerate(exit_rows, 1):
        color = "#ef4444" if i == 1 else ("#f97316" if i == 2 else "#eab308")
        st.markdown(f"""
<div style="background:#1e1e2e;border-left:4px solid {color};padding:10px;border-radius:6px;margin:6px 0">
<b>#{i} {r['標的']}</b>　現價 {r['現價']}　損益 <span style="color:{color}">{r['損益']}</span>　停損 {r['停損']}<br>
<span style="font-size:13px;color:#94a3b8">{r['原因']}</span>
</div>""", unsafe_allow_html=True)
    if not exit_rows:
        st.info("目前無出場建議")

with col_entry:
    st.subheader("🚀 進場優先排名")
    entry_rows = []
    # 已持倉 BUY
    seen_syms = set()
    for _, row in df.iterrows():
        raw = row["標的"]
        sym = raw.split("→")[-1] if "→" in raw else raw
        if sym in seen_syms: continue
        seen_syms.add(sym)
        info = ANALYST.get(sym)
        if not info or info["action"] != "BUY": continue
        price = row["現價"]
        target = info.get("target", 0)
        upside = (target - price) / price * 100 if target and price else 0
        entry_rows.append({
            "_upside": upside,
            "標的": sym,
            "類型": "持倉加碼",
            "現價": f"${price:.2f}",
            "目標": f"${target:.0f}",
            "潛力": f"+{upside:.0f}%",
            "原因": info["reason"],
        })
    # 觀察清單進場區
    wl_q2 = fetch_us_quotes(tuple(WATCHLIST.keys()))
    for sym, info in WATCHLIST.items():
        q = wl_q2.get(sym, {})
        price = q.get("price", 0)
        if not price: continue
        lo, hi = info["entry_zone"]
        if price > hi * 1.05: continue  # 距進場區超過5%不顯示
        upside = (info["target"] - price) / price * 100 if price else 0
        status = "🟢 已進場區" if price <= hi else "🟡 接近進場"
        entry_rows.append({
            "_upside": upside + (20 if price <= hi else 0),
            "標的": sym,
            "類型": status,
            "現價": f"${price:.2f}",
            "目標": f"${info['target']:.0f}",
            "潛力": f"+{upside:.0f}%",
            "原因": info["reason"],
        })
    entry_rows.sort(key=lambda x: x["_upside"], reverse=True)
    for i, r in enumerate(entry_rows[:6], 1):
        color = "#22c55e" if "進場區" in r["類型"] else ("#0ea5e9" if i <= 2 else "#7c3aed")
        st.markdown(f"""
<div style="background:#1e1e2e;border-left:4px solid {color};padding:10px;border-radius:6px;margin:6px 0">
<b>#{i} {r['標的']}</b>　<span style="color:{color}">{r['類型']}</span>　{r['現價']} → {r['目標']}　<b style="color:{color}">{r['潛力']}</b><br>
<span style="font-size:13px;color:#94a3b8">{r['原因']}</span>
</div>""", unsafe_allow_html=True)
    if not entry_rows:
        st.info("目前無進場機會")

st.divider()

# ── 財報提醒 + 資金分析 ───────────────────────────────
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
        if days_left < 0:
            continue
        urgency = "🔴" if days_left <= 7 else ("🟡" if days_left <= 14 else "🟢")
        st.markdown(f"{urgency} **{e['sym']}**　{e['date']}　（{days_left}天後）　{e['note']}")

with fund_col:
    st.subheader("💵 資金利用率")
    usdt_val  = df[df["標的"]=="USDT"]["現值(TWD)"].sum()
    total_all = df["現值(TWD)"].sum()
    invested  = total_all - usdt_val
    util_pct  = invested / total_all * 100 if total_all else 0
    idle_usd  = usdt_val / _exrate

    # 出場候選可釋放
    sell_syms = ["JOBY","NVDL","PYPL","RUN"]
    sell_val  = df[df["標的"].isin(sell_syms)]["現值(TWD)"].sum()
    sell_usd  = sell_val / _exrate

    st.metric("閒置 USDT", f"${idle_usd:.0f}　≈ NT${usdt_val:,.0f}")
    st.metric("投資部位", f"{util_pct:.1f}% 已投入",
              delta=f"閒置 {100-util_pct:.1f}%")
    if sell_val > 0:
        st.info(f"📤 出場候選（{', '.join(sell_syms)}）\n可釋放 **NT${sell_val:,.0f}**（≈ **${sell_usd:.0f}**）")

st.divider()

# ── 操作建議 ─────────────────────────────────────────
st.subheader("🎯 操作建議")

def build_rec_rows(df):
    buy_r,hold_r,sell_r=[],[],[]
    seen=set()
    for _,row in df.iterrows():
        raw=row["標的"]; sym=raw.split("→")[-1] if "→" in raw else raw
        if sym in seen or sym in ("USDT","ETH","ADA","ARKM"): continue
        seen.add(sym)
        info=ANALYST.get(sym)
        if not info: continue
        price=row["現價"]; target=info["target"]
        upside=(target-price)/price*100 if target and price else 0
        plat="/".join(set(df[df["標的"].str.contains(sym,na=False)]["平台"].tolist()))
        dist_stop = (price-info["stop"])/price*100 if info.get("stop") and price else 0
        rec_date = info.get("date","")
        try:
            days_old = (datetime.now() - datetime.strptime(rec_date, "%Y-%m-%d")).days
            date_label = f"{rec_date} ({'今日' if days_old==0 else f'{days_old}天前'}{'⚠️' if days_old>=7 else ''})"
        except:
            date_label = rec_date
        rec={"標的":sym,"現價":f"${price:.2f}","目標":f"${target:.0f}" if target else "—",
             "距目標":f"+{upside:.0f}%" if upside>0 else "—",
             "距停損":f"-{dist_stop:.1f}%",
             "持倉損益":f"{row['總損益(%)']:+.1f}%",
             "停損":f"${info['stop']:.0f}" if info.get('stop') else "—",
             "平台":plat,"更新":date_label,"理由":info["reason"]}
        if info["action"]=="BUY":   buy_r.append(rec)
        elif info["action"]=="SELL":sell_r.append(rec)
        else:                       hold_r.append(rec)
    return buy_r,hold_r,sell_r

buy_r,hold_r,sell_r=build_rec_rows(df)
_rb, _rh, _rs = st.columns(3)

def _rec_card(rec, color):
    return (f'<div style="background:#1e1e2e;border-left:3px solid {color};padding:8px;'
            f'border-radius:4px;margin:4px 0;font-size:13px">'
            f'<b>{rec["標的"]}</b>　{rec["現價"]} → <b style="color:{color}">{rec["目標"]}</b>　{rec["距目標"]}<br>'
            f'損益 {rec["持倉損益"]}　停損 {rec["停損"]}<br>'
            f'<span style="color:#94a3b8">{rec["理由"]}</span></div>')

with _rb:
    st.markdown(f"**✅ 加碼 ({len(buy_r)})**")
    for r in buy_r:
        st.markdown(_rec_card(r,"#22c55e"), unsafe_allow_html=True)
with _rh:
    st.markdown(f"**⏸️ 觀望 ({len(hold_r)})**")
    for r in hold_r:
        st.markdown(_rec_card(r,"#94a3b8"), unsafe_allow_html=True)
with _rs:
    st.markdown(f"**🚨 出場 ({len(sell_r)})**")
    for r in sell_r:
        st.markdown(_rec_card(r,"#ef4444"), unsafe_allow_html=True)

st.divider()

# ── 圖表 + 新聞 ──────────────────────────────────────
left,right=st.columns([1.2,1])

with left:
    pie=df.groupby("平台")["現值(TWD)"].sum().reset_index()
    fig_pie=px.pie(pie,names="平台",values="現值(TWD)",hole=0.4,title="帳戶分佈",
                   color_discrete_sequence=["#7c3aed","#f59e0b","#0ea5e9","#10b981"])
    st.plotly_chart(fig_pie,use_container_width=True)

    today_df=df[~df["標的"].isin(["USDT"])].sort_values("今日(TWD)").copy()
    plat_colors={"國泰美股":"#0ea5e9","國泰台股":"#f59e0b","派網":"#7c3aed","Firstrade":"#10b981"}
    today_df["顏色"]=today_df.apply(
        lambda r: plat_colors.get(r["平台"],"#6b7280") if r["今日(TWD)"]>=0
                  else "#ef4444", axis=1)
    fig_today=go.Figure(go.Bar(
        x=today_df["今日(TWD)"],y=today_df["標的"],orientation='h',
        marker_color=today_df["顏色"],
        text=[f"NT${v:+,}" for v in today_df["今日(TWD)"]],textposition='outside',
        customdata=today_df["平台"],
        hovertemplate="%{y}  %{customdata}<br>今日 NT$%{x:+,}<extra></extra>"))
    fig_today.update_layout(title="今日損益排行(NT$)　各平台分色",height=520,
                             margin=dict(l=0,r=80,t=40,b=0))
    st.plotly_chart(fig_today,use_container_width=True)

with right:
    st.subheader("🎙️ FinancialJuice 即時新聞")
    components.iframe("https://www.financialjuice.com/feed",height=750,scrolling=True)

st.divider()

# ── 觀察清單 ─────────────────────────────────────────
st.subheader("👀 觀察清單")
wl_q = fetch_us_quotes(tuple(WATCHLIST.keys()))
wl_rows=[]
for sym,info in WATCHLIST.items():
    q=wl_q.get(sym,{}); price=q.get("price",0); chg=q.get("chg_pct",0)
    lo,hi=info["entry_zone"]
    if price==0: status="❓"
    elif price<=lo: status="🟢 進場！"
    elif price<=hi: status="🟡 接近"
    elif (price-hi)/hi*100<=10: status="🔵 觀察"
    else: status="⚪ 等待"
    upside=(info["target"]-price)/price*100 if price else 0
    pct_away=f"+{(price-hi)/hi*100:.0f}%" if price>hi else "✓進場區"

    tech=fetch_technicals(sym)
    wl_rows.append({
        "狀態":status,"標的":sym,"主題":info["theme"],
        "現價":f"${price:.2f}","今日":f"{chg:+.1f}%",
        "多空":tech.get("sentiment","—"),"RSI":tech.get("rsi","—"),
        "支撐":f"${tech['support']}" if tech.get("support") else "—",
        "壓力":f"${tech['resist']}"  if tech.get("resist")  else "—",
        "進場區":f"${lo}~${hi}","距進場":pct_away,
        "目標":f"${info['target']:.0f}","潛在獲利":f"+{upside:.0f}%",
        "停損":f"${info['stop']:.0f}","更新":info["date"],"邏輯":info["reason"],
    })

wl_df=pd.DataFrame(wl_rows)
ready=wl_df[wl_df["狀態"].str.contains("進場！",na=False)]
near =wl_df[wl_df["狀態"].str.contains("接近",na=False)]
if not ready.empty: st.success(f"🟢 已入進場區：{', '.join(ready['標的'])}")
if not near.empty:  st.warning(f"🟡 接近進場：{', '.join(near['標的'])}")

def color_wl(val):
    if "進場！" in str(val): return "background:#14532d;color:#86efac"
    if "接近"   in str(val): return "background:#713f12;color:#fde68a"
    return ""
st.dataframe(wl_df.style.map(color_wl,subset=["狀態"]),
             use_container_width=True,hide_index=True)

with st.expander("📈 個股深度分析"):
    pick=st.selectbox("選擇：",list(WATCHLIST.keys()),key="wl_pick")
    info=WATCHLIST[pick]; q=wl_q.get(pick,{}); price=q.get("price",0)
    tech=fetch_technicals(pick)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("現價",f"${price:.2f}",f"{q.get('chg_pct',0):+.2f}%")
    c2.metric("進場區",f"${info['entry_zone'][0]}~${info['entry_zone'][1]}")
    c3.metric("目標",f"${info['target']:.0f}",f"+{(info['target']-price)/price*100:.0f}%" if price else None)
    c4.metric("RSI",tech.get("rsi","—"))
    if tech:
        s,r=tech["support"],tech["resist"]
        pos=max(0,min(100,(price-s)/(r-s)*100)) if r!=s else 50
        st.progress(int(pos),text=f"支撐 ${s}  ←  ${price:.2f}  →  壓力 ${r}")
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

# ── 投資組合歷史走勢 ──────────────────────────────────
render_portfolio_history()
st.divider()

# ── 4 帳戶詳細持倉 ────────────────────────────────────
st.subheader("📋 持倉明細")

def render_platform_detail(df, platform):
    sub = df[df["平台"] == platform].copy()
    sub = sub.sort_values("今日(TWD)", ascending=False)
    v = sub["現值(TWD)"].sum()
    p = sub["損益(TWD)"].sum()
    t = sub["今日(TWD)"].sum()
    t_color = "🟢" if t >= 0 else "🔴"
    p_color = "🟢" if p >= 0 else "🔴"
    label = (f"{t_color} {platform}　市值 NT${v:,}　"
             f"今日 {'▲' if t>=0 else '▼'} NT${abs(t):,}　"
             f"累積 {'▲' if p>=0 else '▼'} NT${abs(p):,}")
    with st.expander(label):
        # 平台匯總指標
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("總市值", f"NT${v:,}")
        mc2.metric("今日損益", f"NT${t:+,}", delta_color="normal" if t >= 0 else "inverse")
        mc3.metric("累積損益", f"NT${p:+,}", delta_color="normal" if p >= 0 else "inverse")
        st.divider()

        # 今日漲最多的標的標示
        if not sub.empty:
            top_sym = sub.iloc[0]["標的"]
            top_today = sub.iloc[0]["今日(TWD)"]
            if top_today > 0:
                st.success(f"🏆 今日最強：**{top_sym}**　今日 NT${top_today:+,}")
            elif top_today < 0:
                st.error(f"📉 今日最弱：**{top_sym}**　今日 NT${top_today:+,}")

        # 每檔排名卡片
        max_abs = sub["今日(TWD)"].abs().max() or 1
        for rank_i, (_, row) in enumerate(sub.iterrows()):
            sym      = row["標的"]
            price    = row["現價"]
            value    = row["現值(TWD)"]
            today_v  = int(row["今日(TWD)"])
            total_v  = int(row["損益(TWD)"])
            today_pct= row["漲跌幅(%)"]
            total_pct= row["總損益(%)"]
            bar_w    = int(abs(today_v) / max_abs * 100)
            tc = "#22c55e" if today_v >= 0 else "#ef4444"
            pc = "#22c55e" if total_v >= 0 else "#ef4444"
            medal = ("🥇" if rank_i == 0 else
                     "🥈" if rank_i == 1 else
                     "🥉" if rank_i == 2 else f"&nbsp;&nbsp;{rank_i+1}.")
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

for plat in ["國泰美股","國泰台股","派網","Firstrade"]:
    render_platform_detail(df, plat)

# ── Finviz + 個股圖 ───────────────────────────────────
st.divider()
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

# ── Insider Trading ──────────────────────────────────
st.divider()
_held_syms = list(set(df["標的"].str.split("→").str[-1].tolist()))
render_insider_trading(_held_syms)

# ── 加密貨幣追蹤 + 觀察清單 ───────────────────────────
st.divider()
render_crypto_dashboard(cry_q, _exrate)

# ── YouTube 研究筆記 + 待辦事項 ───────────────────────
st.divider()
render_research_notes()

# ── 撿漏監控 ─────────────────────────────────────────
st.divider()
st.header("🛒 FB Marketplace 撿漏監控")

_deals_file = os.path.join(os.path.dirname(__file__), "deals.json")
_config_file = os.path.join(os.path.dirname(__file__), "config.json")

def _load_deals():
    try:
        with open(_deals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_scan": None, "deals": []}

def _load_scraper_config():
    try:
        with open(_config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_deal_data = _load_deals()
_scraper_cfg = _load_scraper_config()
_threshold = _scraper_cfg.get("threshold_ratio", 0.6)

# 狀態列
_col_info1, _col_info2, _col_info3 = st.columns(3)
with _col_info1:
    _scan_time = _deal_data.get("last_scan")
    if _scan_time:
        st.metric("上次掃描", _scan_time[:16].replace("T", " "))
    else:
        st.metric("上次掃描", "尚未執行")
with _col_info2:
    st.metric("監控標的數", len(_scraper_cfg.get("targets", [])))
with _col_info3:
    st.metric("本次發現好物", len(_deal_data.get("deals", [])))

# 手動執行掃描
if st.button("🔍 立即執行掃描（需安裝 playwright）"):
    with st.spinner("爬蟲執行中，請稍候..."):
        try:
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "fb_scraper.py")],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                st.success("掃描完成！")
                st.text(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
            else:
                st.error("掃描時發生錯誤")
                st.text(result.stderr[-1000:])
        except Exception as _e:
            st.error(f"無法啟動爬蟲：{_e}")
    st.rerun()

# 顯示發現的標的
_deals = _deal_data.get("deals", [])
if _deals:
    st.subheader(f"🔥 發現 {len(_deals)} 個撿漏標的")
    # 按品項分組，每組用一行卡片呈現
    from collections import defaultdict
    _grouped = defaultdict(list)
    for _d in _deals:
        _grouped[_d.get("item","其他")].append(_d)
    for _item, _items in _grouped.items():
        _best = _items[0]  # 已按價格排序，第一筆最便宜
        _disc = _best.get("discount_pct", 0)
        _price = _best.get("price", 0)
        _market = _best.get("market_price", 0)
        _title = _best.get("title","")[:35]
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
        _tdf = pd.DataFrame([{
            "器材": t["name"],
            "行情": f"NT${t['market_price']:,}",
            f"觸發 ({_threshold:.0%})": f"NT${int(t['market_price']*_threshold):,}",
        } for t in _targets])
        st.dataframe(_tdf, use_container_width=True, hide_index=True)
    else:
        st.write("config.json 未找到監控清單")

# ── 刷新 ─────────────────────────────────────────────
st.divider()
c1,c2=st.columns([1,5])
with c1:
    if st.button("🔄 立即刷新"):
        st.cache_data.clear(); st.rerun()
with c2:
    st.caption(f"更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}　每60秒自動刷新")
# 自動刷新（60秒）
components.html("""<script>
// 只有在使用者沒有在填表單時才自動刷新（5分鐘）
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
}, 300000);
</script>""", height=0)
