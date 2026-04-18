#!/usr/bin/env python3
"""
market_agent.py — 全天候掃描代理
每天早晨自動掃描持倉標的異動，整理成決策簡報發送 Email + LINE
"""

import urllib.request, urllib.parse, json, os, time, smtplib
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ── 監控標的 ──────────────────────────────────────────
WATCH_SYMBOLS = [
    "NKE", "TSLA", "MSFT", "META", "ORCL",
    "SMCI", "HIMS", "OKLO", "IONQ", "JOBY",
]

# ── 觸發閾值 ──────────────────────────────────────────
PRICE_ALERT_PCT = 3.0    # 價格漲跌超過 3% 觸發
VOLUME_RATIO    = 2.0    # 成交量超過 20 日均量 2 倍觸發

# ── 環境變數 ──────────────────────────────────────────
GMAIL_USER  = os.getenv("GMAIL_USER",         "")
GMAIL_PASS  = os.getenv("GMAIL_APP_PASSWORD", "")
TO_EMAIL    = os.getenv("TO_EMAIL",           "jay0916746661@gmail.com")
LINE_TOKEN  = os.getenv("LINE_NOTIFY_TOKEN",  "")


# ════════════════════════════════════════════════════
# 資料抓取
# ════════════════════════════════════════════════════
def http_get(url: str, timeout: int = 10) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 market-agent/1.0"
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_quote(sym: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=30d"
    data    = json.loads(http_get(url))
    result  = data["chart"]["result"][0]
    quotes  = result["indicators"]["quote"][0]
    meta    = result.get("meta", {})
    closes  = [c for c in quotes.get("close",  []) if c]
    volumes = [v for v in quotes.get("volume", []) if v]
    price     = closes[-1]  if closes  else 0.0
    prev      = closes[-2]  if len(closes)  >= 2 else price
    vol_today = volumes[-1] if volumes else 0
    vol_avg   = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else vol_today
    return {
        "price":     round(price, 2),
        "prev":      round(prev,  2),
        "chg_pct":   round((price - prev) / prev * 100, 2) if prev else 0.0,
        "vol_today": vol_today,
        "vol_avg":   vol_avg,
        "vol_ratio": round(vol_today / vol_avg, 2) if vol_avg else 1.0,
        "52w_high":  meta.get("fiftyTwoWeekHigh", 0),
        "52w_low":   meta.get("fiftyTwoWeekLow",  0),
    }


def fetch_news(sym: str, max_items: int = 5) -> list:
    """Google News RSS — 涵蓋 Reuters / CNBC / Bloomberg / MarketWatch"""
    sources = [
        f"https://news.google.com/rss/search?q={sym}+stock&hl=en-US&gl=US&ceid=US:en",
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US",
    ]
    items = []
    for url in sources:
        try:
            root = ET.fromstring(http_get(url, timeout=8))
            for item in root.findall(".//item")[:max_items]:
                title = item.findtext("title", "").strip()
                link  = item.findtext("link",  "").strip()
                pub   = item.findtext("pubDate", "")[:16]
                src   = item.findtext("source", "")
                if title and title not in [i["title"] for i in items]:
                    items.append({"title": title, "link": link, "date": pub, "src": src})
        except:
            pass
        time.sleep(0.2)
    return items[:max_items]


def fetch_sec_filings(sym: str) -> list:
    """SEC EDGAR：Form 4（內部人交易）+ 8-K（重大事件）"""
    start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end   = datetime.now().strftime("%Y-%m-%d")
    results = []
    for form in ["4", "8-K"]:
        try:
            url = (f"https://efts.sec.gov/LATEST/search-index?q=%22{sym}%22"
                   f"&forms={form}&dateRange=custom&startdt={start}&enddt={end}")
            data = json.loads(http_get(url, timeout=10))
            for hit in data.get("hits", {}).get("hits", [])[:3]:
                s = hit.get("_source", {})
                results.append({
                    "form":   form,
                    "date":   s.get("file_date", "")[:10],
                    "entity": (s.get("entity_name")    or "")[:30],
                    "filer":  (s.get("display_names") or [""])[0][:30],
                    "url":    f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={sym}&type={form}&dateb=&owner=include&count=5",
                })
        except:
            pass
        time.sleep(0.3)
    return results


def fetch_financials_summary(sym: str) -> dict:
    """Yahoo Finance 財務摘要：本益比、EPS、市值"""
    try:
        url  = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=defaultKeyStatistics,financialData"
        data = json.loads(http_get(url, timeout=10))
        ks   = data["quoteSummary"]["result"][0].get("defaultKeyStatistics", {})
        fd   = data["quoteSummary"]["result"][0].get("financialData", {})
        def v(d, k): return d.get(k, {}).get("fmt", "—") if isinstance(d.get(k), dict) else "—"
        return {
            "pe":            v(ks, "forwardPE"),
            "eps":           v(ks, "forwardEps"),
            "market_cap":    v(ks, "marketCap"),
            "profit_margin": v(fd, "profitMargins"),
            "revenue_growth":v(fd, "revenueGrowth"),
            "target_price":  v(fd, "targetMeanPrice"),
        }
    except:
        return {}


# ════════════════════════════════════════════════════
# 通知發送
# ════════════════════════════════════════════════════
def send_line(msg: str):
    if not LINE_TOKEN:
        return
    try:
        data = urllib.parse.urlencode({"message": msg}).encode()
        req  = urllib.request.Request(
            "https://notify-api.line.me/api/notify", data=data,
            headers={"Authorization": f"Bearer {LINE_TOKEN}"}
        )
        urllib.request.urlopen(req, timeout=10)
        print("LINE 通知已發送")
    except Exception as e:
        print(f"LINE 發送失敗: {e}")


def send_email(subject: str, html_body: str):
    if not GMAIL_USER or not GMAIL_PASS:
        print("⚠️  GMAIL_USER / GMAIL_APP_PASSWORD 未設定，跳過 Email")
        return
    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = TO_EMAIL
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        print(f"Email 已發送 → {TO_EMAIL}")
    except Exception as e:
        print(f"Email 發送失敗: {e}")


# ════════════════════════════════════════════════════
# Email 模板
# ════════════════════════════════════════════════════
def build_email(now_str: str, triggers: list, sections: list) -> str:
    trigger_badges = "".join(
        f'<span style="background:#7c3aed;color:#fff;padding:2px 8px;border-radius:4px;margin:2px;font-size:13px">{s}</span>'
        for s in triggers
    )
    return f"""
<html><body style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:700px;
  margin:auto;background:#0f172a;color:#e2e8f0;padding:24px">

<div style="border-bottom:2px solid #7c3aed;padding-bottom:12px;margin-bottom:20px">
  <h1 style="margin:0;color:#22c55e;font-size:22px">
    🔍 全天候掃描代理　<small style="color:#94a3b8;font-size:14px">{now_str}</small>
  </h1>
  <p style="margin:8px 0 0">今日觸發標的：{trigger_badges}</p>
</div>

{''.join(sections)}

<div style="margin-top:32px;border-top:1px solid #334155;padding-top:12px;
  color:#64748b;font-size:11px">
  資料來源：Yahoo Finance · Google News · SEC EDGAR<br>
  此報告由 Jim 全天候掃描代理自動生成，僅供參考，不構成投資建議。
</div>
</body></html>"""


def build_section(sym: str, q: dict, news: list, filings: list, fin: dict) -> str:
    chg_color = "#22c55e" if q["chg_pct"] >= 0 else "#ef4444"
    arrow     = "▲" if q["chg_pct"] >= 0 else "▼"

    alerts_html = ""
    if abs(q["chg_pct"]) >= PRICE_ALERT_PCT:
        alerts_html += f'<span style="background:{chg_color}33;color:{chg_color};padding:3px 8px;border-radius:4px;margin-right:6px">{"📈" if q["chg_pct"]>0 else "📉"} 價格異動 {q["chg_pct"]:+.1f}%</span>'
    if q["vol_ratio"] >= VOLUME_RATIO:
        alerts_html += f'<span style="background:#f59e0b33;color:#f59e0b;padding:3px 8px;border-radius:4px">🔊 爆量 {q["vol_ratio"]:.1f}x 均量</span>'

    news_html = ""
    if news:
        news_html = "<h4 style='color:#94a3b8;margin:12px 0 6px'>📰 最新新聞</h4><ul style='margin:0;padding-left:18px'>"
        for n in news[:4]:
            news_html += f'<li style="margin:4px 0"><a href="{n["link"]}" style="color:#7c3aed">{n["title"]}</a> <small style="color:#64748b">({n["date"][:10]})</small></li>'
        news_html += "</ul>"

    filings_html = ""
    if filings:
        filings_html = "<h4 style='color:#94a3b8;margin:12px 0 6px'>📋 SEC 申報</h4><ul style='margin:0;padding-left:18px'>"
        for f in filings:
            label = "🔴 內部人交易" if f["form"] == "4" else "⚡ 重大事件"
            filings_html += f'<li style="margin:4px 0">{label} [{f["form"]}] {f["date"]} — <a href="{f["url"]}" style="color:#7c3aed">{f["filer"]}</a></li>'
        filings_html += "</ul>"

    fin_html = ""
    if any(fin.values()):
        fin_html = f"""
<div style="background:#1e293b;border-radius:6px;padding:10px;margin-top:10px;font-size:13px">
  📊 財務快覽：本益比 <b>{fin.get('pe','—')}</b> ｜
  EPS <b>{fin.get('eps','—')}</b> ｜
  市值 <b>{fin.get('market_cap','—')}</b> ｜
  毛利率 <b>{fin.get('profit_margin','—')}</b> ｜
  分析師目標 <b style="color:#22c55e">{fin.get('target_price','—')}</b>
</div>"""

    return f"""
<div style="background:#1e1e2e;border-radius:8px;padding:16px;margin-bottom:16px;
  border-left:4px solid {chg_color}">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <h2 style="margin:0;font-size:18px">{sym}</h2>
    <span style="font-size:22px;color:{chg_color};font-weight:bold">
      ${q['price']:.2f} <small>{arrow}{abs(q['chg_pct']):.1f}%</small>
    </span>
  </div>
  <div style="margin:6px 0">{alerts_html}</div>
  <p style="color:#64748b;font-size:12px;margin:4px 0">
    52週 高 ${q['52w_high']:.2f} ／ 低 ${q['52w_low']:.2f} ｜
    今日量 {q['vol_today']:,} ／ 均量 {int(q['vol_avg']):,} ({q['vol_ratio']:.1f}x)
  </p>
  {fin_html}
  {news_html}
  {filings_html}
</div>"""


# ════════════════════════════════════════════════════
# 主掃描流程
# ════════════════════════════════════════════════════
def scan():
    now_str  = datetime.now().strftime("%Y-%m-%d %H:%M")
    triggers = []
    sections = []

    print(f"[{now_str}] 全天候掃描代理啟動，監控 {len(WATCH_SYMBOLS)} 個標的...")

    for sym in WATCH_SYMBOLS:
        print(f"  掃描 {sym}...", end=" ")
        try:
            q = fetch_quote(sym)
        except Exception as e:
            print(f"報價失敗 ({e})")
            continue

        price_triggered  = abs(q["chg_pct"])  >= PRICE_ALERT_PCT
        volume_triggered = q["vol_ratio"]      >= VOLUME_RATIO

        news     = fetch_news(sym)
        filings  = fetch_sec_filings(sym)
        fin      = fetch_financials_summary(sym) if (price_triggered or volume_triggered) else {}

        has_trigger = price_triggered or volume_triggered or filings
        flag = "🔔" if has_trigger else "✓"
        print(f"{flag}  價格{q['chg_pct']:+.1f}%  量{q['vol_ratio']:.1f}x  新聞{len(news)}則  申報{len(filings)}筆")

        if has_trigger or news:
            triggers.append(sym)
            sections.append(build_section(sym, q, news, filings, fin))

        time.sleep(0.5)

    if not sections:
        print("\n無重大異動，今日不發送報告。")
        return

    # ── 發送 Email ────────────────────────────────────
    subject   = f"📊 [{datetime.now().strftime('%m/%d')}] 掃描報告 | 觸發：{', '.join(triggers)}"
    html_body = build_email(now_str, triggers, sections)
    send_email(subject, html_body)

    # ── 發送 LINE 摘要 ────────────────────────────────
    line_msg = f"\n📊 全天候掃描 {now_str}\n觸發標的：{', '.join(triggers)}\n\n"
    for sym in triggers[:4]:
        try:
            q = fetch_quote(sym)
            line_msg += f"• {sym}  ${q['price']:.2f}  ({q['chg_pct']:+.1f}%)  量{q['vol_ratio']:.1f}x\n"
        except:
            pass
    line_msg += "\n詳細報告已寄至 Email"
    send_line(line_msg)

    print(f"\n完成！觸發 {len(triggers)} 個標的：{', '.join(triggers)}")


if __name__ == "__main__":
    scan()
