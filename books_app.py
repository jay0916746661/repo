"""
Jim's 書庫 — 完整閱讀面板
功能：書架瀏覽 / 目錄 / 導讀 / 章節摘錄 / AI 精讀分析
"""
import streamlit as st
import json, os, hashlib, random
import re
from pathlib import Path
from collections import Counter

st.set_page_config(
    page_title="📚 Jim 書庫",
    page_icon="📚",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap');
html,body,.stApp{background:linear-gradient(180deg,#f2ece3 0%, #e8dfd2 100%);color:#2a241e;font-family:'Noto Sans TC',sans-serif;}
[data-testid="stAppViewContainer"]{background:transparent;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#efe7dc;}
.block-container{padding-top:1.6rem;}
.stTabs [data-baseweb="tab-list"]{
  gap:8px;
}
.stTabs [data-baseweb="tab"]{
  background:#f6efe6;
  border:1px solid #d8cdbf;
  border-radius:12px;
  padding:10px 14px;
  color:#5f564c;
}
.stTabs [aria-selected="true"]{
  background:#fffaf3 !important;
  border-color:#b78157 !important;
  color:#251f19 !important;
}
.editor-shell{
  background:
    linear-gradient(180deg, rgba(246,242,234,.98), rgba(238,233,223,.96)),
    radial-gradient(circle at top right, rgba(201,100,66,.10), transparent 24%);
  color:#251f19;
  border:1px solid #d7cfc4;
  border-radius:20px;
  padding:22px 24px;
  box-shadow:0 18px 40px rgba(0,0,0,.18);
  margin-bottom:18px;
  position:relative;
  overflow:hidden;
}
.editor-shell::before{
  content:"";
  position:absolute;
  inset:0;
  background-image:
    linear-gradient(rgba(0,0,0,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,.03) 1px, transparent 1px);
  background-size:28px 28px;
  opacity:.22;
  pointer-events:none;
}
.editor-shell > *{position:relative;z-index:1;}
.editor-kicker{
  font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:#8b5e3c;font-family:monospace;margin-bottom:8px;
}
.editor-title{
  font-size:32px;font-weight:900;line-height:1.15;color:#201a16;margin:0 0 8px 0;
}
.editor-subtitle{
  font-size:14px;line-height:1.9;color:#5f564f;max-width:860px;
}
.editor-quote{
  margin-top:14px;padding:14px 0;border-top:1px solid #d8cfc4;border-bottom:1px solid #d8cfc4;
  font-size:20px;line-height:1.8;color:#352b24;
}
.reading-panel{
  background:
    linear-gradient(180deg, rgba(248,245,239,.98), rgba(242,237,230,.96));
  border:1px solid #d7cfc4;
  border-radius:18px;
  padding:16px 18px 18px;
  box-shadow:0 16px 36px rgba(0,0,0,.14);
  color:#2c251f;
}
.paper-note{
  background:#fffdf8;border:1px solid #ded3c5;border-radius:12px;
  padding:14px 16px;color:#5c5148;font-size:13px;line-height:1.85;
}
.mag-wrap{
  background:
    linear-gradient(135deg,#faf4eb 0%,#f0e6d9 58%,#ebdfd0 100%);
  border:1px solid #d7cab9;border-radius:18px;padding:22px 22px 18px;margin-bottom:18px;
  box-shadow:0 18px 40px rgba(67,45,29,.10);
}
.mag-grid{display:grid;grid-template-columns:1.45fr .9fr;gap:18px;align-items:stretch;}
.mag-kicker{font-size:11px;letter-spacing:.12em;color:#9a6a46;text-transform:uppercase;font-family:monospace;margin-bottom:10px;}
.mag-title{font-size:34px;font-weight:900;line-height:1.06;color:#201a16;margin:0 0 10px 0;}
.mag-desc{font-size:14px;line-height:1.9;color:#5f564c;max-width:760px;}
.mag-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;}
.mag-pill{
  background:#fffaf2;border:1px solid #dccfbe;border-radius:999px;
  padding:5px 10px;font-size:11px;color:#62574e;
}
.cover-card{
  border-radius:16px;padding:18px;background:
  radial-gradient(circle at top right,#c9966844,transparent 28%),
  linear-gradient(180deg,#d7b392,#c79f7d 70%,#b98e6c);
  border:1px solid #d3b498;min-height:220px;display:flex;flex-direction:column;justify-content:space-between;
}
.cover-title{font-size:28px;font-weight:900;line-height:1.02;color:#2c2018;margin:0;max-width:220px;}
.cover-sub{font-size:13px;line-height:1.8;color:#4f3d31;}
.issue-strip{
  background:#f7f0e7;border:1px solid #d9ccbc;border-radius:14px;padding:16px 18px;margin-bottom:18px;
}
.issue-title{font-size:18px;font-weight:800;color:#241d18;margin-bottom:6px;}
.issue-note{font-size:13px;line-height:1.85;color:#62574e;}
.issue-books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px;}
.issue-book{
  background:#fffaf3;border:1px solid #ddd0c1;border-radius:12px;padding:12px 12px 10px;
}
.issue-book strong{display:block;font-size:14px;color:#2c241d;line-height:1.5;margin-bottom:6px;}
.issue-book p{margin:0;font-size:12px;line-height:1.75;color:#6a5f56;}
.daily-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px;}
.daily-card{
  background:#fffaf3;border:1px solid #ddd0c1;border-radius:12px;padding:12px;
}
.daily-card strong{display:block;font-size:13px;color:#2c241d;margin-bottom:4px;}
.daily-card div{font-size:11px;line-height:1.7;color:#6a5f56;}
.bk-card{background:#fbf6ef;border-radius:10px;overflow:hidden;border:1px solid #d9ccbc;
  margin:5px 0;cursor:pointer;transition:border-color .15s;}
.bk-card:hover{border-color:#b88a63;}
.bk-card.selected{border-color:#b78157;box-shadow:0 0 0 2px #b7815740;}
.bk-cover{height:64px;display:flex;align-items:center;justify-content:center;
  font-size:26px;position:relative;}
.bk-body{padding:8px 10px 6px;}
.bk-title{font-size:11px;font-weight:700;color:#2a241e;line-height:1.4;min-height:30px;}
.bk-meta{display:flex;justify-content:space-between;align-items:center;margin-top:5px;}
.catalog-label{
  font-size:10px;letter-spacing:.14em;text-transform:uppercase;
  color:#8d7f72;font-family:monospace;margin-bottom:6px;
}
.left-note{
  font-size:12px;line-height:1.8;color:#7b6d61;margin-bottom:10px;
}
.badge{font-size:9px;padding:2px 6px;border-radius:99px;}
.status-dot{font-size:9px;padding:2px 6px;border-radius:99px;}
.toc-item{padding:7px 10px;border-radius:6px;margin:2px 0;cursor:pointer;
  font-size:13px;border-left:2px solid transparent;transition:all .1s;}
.toc-item:hover{background:#f0e8de;border-left-color:#b78157;}
.toc-item.active{background:#efe4d7;border-left-color:#b78157;color:#8b5e3c;}
.excerpt-box{background:#fffdf8;border-radius:14px;padding:22px 24px;
  border:1px solid #ddd2c4;font-size:15px;line-height:2;color:#2e2721;
  white-space:pre-wrap;max-height:780px;overflow-y:auto;box-shadow:inset 0 1px 0 rgba(255,255,255,.4);}
.intro-box{background:#f7efe7;border-radius:14px;padding:22px 24px;
  border:1px solid #d8c4b2;font-size:15px;line-height:2;color:#332b25;
  white-space:pre-wrap;max-height:620px;overflow-y:auto;}
.ai-box{background:#eef6ef;border-radius:12px;padding:16px 20px;
  border:1px solid #cfe0cf;font-size:13.5px;line-height:1.9;color:#2e4d34;}
.section-title{font-size:11px;letter-spacing:.1em;color:#8b8178;
  text-transform:uppercase;font-family:monospace;margin:14px 0 6px;}
div[data-testid="stVerticalBlock"] > div:has(> iframe){height:auto;}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stCaption, label, .stMarkdown, .stText, p, div{
  color: inherit;
}
button[kind="secondary"], .stButton > button{
  border-radius:12px !important;
}
.stButton > button[kind="secondary"]{
  background:#f8f1e8 !important;
  color:#3c3128 !important;
  border:1px solid #d7cab9 !important;
}
.stButton > button[kind="primary"]{
  background:#b78157 !important;
  color:#fffaf4 !important;
  border:1px solid #a56f48 !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stTextInput input{
  background:#fcf7f0 !important;
  color:#2a241e !important;
  border-color:#d8cdbf !important;
}
@media (max-width: 900px){
  .mag-grid,.issue-books,.daily-grid{grid-template-columns:1fr;}
}
</style>
""", unsafe_allow_html=True)

# ── 設定 ────────────────────────────────────────────
CAT_C  = {"AI/科技":"#6f8c8a","投資/財富":"#6f8b5f","人性/心理":"#a16a5b",
           "商業/創業":"#b07a4f","生活/心智":"#8c7a63","溝通/談判":"#7a6d5a",
           "關係/情緒":"#a87b72","其他":"#8b8178"}
CAT_EM = {"AI/科技":"🤖","投資/財富":"💰","人性/心理":"🧠","商業/創業":"🚀",
           "生活/心智":"🌱","溝通/談判":"🤝","關係/情緒":"💞","其他":"📖"}
ST_C   = {"待讀":"#64748b","讀中":"#f59e0b","已讀":"#22c55e"}

BASE          = Path(__file__).parent
LOCAL_FILE    = BASE / "data" / "local_books.json"
CLOUD_FILE    = BASE / "data" / "books.json"
CONTENT_DIR   = BASE / "data" / "book_contents"
CONFIG_FILE   = BASE / "config.json"
ISSUE_FILE    = BASE / "data" / "reading_issue.json"

# ── 資料載入 ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all_books():
    books = []
    try:
        for b in json.loads(LOCAL_FILE.read_text(encoding="utf-8")):
            b["_source"] = "local"
            b.setdefault("status","待讀")
            b.setdefault("category","其他")
            books.append(b)
    except Exception: pass
    try:
        for b in json.loads(CLOUD_FILE.read_text(encoding="utf-8")):
            b["_source"] = "cloud"
            b.setdefault("status","待讀")
            b.setdefault("drive_id","")
            b.setdefault("id", hashlib.md5(b["title"].encode()).hexdigest()[:12])
            books.append(b)
    except Exception: pass
    return books

def load_content(book_id: str) -> dict | None:
    f = CONTENT_DIR / f"{book_id}.json"
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except: return None
    return None

def save_local_books(books):
    local = [b for b in books if b.get("_source") == "local"]
    try: LOCAL_FILE.write_text(json.dumps(local, ensure_ascii=False, indent=2), encoding="utf-8")
    except: pass

def get_api_key():
    try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("anthropic_api_key","")
    except: return ""

def clean_title(title: str) -> str:
    if not title:
        return ""
    t = re.sub(r"\s+", " ", title).strip()
    t = re.sub(r"\(Z-Library.*?\)", "", t, flags=re.I)
    t = re.sub(r"【.*?】", "", t)
    t = re.sub(r"\(.*?文字版.*?\)", "", t)
    t = re.sub(r"\s*=\s*.*$", "", t)
    for sep in ["：", ":", "｜", "|"]:
        if sep in t and len(t) > 18:
            head = t.split(sep)[0].strip()
            if 3 <= len(head) <= 18:
                t = head
                break
    t = re.sub(r"\s+", " ", t).strip(" -_()（）")
    return t

def short_catalog_title(title: str, limit: int = 12) -> str:
    t = clean_title(title)
    if len(t) <= limit:
        return t
    return t[:limit] + "…"

def load_issue_data():
    if ISSUE_FILE.exists():
        try:
            return json.loads(ISSUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def pick_featured_books(all_books, n=4):
    preferred = ["生活/心智", "關係/情緒", "投資/財富", "溝通/談判", "商業/創業", "人性/心理", "AI/科技"]
    picked = []
    used = set()
    for cat in preferred:
        for b in all_books:
            bid = b.get("id") or hashlib.md5(b["title"].encode()).hexdigest()[:12]
            if b.get("category", "其他") == cat and bid not in used:
                b = dict(b)
                b["id"] = bid
                picked.append(b)
                used.add(bid)
                break
        if len(picked) >= n:
            return picked[:n]
    for b in all_books:
        bid = b.get("id") or hashlib.md5(b["title"].encode()).hexdigest()[:12]
        if bid not in used:
            b = dict(b)
            b["id"] = bid
            picked.append(b)
            used.add(bid)
        if len(picked) >= n:
            break
    return picked[:n]

def build_fallback_issue(all_books):
    featured = pick_featured_books(all_books, 4)
    daily_names = ["週一", "週二", "週三", "週四"]
    daily_focus = ["重新進入狀態", "建立關係感", "想清楚一個選擇", "把重點做完"]
    daily_plan = []
    for i, b in enumerate(featured[:4]):
        daily_plan.append({
            "day": daily_names[i],
            "book": b["title"],
            "pages": f"{2 + i%2}-{4 + i%2} 頁",
            "goal": daily_focus[i],
        })
    return {
        "issue_id": "current",
        "title": "閱讀提案",
        "subtitle": "先把收藏變成正在發生的閱讀",
        "theme": "用每月主題把電子書重新排成一套可實際進行的閱讀節奏。",
        "editor_note": "這裡先用你現有書庫自動編一份本期提案。真正理想的狀態，是每月一個主題，再從你已有的書中選出最適合的幾本。",
        "featured_books": [
            {
                "title": b["title"],
                "category": b.get("category", "其他"),
                "why_this_month": f"這本很適合你目前的{b.get('category', '閱讀')}階段。",
                "daily_pages": f"{2 + idx%2}-{4 + idx%2} 頁",
                "editor_prompt": "先讀一小段，再想一件今天真的能做的事。"
            }
            for idx, b in enumerate(featured)
        ],
        "daily_plan": daily_plan,
    }

def render_issue_header(issue):
    st.markdown(
        f"""
        <div class="mag-wrap">
          <div class="mag-grid">
            <div>
              <div class="mag-kicker">Monthly Reading Proposal</div>
              <div class="mag-title">{issue.get('subtitle') or issue.get('title','閱讀提案')}</div>
              <div class="mag-desc">{issue.get('theme','')}</div>
              <div class="mag-meta">
                <span class="mag-pill">{issue.get('title','閱讀提案')}</span>
                <span class="mag-pill">每次先讀幾頁</span>
                <span class="mag-pill">先有主題，再有選書</span>
                <span class="mag-pill">書庫 + 摘錄 + AI 精讀</span>
              </div>
            </div>
            <div class="cover-card">
              <div class="mag-kicker" style="color:#6f5540">Current Issue</div>
              <div class="cover-title">{issue.get('title','閱讀提案')}</div>
              <div class="cover-sub">{issue.get('editor_note','')}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_issue_blocks(issue):
    featured = issue.get("featured_books", [])[:4]
    daily_plan = issue.get("daily_plan", [])[:4]
    st.markdown(
        f"""
        <div class="issue-strip">
          <div class="issue-title">本期提案</div>
          <div class="issue-note">{issue.get('editor_note','')}</div>
          <div class="issue-books">
            {''.join(
                f"<div class='issue-book'><strong>{item.get('title','')}</strong>"
                f"<p>{item.get('why_this_month','')}</p>"
                f"<p style='margin-top:6px;color:#8b5e3c'>今日建議：{item.get('daily_pages','')}</p></div>"
                for item in featured
            )}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if daily_plan:
        st.markdown("<div class='section-title'>今日幾頁</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="daily-grid">
              {''.join(
                  f"<div class='daily-card'><strong>{item.get('day','')}</strong>"
                  f"<div>{item.get('book','')}</div>"
                  f"<div>{item.get('pages','')}</div>"
                  f"<div>{item.get('goal','')}</div></div>"
                  for item in daily_plan
              )}
            </div>
            """,
            unsafe_allow_html=True,
        )

books = load_all_books()
issue_data = load_issue_data() or build_fallback_issue(books)

# ── Session State ────────────────────────────────────
if "sel_book" not in st.session_state: st.session_state.sel_book = None
if "sel_chapter" not in st.session_state: st.session_state.sel_chapter = 0
if "ai_cache" not in st.session_state: st.session_state.ai_cache = {}
if "focus_mode" not in st.session_state: st.session_state.focus_mode = True

# ══════════════════════════════════════════════════════
# 左欄：書架
# ══════════════════════════════════════════════════════
is_focus_layout = bool(st.session_state.focus_mode and st.session_state.sel_book)
left_ratio = [0.75, 3.85] if is_focus_layout else [1, 2.85]
left, right = st.columns(left_ratio, gap="large")

with left:
    title_size = "18px" if is_focus_layout else "20px"
    st.markdown("<div class='catalog-label'>Catalogue ・ 書架</div>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='font-size:{title_size};font-weight:900;margin-bottom:4px'>📚 書庫</h2>", unsafe_allow_html=True)
    st.markdown("<div class='left-note'>先選一本到兩本真正想開始的，不要讓原始書名把閱讀節奏弄亂。</div>", unsafe_allow_html=True)

    # 統計
    has_content = sum(1 for b in books if (CONTENT_DIR / f"{b.get('id','')}.json").exists())
    local_cnt   = sum(1 for b in books if b.get("_source") == "local")
    cloud_cnt   = sum(1 for b in books if b.get("_source") == "cloud")
    st.markdown(
        f"<div style='font-size:11px;color:#64748b;margin-bottom:10px'>"
        f"共 {len(books)} 本 · 💻 本機 {local_cnt} · ☁️ Drive {cloud_cnt} · "
        f"📄 有內容 {has_content}</div>", unsafe_allow_html=True)

    # 篩選
    sf = st.selectbox("", ["全部","待讀","讀中","已讀"], label_visibility="collapsed", key="sf")
    cf = st.selectbox("", ["全部分類"]+list(CAT_C.keys()), label_visibility="collapsed", key="cf")
    sq = st.text_input("", placeholder="搜尋...", label_visibility="collapsed", key="sq")

    filtered = [b for b in books
                if (sf == "全部" or b.get("status","待讀") == sf)
                and (cf == "全部分類" or b.get("category","其他") == cf)]
    if sq:
        filtered = [b for b in filtered if sq.lower() in b.get("title","").lower()]

    has_filter = lambda b: (CONTENT_DIR / f"{b.get('id','')}.json").exists()

    # 有內容的排前面
    filtered.sort(key=lambda b: (0 if has_filter(b) else 1, b.get("title","")))

    st.caption(f"顯示 {len(filtered)} 本")
    st.divider()

    # 書單
    for b in filtered[:80]:
        bid   = b.get("id","")
        cc    = CAT_C.get(b.get("category","其他"),"#64748b")
        em    = CAT_EM.get(b.get("category","其他"),"📖")
        bst   = b.get("status","待讀")
        stc   = ST_C.get(bst,"#64748b")
        ttl   = b.get("title","")
        clean = clean_title(ttl)
        short = short_catalog_title(ttl, 12 if is_focus_layout else 16)
        has_c = has_filter(b)
        sel   = st.session_state.sel_book == bid
        icon  = "📄" if has_c else "☁️"

        st.markdown(
            f"<div style='font-size:10px;color:#8b8178;letter-spacing:.08em;text-transform:uppercase;"
            f"margin:8px 0 4px 2px'>{clean[:28]}{'…' if len(clean) > 28 else ''}</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            f"{em} {short}",
            key=f"btn_{bid}",
            help=ttl,
            use_container_width=True,
            type="primary" if sel else "secondary",
        ):
            st.session_state.sel_book    = bid
            st.session_state.sel_chapter = 0
            st.rerun()

# ══════════════════════════════════════════════════════
# 右欄：閱讀面板
# ══════════════════════════════════════════════════════
with right:
    sel_id = st.session_state.sel_book
    render_issue_header(issue_data)
    render_issue_blocks(issue_data)
    top_a, top_b = st.columns([4, 1])
    with top_a:
        st.markdown("<div class='section-title'>閱讀模式</div>", unsafe_allow_html=True)
    with top_b:
        focus_label = "縮小內容區" if st.session_state.focus_mode else "放大內容區"
        if st.button(focus_label, key="toggle_focus_mode", use_container_width=True):
            st.session_state.focus_mode = not st.session_state.focus_mode
            st.rerun()
    st.divider()

    if not sel_id:
        st.markdown("""
<div style='height:400px;display:flex;flex-direction:column;align-items:center;
     justify-content:center;color:#4a4a5a;text-align:center;gap:12px'>
  <div style='font-size:56px'>📖</div>
  <div style='font-size:16px;font-weight:700'>選一本書開始閱讀</div>
  <div style='font-size:13px'>從左側書架選擇，有 📄 標記的書有完整內容</div>
</div>""", unsafe_allow_html=True)
        st.stop()

    # 找到書
    book = next((b for b in books if b.get("id") == sel_id), None)
    if not book:
        st.info("找不到書籍")
        st.stop()

    content = load_content(sel_id)
    cc  = CAT_C.get(book.get("category","其他"),"#64748b")
    em  = CAT_EM.get(book.get("category","其他"),"📖")
    bst = book.get("status","待讀")
    stc = ST_C.get(bst,"#64748b")

    quote_map = {
        "生活/心智": "慢一點，內容才有機會真的留下來。",
        "投資/財富": "最重要的不是知道更多，而是判斷哪些值得反覆重讀。",
        "關係/情緒": "真正有價值的連結，往往始於一次沒有立刻求回報的接觸。",
        "溝通/談判": "好的談判，不只是贏，而是讓對方也願意繼續走下去。",
        "人性/心理": "理解自己與他人，常常比急著給答案更重要。",
        "AI/科技": "工具再多，最後還是回到你怎麼安排注意力。 ",
        "商業/創業": "把優勢排好順序，比盲目多做更重要。 ",
        "其他": "先讀幾頁，讓一本書先真的開始。 "
    }
    meta = []
    if content:
        meta.append(f"📄 {content['total_pages']} 頁")
    meta.append(f"<span style='background:{cc}22;color:{cc};padding:3px 9px;border-radius:99px;font-size:11px'>{book.get('category','')}</span>")
    meta.append(f"<span style='background:{stc}22;color:{stc};padding:3px 9px;border-radius:99px;font-size:11px'>{bst}</span>")
    meta.append("💻 本機" if book.get("_source") == "local" else "☁️ Drive")
    editor_quote = quote_map.get(book.get("category", "其他"), quote_map["其他"]).strip()
    st.markdown(
        f"""
        <div class="editor-shell">
          <div class="editor-kicker">Reading Feature</div>
          <div class="editor-title">{em} {book['title']}</div>
          <div class="editor-subtitle">這裡開始不只是書籍閱讀器，而是比較像提案誌的單書閱讀頁。你可以先讀前幾頁、看章節，再讓 AI 幫你把它變成可行動的重點。</div>
          <div style="margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">{' '.join(meta)}</div>
          <div class="editor-quote">「{editor_quote}」</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl_a, ctrl_b, ctrl_c = st.columns([3.6, 1.2, 1.2])
    with ctrl_a:
        st.markdown("<div class='paper-note'>建議閱讀方式：先看導讀，再進章節，最後用 AI 精讀把這本書收斂成你今天能做的一件事。</div>", unsafe_allow_html=True)
    with ctrl_b:
        opts = ["待讀","讀中","已讀"]
        cur  = opts.index(bst) if bst in opts else 0
        nst  = st.selectbox("閱讀狀態", opts, index=cur, key="bk_status")
        if nst != bst:
            book["status"] = nst
            save_local_books(books)
            load_all_books.clear()
            st.rerun()
    with ctrl_c:
        if content and content.get("has_toc"):
            st.markdown(
                f"<div class='paper-note' style='text-align:center;padding:13px 10px'>"
                f"<div style='font-size:11px;color:#8c8177'>章節數</div>"
                f"<div style='font-size:22px;font-weight:900;color:#302720'>{len(content['toc'])}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.divider()

    if not content:
        # 只有 AI 摘要（雲端書）
        st.info("☁️ 這是 Google Drive 書籍，沒有本機 PDF，僅提供 AI 摘要。")
        ak = get_api_key()
        cache_key = f"ai_{sel_id}"
        if cache_key in st.session_state.ai_cache:
            st.markdown(f"<div class='ai-box'>{st.session_state.ai_cache[cache_key]}</div>", unsafe_allow_html=True)
        elif ak:
            if st.button("✨ 生成 AI 書籍摘要", type="primary"):
                with st.spinner("AI 分析中..."):
                    try:
                        import anthropic
                        r = anthropic.Anthropic(api_key=ak).messages.create(
                            model="claude-haiku-4-5-20251001", max_tokens=600,
                            messages=[{"role":"user","content":
                                f"請用繁體中文為《{book['title']}》這本書提供：\n"
                                f"1. 一段導讀（3句話）\n"
                                f"2. 3個核心概念\n"
                                f"3. 最值得讀的原因\n"
                                f"4. 適合在什麼狀態下讀\n"
                                f"5. 讀完後可以做的一件事"}])
                        txt = r.content[0].text
                        st.session_state.ai_cache[cache_key] = txt
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            st.warning("請設定 Anthropic API Key 以使用 AI 摘要")
        st.stop()

    # ── 有內容：顯示完整閱讀器 ───────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📖 導讀", "📋 目錄 & 章節", "🔍 原文摘錄", "🤖 AI 精讀"])

    # ── Tab 1：導讀 ─────────────────────────────────
    with tab1:
        st.markdown("<div class='reading-panel'>", unsafe_allow_html=True)
        if content.get("intro"):
            st.markdown("<div class='section-title'>書籍導讀 · 前幾頁原文</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='intro-box'>{content['intro']}</div>", unsafe_allow_html=True)
        else:
            st.info("此書的導讀頁無法抽取文字（可能是掃描版）")

        # AI 導讀摘要
        ak = get_api_key()
        ai_key = f"intro_{sel_id}"
        st.markdown("<div class='section-title'>AI 生成導讀</div>", unsafe_allow_html=True)
        if ai_key in st.session_state.ai_cache:
            st.markdown(f"<div class='ai-box'>{st.session_state.ai_cache[ai_key]}</div>", unsafe_allow_html=True)
            if st.button("重新生成", key="regen_intro"):
                del st.session_state.ai_cache[ai_key]; st.rerun()
        elif ak:
            if st.button("✨ AI 生成導讀摘要", key="gen_intro", type="primary"):
                intro_text = content.get("intro","")[:1500]
                with st.spinner("AI 分析中..."):
                    try:
                        import anthropic
                        prompt = (
                            f"書名：《{book['title']}》\n"
                            f"分類：{book.get('category','')}\n"
                            f"書籍前幾頁原文（節錄）：\n{intro_text}\n\n"
                            f"請用繁體中文提供：\n"
                            f"【這本書在說什麼】（2-3句）\n"
                            f"【你應該讀這本書，如果你...】（列3個情況）\n"
                            f"【三個核心主題】（各一句說明）\n"
                            f"【讀完能獲得什麼】（一段話）"
                        )
                        r = anthropic.Anthropic(api_key=ak).messages.create(
                            model="claude-haiku-4-5-20251001", max_tokens=600,
                            messages=[{"role":"user","content":prompt}])
                        st.session_state.ai_cache[ai_key] = r.content[0].text
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            st.caption("設定 Anthropic API Key 可生成 AI 導讀")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 2：目錄 & 章節 ────────────────────────────
    with tab2:
        st.markdown("<div class='reading-panel'>", unsafe_allow_html=True)
        chapters = content.get("chapters", [])
        toc      = content.get("toc", [])

        if not chapters:
            st.info("此書沒有可解析的章節內容")
        else:
            c_left, c_right = st.columns([0.8, 2.7], gap="large")
            with c_left:
                st.markdown("<div class='section-title'>章節目錄</div>", unsafe_allow_html=True)
                for i, ch in enumerate(chapters):
                    label = ch["title"][:24] + ("…" if len(ch["title"])>24 else "")
                    is_sel = st.session_state.sel_chapter == i
                    if st.button(
                        f"{'▶ ' if is_sel else '　'}{label}",
                        key=f"ch_{sel_id}_{i}",
                        use_container_width=True,
                        type="primary" if is_sel else "secondary",
                    ):
                        st.session_state.sel_chapter = i
                        st.rerun()

            with c_right:
                idx = st.session_state.sel_chapter
                if idx < len(chapters):
                    ch = chapters[idx]
                    st.markdown(
                        f"<div style='font-size:16px;font-weight:700;color:#8b5e3c;margin-bottom:8px'>"
                        f"第 {idx+1} 章 · {ch['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='excerpt-box'>{ch['excerpt']}</div>", unsafe_allow_html=True)

                    # AI 章節分析
                    ak = get_api_key()
                    ck = f"ch_{sel_id}_{idx}"
                    st.markdown("<div class='section-title'>AI 章節重點</div>", unsafe_allow_html=True)
                    if ck in st.session_state.ai_cache:
                        st.markdown(f"<div class='ai-box'>{st.session_state.ai_cache[ck]}</div>", unsafe_allow_html=True)
                    elif ak:
                        if st.button("✨ 分析這章重點", key=f"gen_ch_{idx}", type="primary"):
                            with st.spinner("AI 分析中..."):
                                try:
                                    import anthropic
                                    r = anthropic.Anthropic(api_key=ak).messages.create(
                                        model="claude-haiku-4-5-20251001", max_tokens=400,
                                        messages=[{"role":"user","content":
                                            f"書名：《{book['title']}》\n"
                                            f"章節：{ch['title']}\n"
                                            f"原文摘錄：\n{ch['excerpt']}\n\n"
                                            f"請用繁體中文簡短整理：\n"
                                            f"1. 這章的核心論點（1句）\n"
                                            f"2. 2-3個關鍵概念\n"
                                            f"3. 可以馬上應用的1個行動"}])
                                    st.session_state.ai_cache[ck] = r.content[0].text
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3：原文摘錄 ───────────────────────────────
    with tab3:
        st.markdown("<div class='reading-panel'>", unsafe_allow_html=True)
        chapters = content.get("chapters", [])
        if chapters:
            sel_title = st.selectbox(
                "選擇章節",
                [f"{i+1}. {ch['title']}" for i, ch in enumerate(chapters)],
                key="excerpt_sel"
            )
            idx2 = int(sel_title.split(".")[0]) - 1
            ch2  = chapters[idx2]
            pg   = ch2.get("page", 0)
            st.caption(f"第 {pg} 頁起 · {len(ch2['excerpt'])} 字")
            st.markdown(f"<div class='excerpt-box'>{ch2['excerpt']}</div>", unsafe_allow_html=True)
        else:
            st.info("沒有章節原文可顯示")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 4：AI 精讀 ────────────────────────────────
    with tab4:
        st.markdown("<div class='reading-panel'>", unsafe_allow_html=True)
        ak = get_api_key()
        full_key = f"full_{sel_id}"

        if not ak:
            st.warning("請設定 Anthropic API Key（config.json 中的 anthropic_api_key）")
        else:
            if full_key in st.session_state.ai_cache:
                st.markdown(f"<div class='ai-box'>{st.session_state.ai_cache[full_key]}</div>", unsafe_allow_html=True)
                if st.button("🔄 重新生成", key="regen_full"):
                    del st.session_state.ai_cache[full_key]; st.rerun()
            else:
                st.markdown("AI 會根據真實原文摘錄生成精讀報告，包含：核心論點、重要概念、章節地圖、立即行動。")
                if st.button("✨ 生成完整精讀報告", type="primary", key="gen_full"):
                    # 組合前幾章摘錄
                    chs = content.get("chapters",[])[:6]
                    ch_text = "\n\n".join(
                        f"【{ch['title']}】\n{ch['excerpt'][:600]}"
                        for ch in chs
                    )
                    intro = content.get("intro","")[:800]
                    with st.spinner("AI 深度分析中（約 15 秒）..."):
                        try:
                            import anthropic
                            r = anthropic.Anthropic(api_key=ak).messages.create(
                                model="claude-haiku-4-5-20251001", max_tokens=900,
                                messages=[{"role":"user","content":
                                    f"書名：《{book['title']}》\n"
                                    f"分類：{book.get('category','')}\n"
                                    f"導讀原文：\n{intro}\n\n"
                                    f"各章節原文摘錄：\n{ch_text}\n\n"
                                    f"請用繁體中文生成一份精讀報告，包含：\n\n"
                                    f"## 📖 書籍總覽\n（這本書的核心主張，2-3句）\n\n"
                                    f"## 🧠 五個關鍵概念\n（每個概念附上原文依據和實際意義）\n\n"
                                    f"## 🗺️ 閱讀地圖\n（各章節的邏輯關係，一段話）\n\n"
                                    f"## ⚡ 三個立即行動\n（讀完可以馬上做的事）\n\n"
                                    f"## 💡 最值得記住的一句話\n（從書中提煉）"}])
                            st.session_state.ai_cache[full_key] = r.content[0].text
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)
