"""
LLM 模型管理
"""
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from ..config import LLM_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_TEMPERATURE

_llm_instance = None

def get_llm() -> ChatOpenAI:
    """获取 LLM 实例（全局只创建一次）"""
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model=LLM_MODEL,
            api_key=SecretStr(LLM_API_KEY),
            base_url=LLM_BASE_URL,
            temperature=LLM_TEMPERATURE
        )
        print(f"✅ LLM 已就绪: {LLM_MODEL}")

    return _llm_instance