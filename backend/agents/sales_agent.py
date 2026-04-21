from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

SALES_PROMPT = PromptTemplate(
    input_variables=["company", "contact", "product", "language"],
    template="""
你是一位專業的 B2B 業務開發專員，幫我撰寫一封開發信。

目標公司：{company}
聯絡人：{contact}
產品/服務：{product}
語言：{language}

請撰寫：
1. 主旨行（吸睛、簡短）
2. 開場（個人化、提及對方痛點）
3. 價值主張（3個重點）
4. CTA（清晰的下一步）

格式：JSON
{{
  "subject": "...",
  "body": "...",
  "cta": "..."
}}
"""
)

def get_sales_agent(model: str, ollama_url: str):
    llm = Ollama(model=model, base_url=ollama_url, temperature=0.7)
    return LLMChain(llm=llm, prompt=SALES_PROMPT)
