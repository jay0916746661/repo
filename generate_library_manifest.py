from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
MAGAZINE = BASE / "magazine"
PAGE_DIR = MAGAZINE / "page_images"
COVER_DIR = DATA / "covers"
LOCAL_FILE = DATA / "local_books.json"
CLOUD_FILE = DATA / "books.json"
CONTENT_DIR = DATA / "book_contents"
OUT_FILE = MAGAZINE / "library_manifest.js"
SYNC_LIBRARY_FILE = Path("/Users/jimlin/Downloads/claude/book_library.json")

IMAGE_ONLY_PAGE_LIMIT = 8
IMAGE_SAMPLE_LIMIT = 4
TEXT_FALLBACK_PAGE_LIMIT = 30
TEXT_CHUNK_PAGES = 6
MAX_CHAPTERS = 12
EPUB_DOC_LIMIT = 24


def clean_text(text: str) -> str:
    text = str(text or "").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def normalize_paragraphs(text: str) -> list[str]:
    lines = [line.strip() for line in clean_text(text).split("\n") if line.strip()]
    paragraphs: list[str] = []
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf.strip():
            paragraphs.append(buf.strip())
            buf = ""

    for line in lines:
        if re.fullmatch(r"\d{1,3}", line):
            continue
        if re.match(r"^(第[\d一二三四五六七八九十百千]+[章節回部篇]|Chapter\s+\d+)", line, re.I):
            flush()
            paragraphs.append(line)
            continue
        if not buf:
            buf = line
        else:
            joiner = " " if re.search(r"[A-Za-z0-9,.;:!?)]$", buf) and re.match(r"^[A-Za-z0-9(]", line) else ""
            buf += joiner + line
            if re.search(r"[。！？）」』】]$", line) and len(buf) >= 140:
                flush()
    flush()
    return paragraphs


def chunk_pages(page_texts: list[str]) -> tuple[str, list[dict], list[str]]:
    pages = ["\n\n".join(normalize_paragraphs(t)) for t in page_texts if clean_text(t)]
    pages = [p for p in pages if p]
    if not pages:
        return "", [], []

    chunks = []
    for i in range(0, len(pages), TEXT_CHUNK_PAGES):
        text = "\n\n".join(pages[i : i + TEXT_CHUNK_PAGES]).strip()
        if text:
            chunks.append({"page": i + 1, "text": text})

    summary = chunks[0]["text"][:700] if chunks else ""
    chapters = []
    full_reading = []
    for idx, chunk in enumerate(chunks[:MAX_CHAPTERS]):
        title_line = chunk["text"].split("\n")[0].strip()
        title = title_line if title_line and len(title_line) <= 30 and not re.search(r"[。！？]", title_line) else f"第 {idx + 1} 節"
        desc = re.sub(r"\s+", "", chunk["text"])[:260]
        chapters.append({
            "title": title,
            "excerpt": desc or "請進入閱讀查看內容。",
            "page": chunk["page"],
        })
        full_reading.append(chunk["text"])
    return summary, chapters, full_reading


def strip_html(text: str) -> str:
    text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def render_page_images(book_id: str, pdf_path: Path, limit: int = IMAGE_ONLY_PAGE_LIMIT, page_numbers: list[int] | None = None) -> list[str]:
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    urls = []
    doc = fitz.open(pdf_path)
    try:
        sequence = page_numbers or list(range(min(limit, doc.page_count)))
        for page_index in sequence[:limit]:
            out = PAGE_DIR / f"{book_id}_{page_index + 1:03d}.jpg"
            if not out.exists():
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
                pix.save(out)
            urls.append(f"./page_images/{out.name}")
    finally:
        doc.close()
    return urls


def copy_cover(source: str, book_id: str) -> str:
    if not source:
        return ""
    src = Path(source)
    if not src.exists():
        return ""
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ""
    dest = COVER_DIR / f"{book_id}{ext}"
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
    return f"../data/covers/{dest.name}"


def extract_pdf_content(book_id: str, local_path: Path, existing_preview: str = "") -> tuple[str, int, list[dict], list[str], list[str]]:
    page_texts = []
    doc = fitz.open(local_path)
    try:
        page_count = doc.page_count
        for page_index in range(min(TEXT_FALLBACK_PAGE_LIMIT, doc.page_count)):
            txt = clean_text(doc.load_page(page_index).get_text("text"))
            if txt:
                page_texts.append(txt)
        summary, chapters, full_reading = chunk_pages(page_texts)
        image_pages = [page_number for page_number in range(min(12, doc.page_count)) if doc.load_page(page_number).get_images(full=True)]
        page_images = []
        if image_pages:
            page_images = render_page_images(book_id, local_path, limit=IMAGE_SAMPLE_LIMIT, page_numbers=image_pages)
        elif not summary and doc.page_count:
            page_images = render_page_images(book_id, local_path)
        if not summary and existing_preview:
            summary = existing_preview[:700]
        if not chapters:
            chapters = [{"title": "第一節", "excerpt": re.sub(r"\s+", "", (existing_preview or summary))[:260] or "請進入閱讀查看內容。", "page": 1}]
        if not full_reading:
            full_reading = [existing_preview or summary or "此書以圖像頁或掃描頁為主。"]
        return summary, page_count, chapters, full_reading, page_images
    finally:
        doc.close()


