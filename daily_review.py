#!/usr/bin/env python3
"""
daily_review.py — 24 小時人生重啟系統每日表單
五階段：前夜清障 → 主動開局 → 深度執行 → 中段重置 → 晚間復盤
"""

import csv
import os
import subprocess
from datetime import date, datetime

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CSV_PATH = os.path.join(DATA, "review_history.csv")

os.makedirs(DATA, exist_ok=True)

st.set_page_config(page_title="人生重啟系統", page_icon="🔄", layout="wide")
st.title("🔄 24 小時人生重啟系統")


def append_csv(path, row: dict):
    file_exists = os.path.isfile(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def notify(message):
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "人生重啟系統"'],
            check=False,
        )
    except Exception:
        pass


def load_history() -> pd.DataFrame:
    if not os.path.isfile(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    return df.sort_values("date", ascending=False)


tab_form, tab_history = st.tabs(["📝 填寫今日表單", "📊 歷史紀錄"])

# ── 填寫表單 ─────────────────────────────────────────────────────────────────

with tab_form:
    today = date.today()
    entry_date = st.date_input("填寫日期", value=today)

    # ── Phase 1：前夜清障 ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🌙 第一階段：前夜清障")
    st.caption("決定明天勝負的關鍵在於前一天晚上的準備，減少隔天的「決策耗損」。")

    col1, col2 = st.columns([2, 1])
    with col1:
        phase1_task = st.text_input(
            "明天第一任務",
            placeholder="明天 [時間]，我要完成 [任務] 的第一步",
        )
        phase1_rule = st.text_input(
            "啟動規則",
            placeholder="如果明天想拖延，就先做 5 分鐘",
        )
        phase1_motivation = st.text_input(
            "啟動動力",
            placeholder="明天只做一件事：把系統跑起來",
        )
    with col2:
        st.write("")
        phase1_env = st.checkbox("已清空桌面 / 備妥環境")
        phase1_block = st.checkbox("已封鎖誘惑入口（手機遠離床邊、卸載短影音）")

    # ── Phase 2：主動開局 ────────────────────────────────────────────────────
    st.divider()
    st.subheader("☀️ 第二階段：主動開局（起床後前 60 分鐘）")
    st.caption("這段時間決定了你一天的「預設模式」，避免被動接收資訊。")

    mit = st.text_input(
        "MIT — 今天最重要的一件事（只能設定一個）",
        placeholder="完成一個可見交付，贏得今天的閉環",
    )

    col1, col2 = st.columns(2)
    with col1:
        phase2_bed = st.checkbox("5 分鐘內下床")
        phase2_light = st.checkbox("已接觸自然光 + 喝水")
    with col2:
        phase2_exercise = st.checkbox("完成低強度運動（伸展 / 深蹲 5 分鐘）")
        phase2_no_social = st.checkbox("起床後未刷訊息（保持主動產出模式）")

    # ── Phase 3：深度執行 ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🎯 第三階段：深度執行（90–120 分鐘）")
    st.caption("先產出再修正；做出來是起點，做得好是終點。")

    col1, col2 = st.columns([1, 2])
    with col1:
        phase3_pomodoros = st.number_input(
            "番茄鐘完成輪數（25–45 min / 輪）", min_value=0, max_value=10, value=0, step=1
        )
    with col2:
        phase3_deliverable = st.text_area(
            "本日交付成果（可見的輸出是什麼？）",
            placeholder="例如：完成簡報第 1–3 頁草稿、寫完報告開頭 500 字…",
            height=80,
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        phase3_output_first = st.checkbox("先產出再修正")
    with col2:
        phase3_delivery_std = st.checkbox("每輪前寫下交付標準")
    with col3:
        phase3_downgrade = st.checkbox("卡住時使用降級動作（降難度繼續做）")

    # ── Phase 4：中段重置 ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔁 第四階段：中段重置與下午推進")
    st.caption("輕運動、簡短進食、寫下復位卡，然後繼續推進早上的任務。")

    col1, col2 = st.columns([1, 2])
    with col1:
        phase4_reset = st.checkbox("已完成中段重置（30–60 分鐘）")
        phase4_continue = st.checkbox("下午繼續推進同一任務（避免隱形損耗）")
    with col2:
        phase4_reset_note = st.text_area(
            "復位卡（上午總結 + 下午開始時間）",
            placeholder="上午完成了…\n下午 [時間] 繼續…",
            height=80,
        )

    # ── Phase 5：晚間復盤 ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🌜 第五階段：晚間復盤（15 分鐘）")
    st.caption("把復盤視為「系統升級」，而非自責大會。")

    col1, col2 = st.columns(2)
    with col1:
        phase5_q1 = st.text_input("1. 今天最有效的動作是什麼？")
        phase5_q2 = st.text_input("2. 最大的阻力是什麼？")
        phase5_q3 = st.text_input("3. 阻力出現是因為我做了什麼？")
    with col2:
        phase5_q4 = st.text_input("4. 明天要保留哪個動作？")
        phase5_q5 = st.text_input("5. 明天要刪除哪個動作？")

    phase5_score = st.slider("今日整體評分", min_value=1, max_value=10, value=7)
    st.caption(f"{'⭐' * phase5_score}  {phase5_score} / 10")

    # ── 提交 ─────────────────────────────────────────────────────────────────
    st.divider()
    col_submit, col_msg = st.columns([1, 3])
    with col_submit:
        submitted = st.button("✅ 儲存今日紀錄", use_container_width=True, type="primary")

    if submitted:
        row = {
            "date": entry_date.isoformat(),
            "mit": mit,
            "phase1_task": phase1_task,
            "phase1_env": phase1_env,
            "phase1_block": phase1_block,
            "phase1_rule": phase1_rule,
            "phase1_motivation": phase1_motivation,
            "phase2_bed": phase2_bed,
            "phase2_light": phase2_light,
            "phase2_exercise": phase2_exercise,
            "phase2_no_social": phase2_no_social,
            "phase3_pomodoros": phase3_pomodoros,
            "phase3_output_first": phase3_output_first,
            "phase3_delivery_std": phase3_delivery_std,
            "phase3_downgrade": phase3_downgrade,
            "phase3_deliverable": phase3_deliverable,
            "phase4_reset": phase4_reset,
            "phase4_continue": phase4_continue,
            "phase4_reset_note": phase4_reset_note,
            "phase5_q1": phase5_q1,
            "phase5_q2": phase5_q2,
            "phase5_q3": phase5_q3,
            "phase5_q4": phase5_q4,
            "phase5_q5": phase5_q5,
            "phase5_score": phase5_score,
        }
        append_csv(CSV_PATH, row)
        notify(f"今日復盤完成！評分 {phase5_score}/10，MIT：{mit or '未填'}")
        with col_msg:
            st.success(f"已儲存 {entry_date} 的紀錄！評分 {phase5_score}/10")
        st.balloons()

# ── 歷史紀錄 ─────────────────────────────────────────────────────────────────

with tab_history:
    df = load_history()

    if df.empty:
        st.info("尚無歷史紀錄，填寫第一份表單後就會出現在這裡。")
    else:
        st.subheader("📈 每日評分趨勢")
        chart_df = df.set_index("date")[["phase5_score"]].sort_index()
        st.line_chart(chart_df, y="phase5_score")

        st.subheader("🍅 番茄鐘完成數趨勢")
        pomo_df = df.set_index("date")[["phase3_pomodoros"]].sort_index()
        st.bar_chart(pomo_df, y="phase3_pomodoros")

        st.divider()
        st.subheader("📋 完整紀錄")

        bool_cols = [
            "phase1_env", "phase1_block",
            "phase2_bed", "phase2_light", "phase2_exercise", "phase2_no_social",
            "phase3_output_first", "phase3_delivery_std", "phase3_downgrade",
            "phase4_reset", "phase4_continue",
        ]
        display_df = df.copy()
        for col in bool_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].map(
                    lambda v: "✅" if str(v).lower() in ("true", "1", "yes") else "❌"
                )

        st.dataframe(display_df, use_container_width=True)

        latest = df.iloc[0]
        st.divider()
        st.subheader(f"🗒️ 最近一筆紀錄（{latest['date'].date() if hasattr(latest['date'], 'date') else latest['date']}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("今日評分", f"{int(latest.get('phase5_score', 0))} / 10")
        col2.metric("番茄鐘輪數", int(latest.get("phase3_pomodoros", 0)))
        col3.metric("MIT", latest.get("mit", "—") or "—")

        with st.expander("晚間復盤五問"):
            for i, q in enumerate([
                "今天最有效的動作是什麼？",
                "最大的阻力是什麼？",
                "阻力出現是因為我做了什麼？",
                "明天要保留哪個動作？",
                "明天要刪除哪個動作？",
            ], 1):
                ans = latest.get(f"phase5_q{i}", "") or "（未填）"
                st.markdown(f"**{i}. {q}**  \n{ans}")
