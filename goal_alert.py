#!/usr/bin/env python3
"""
goal_alert.py — Jim 人生目標警示系統
類比 price_alert.py，定期檢查各面向是否落後目標
執行方式：
  python goal_alert.py           # 單次檢查
  python goal_alert.py --watch   # 每小時持續監控
"""

import csv
import os
import subprocess
import sys
import time
import logging
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
LOG  = os.path.join(BASE, "goal_alert.log")

logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── 設定 ──────────────────────────────────────────────────

SETTINGS = {
    "savings_goal":       100_000,   # 存錢目標（元）
    "work_target_pct":    80,        # 月底前業績目標達成率 %
    "work_warn_days_left": 7,        # 剩幾天開始警示
    "learning_min_daily": 30,        # 每日最低學習分鐘
    "learning_no_streak": 3,         # 連續幾天未學習才警示
    "network_stale_days": 30,        # 重要聯絡人幾天沒聯絡要提醒
    "network_importance": 4,         # 重要度 >= 幾才追蹤
}


# ── 工具 ──────────────────────────────────────────────────

def notify(title, message):
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            check=False
        )
    except Exception:
        pass


def read_csv_last(path) -> dict | None:
    """讀取 CSV 最後一筆紀錄"""
    if not os.path.isfile(path):
        return None
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def read_csv_all(path) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── 各項檢查 ──────────────────────────────────────────────

def check_savings(alerts: list):
    last = read_csv_last(os.path.join(DATA, "life_history.csv"))
    if not last:
        return
    try:
        savings = float(last.get("total_savings", 0) or 0)
        goal = SETTINGS["savings_goal"]
        pct = savings / goal * 100
        print(f"  💰 存款進度：{savings:,.0f} / {goal:,} 元  ({pct:.1f}%)")
        if pct < 50:
            msg = f"存款 {savings:,.0f} 元，距離 10 萬目標還有 {goal - savings:,.0f} 元"
            alerts.append(("💰 存錢落後", msg))
    except (ValueError, TypeError):
        pass


def check_work(alerts: list):
    last = read_csv_last(os.path.join(DATA, "work_history.csv"))
    if not last:
        return
    try:
        actual = float(last.get("sales_actual", 0) or 0)
        target = float(last.get("sales_target", 0) or 0)
        if target <= 0:
            return
        pct = actual / target * 100

        today = date.today()
        # 計算本月剩餘天數
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        days_left = (next_month - today).days

        print(f"  💼 業績達成率：{pct:.1f}%  （月底剩 {days_left} 天）")
        if days_left <= SETTINGS["work_warn_days_left"] and pct < SETTINGS["work_target_pct"]:
            msg = f"業績達成率 {pct:.0f}%，月底剩 {days_left} 天，衝刺！"
            alerts.append(("⚠️ 業績落後", msg))
    except (ValueError, TypeError):
        pass


def check_learning(alerts: list):
    rows = read_csv_all(os.path.join(DATA, "learning_history.csv"))
    if not rows:
        return

    today = date.today()
    no_study_days = 0
    for row in reversed(rows):
        try:
            d = date.fromisoformat(row["date"])
            total = int(row.get("japanese_min", 0) or 0) + int(row.get("guitar_min", 0) or 0)
            delta = (today - d).days
            if delta == no_study_days and total == 0:
                no_study_days += 1
            elif delta > no_study_days:
                break
            else:
                break
        except (ValueError, KeyError):
            continue

    # 最新 streak
    last = rows[-1]
    streak = int(last.get("streak_days", 0) or 0)
    last_total = int(last.get("japanese_min", 0) or 0) + int(last.get("guitar_min", 0) or 0)
    print(f"  📚 學習連續天數：{streak} 天  （最近紀錄：{last_total} 分鐘）")

    if no_study_days >= SETTINGS["learning_no_streak"]:
        msg = f"已連續 {no_study_days} 天沒有學習紀錄，快去練日文或吉他！"
        alerts.append(("📚 學習中斷", msg))


def check_network(alerts: list):
    rows = read_csv_all(os.path.join(DATA, "contacts.csv"))
    if not rows:
        return

    today = date.today()
    stale = []
    for row in rows:
        try:
            importance = int(row.get("importance", 0) or 0)
            if importance < SETTINGS["network_importance"]:
                continue
            last_str = row.get("last_contact", "")
            if not last_str:
                continue
            last_date = date.fromisoformat(last_str)
            days_ago = (today - last_date).days
            if days_ago >= SETTINGS["network_stale_days"]:
                stale.append((row["name"], days_ago))
        except (ValueError, KeyError):
            continue

    print(f"  🤝 需要聯絡的重要人脈：{len(stale)} 位")
    for name, days in stale[:3]:
        print(f"     ⚠️  {name}  已 {days} 天未聯絡")

    if stale:
        names = "、".join(n for n, _ in stale[:3])
        msg = f"{names} 等 {len(stale)} 位重要聯絡人超過 {SETTINGS['network_stale_days']} 天未聯絡"
        alerts.append(("🤝 人脈警示", msg))


# ── 主流程 ────────────────────────────────────────────────

def run_once():
    today = date.today().isoformat()
    print(f"\n🔔 目標警示檢查  ─  {today}")
    print("-" * 40)

    alerts = []
    check_savings(alerts)
    check_work(alerts)
    check_learning(alerts)
    check_network(alerts)

    print("-" * 40)
    if alerts:
        print(f"\n🚨 共 {len(alerts)} 項警示：")
        for title, msg in alerts:
            print(f"  {title}：{msg}")
            notify(title, msg)
            logging.warning(f"{title}: {msg}")
    else:
        print("✅ 所有目標進度正常！")
        logging.info("All goals on track")

    return alerts


def main():
    watch = "--watch" in sys.argv
    if watch:
        print("👀 持續監控模式（每小時檢查一次）...")
        while True:
            run_once()
            time.sleep(3600)
    else:
        run_once()


if __name__ == "__main__":
    main()
