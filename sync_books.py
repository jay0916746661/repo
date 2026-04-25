"""
從 Google Drive 公開資料夾同步電子書書單到 data/books.json
使用 gdown，不需要 OAuth 憑證
"""
import json, re
from pathlib import Path
import gdown

BASE = Path(__file__).parent
BOOKS_FILE = BASE / "data" / "books.json"

FOLDERS = {
    "1M5rpvl_NhAMxyHI0ctESFTVk1PCgI-SP": "電子書",
    "1dkXy8stPOmvIFpv1kqY6AXcwtFvRDQ0w": "待看電子書",
}

CATEGORY_KEYWORDS = {
    "投資/財富":  ["投資","財富","錢","理財","股票","經濟","致富","資產","money","金錢","退休","財務"],
    "AI/科技":    ["AI","人工智慧","GPT","奧爾特曼","altman","科技","程式","大腦","第二大腦"],
    "人性/心理":  ["人性","心理","洞察","博弈","消費","認知","思考","自卑","mindfuck"],
    "生活/心智":  ["生活","冥想","專注","習慣","成長","覺悟","多巴胺","軟技能","破圈","槓桿","減法"],
    "溝通/談判":  ["談判","溝通","關係","說話","影響","能見","表達"],
    "商業/創業":  ["商業","發售","變現","社群","行銷","創業","robbins"],
    "其他":       [],
}

def guess_category(title: str) -> str:
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if cat == "其他":
            continue
        if any(k.lower() in t for k in kws):
            return cat
    return "其他"

def clean_title(raw: str) -> str:
    name = Path(raw).stem
    name = re.sub(r'\s*[=＝]\s*.*', '', name)
    name = re.sub(r'\s*\(.*?\)', '', name)
    name = re.sub(r'\s*(Z-Library|Z_Library).*', '', name, flags=re.IGNORECASE)
    return name.strip()

def sync():
    books = []
    for folder_id, shelf in FOLDERS.items():
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        print(f"📂 讀取 {shelf}...")
        try:
            files = gdown.download_folder(url, quiet=True, use_cookies=False, skip_download=True)
        except Exception as e:
            print(f"  ⚠️ 失敗: {e}")
            continue

        if not files:
            print(f"  （空資料夾）")
            continue

        seen = set()
        for f in files:
            raw_name = Path(f.path).name if hasattr(f, 'path') else str(f)
            title = clean_title(raw_name)
            if not title or title in seen:
                continue
            seen.add(title)
            books.append({
                "title": title,
                "shelf": shelf,
                "category": guess_category(title),
            })
        print(f"  ✅ {len(seen)} 本")

    BOOKS_FILE.parent.mkdir(exist_ok=True)
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"\n共 {len(books)} 本書已存到 {BOOKS_FILE}")
    return books

if __name__ == "__main__":
    sync()
