#!/usr/bin/env python3
"""
generate_youtube_feed.py
從 data/youtube_subs.json 篩選精華頻道，抓取 RSS 最新影片，
輸出 magazine/youtube_feed.js
"""

import json
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request
import urllib.error

BASE_DIR = Path(__file__).parent
SUBS_FILE = BASE_DIR / "data" / "youtube_subs.json"
OUTPUT_FILE = BASE_DIR / "magazine" / "youtube_feed.js"

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
THUMB_URL = "https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# 每類上限頻道數
CAT_QUOTA = 12
# 硬白名單（channel name 完全匹配，優先納入）
WHITELIST = {
    "3Blue1Brown": "knowledge",
    "Acquired": "biz",
    "Andrew Huberman": "knowledge",
    "Veritasium": "knowledge",
    "Kurzgesagt – In a Nutshell": "knowledge",
    "Y Combinator": "biz",
    "NiceKate AI": "tech",
    "3%財富覺醒": "finance",
    "NaNa說美股": "finance",
}

# 分類關鍵字（比對 channel name + description，小寫）
CATEGORY_KEYWORDS = {
    "tech": [
        "ai", "artificial intelligence", "gpt", "llm", "python", "coding", "程式",
        "software", "open source", "machine learning", "deep learning", "晶片",
        "科技", "developer", "tech", "engineering", "github", "claude", "openai",
        "automation", "automation", "自動化", "資訊", "電腦", "hardware",
    ],
    "finance": [
        "投資", "股票", "財富", "crypto", "bitcoin", "finance", "經濟", "基金",
        "trading", "市場", "etf", "wealth", "money", "dividend", "資產", "理財",
        "巴菲特", "warren buffett", "value investing", "portfolio", "美股",
        "加密貨幣", "blockchain", "forex", "匯率",
    ],
    "music": [
        "piano", "guitar", "吉他", "鋼琴", "jazz", "vocal", "drum", "bass",
        "樂器", "music", "band", "musician", "singer", "歌手", "concert",
        "音樂", "recording", "mixing", "producer", "beat", "chord", "ukulele",
        "violin", "小提琴", "keyboard",
    ],
    "knowledge": [
        "science", "math", "physics", "biology", "chemistry", "astronomy",
        "history", "philosophy", "3blue", "veritasium", "kurzgesagt",
        "huberman", "education", "learn", "university", "professor", "ted",
        "documentary", "紀錄片", "知識", "學習",
    ],
    "biz": [
        "startup", "創業", "business", "entrepreneurship", "ycombinator",
        "商業", "行銷", "marketing", "sales", "venture", "investor",
        "product", "brand", "agency", "consultant", "ceo", "founder",
    ],
    "fun": [
        "vlog", "lifestyle", "travel", "旅遊", "生活", "dance", "comedy",
        "entertainment", "gaming", "food", "cooking", "photography",
        "攝影", "影片", "短片",
    ],
}


def classify_channel(name: str, description: str) -> str | None:
    text = f"{name} {description}".lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += (3 if kw in name.lower() else 1)
    best_cat = max(scores, key=lambda c: scores[c])
    return best_cat if scores[best_cat] > 0 else None


def score_channel(ch: dict) -> int:
    name = ch.get("channel", "")
    desc = ch.get("description", "")
    if name in WHITELIST:
        return 100
    score = 0
    text = f"{name} {desc}".lower()
    for keywords in CATEGORY_KEYWORDS.values():
        for kw in keywords:
            if kw in text:
                score += (3 if kw in name.lower() else 1)
    if len(desc) > 200:
        score += 2
    elif len(desc) > 50:
        score += 1
    return score


