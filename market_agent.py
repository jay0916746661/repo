import google.generativeai as genai

class MarketAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def analyze_portfolio(self):
        prompt = """
你是一位專業的量化分析師，請幫我分析以下資產配置狀態，並用繁體中文給出具體的調整建議：

【跨市場觀測與配置板塊】：
1. 科技板塊：NVIDIA (NVDA)、台積電 (TSM)
2. 消費板塊：Nike (NKE)
3. 加密貨幣：比特幣 (BTC)、ARKM 等 AI 概念幣

考量到未來這個分析會透過 Express 後端傳遞給 React 前端 Dashboard 顯示，請用條理清晰、排版乾淨的結構回答，包含資金連動性、潛在風險與短期切入時機。
"""
        print("🤖 正在呼叫 Google Gemini 1.5 Pro 進行運算中...\n")
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ API 呼叫失敗：{e}"

if __name__ == "__main__":
    # 你專屬的 API Key
    GOOGLE_API_KEY = "AIzaSyAXRESpi_7_bTR4PX2LFVSUBCsJgQVes2c"
    agent = MarketAgent(GOOGLE_API_KEY)
    print("================ 📊 AI 深度分析結果 ================\n")
    print(agent.analyze_portfolio())
    print("\n====================================================")