def extract_epub_content(local_path: Path, existing_preview: str = "") -> tuple[str, int, list[dict], list[str]]:
    page_texts = []
    with zipfile.ZipFile(local_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".html", ".xhtml", ".htm"))]
        for name in names[:EPUB_DOC_LIMIT]:
            try:
                raw = zf.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            text = strip_html(raw)
            if text:
                page_texts.append(text)
    summary, chapters, full_reading = chunk_pages(page_texts)
    if not summary and existing_preview:
        summary = existing_preview[:700]
    if not chapters:
        chapters = [{"title": "第一節", "excerpt": re.sub(r"\s+", "", (existing_preview or summary))[:260] or "請進入閱讀查看內容。", "page": 1}]
    if not full_reading:
        full_reading = [existing_preview or summary or "請進入閱讀查看內容。"]
    return summary, len(page_texts), chapters, full_reading


def build_from_synced_library() -> list[dict]:
    synced = json.loads(SYNC_LIBRARY_FILE.read_text(encoding="utf-8"))
    out: list[dict] = []
    for book in synced:
        title = book.get("title", "")
        if not title or title == ".DS_Store":
            continue
        local_path = Path(book.get("local_path", ""))
        preview = clean_text(book.get("preview", ""))
        item = {
            "id": book.get("id"),
            "title": title,
            "author": book.get("author", ""),
            "category": book.get("category", "其他"),
            "status": book.get("status", "待讀"),
            "tags": book.get("tags", []),
            "added_date": book.get("added_date", ""),
            "cover": copy_cover(book.get("cover_path", ""), book.get("id", "book")),
            "total_pages": int(book.get("page_count") or 0),
            "intro": preview[:1200],
            "chapters": [],
            "fullReading": [],
            "pageImages": [],
            "userAdded": False,
        }

        if local_path.exists():
            try:
                if local_path.suffix.lower() == ".pdf":
                    summary, page_count, chapters, full_reading, page_images = extract_pdf_content(book.get("id", "book"), local_path, preview)
                    item["intro"] = (summary or item["intro"])[:1200]
                    item["total_pages"] = page_count or item["total_pages"]
                    item["chapters"] = chapters
                    item["fullReading"] = full_reading
                    item["pageImages"] = page_images
                elif local_path.suffix.lower() == ".epub":
                    summary, page_count, chapters, full_reading = extract_epub_content(local_path, preview)
                    item["intro"] = (summary or item["intro"])[:1200]
                    item["total_pages"] = page_count or item["total_pages"]
                    item["chapters"] = chapters
                    item["fullReading"] = full_reading
            except Exception:
                pass

        if not item["chapters"] and item["intro"]:
            item["chapters"] = [{
                "title": "第一節",
                "excerpt": re.sub(r"\s+", "", item["intro"])[:260] or "請進入閱讀查看內容。",
                "page": 1,
            }]
        if not item["fullReading"] and item["intro"]:
            item["fullReading"] = [item["intro"]]
        out.append(item)
    return out


def build_from_repo_data() -> list[dict]:
    out: list[dict] = []
    local_books = json.loads(LOCAL_FILE.read_text(encoding="utf-8")) if LOCAL_FILE.exists() else []
    for book in local_books:
        item = {
            "id": book["id"],
            "title": book.get("title", ""),
            "author": book.get("author", ""),
            "category": book.get("category", "其他"),
            "status": book.get("status", "待讀"),
            "tags": book.get("tags", []),
            "added_date": book.get("added_date", ""),
            "cover": f"../data/covers/{book['id']}.jpg",
            "total_pages": 0,
            "intro": "",
            "chapters": [],
            "fullReading": [],
            "pageImages": [],
            "userAdded": False,
        }
        content_file = CONTENT_DIR / f"{book['id']}.json"
        if content_file.exists():
            content = json.loads(content_file.read_text(encoding="utf-8"))
            item["total_pages"] = content.get("total_pages", 0)
            item["intro"] = content.get("intro", "")[:1200]
            item["chapters"] = content.get("chapters", [])
        out.append(item)

    cloud_books = json.loads(CLOUD_FILE.read_text(encoding="utf-8")) if CLOUD_FILE.exists() else []
    for idx, book in enumerate(cloud_books, start=len(out)):
        out.append({
            "id": f"cloud_{idx:04d}",
            "title": book.get("title", ""),
            "author": book.get("author", ""),
            "category": book.get("category", "其他"),
            "status": book.get("status", "待讀"),
            "tags": book.get("tags", []),
            "added_date": book.get("added_date", ""),
            "cover": "",
            "total_pages": book.get("total_pages", 0),
            "intro": book.get("intro", ""),
            "chapters": book.get("chapters", []),
            "fullReading": [],
            "pageImages": [],
            "userAdded": False,
        })
    return out


def main() -> None:
    if SYNC_LIBRARY_FILE.exists():
        all_books = build_from_synced_library()
        source = str(SYNC_LIBRARY_FILE)
    else:
        all_books = build_from_repo_data()
        source = "repo data files"
    OUT_FILE.write_text(
        "window.LIBRARY_MANIFEST = " + json.dumps(all_books, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_FILE} with {len(all_books)} books from {source}")


if __name__ == "__main__":
    main()
