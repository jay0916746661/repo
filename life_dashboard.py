#!/usr/bin/env python3
"""
life_dashboard.py — Jim 人生儀錶板（Streamlit）
執行方式：streamlit run life_dashboard.py
"""

import csv
import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
SAVINGS_GOAL = 100_000

st.set_page_config(
    page_title="Jim 人生儀錶板",
    page_icon="🌟",
    layout="wide",
)


# ── 資料讀取 ──────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_csv(filename) -> pd.DataFrame:
    path = os.path.join(DATA, filename)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def safe_last(df: pd.DataFrame, col: str, default=0):
    if df.empty or col not in df.columns:
        return default
    val = df.iloc[-1][col]
    try:
        return float(val) if val == val else default
    except (TypeError, ValueError):
        return default


# ── 頁籤 ──────────────────────────────────────────────────

tab_invest, tab_work, tab_learn, tab_network, tab_goal = st.tabs([
    "💰 投資", "💼 工作業績", "📚 學習成長", "🤝 人脈網絡", "🎯 年度目標"
])


# ── 1. 投資（連結現有系統）─────────────────────────────────

with tab_invest:
    st.header("💰 投資組合")
    portfolio_path = os.path.join(BASE, "portfolio_history.csv")
    if os.path.isfile(portfolio_path) and os.path.getsize(portfolio_path) > 5:
        df_p = pd.read_csv(portfolio_path)
        if not df_p.empty:
            st.metric("總資產（TWD）", f"{df_p.iloc[-1, 1]:,.0f} 元")
            st.line_chart(df_p.set_index(df_p.columns[0])[df_p.columns[1]])
        else:
            st.info("投資組合資料尚無歷史紀錄")
    else:
        st.info("請先執行 `portfolio_report.py` 產生歷史資料")
    st.caption("詳細即時資料請執行 `streamlit run dashboard.py`")


# ── 2. 工作業績 ───────────────────────────────────────────

with tab_work:
    st.header("💼 工作業績")
    df_w = load_csv("work_history.csv")

    if df_w.empty:
        st.warning("尚無工作資料，請先執行 `daily_checkin.py`")
    else:
        last = df_w.iloc[-1]
        actual = float(last.get("sales_actual", 0) or 0)
        target = float(last.get("sales_target", 0) or 0)
        pct = actual / target * 100 if target > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("業績達成率", f"{pct:.1f}%",
                    delta=f"差 {target - actual:,.0f} 元" if pct < 100 else "已達標 ✅")
        col2.metric("新增客戶（最新）", f"{int(last.get('new_clients', 0) or 0)} 位")
        col3.metric("月收入", f"{float(last.get('income', 0) or 0):,.0f} 元")

        st.subheader("業績走勢")
        if "sales_actual" in df_w.columns:
            chart_df = df_w[["date", "sales_actual", "sales_target"]].dropna()
            if not chart_df.empty:
                st.line_chart(chart_df.set_index("date"))

        st.subheader("拜訪次數")
        if "visits" in df_w.columns:
            visits_df = df_w[["date", "visits"]].dropna()
            if not visits_df.empty:
                st.bar_chart(visits_df.set_index("date"))


# ── 3. 學習成長 ───────────────────────────────────────────

