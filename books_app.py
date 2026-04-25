"""
Jim's 書庫 — 完整閱讀面板
功能：書架瀏覽 / 目錄 / 導讀 / 章節摘錄 / AI 精讀分析
"""
import streamlit as st
import json, os, hashlib
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
html,body,.stApp{background:#0d0d14;color:#e2e2e6;font-family:'Noto Sans TC',sans-serif;}
.bk-card{background:#16161e;border-radius:10px;overflow:hidden;border:1px solid #22222e;
  margin:5px 0;cursor:pointer;transition:border-color .15s;}
.bk-card:hover{border-color:#3a3a50;}
.bk-card.selected{border-color:#7c3aed;box-shadow:0 0 0 2px #7c3aed44;}
.bk-cover{height:64px;display:flex;align-items:center;justify-content:center;
  font-size:26px;position:relative;}
.bk-body{padding:8px 10px 6px;}
.bk-title{font-size:11px;font-weight:700;color:#e2e2e6;line-height:1.4;min-height:30px;}
.bk-meta{display:flex;justify-content:space-between;align-items:center;margin-top:5px;}
.badge{font-size:9px;padding:2px 6px;border-radius:99px;}
.status-dot{font-size:9px;padding:2px 6px;border-radius:99px;}
.toc-item{padding:7px 10px;border-radius:6px;margin:2px 0;cursor:pointer;
  font-size:13px;border-left:2px solid transparent;transition:all .1s;}
.toc-item:hover{background:#1e1e2a;border-left-color:#7c3aed;}
.toc-item.active{background:#1e1e2a;border-left-color:#7c3aed;color:#a78bfa;}
.excerpt-box{background:#16161e;border-radius:8px;padding:16px 20px;
  border:1px solid #22222e;font-size:13.5px;line-height:1.9;color:#d0d0da;
  white-space:pre-wrap;max-height:480px;overflow-y:auto;}
.intro-box{background:#1a1030;border-radius:8px;padding:16px 20px;
  border:1px solid #4a2080;font-size:13.5px;line-height:1.9;color:#d0d0da;
  white-space:pre-wrap;max-height:360px;overflow-y:auto;}
.ai-box{background:#0a1a10;border-radius:8px;padding:16px 20px;
  border:1px solid #14532d;font-size:13.5px;line-height:1.9;color:#d4edda;}
.section-title{font-size:11px;letter-spacing:.1em;color:#6c6c80;
  text-transform:uppercase;font-family:monospace;margin:14px 0 6px;}
div[data-testid="stVerticalBlock"] > div:has(> iframe){height:auto;}
</style>
""", unsafe_allow_html=True)

# ── 設定 ────────────────────────────────────────────
CAT_C  = {"AI/科技":"#06b6d4","投資/財富":"#22c55e","人性/心理":"#ec4899",
           "商業/創業":"#f59e0b","生活/心智":"#8b5cf6","溝通/談判":"#3b82f6",
           "關係/情緒":"#f472b6","其他":"#64748b"}
CAT_EM = {"AI/科技":"🤖","投資/財富":"💰","人性/心理":"🧠","商業/創業":"🚀",
           "生活/心智":"🌱","溝通/談判":"🤝","關係/情緒":"💞","其他":"📖"}
ST_C   = {"待讀":"#64748b","讀中":"#f59e0b","已讀":"#22c55e"}

BASE          = Path(__file__).parent
LOCAL_FILE    = BASE / "data" / "local_books.json"
CLOUD_FILE    = BASE / "data" / "books.json"
CONTENT_DIR   = BASE / "data" / "book_contents"
CONFIG_FILE   = BASE / "config.json"

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

books = load_all_books()

# ── Session State ────────────────────────────────────
if "sel_book" not in st.session_state: st.session_state.sel_book = None
if "sel_chapter" not in st.session_state: st.session_state.sel_chapter = 0
if "ai_cache" not in st.session_state: st.session_state.ai_cache = {}

# ══════════════════════════════════════════════════════
# 左欄：書架
# ══════════════════════════════════════════════════════
left, right = st.columns([1, 2.6], gap="medium")

with left:
    st.markdown("<h2 style='font-size:20px;font-weight:900;margin-bottom:4px'>📚 書庫</h2>", unsafe_allow_html=True)

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
        short = ttl[:28]+("…" if len(ttl)>28 else "")
        has_c = has_filter(b)
        sel   = st.session_state.sel_book == bid
        icon  = "📄" if has_c else "☁️"

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

    # ── 書名列 ──────────────────────────────────────
    ha, hb, hc = st.columns([4, 1, 1])
    with ha:
        st.markdown(
            f"<h2 style='font-size:20px;font-weight:900;line-height:1.4;margin:0'>"
            f"{em} {book['title']}</h2>", unsafe_allow_html=True)
        meta = []
        if content: meta.append(f"📄 {content['total_pages']} 頁")
        meta.append(f"<span style='background:{cc}22;color:{cc};padding:2px 8px;border-radius:99px;font-size:11px'>{book.get('category','')}</span>")
        meta.append(f"<span style='background:{stc}22;color:{stc};padding:2px 8px;border-radius:99px;font-size:11px'>{bst}</span>")
        if book.get("_source") == "local": meta.append("💻 本機")
        else: meta.append("☁️ Drive")
        st.markdown("<div style='margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap'>" + " ".join(meta) + "</div>", unsafe_allow_html=True)
    with hb:
        opts = ["待讀","讀中","已讀"]
        cur  = opts.index(bst) if bst in opts else 0
        nst  = st.selectbox("閱讀狀態", opts, index=cur, key="bk_status")
        if nst != bst:
            book["status"] = nst
            save_local_books(books)
            load_all_books.clear()
            st.rerun()
    with hc:
        if content and content.get("has_toc"):
            st.markdown(f"<div style='text-align:center;font-size:11px;color:#64748b;padding-top:8px'>目錄 {len(content['toc'])} 項</div>", unsafe_allow_html=True)

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

    # ── Tab 2：目錄 & 章節 ────────────────────────────
    with tab2:
        chapters = content.get("chapters", [])
        toc      = content.get("toc", [])

        if not chapters:
            st.info("此書沒有可解析的章節內容")
        else:
            c_left, c_right = st.columns([1, 2])
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
                        f"<div style='font-size:16px;font-weight:700;color:#a78bfa;margin-bottom:8px'>"
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

    # ── Tab 3：原文摘錄 ───────────────────────────────
    with tab3:
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

    # ── Tab 4：AI 精讀 ────────────────────────────────
    with tab4:
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
