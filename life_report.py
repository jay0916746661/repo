#!/usr/bin/env python3
"""
life_report.py — Jim 每日人生報告
類比 portfolio_report.py，彙整工作/學習/人脈/財務四個面向
輸出 txt 報告並可同步到 Google Drive
"""

import csv
import os
import subprocess
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
REPORTS_DIR = os.path.join(BASE, "reports")
LOG = os.path.join(BASE, "life_report.log")

SAVINGS_GOAL = 100_000  # 10 萬存款目標


# ── 資料讀取 ──────────────────────────────────────────────

def read_csv_last(path) -> dict | None:
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def read_csv_all(path) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val, default=0.0) -> float:
    try:
        return float(val or default)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0) -> int:
    try:
        return int(val or default)
    except (ValueError, TypeError):
        return default


# ── 各模組摘要 ────────────────────────────────────────────

def work_summary() -> dict:
    last = read_csv_last(os.path.join(DATA, "work_history.csv"))
    if not last:
        return {}
    actual = safe_float(last.get("sales_actual"))
    target = safe_float(last.get("sales_target"))
    pct = actual / target * 100 if target > 0 else 0
    return {
        "sales_actual": actual,
        "sales_target": target,
        "achievement_pct": pct,
        "new_clients": safe_int(last.get("new_clients")),
        "visits": safe_int(last.get("visits")),
        "income": safe_float(last.get("income")),
    }


def learning_summary() -> dict:
    rows = read_csv_all(os.path.join(DATA, "learning_history.csv"))
    if not rows:
        return {}
    last = rows[-1]

    # 本週學習時數
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_min = 0
    for row in rows:
        try:
            d = date.fromisoformat(row["date"])
            if d >= week_start:
                week_min += safe_int(row.get("japanese_min")) + safe_int(row.get("guitar_min"))
        except ValueError:
            continue

    return {
        "japanese_min": safe_int(last.get("japanese_min")),
        "guitar_min": safe_int(last.get("guitar_min")),
        "reading_pages": safe_int(last.get("reading_pages")),
        "streak_days": safe_int(last.get("streak_days")),
        "week_min": week_min,
    }


def network_summary() -> dict:
    rows = read_csv_all(os.path.join(DATA, "contacts.csv"))
    if not rows:
        return {"total": 0, "stale_important": []}

    today = date.today()
    stale = []
    by_type: dict[str, int] = {}
    for row in rows:
        ctype = row.get("type", "其他")
        by_type[ctype] = by_type.get(ctype, 0) + 1
        try:
            importance = safe_int(row.get("importance"))
            if importance >= 4:
                last_str = row.get("last_contact", "")
                if last_str:
                    days_ago = (today - date.fromisoformat(last_str)).days
                    if days_ago >= 30:
                        stale.append((row["name"], days_ago))
        except ValueError:
            pass

    return {
        "total": len(rows),
        "by_type": by_type,
        "stale_important": sorted(stale, key=lambda x: -x[1]),
    }


def finance_summary() -> dict:
    last = read_csv_last(os.path.join(DATA, "life_history.csv"))
    if not last:
        return {}
    savings = safe_float(last.get("total_savings"))
    pct = savings / SAVINGS_GOAL * 100
    return {
        "savings": savings,
        "goal": SAVINGS_GOAL,
        "pct": pct,
        "remaining": SAVINGS_GOAL - savings,
    }


def mood_summary() -> dict:
    rows = read_csv_all(os.path.join(DATA, "life_history.csv"))
    if not rows:
        return {}
    last = rows[-1]
    # 最近 7 天平均心情
    today = date.today()
    moods = []
    for row in rows[-7:]:
        m = safe_int(row.get("mood_score"))
        if m > 0:
            moods.append(m)
    avg_mood = sum(moods) / len(moods) if moods else 0
    return {
        "today": safe_int(last.get("mood_score")),
        "week_avg": avg_mood,
    }


# ── 報告產生 ──────────────────────────────────────────────

def build_report(today: date) -> str:
    work = work_summary()
    learn = learning_summary()
    net = network_summary()
    fin = finance_summary()
    mood = mood_summary()

    sep = "─" * 44
    lines = [
        "╔════════════════════════════════════════════╗",
        f"║  Jim 人生日報  ─  {today.isoformat()}             ║",
        "╚════════════════════════════════════════════╝",
        "",
        f"  💼  工作業績",
        sep,
    ]

    if work:
        bar_len = 20
        filled = int(work["achievement_pct"] / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        lines += [
            f"  達成率   [{bar}] {work['achievement_pct']:.1f}%",
            f"  業績     {work['sales_actual']:>10,.0f} / {work['sales_target']:,.0f} 元",
            f"  新客戶   {work['new_clients']} 位    拜訪 {work['visits']} 次",
            f"  月收入   {work['income']:,.0f} 元",
        ]
    else:
        lines.append("  （尚無資料，請執行 daily_checkin.py）")

    lines += ["", f"  📚  學習成長", sep]
    if learn:
        lines += [
            f"  日文     {learn['japanese_min']} 分鐘",
            f"  吉他     {learn['guitar_min']} 分鐘",
            f"  閱讀     {learn['reading_pages']} 頁",
            f"  🔥 連續學習  {learn['streak_days']} 天    本週累計 {learn['week_min']} 分鐘",
        ]
    else:
        lines.append("  （尚無資料）")

    lines += ["", f"  🤝  人脈網絡", sep]
    if net:
        lines.append(f"  聯絡人總數  {net['total']} 位")
        for ctype, cnt in net.get("by_type", {}).items():
            lines.append(f"    • {ctype:<8} {cnt} 位")
        if net["stale_important"]:
            lines.append(f"  ⚠️  需要聯絡（>30天）：")
            for name, days in net["stale_important"][:5]:
                lines.append(f"    → {name}  已 {days} 天")
    else:
        lines.append("  （尚無資料）")

    lines += ["", f"  💰  財務目標", sep]
    if fin:
        bar_len = 20
        filled = int(min(fin["pct"], 100) / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        lines += [
            f"  存款目標 [{bar}] {fin['pct']:.1f}%",
            f"  目前存款  {fin['savings']:>10,.0f} 元",
            f"  目標      {fin['goal']:>10,.0f} 元",
            f"  還差      {fin['remaining']:>10,.0f} 元",
        ]
    else:
        lines.append("  （尚無資料）")

    lines += ["", f"  😊  今日心情", sep]
    if mood:
        emoji = "😊" if mood["today"] >= 7 else "😐" if mood["today"] >= 5 else "😔"
        lines += [
            f"  今日   {mood['today']}/10  {emoji}",
            f"  近7天平均  {mood['week_avg']:.1f}/10",
        ]
    else:
        lines.append("  （尚無資料）")

    lines += ["", "═" * 44, ""]
    return "\n".join(lines)


def notify(title, message):
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            check=False
        )
    except Exception:
        pass


def main():
    today = date.today()
    report = build_report(today)
    print(report)

    # 儲存報告
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"life_report_{today.isoformat()}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📄 報告已儲存：{report_path}")

    # 寫 log
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{today.isoformat()} - report generated\n")

    notify("📊 人生日報", f"報告已產生！執行 life_dashboard.py 查看完整圖表")


if __name__ == "__main__":
    main()