with tab_learn:
    st.header("📚 學習成長")
    df_l = load_csv("learning_history.csv")

    if df_l.empty:
        st.warning("尚無學習資料，請先執行 `daily_checkin.py`")
    else:
        last = df_l.iloc[-1]
        streak = int(last.get("streak_days", 0) or 0)
        japanese = int(last.get("japanese_min", 0) or 0)
        guitar = int(last.get("guitar_min", 0) or 0)
        reading = int(last.get("reading_pages", 0) or 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔥 連續學習", f"{streak} 天")
        col2.metric("🇯🇵 日文（今日）", f"{japanese} 分")
        col3.metric("🎸 吉他（今日）", f"{guitar} 分")
        col4.metric("📖 閱讀（今日）", f"{reading} 頁")

        st.subheader("學習時數趨勢（最近 30 天）")
        if "japanese_min" in df_l.columns and "guitar_min" in df_l.columns:
            trend = df_l[["date", "japanese_min", "guitar_min"]].tail(30).dropna()
            if not trend.empty:
                trend.columns = ["日期", "日文（分）", "吉他（分）"]
                st.area_chart(trend.set_index("日期"))

        # 技能佔比
        st.subheader("本週技能分佈")
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_df = df_l[df_l["date"] >= pd.Timestamp(week_start)]
        if not week_df.empty:
            j_sum = int(week_df["japanese_min"].sum())
            g_sum = int(week_df["guitar_min"].sum())
            r_sum = int(week_df["reading_pages"].sum()) * 2  # 頁數換算分鐘（估）
            if j_sum + g_sum + r_sum > 0:
                skill_df = pd.DataFrame({
                    "技能": ["日文", "吉他", "閱讀（估）"],
                    "分鐘": [j_sum, g_sum, r_sum]
                })
                st.bar_chart(skill_df.set_index("技能"))
            else:
                st.info("本週尚無學習紀錄")


# ── 4. 人脈網絡 ───────────────────────────────────────────

with tab_network:
    st.header("🤝 人脈網絡")
    df_c = load_csv("contacts.csv")

    if df_c.empty:
        st.warning("尚無人脈資料，請先執行 `daily_checkin.py` 新增聯絡人")
    else:
        st.metric("聯絡人總數", f"{len(df_c)} 位")

        col1, col2 = st.columns(2)

        # 人脈分類
        with col1:
            st.subheader("人脈類型分佈")
            if "type" in df_c.columns:
                type_count = df_c["type"].value_counts().reset_index()
                type_count.columns = ["類型", "人數"]
                st.bar_chart(type_count.set_index("類型"))

        # 需要聯絡清單
        with col2:
            st.subheader("⚠️ 需要聯絡（>30天未聯絡）")
            today = date.today()
            if "last_contact" in df_c.columns and "importance" in df_c.columns:
                stale_rows = []
                for _, row in df_c.iterrows():
                    try:
                        importance = int(row.get("importance", 0) or 0)
                        if importance < 4:
                            continue
                        last_str = row.get("last_contact", "")
                        if not last_str or str(last_str) == "nan":
                            continue
                        last_date = date.fromisoformat(str(last_str))
                        days_ago = (today - last_date).days
                        if days_ago >= 30:
                            stale_rows.append({
                                "姓名": row["name"],
                                "類型": row.get("type", ""),
                                "重要度": importance,
                                "距今天數": days_ago,
                            })
                    except (ValueError, TypeError):
                        continue
                if stale_rows:
                    stale_df = pd.DataFrame(stale_rows).sort_values("距今天數", ascending=False)
                    st.dataframe(stale_df, use_container_width=True)
                else:
                    st.success("所有重要聯絡人都保持聯繫中！")

        # 完整聯絡人列表
        st.subheader("聯絡人列表")
        st.dataframe(df_c, use_container_width=True)


# ── 5. 年度目標 ───────────────────────────────────────────

with tab_goal:
    st.header("🎯 年度目標總覽")
    df_life = load_csv("life_history.csv")

    # 存錢目標
    st.subheader("💰 存款目標：10 萬元")
    savings = safe_last(df_life, "total_savings")
    savings_pct = min(savings / SAVINGS_GOAL * 100, 100)
    col1, col2, col3 = st.columns(3)
    col1.metric("目前存款", f"{savings:,.0f} 元")
    col2.metric("達成率", f"{savings_pct:.1f}%")
    col3.metric("還差", f"{max(SAVINGS_GOAL - savings, 0):,.0f} 元")
    st.progress(savings_pct / 100)

    st.divider()

    # 心情走勢
    st.subheader("😊 近期心情走勢")
    if not df_life.empty and "mood_score" in df_life.columns:
        mood_df = df_life[["date", "mood_score"]].tail(30).dropna()
        if not mood_df.empty:
            st.line_chart(mood_df.set_index("date"))
        else:
            st.info("尚無心情資料")

    # 各面向近期趨勢
    st.divider()
    st.subheader("📈 各面向達成率趨勢")
    if not df_life.empty:
        cols_to_show = [c for c in ["work_achievement_pct", "learning_min_total"] if c in df_life.columns]
        if cols_to_show:
            trend_df = df_life[["date"] + cols_to_show].tail(30).dropna()
            if not trend_df.empty:
                rename_map = {
                    "work_achievement_pct": "業績達成率(%)",
                    "learning_min_total": "學習時數(分)",
                }
                trend_df = trend_df.rename(columns=rename_map)
                st.line_chart(trend_df.set_index("date"))

    st.caption(f"最後更新：{date.today().isoformat()} | 資料來源：{DATA}")
