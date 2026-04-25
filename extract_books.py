"""
從本機 PDF 抽取：目錄 / 導讀 / 章節摘錄
輸出：data/book_contents/{book_id}.json
執行：python extract_books.py
"""
import json, os, re, time
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("請先安裝：pip install pymupdf")
    raise

BASE         = Path(__file__).parent
LOCAL_FILE   = BASE / "data" / "local_books.json"
CONTENT_DIR  = BASE / "data" / "book_contents"
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

MAX_INTRO_CHARS    = 3000   # 導讀取前幾頁字數
MAX_CHAPTER_CHARS  = 1500   # 每章節摘錄字數
MAX_CHAPTERS       = 20     # 最多抽幾章


def clean_text(t: str) -> str:
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'(\d+\s*){5,}', '', t)          # 去掉頁碼連排
    return t


def extract_toc(doc) -> list[dict]:
    raw = doc.get_toc()
    toc = []
    for level, title, page in raw:
        title = clean_text(title)
        if title and len(title) > 1:
            toc.append({"level": level, "title": title, "page": page})
    return toc[:60]


def extract_intro(doc, pages=5) -> str:
    texts = []
    for i in range(min(pages, len(doc))):
        texts.append(doc[i].get_text())
    return clean_text(" ".join(texts))[:MAX_INTRO_CHARS]


def extract_chapters(doc, toc: list) -> list[dict]:
    chapters = []
    if toc:
        # 有目錄 → 按目錄抽頭幾段
        ch_pages = [(c["title"], c["page"]-1) for c in toc if c["level"] <= 2]
        for i, (title, pg) in enumerate(ch_pages[:MAX_CHAPTERS]):
            pg = max(0, min(pg, len(doc)-1))
            # 讀 2 頁
            text = ""
            for p in range(pg, min(pg+2, len(doc))):
                text += doc[p].get_text()
            excerpt = clean_text(text)[:MAX_CHAPTER_CHARS]
            if excerpt:
                chapters.append({"title": title, "page": pg+1, "excerpt": excerpt})
    else:
        # 無目錄 → 每 N 頁取一段
        total = len(doc)
        step  = max(1, total // 10)
        for i, pg in enumerate(range(0, total, step)):
            if i >= MAX_CHAPTERS: break
            text = doc[pg].get_text()
            excerpt = clean_text(text)[:MAX_CHAPTER_CHARS]
            if len(excerpt) > 50:
                chapters.append({"title": f"第 {pg+1} 頁起", "page": pg+1, "excerpt": excerpt})
    return chapters


def process_book(book: dict) -> dict | None:
    local_path = book.get("local_path", "")
    if not local_path or not os.path.exists(local_path):
        return None
    try:
        doc = fitz.open(local_path)
        toc      = extract_toc(doc)
        intro    = extract_intro(doc, pages=6)
        chapters = extract_chapters(doc, toc)
        total    = len(doc)
        doc.close()
        return {
            "id":           book["id"],
            "title":        book["title"],
            "category":     book.get("category", "其他"),
            "total_pages":  total,
            "toc":          toc,
            "intro":        intro,
            "chapters":     chapters,
            "has_toc":      len(toc) > 0,
            "extracted_at": time.strftime("%Y-%m-%d"),
        }
    except Exception as e:
        print(f"  ⚠️  {book['title'][:30]} — {e}")
        return None


def run():
    books = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
    print(f"📚 共 {len(books)} 本本機書籍，開始抽取...\n")
    ok, skip, fail = 0, 0, 0

    for i, book in enumerate(books, 1):
        out_file = CONTENT_DIR / f"{book['id']}.json"
        title_short = book['title'][:35]

        if out_file.exists():
            print(f"  [{i:3d}] ✓ 已存在  {title_short}")
            skip += 1
            continue

        print(f"  [{i:3d}] 抽取中  {title_short}...", end=" ", flush=True)
        result = process_book(book)
        if result:
            out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅  {result['total_pages']} 頁，{len(result['chapters'])} 章節")
            ok += 1
        else:
            print("❌  跳過（找不到或解析失敗）")
            fail += 1

    print(f"\n完成：成功 {ok}，已存在跳過 {skip}，失敗 {fail}")
    print(f"輸出目錄：{CONTENT_DIR}")


if __name__ == "__main__":
    run()
