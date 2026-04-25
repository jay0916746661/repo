from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
MAGAZINE = BASE / "magazine"
PAGE_DIR = MAGAZINE / "page_images"
LOCAL_FILE = DATA / "local_books.json"
CLOUD_FILE = DATA / "books.json"
CONTENT_DIR = DATA / "book_contents"
OUT_FILE = MAGAZINE / "library_manifest.js"

IMAGE_ONLY_PAGE_LIMIT = 8
IMAGE_SAMPLE_LIMIT = 4
TEXT_FALLBACK_PAGE_LIMIT = 30
TEXT_CHUNK_PAGES = 6
MAX_CHAPTERS = 12


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n").replace("\x00", "")
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

    summary = chunks[0]["text"][:420] if chunks else ""
    chapters = []
    full_reading = []
    for idx, chunk in enumerate(chunks[:MAX_CHAPTERS]):
        title_line = chunk["text"].split("\n")[0].strip()
        title = title_line if title_line and len(title_line) <= 24 and not re.search(r"[。！？]", title_line) else f"第 {idx + 1} 節"
        desc = re.sub(r"\s+", "", chunk["text"])[:260]
        chapters.append({
            "title": title,
            "excerpt": desc or "請進入閱讀查看內容。",
            "page": chunk["page"],
        })
        full_reading.append(chunk["text"])
    return summary, chapters, full_reading


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


def build_local_manifest() -> list[dict]:
    local_books = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
    out: list[dict] = []

    for idx, book in enumerate(local_books):
        item = {
            "id": book["id"],
            "title": book.get("title", ""),
            "author": book.get("author", ""),
            "category": book.get("category", "其他"),
            "status": book.get("status", "待讀"),
            "tags": book.get("tags", []),
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

        local_path = Path(book.get("local_path", ""))
        has_text = bool(item["intro"].strip() or item["chapters"])

        if local_path.exists() and local_path.suffix.lower() == ".pdf":
            doc = fitz.open(local_path)
            try:
                if not has_text:
                    page_texts = []
                    for page_index in range(min(TEXT_FALLBACK_PAGE_LIMIT, doc.page_count)):
                        txt = clean_text(doc.load_page(page_index).get_text("text"))
                        if txt:
                            page_texts.append(txt)
                    summary, chapters, full_reading = chunk_pages(page_texts)
                    if summary:
                        item["intro"] = summary
                    if chapters:
                        item["chapters"] = chapters
                    if full_reading:
                        item["fullReading"] = full_reading
                    has_text = bool(summary or chapters)

                needs_images = (
                    not has_text
                    or any("image" in (toc.get("title", "").lower()) for toc in (content.get("toc", []) if content_file.exists() else []))
                )
                if needs_images:
                    item["pageImages"] = render_page_images(book["id"], local_path)
                    if not item["chapters"]:
                        item["chapters"] = [{
                            "title": "圖像頁選",
                            "excerpt": "此書以圖像頁為主，可直接在閱讀頁查看書內頁面。",
                            "page": 1,
                        }]
                        item["fullReading"] = ["此書以圖像頁為主，請向下查看書內圖片。"]
                elif not item["pageImages"]:
                    image_pages = [page_number for page_number in range(min(12, doc.page_count)) if doc.load_page(page_number).get_images(full=True)]
                    if image_pages:
                        item["pageImages"] = render_page_images(book["id"], local_path, limit=IMAGE_SAMPLE_LIMIT, page_numbers=image_pages)
            finally:
                doc.close()

        out.append(item)

    return out


def build_cloud_manifest(start_index: int) -> list[dict]:
    cloud_books = json.loads(CLOUD_FILE.read_text(encoding="utf-8"))
    out: list[dict] = []
    for idx, book in enumerate(cloud_books, start=start_index):
        title = book.get("title", "")
        out.append({
            "id": f"cloud_{idx:04d}",
            "title": title,
            "author": book.get("author", ""),
            "category": book.get("category", "其他"),
            "status": book.get("status", "待讀"),
            "tags": book.get("tags", []),
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
    local_manifest = build_local_manifest()
    cloud_manifest = build_cloud_manifest(len(local_manifest))
    all_books = local_manifest + cloud_manifest
    OUT_FILE.write_text(
        "window.LIBRARY_MANIFEST = " + json.dumps(all_books, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_FILE} with {len(all_books)} books")


if __name__ == "__main__":
    main()