def select_channels(all_subs: list) -> list:
    """從所有訂閱中篩選精華頻道，每類最多 CAT_QUOTA 個"""
    # 先處理白名單
    whitelist_channels = []
    remaining = []
    for ch in all_subs:
        name = ch.get("channel", "")
        if name in WHITELIST:
            cat = WHITELIST[name]
            whitelist_channels.append({**ch, "category": cat, "score": 100})
        else:
            remaining.append(ch)

    # 對其餘頻道評分並分類
    scored = []
    for ch in remaining:
        name = ch.get("channel", "")
        desc = ch.get("description", "")
        cat = classify_channel(name, desc)
        if cat is None:
            continue
        s = score_channel(ch)
        if s > 0:
            scored.append({**ch, "category": cat, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)

    # 每類配額
    cat_counts = {cat: 0 for cat in CATEGORY_KEYWORDS}
    selected = list(whitelist_channels)
    for wl in whitelist_channels:
        cat = wl["category"]
        if cat in cat_counts:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    for ch in scored:
        cat = ch["category"]
        if cat_counts.get(cat, 0) < CAT_QUOTA:
            selected.append(ch)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print(f"精華頻道：{len(selected)} 個")
    for cat in CATEGORY_KEYWORDS:
        count = sum(1 for c in selected if c.get("category") == cat)
        print(f"  {cat}: {count}")

    return selected


def fetch_rss(channel: dict) -> list:
    """抓取單一頻道的 RSS，回傳影片列表"""
    channel_id = channel.get("channel_id", "")
    channel_name = channel.get("channel", "")
    cat = channel.get("category", "fun")

    url = RSS_URL.format(channel_id=channel_id)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        root = ET.fromstring(data)

        videos = []
        entries = root.findall("atom:entry", NS)
        for entry in entries[:5]:
            vid_id_el = entry.find("yt:videoId", NS)
            title_el = entry.find("atom:title", NS)
            pub_el = entry.find("atom:published", NS)
            desc_el = entry.find(".//media:description", NS)

            if vid_id_el is None or title_el is None:
                continue

            vid_id = vid_id_el.text or ""
            title = title_el.text or ""
            published = (pub_el.text or "") if pub_el is not None else ""
            description = (desc_el.text or "")[:200] if desc_el is not None else ""

            videos.append({
                "video_id": vid_id,
                "title": title,
                "channel_id": channel_id,
                "channel_name": channel_name,
                "published": published,
                "thumbnail": THUMB_URL.format(video_id=vid_id),
                "description": description,
                "category": cat,
                "url": f"https://youtube.com/watch?v={vid_id}",
            })
        return videos

    except Exception:
        return []


def is_recent(published: str, days: int = 30) -> bool:
    if not published:
        return False
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return dt > cutoff
    except Exception:
        return True  # 解析失敗時保留


def main():
    print("讀取訂閱資料…")
    with open(SUBS_FILE, encoding="utf-8") as f:
        all_subs = json.load(f)
    print(f"總訂閱：{len(all_subs)} 個")

    selected = select_channels(all_subs)

    print(f"\n開始抓取 RSS（{len(selected)} 個頻道）…")
    all_videos = []
    failed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_rss, ch): ch for ch in selected}
        done = 0
        for future in as_completed(futures):
            done += 1
            videos = future.result()
            if videos:
                all_videos.extend(videos)
            else:
                failed += 1
            if done % 10 == 0:
                print(f"  進度 {done}/{len(selected)}…")
            time.sleep(0.05)

    print(f"抓取完成，成功頻道：{len(selected) - failed}，失敗：{failed}")
    print(f"影片總數（過濾前）：{len(all_videos)}")

    # 過濾 30 天以上的舊影片
    all_videos = [v for v in all_videos if is_recent(v["published"], days=30)]
    print(f"影片總數（30天內）：{len(all_videos)}")

    # 排序：最新在前
    all_videos.sort(key=lambda v: v["published"], reverse=True)

    # 上限 200 支
    all_videos = all_videos[:200]

    # 組裝頻道清單
    channels_out = [
        {
            "id": ch.get("channel_id", ""),
            "name": ch.get("channel", ""),
            "category": ch.get("category", "fun"),
            "description": ch.get("description", "")[:150],
        }
        for ch in selected
    ]

    feed = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "channels": channels_out,
        "videos": all_videos,
    }

    js_content = "window.YOUTUBE_FEED = " + json.dumps(feed, ensure_ascii=False, indent=2) + ";\n"
    OUTPUT_FILE.write_text(js_content, encoding="utf-8")

    size_kb = OUTPUT_FILE.stat().st_size // 1024
    print(f"\n完成！輸出：{OUTPUT_FILE}（{size_kb} KB，{len(all_videos)} 支影片）")


if __name__ == "__main__":
    main()
