# Jim 的 AI 系統完整背景
> 貼給任何 AI 使用，讓對方立刻了解我的狀況
> 最後更新：2026-04-24

---

## 我是誰

- **名字**：Jim，台灣
- **背景**：無程式背景，從 2026-04-15 開始用 Claude Code
- **職業**：樂器業務（主要販售吉他類二手/新品給工作室、錄音室）
- **投資**：美股、台股、加密幣（派網）
- **核心目標**：一年內透過 AI 協助業務成長 + 投資紀律 + 個人提升，目標 2026 年底 AI 帶來 NT$10,000+/月

---

## 已建立的系統完整清單

### 🖥️ 主要 Dashboard（Streamlit）
- **本機**：`streamlit run /Users/jimlin/Downloads/claude/dashboard.py`（4338 行）
- **線上**：https://jim-finance-2026-hogvfrsqmozcws6rujjq5x.streamlit.app/
- **4 個核心分頁**：
  - 🌅 今日總覽：投資警報 + 今日 AI 任務 + 客戶跟進提醒 + 快速 AI 派遣
  - 🧠 AI 練功場：AI 問答 + 問題派遣台（歷史/分析/智慧推送）+ 學習地圖
  - 📈 投資：持倉追蹤 + Beta 壓力測試 + 出場/進場排名 + 台股 + 加密 + 撿漏轉賣
  - 💼 業務：客戶 CRM + Pipeline 視覺化 + AI 訊息生成

### 🤖 自動化腳本

| 檔案 | 功能 | 執行方式 |
|------|------|---------|
| `smart_recommend.py` | 讀電子書+YouTube訂閱偏好 → Gemini 生成推薦 → 推播 Telegram | 手動或定時 |
| `sync_books.py` | 同步 Google Drive 電子書到本機 JSON（gdown，不需 OAuth） | 手動執行 |
| `youtube_auth.py` | OAuth 授權 + 抓取 YouTube 訂閱頻道（974 個）| 一次性 |
| `market_agent.py` | 全天候市場掃描 + Email/LINE 通知 | GitHub Actions 每天 06:30 |
| `fb_scraper.py` | Facebook Marketplace 撿漏商品掃描 | GitHub Actions 每 30 分鐘 |
| `price_alert.py` | 監控 ETH/TSLA 等價格警報 + 每小時推播報價 | 持續執行 |
| `goal_alert.py` | 人生目標進度監控 | 手動或定時 |
| `daily_checkin.py` | 每日打卡系統 | 手動 |
| `daily_review.py` | 每日回顧 | 手動 |
| `life_report.py` | 生活報告生成 | 手動 |

### ☁️ GitHub Actions 自動化（已上線）
- `market_agent.yml`：每天 06:30 台灣時間自動掃描市場，通知 Gmail + LINE
- `fb_scan.yml`：每 30 分鐘自動掃描 FB Marketplace 撿漏商品，寫回 repo

### 🗂️ Backend（開發中）
- `backend/agents/sales_agent.py`：B2B 業務開發信 AI（LangChain + Ollama）
- `backend/agents/research_agent.py`：市場研究分析 AI
- `frontend/`：React + Vite 前端（含 AgentPanel、ChatInterface、ModelSelector）

### 📊 資料資產

| 資料 | 數量/內容 |
|------|---------|
| Google Drive 電子書 | 136 本（含分類、書架資訊）|
| 本機電子書 | 112 本（含封面圖片）|
| YouTube 訂閱頻道 | 974 個（含頻道名稱、ID、描述）|
| 投資持倉 | 美股、台股、派網加密、Firstrade 全帳戶 |
| 學習/生活/工作歷史 | CSV 格式紀錄 |
| 撿漏轉賣追蹤 | 商品成本/行情/售價 JSON |

---

## 投資帳戶結構

| 帳戶 | 類型 | 主要持倉方向 |
|------|------|------------|
| 國泰美股 | 美股券商 | 科技、ETF |
| 國泰台股 | 台股券商 | 台灣個股 |
| 派網加密 | 幣圈 | BTC/ETH/SOL 等，有 Grid Bot |
| 派網股票 | 美股槓桿 | 槓桿 ETF |
| Firstrade | 美股券商 | 另一帳戶 |

---

## AI 平台分工

```
你的問題 / 任務
│
├── 加密幣策略、派網機器人設定         → 派網 AI（App 內建）
├── 程式修改、Dashboard 新功能        → Claude Code（這個環境）
├── 即時搜尋、Google 服務、YouTube    → Gemini
├── 翻譯、圖片、輕量雜問              → GPT 免費版（省額度）
└── 深度分析、策略規劃、長文件         → Claude（claude.ai）
```

---

## 通知管道

| 管道 | 用途 |
|------|------|
| Telegram Bot（@jimrecommend_bot）| 每日內容推薦 |
| LINE Notify | 市場警報 |
| Gmail | GitHub Actions 報告 |

---

## 技術環境

- **本機**：macOS，Python 3.10（miniforge/conda）
- **雲端**：Streamlit Cloud（自動從 GitHub main branch 部署）
- **GitHub**：`jay0916746661/repo`（private）
- **配置**：`config.json`（gitignore，含所有 API key）
- **重要路徑**：
  - 專案：`/Users/jimlin/Downloads/claude/`
  - 資料：`/Users/jimlin/Downloads/claude/data/`
  - 持倉：`holdings.json`
  - 書單：`data/books.json`
  - YouTube：`data/youtube_subs.json`

---

## 使用習慣 & 偏好

- 不要教我怎麼做，**直接幫我做完**
- 回答用**繁體中文**
- **先給結果，再說原因**
- 給程式碼要說明**放在哪個檔案的哪裡**
- 不要加不必要的功能，做我要的就好

---

## 學習進度（2026-04-24）

**已完成（Week 1-2）：**
- 建出完整投資 Dashboard（4338 行）
- GitHub Actions 自動化（market scan + FB scan）
- Telegram 推播系統
- YouTube 訂閱分析
- AI 派遣台（問題路由 + 歷史分析 + 智慧推送）
- 業務 CRM

**當前等級：L1 指揮官**
> 能精準描述需求，讓 AI 建出自己要的工具，每天用到 Claude 額度上限

**接下來（5-6 月）：**
- CRM 填入客戶，開始追蹤
- 第一個完全自動化的業務流程
- 業務客戶 2 → 5 個

---

## Prompt 技巧備忘

| 技巧 | 用法 |
|------|------|
| **Few-Shot** | 先貼一個我喜歡的範例，再叫 AI 照格式做 |
| **Chain-of-Thought** | 加「請一步一步分析」，提升複雜問題準確度 |
| **Prompt Chaining** | 複雜任務先問「步驟」，再逐步問每一步 |
| **RAG** | 把資料（書單/持倉/客戶）貼進來，讓 AI 根據真實數據回答 |
