import json
import re
from pathlib import Path

import fitz


BASE = Path("/Users/jimlin/Downloads/claude")
LOCAL_FILE = BASE / "data" / "local_books.json"
CONTENT_DIR = BASE / "data" / "book_contents"
OUT_JS = BASE / "magazine" / "full_reading.js"

MAX_CHARS = 5000
MAX_PAGES_PER_CHAPTER = 6


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"(\d+\s*){5,}", "", text)
    return text


def load_local_books() -> list[dict]:
    return json.loads(LOCAL_FILE.read_text(encoding="utf-8"))


def load_book_content(book_id: str) -> dict | None:
    p = CONTENT_DIR / f"{book_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def extract_full_chapters(pdf_path: str, chapters: list[dict], total_pages: int) -> list[str]:
    doc = fitz.open(pdf_path)
    results = []
    for idx, ch in enumerate(chapters):
        start_page = max(0, int(ch.get("page", 1)) - 1)
        if idx + 1 < len(chapters):
            next_page = max(start_page + 1, int(chapters[idx + 1].get("page", total_pages)) - 1)
        else:
            next_page = total_pages
        end_page = min(next_page, start_page + MAX_PAGES_PER_CHAPTER)
        text = []
        for pno in range(start_page, min(end_page, total_pages)):
            try:
                text.append(doc[pno].get_text())
            except Exception:
                continue
        merged = clean_text(" ".join(text))[:MAX_CHARS]
        results.append(merged or ch.get("excerpt", ""))
    doc.close()
    return results


def main():
    books = load_local_books()
    output = {}
    done = 0
    for book in books:
        pdf_path = book.get("local_path")
        if not pdf_path or not Path(pdf_path).exists():
            continue
        content = load_book_content(book["id"])
        if not content:
            continue
        chapters = content.get("chapters", [])
        total_pages = int(content.get("total_pages", 0) or 0)
        if not chapters or total_pages <= 0:
            continue
        try:
            output[book["id"]] = extract_full_chapters(pdf_path, chapters, total_pages)
            done += 1
        except Exception as e:
            print(f"skip {book['title'][:30]}: {e}")
            continue

    OUT_JS.write_text(
        "window.FULL_READING = " + json.dumps(output, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_JS} for {done} books")


if __name__ == "__main__":
    main()
