"""
Jim's 書庫 — 獨立頁面
讀取 data/books.json（Google Drive 同步），雜誌感瀏覽 + AI 選書
"""
import streamlit as st
import json, os, hashlib, random
from datetime import date
from collections import Counter

st.set_page_config(
    page_title="📚 Jim 書庫",
    page_icon="📚",
    layout="wide",
)

# ── 樣式 ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap');
html, body, .stApp { background:#0e0e16; color:#e9e9ec; font-family:'Noto Sans TC',sans-serif; }
.bk-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:14px; margin-top:12px; }
.bk-card {
  background:#1a1a20; border-radius:12px; overflow:hidden;
  border:1px solid #2a2a34; transition:transform .15s, border-color .15s;
}
.bk-card:hover { transform:translateY(-3px); border-color:#4a4a5a; }
.bk-cover {
  height:80px; display:flex; align-items:center; justify-content:center;
  position:relative; font-size:32px;
}
.bk-body { padding:10px 12px 8px; }
.bk-title { font-size:12px; font-weight:700; color:#e9e9ec; line-height:1.45; min-height:34px; }
.bk-footer { display:flex; justify-content:space-between; align-items:center; margin-top:6px; }
.bk-badge { font-size:10px; padding:2px 7px; border-radius:99px; }
.bk-shelf { font-size:10px; color:#4a4a5a; }
.bk-status { position:absolute; top:7px; right:9px; font-size:9px; padding:2px 7px; border-radius:99px; }
.stat-card { background:#1a1a20; border-radius:10px; padding:14px 12px; text-align:center; border:1px solid #2a2a34; }
.stat-num { font-size:28px; font-weight:900; }
.stat-label { font-size:11px; margin-top:2px; }
div[data-testid="stSelectbox"] > div { background:#1a1a20 !important; }
</style>
""", unsafe_allow_html=True)

# ── 設定 ────────────────────────────────────────────
CAT_C  = {"AI/科技":"#06b6d4","投資/財富":"#22c55e","人性/心理":"#ec4899",
           "商業/創業":"#f59e0b","生活/心智":"#8b5cf6","溝通/談判":"#3b82f6","其他":"#64748b"}
CAT_EM = {"AI/科技":"🤖","投資/財富":"💰","人性/心理":"🧠",
           "商業/創業":"🚀","生活/心智":"🌱","溝通/談判":"🤝","其他":"📖"}
ST_C   = {"待讀":"#64748b","讀中":"#f59e0b","已讀":"#22c55e"}

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS_FILE = os.path.join(BASE, "data", "books.json")
CONFIG_FILE = os.path.join(BASE, "config.json")

def _tid(title): return hashlib.md5(title.encode()).hexdigest()[:8]

def _load_books():
    try:
        books = json.load(open(BOOKS_FILE, encoding="utf-8"))
        for b in books:
            b.setdefault("status", "待讀")
            b.setdefault("category", "其他")
            b.setdefault("shelf", "電子書")
        return books
    except Exception:
        return []

def _save_books(books):
    try:
        json.dump(books, open(BOOKS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception:
        pass

def _get_api_key():
    try:
        return json.load(open(CONFIG_FILE, encoding="utf-8")).get("anthropic_api_key", "")
    except Exception:
        return ""

# ── 載入書單 ────────────────────────────────────────
books = _load_books()

if not books:
    st.error("📭 找不到書單。請在本機執行 `python sync_books.py` 後重新 push 到 GitHub。")
    st.stop()

# ── Header ──────────────────────────────────────────
cat_cnt = Counter(b["category"] for b in books)
st_cnt  = Counter(b.get("status","待讀") for b in books)

st.markdown("<h1 style='font-size:28px;font-weight:900;margin-bottom:4px'>📚 Jim 的書庫</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#64748b;font-size:13px'>共 {len(books)} 本 · 最後同步自 Google Drive</p>", unsafe_allow_html=True)

# 統計列
col1, col2, col3, col4 = st.columns(4)
for col, label, val, color in [
    (col1, "全部", len(books),            "#e9e9ec"),
    (col2, "待讀", st_cnt.get("待讀",0), "#64748b"),
    (col3, "讀中", st_cnt.get("讀中",0), "#f59e0b"),
    (col4, "已讀", st_cnt.get("已讀",0), "#22c55e"),
]:
    col.markdown(
        f"<div class='stat-card'>"
        f"<div class='stat-num' style='color:{color}'>{val}</div>"
        f"<div class='stat-label' style='color:#64748b'>{label}</div>"
        f"</div>", unsafe_allow_html=True)

st.divider()

# ── 分類色條 ─────────────────────────────────────────
cats_sorted = sorted(cat_cnt.items(), key=lambda x:-x[1])
cat_cols = st.columns(len(cats_sorted))
for i, (cname, cnt) in enumerate(cats_sorted):
    cc  = CAT_C.get(cname, "#64748b")
    em  = CAT_EM.get(cname, "📖")
    pct = cnt / len(books) * 100
    cat_cols[i].markdown(
        f"<div style='text-align:center;padding:6px 2px'>"
        f"<div style='font-size:20px'>{em}</div>"
        f"<div style='font-size:10px;color:{cc};font-weight:700;margin:3px 0'>{cname}</div>"
        f"<div style='font-size:18px;font-weight:900;color:#e9e9ec'>{cnt}</div>"
        f"<div style='background:#24242c;border-radius:4px;height:3px;margin-top:5px'>"
        f"<div style='background:{cc};width:{pct:.0f}%;height:3px;border-radius:4px'></div></div>"
        f"</div>", unsafe_allow_html=True)

st.divider()

# ── AI 選書 ──────────────────────────────────────────
with st.expander("🤖 幫我選書", expanded=False):
    mood = st.text_area("", placeholder="你現在的狀態，例：想了解投資策略、最近壓力大想放鬆、想學 AI 應用...",
                        height=60, label_visibility="collapsed")
    if st.button("幫我挑", type="primary"):
        if mood.strip():
            unread = [b for b in books if b.get("status") != "已讀"]
            blist  = "\n".join(f"- 《{b['title']}》({b['category']})" for b in unread[:80])
            with st.spinner("AI 選書中..."):
                try:
                    ak = _get_api_key()
                    if ak:
                        import anthropic
                        r = anthropic.Anthropic(api_key=ak).messages.create(
                            model="claude-haiku-4-5-20251001", max_tokens=300,
                            messages=[{"role":"user","content":
                                f"我的狀態：{mood}\n我的書單：\n{blist}\n\n"
                                f"推薦1-2本最適合現在讀的，說明理由。繁體中文，簡短有力。"}])
                        st.success(r.content[0].text)
                    else:
                        st.warning("Anthropic API Key 未設定（config.json）")
                except Exception as e:
                    st.error(str(e))
        else:
            st.warning("請描述你的狀態")

# ── 篩選列 ────────────────────────────────────────────
fa, fb, fc = st.columns([1, 1, 3])
with fa:
    sf = st.selectbox("", ["全部狀態","待讀","讀中","已讀"], label_visibility="collapsed")
with fb:
    cf = st.selectbox("", ["全部分類"] + list(CAT_C.keys()), label_visibility="collapsed")
with fc:
    sq = st.text_input("", placeholder="搜尋書名...", label_visibility="collapsed")

filtered = [b for b in books
            if (sf == "全部狀態" or b.get("status","待讀") == sf)
            and (cf == "全部分類" or b.get("category","其他") == cf)]
if sq:
    filtered = [b for b in filtered if sq.lower() in b.get("title","").lower()]

st.caption(f"顯示 {len(filtered)} 本")

# ── 書籍網格 ──────────────────────────────────────────
NCOLS = 5
for ri in range(0, min(len(filtered), 100), NCOLS):
    row   = filtered[ri:ri+NCOLS]
    rcols = st.columns(NCOLS)
    for ci, b in enumerate(row):
        cc   = CAT_C.get(b.get("category","其他"), "#64748b")
        em   = CAT_EM.get(b.get("category","其他"), "📖")
        bst  = b.get("status","待讀")
        stc  = ST_C.get(bst, "#64748b")
        ttl  = b.get("title","")
        short = ttl[:30] + ("…" if len(ttl)>30 else "")
        shelf = b.get("shelf","")
        tid  = _tid(ttl)

        with rcols[ci]:
            st.markdown(f"""
<div class='bk-card'>
  <div class='bk-cover' style='background:linear-gradient(135deg,{cc}30 0%,{cc}08 100%)'>
    <span class='bk-status' style='background:{stc}28;color:{stc}'>{bst}</span>
    <span>{em}</span>
  </div>
  <div class='bk-body'>
    <div class='bk-title'>{short}</div>
    <div class='bk-footer'>
      <span class='bk-badge' style='background:{cc}18;color:{cc}'>{b.get("category","")}</span>
      <span class='bk-shelf'>{shelf}</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

            opts = ["待讀","讀中","已讀"]
            cur  = opts.index(bst) if bst in opts else 0
            nst  = st.selectbox("", opts, index=cur,
                                key=f"s_{tid}", label_visibility="collapsed")
            if nst != bst:
                for rb in books:
                    if rb.get("title") == ttl:
                        rb["status"] = nst; break
                _save_books(books)
                st.rerun()

# ── Footer ────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#4a4a5a'>"
    f"更新書單：本機執行 <code>python sync_books.py</code> 後 git push · {date.today()}</div>",
    unsafe_allow_html=True)
