import json, time
from pathlib import Path
from google import genai

config = json.loads((Path(__file__).parent / "config.json").read_text())
client = genai.Client(api_key=config["gemini_api_key"])

print("🚀 正在直接連線 Google 伺服器...")
start = time.time()
try:
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="這是一個連線測試，請用繁體中文回覆我『API 串接成功』。"
    )
    print(f"✅ 連線成功！耗時 {time.time() - start:.2f} 秒")
    print(f"🤖 AI 回覆: {resp.text.strip()}")
except Exception as e:
    print(f"❌ 連線失敗: {e}")
