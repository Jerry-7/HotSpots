"""
RAG 链：把 Retriever + Prompt + LLM 组装成 LCEL 链
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..core.llm import get_llm
from ..core.vectorstore import get_vectorstore
from ..config import RETRIEVER_K

RAG_PROMPT_TEMPLATE = """你是公司的行政助手。请严格根据【参考资料】回答员工的问题。
如果参考资料中没有相关信息，请直接说"抱歉，我没有找到相关规定"。
回答时请注明信息来源。

【参考资料】:
{context}

【问题】:
{question}
"""


def _format_docs(docs) -> str:
    """把检索到的 Document 列表格式化为字符串"""
    lines = []
    for doc in docs:
        source = doc.metadata.get("source", "未知")
        lines.append(f"[来源: {source}] {doc.page_content}")
    return "\n".join(lines)


def build_rag_chain():
    """构建完整的 RAG 链"""
    # 1. 获取组件
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

    # 2. 组装 LCEL 链
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("✅ RAG 链组装完成")
    return chain, retriever  # 同时返回 retriever，方便 debug 模式使用