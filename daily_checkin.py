#!/usr/bin/env python3
"""
daily_checkin.py — Jim 人生儀錶板每日 Check-in
統一輸入工作、學習、人脈、財務資料，自動寫入 CSV
"""

import csv
import os
import subprocess
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


# ── 工具函式 ──────────────────────────────────────────────

def ask(prompt, default=None, cast=float):
    """帶預設值的輸入，支援型別轉換"""
    hint = f"（預設 {default}）" if default is not None else ""
    raw = input(f"{prompt}{hint}: ").strip()
    if not raw and default is not None:
        return default
    try:
        return cast(raw) if raw else default
    except (ValueError, TypeError):
        return default


def notify(title, message):
    """Mac 系統通知"""
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            check=False
        )
    except Exception:
        pass


def append_csv(path, row: dict):
    """append 一筆資料到 CSV（自動建 header）"""
    file_exists = os.path.isfile(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def get_learning_streak(path) -> int:
    """計算連續學習天數"""
    if not os.path.isfile(path):
        return 0
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0

    today = date.today()
    streak = 0
    for row in reversed(rows):
        try:
            d = date.fromisoformat(row["date"])
            total = int(row.get("japanese_min", 0) or 0) + int(row.get("guitar_min", 0) or 0)
            delta = (today - d).days
            if delta == streak and total > 0:
                streak += 1
            elif delta > streak:
                break
        except (ValueError, KeyError):
            continue
    return streak


# ── 各模組輸入 ────────────────────────────────────────────

def checkin_work(today_str):
    print("\n💼 工作")
    sales_actual = ask("  今日累積業績（元）", 0, float)
    sales_target  = ask("  本月目標業績（元）", 0, float)
    new_clients   = ask("  新增客戶數", 0, int)
    visits        = ask("  今日拜訪/通話次數", 0, int)
    income        = ask("  本月預估收入（元）", 0, float)
    notes         = input("  備註（可留空）: ").strip()

    row = dict(
        date=today_str,
        sales_actual=sales_actual,
        sales_target=sales_target,
        new_clients=new_clients,
        visits=visits,
        income=income,
        notes=notes,
    )
    append_csv(os.path.join(DATA, "work_history.csv"), row)

    # 警示：月底 7 天內業績不足 60%
    if sales_target > 0:
        pct = sales_actual / sales_target * 100
        days_left = (date.today().replace(day=1).replace(month=date.today().month % 12 + 1) - date.today()).days
        if days_left <= 7 and pct < 60:
            notify("⚠️ 業績警示", f"月底剩 {days_left} 天，業績僅 {pct:.0f}%！")
            print(f"  ⚠️  月底剩 {days_left} 天，業績僅 {pct:.0f}%，加油！")
    return sales_actual, sales_target


def checkin_learning(today_str):
    print("\n📚 學習")
    japanese_min  = ask("  日文學習（分鐘）", 0, int)
    guitar_min    = ask("  吉他練習（分鐘）", 0, int)
    reading_pages = ask("  閱讀頁數", 0, int)
    notes         = input("  備註（可留空）: ").strip()

    learning_path = os.path.join(DATA, "learning_history.csv")
    streak = get_learning_streak(learning_path)
    total_today = japanese_min + guitar_min
    if total_today > 0:
        streak += 1

    row = dict(
        date=today_str,
        japanese_min=japanese_min,
        guitar_min=guitar_min,
        reading_pages=reading_pages,
        streak_days=streak,
        notes=notes,
    )
    append_csv(learning_path, row)

    if total_today == 0:
        print("  ⚠️  今天沒有學習紀錄，明天繼續加油！")
        notify("📚 學習提醒", "今天還沒學習，記得練日文或吉他喔")
    else:
        print(f"  🔥 連續學習 {streak} 天！")

    return japanese_min + guitar_min


def checkin_network(today_str):
    print("\n🤝 人脈")
    raw = input("  今天聯絡了誰？（逗號分隔，可留空）: ").strip()
    contacts_today = [c.strip() for c in raw.split(",") if c.strip()] if raw else []
    met = ask("  今天見面/通話次數", 0, int)
    new_contact = input("  新增聯絡人（姓名,類型,重要度1-5，可留空）: ").strip()

    # 更新既有聯絡人的 last_contact
    contacts_path = os.path.join(DATA, "contacts.csv")
    if contacts_today and os.path.isfile(contacts_path):
        rows = []
        with open(contacts_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        updated = set()
        for row in rows:
            if row["name"] in contacts_today:
                row["last_contact"] = today_str
                updated.add(row["name"])
        with open(contacts_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        # 聯絡人不在資料庫中 → 提示新增
        not_found = [c for c in contacts_today if c not in updated]
        if not_found:
            print(f"  ℹ️  以下聯絡人不在資料庫中，建議新增：{', '.join(not_found)}")

    # 新增聯絡人
    if new_contact:
        parts = [p.strip() for p in new_contact.split(",")]
        name = parts[0] if len(parts) > 0 else ""
        ctype = parts[1] if len(parts) > 1 else "朋友"
        importance = parts[2] if len(parts) > 2 else "3"
        if name:
            append_csv(contacts_path, dict(
                name=name, type=ctype,
                last_contact=today_str, importance=importance, notes=""
            ))
            print(f"  ✅ 已新增聯絡人：{name}")

    return len(contacts_today)


def checkin_finance(today_str):
    print("\n💰 財務")
    total_savings = ask("  目前總存款（元）", 0, float)
    expense_today = ask("  今日支出（元，可略填 0）", 0, float)
    notes = input("  備註（可留空）: ").strip()
    return total_savings, expense_today


# ── 主流程 ────────────────────────────────────────────────

def main():
    today_str = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("=" * 45)
    print(f"  📋 Jim 人生 Check-in  ─  {now}")
    print("=" * 45)
    print("（直接 Enter 跳過，使用預設值 0）")

    sales_actual, sales_target = checkin_work(today_str)
    learning_min = checkin_learning(today_str)
    contacts_count = checkin_network(today_str)
    total_savings, _ = checkin_finance(today_str)

    print("\n🎯 整體心情")
    mood = ask("  今日心情分數（1-10）", 5, int)
    mood = max(1, min(10, mood))

    # 寫入 life_history.csv
    work_pct = round(sales_actual / sales_target * 100, 1) if sales_target > 0 else 0
    append_csv(os.path.join(DATA, "life_history.csv"), dict(
        date=today_str,
        mood_score=mood,
        total_savings=total_savings,
        work_achievement_pct=work_pct,
        learning_min_total=learning_min,
        network_contacts=contacts_count,
        notes="",
    ))

    # 存錢目標進度
    SAVINGS_GOAL = 100000
    savings_pct = total_savings / SAVINGS_GOAL * 100 if total_savings > 0 else 0

    print("\n" + "=" * 45)
    print("  ✅ Check-in 完成！今日摘要：")
    print(f"  💼 業績達成率   {work_pct:.1f}%")
    print(f"  📚 學習時數     {learning_min} 分鐘")
    print(f"  🤝 今日聯絡人   {contacts_count} 位")
    print(f"  💰 存錢目標     {savings_pct:.1f}% / 10 萬")
    print(f"  😊 心情分數     {mood}/10")
    print("=" * 45)

    notify("✅ Check-in 完成", f"業績{work_pct:.0f}% | 學習{learning_min}分 | 心情{mood}/10")


if __name__ == "__main__":
    main()
