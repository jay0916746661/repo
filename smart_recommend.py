"""
每日內容推薦 → Telegram 推播
根據 Google Drive 書單 + YouTube 訂閱頻道分析偏好，用 Gemini 生成推薦
"""
import json, random, requests
from pathlib import Path
from datetime import date
from collections import Counter
from google import genai

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text())
BOOKS_FILE = BASE / "data" / "books.json"
YT_SUBS_FILE = BASE / "data" / "youtube_subs.json"

GEMINI_KEY = CONFIG["gemini_api_key"]
BOT_TOKEN  = CONFIG["telegram_bot_token"]
CHAT_ID    = CONFIG["telegram_chat_id"]
TG_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

client = genai.Client(api_key=GEMINI_KEY)

# 頻道名稱關鍵字分類（以 AI、投資、音樂為主）
YT_CATEGORY_KEYWORDS = {
    "AI/科技":   ["ai", "gpt", "llm", "tech", "程式", "科技", "coding", "python", "developer", "machine learning", "元域", "人工智慧"],
    "投資/財富": ["財富", "投資", "股票", "美股", "幣圈", "crypto", "finance", "money", "trading", "理財", "財經", "基金", "期貨"],
    "音樂":      ["music", "piano", "guitar", "鋼琴", "吉他", "band", "jazz", "beats", "song", "音樂", "dance", "vocal", "mixing", "producer"],
    "知識/成長": ["成長", "習慣", "效率", "mindset", "productivity", "motivation", "學習", "知識", "教育", "science", "psychology", "哲學"],
    "商業/創業": ["創業", "business", "entrepreneur", "行銷", "marketing", "startup", "策略"],
    "生活/其他": ["vlog", "生活", "旅遊", "travel", "lifestyle", "日常", "cooking", "fitness"],
}


def load_books() -> list[dict]:
    if not BOOKS_FILE.exists():
        return []
    return json.loads(BOOKS_FILE.read_text())


def load_yt_subs() -> list[dict]:
    if not YT_SUBS_FILE.exists():
        return []
    return json.loads(YT_SUBS_FILE.read_text())


def classify_yt_channel(name: str) -> str:
    n = name.lower()
    for cat, kws in YT_CATEGORY_KEYWORDS.items():
        if any(k.lower() in n for k in kws):
            return cat
    return "其他"


def build_profile(books: list[dict], yt_subs: list[dict]) -> str:
    book_cats = Counter(b["category"] for b in books)
    shelves   = Counter(b["shelf"] for b in books)
    sample_books = [b["title"] for b in random.sample(books, min(15, len(books)))]

    yt_cats = Counter(classify_yt_channel(s["channel"]) for s in yt_subs)
    sample_yt = random.sample(yt_subs, min(20, len(yt_subs)))
    sample_yt_names = [s["channel"] for s in sample_yt]

    lines = [
        "=== 電子書偏好 ===",
        f"書單總數：{len(books)} 本（待看 {shelves.get('待看電子書',0)} 本）",
        f"書單分類：{dict(book_cats)}",
        f"書名範例：{', '.join(sample_books[:12])}",
        "",
        "=== YouTube 訂閱偏好 ===",
        f"訂閱頻道：{len(yt_subs)} 個",
        f"頻道分類：{dict(yt_cats)}",
        f"頻道範例：{', '.join(sample_yt_names[:15])}",
    ]
    return "\n".join(lines)


def generate_recommendation(profile: str) -> str:
    today = date.today().strftime("%Y/%m/%d")
    prompt = f"""
你是一個精準的個人內容推薦助理。根據使用者的書單與YouTube訂閱，推薦最適合他的今日內容。

【使用者偏好】
{profile}

【今天是】{today}

用繁體中文，嚴格按以下格式輸出（不要多餘文字）：

📚 今日推薦 {today}
━━━━━━━━━━━━━━━━━━

📖 今日好書
書名：（推薦一本書，可以是書單中的書，也可以是同類型好書）
原因：（具體說明為什麼適合這個人，2句話）

📺 今日頻道
頻道：（推薦一個YouTube頻道，可以是已訂閱的或同類型新頻道）
原因：（為什麼值得看，1句話）

🔍 延伸主題：（今天可以深入探索的關鍵字，3個）
"""
    for model in ["gemini-2.0-flash", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]:
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            return resp.text.strip()
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "503", "404", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "NOT_FOUND"]):
                print(f"  ⚠️ {model} 不可用，換下一個...")
                continue
            raise
    return None  # 全部失敗


def send_telegram(text: str) -> bool:
    r = requests.post(TG_URL, data={
        "chat_id": CHAT_ID,
        "text": text,
    })
    return r.json().get("ok", False)


def run():
    print("📚 讀取書單...")
    books = load_books()
    if not books:
        print("⚠️ books.json 為空，先執行 python sync_books.py")
        return

    print("📺 讀取 YouTube 訂閱...")
    yt_subs = load_yt_subs()

    print(f"✅ 書單 {len(books)} 本，YouTube 頻道 {len(yt_subs)} 個")
    profile = build_profile(books, yt_subs)

    print("\n🤖 生成推薦中...")
    recommendation = generate_recommendation(profile)
    print("\n" + recommendation)

    print("\n📨 推播到 Telegram...")
    if recommendation is None:
        send_telegram("⚠️ 今日 AI 配額已用完，明天早上 8:30 自動重試。")
        print("⚠️ 配額用完，已送通知")
    else:
        ok = send_telegram(recommendation)
        print("✅ 發送成功！" if ok else "❌ 發送失敗")
        rec_file = BASE / "data" / "today_recommend.json"
        with open(rec_file, "w", encoding="utf-8") as _f:
            json.dump({"date": date.today().isoformat(), "content": recommendation}, _f, ensure_ascii=False)
        print(f"💾 已同步到 {rec_file}")


if __name__ == "__main__":
    run()
