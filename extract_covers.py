"""
掃描本機電子書資料夾，抽取封面圖，更新 data/local_books.json
用法：python extract_covers.py [--folder ~/Desktop/電子書]
"""
import os, re, sys, json, hashlib, zipfile
from pathlib import Path
from datetime import datetime

BASE     = Path(__file__).parent
COVERS   = BASE / "data" / "covers"
OUT_FILE = BASE / "data" / "local_books.json"
DEFAULT_FOLDER = Path.home() / "Desktop" / "電子書"

COVERS.mkdir(parents=True, exist_ok=True)

CATEGORY_KEYWORDS = {
    "投資/財富":  ["投資","財富","錢","理財","股票","經濟","行為","致富","資產","money","金融","基金","巴菲特","財報","持續","帳單"],
    "AI/科技":    ["AI","人工智慧","GPT","奧爾特曼","altman","科技","程式","大腦","第二大腦","deepseek","馬斯克","英偉達","nvidia"],
    "人性/心理":  ["人性","心理","洞察","博弈","行為","消費","認知","思考","自我","意識","神經","成癮","情商"],
    "生活/心智":  ["生活","冥想","專注","習慣","成長","覺悟","多巴胺","軟技能","破圈","番茄","時間","拖延","整理","系統"],
    "關係/情緒":  ["關係","情緒","愛情","伴侶","情書","陷阱","溝通","親密","家庭","社交","人脈"],
    "商業":       ["商業","發售","變現","社群","行銷","創業","談判","影響力","說服","銷售"],
    "攝影":       ["攝影","相機","鏡頭","拍攝","光圈","鏡頭"],
    "塔羅/靈性":  ["塔羅","靈性","占星","冥想","星座","宇宙","靈魂"],
}

SKIP_KEYWORDS = ["移交清單","離職申請","批價表","價格表","presale","sales kit","手冊","文案","_stock","coco guitar","workbook","chord","jazz guitar"]


def short_id(path: str) -> str:
    return hashlib.md5(path.encode()).hexdigest()[:12]


def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r'【.*?】|（.*?）|\(.*?\)|\[.*?\]', '', name)
    name = re.sub(r'文字版|PDF|电子书|雅书|Z-Library|z-lib|1lib|Z_Library|拷貝', '', name, flags=re.I)
    name = re.sub(r'《|》', '', name)
    name = re.sub(r'=.*$', '', name)  # 去掉 "= English Title" 後綴
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.strip('_- ')
    return name or Path(filename).stem


def guess_category(title: str) -> str:
    tl = title.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k.lower() in tl for k in keywords):
            return cat
    return "其他"


def should_skip(filename: str) -> bool:
    tl = filename.lower()
    return any(k.lower() in tl for k in SKIP_KEYWORDS)


def extract_pdf_cover(pdf_path: Path, cover_path: Path) -> bool:
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        if len(doc) == 0:
            return False
        page = doc[0]
        mat  = fitz.Matrix(1.5, 1.5)
        pix  = page.get_pixmap(matrix=mat)
        pix.save(str(cover_path))
        doc.close()
        return True
    except Exception as e:
        return False


def extract_epub_cover(epub_path: Path, cover_path: Path) -> bool:
    try:
        with zipfile.ZipFile(str(epub_path), 'r') as z:
            names = z.namelist()
            # 優先找 cover 命名的圖片
            candidates = [n for n in names if re.search(r'cover', n, re.I)
                          and re.search(r'\.(jpg|jpeg|png|gif|webp)', n, re.I)]
            if not candidates:
                candidates = [n for n in names
                              if re.search(r'\.(jpg|jpeg|png)', n, re.I)]
            if not candidates:
                return False
            candidates.sort(key=lambda x: 0 if 'cover' in x.lower() else 1)
            img_data = z.read(candidates[0])
            cover_path.write_bytes(img_data)
            return True
    except Exception:
        return False


def scan(folder: Path = DEFAULT_FOLDER, verbose: bool = True) -> list:
    if not folder.exists():
        print(f"❌ 找不到資料夾：{folder}")
        return []

    # 載入既有 local_books.json（保留 status 等手動欄位）
    existing = {}
    if OUT_FILE.exists():
        try:
            for b in json.loads(OUT_FILE.read_text(encoding='utf-8')):
                existing[b.get('local_path', '')] = b
        except Exception:
            pass

    books   = []
    added   = 0
    updated = 0

    patterns = list(folder.glob('*.pdf')) + list(folder.glob('*.epub')) + \
               list(folder.glob('*.PDF')) + list(folder.glob('*.EPUB'))

    for fp in sorted(patterns):
        if should_skip(fp.name):
            continue

        local_path = str(fp)
        bid        = short_id(local_path)
        cover_path = COVERS / f"local_{bid}.jpg"
        ext        = fp.suffix.lower()

        title    = clean_title(fp.name)
        category = guess_category(title)

        # 封面抽取
        cover_extracted = cover_path.exists()
        if not cover_extracted:
            if ext == '.pdf':
                cover_extracted = extract_pdf_cover(fp, cover_path)
            elif ext == '.epub':
                cover_extracted = extract_epub_cover(fp, cover_path)

        if local_path in existing:
            b = existing[local_path]
            b['cover_path'] = str(cover_path) if cover_extracted else ''
            books.append(b)
            updated += 1
        else:
            books.append({
                "id":           f"local_{bid}",
                "title":        title,
                "author":       "",
                "category":     category,
                "drive_id":     "",
                "local_path":   local_path,
                "cover_path":   str(cover_path) if cover_extracted else '',
                "status":       "待讀",
                "tags":         [],
                "added_date":   datetime.now().strftime('%Y-%m-%d'),
                "folder":       "本機",
            })
            added += 1
            if verbose:
                print(f"  ➕ {title} [{category}]{'  📷' if cover_extracted else ''}")

    books.sort(key=lambda b: b.get('added_date', ''), reverse=True)
    OUT_FILE.write_text(json.dumps(books, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n✅ 掃描完成：新增 {added} 本，更新 {updated} 本，共 {len(books)} 本")
    print(f"   封面已存到 {COVERS}/")
    return books


if __name__ == '__main__':
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER
    folder = Path(os.path.expanduser(str(folder)))
    print(f"📂 掃描資料夾：{folder}")
    scan(folder)
