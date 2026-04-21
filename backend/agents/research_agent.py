from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

RESEARCH_PROMPT = PromptTemplate(
    input_variables=["topic", "depth"],
    template="""
你是一位市場研究分析師。請針對以下主題提供結構化分析：

主題：{topic}
深度：{depth}

請提供：
1. 市場概況（2-3句）
2. 主要玩家（列表）
3. 趨勢與機會（3點）
4. 潛在風險（3點）
5. 行動建議

輸出格式：繁體中文，Markdown 格式
"""
)

def get_research_agent(model: str, ollama_url: str):
    llm = Ollama(model=model, base_url=ollama_url, temperature=0.4)
    return LLMChain(llm=llm, prompt=RESEARCH_PROMPT)
