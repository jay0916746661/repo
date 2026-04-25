import json
import re
from pathlib import Path


BASE = Path("/Users/jimlin/Downloads/claude")
BOOKS_JS = BASE / "magazine" / "books_data.js"
OUT_JS = BASE / "magazine" / "ai_content.js"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？\n]+", text or "")
    return [p.strip() for p in parts if 18 <= len(p.strip()) <= 180]


def clean_excerpt(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def summarize_excerpt(title: str, excerpt: str) -> str:
    excerpt = clean_excerpt(excerpt)
    sents = split_sentences(excerpt)
    points = sents[:3]
    if not points and excerpt:
        points = [excerpt[:140] + ("…" if len(excerpt) > 140 else "")]
    if not points:
        return f"【{title}】這一章目前還沒有足夠的摘錄內容。"

    lines = [f"【{title}】"]
    for i, p in enumerate(points, start=1):
        lines.append(f"{i}. {p}。")

    if len(sents) >= 2:
        lines.append("重點：先抓這章前 2-3 個觀念，再回頭讀原文。")
    return "\n".join(lines)


def load_books() -> list[dict]:
    text = BOOKS_JS.read_text(encoding="utf-8")
    payload = text.split("=", 1)[1].strip().rstrip(";")
    return json.loads(payload)


def build_ai_content(books: list[dict]) -> dict:
    result = {}
    for book in books:
        chapters = book.get("chapters") or []
        result[book["id"]] = [
            summarize_excerpt(ch.get("title", f"第 {idx+1} 章"), ch.get("excerpt", ""))
            for idx, ch in enumerate(chapters)
        ]
    return result


def main():
    books = load_books()
    content = build_ai_content(books)
    js = "window.AI_CONTENT = " + json.dumps(content, ensure_ascii=False, indent=2) + ";\n"
    OUT_JS.write_text(js, encoding="utf-8")
    print(f"Wrote {OUT_JS} for {len(content)} books")


if __name__ == "__main__":
    main()
