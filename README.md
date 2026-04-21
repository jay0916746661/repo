# AI Workflow Dashboard

本地 AI 工作流面板，整合 Ollama + LangChain Agent。

## 啟動方式

**Terminal 1 — 後端**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

**Terminal 2 — 前端**
```bash
cd frontend
npm install
npm run dev
```

開啟瀏覽器：http://localhost:5173

## 前提
- [Ollama](https://ollama.com) 已安裝並執行
- `ollama pull llama3`
- Python 3.10+、Node.js 18+
