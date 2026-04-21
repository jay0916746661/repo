from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import json
import os
from dotenv import load_dotenv
from agents.sales_agent import get_sales_agent
from agents.research_agent import get_research_agent

load_dotenv()

app = FastAPI(title="AI Workflow Dashboard API", version="1.0.0")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model: str = "llama3"
    system_prompt: Optional[str] = None

class SalesRequest(BaseModel):
    company: str
    contact: str
    product: str
    language: str = "繁體中文"
    model: str = "llama3"

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "中等"
    model: str = "llama3"

@app.get("/health")
async def health():
    return {"status": "ok", "ollama_url": OLLAMA_BASE_URL}

@app.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"models": models}
    except Exception as e:
        return {"models": ["llama3", "mistral", "gemma"], "warning": str(e)}

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        payload = {
            "model": req.model,
            "messages": [
                {"role": "system", "content": req.system_prompt or "你是一個專業的 AI 助理。"},
                {"role": "user", "content": req.message}
            ],
            "stream": True
        }
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/chat",
                json=payload, timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/agent/sales")
async def run_sales_agent(req: SalesRequest):
    try:
        agent = get_sales_agent(req.model, OLLAMA_BASE_URL)
        result = agent.run(company=req.company, contact=req.contact,
                           product=req.product, language=req.language)
        try:
            parsed = json.loads(result)
        except:
            parsed = {"body": result, "subject": "開發信", "cta": "期待您的回覆"}
        return {"success": True, "data": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/research")
async def run_research_agent(req: ResearchRequest):
    try:
        agent = get_research_agent(req.model, OLLAMA_BASE_URL)
        result = agent.run(topic=req.topic, depth=req.depth)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/status")
async def workflow_status():
    return {"active_agents": 0, "completed_tasks": 0, "queue": []}
