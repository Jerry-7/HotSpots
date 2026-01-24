import os

import streamlit as st
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.document_transformers import LongContextReorder
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.llms import Tongyi as LCTongyi
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate

# ===== 配置 =====
DOCS_DIR = "docs"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
PROVIDER = os.getenv("RAG_PROVIDER", "tongyi").lower()
K_VECTOR = 5
K_BM25 = 5
ENSEMBLE_WEIGHTS = [0.6, 0.4]


class SafeDashScopeEmbeddings(DashScopeEmbeddings):
    def embed_documents(self, texts):
        # 确保输入是字符串数组
        texts = [str(t) for t in texts]
        return super().embed_documents(texts)

    def embed_query(self, text):
        # 确保输入是单字符串
        return super().embed_documents([str(text)])[0]


# ===== 文档加载与切分 =====
@st.cache_data(show_spinner=False)
def load_docs():
    if os.path.isdir(DOCS_DIR):
        loader = DirectoryLoader(DOCS_DIR, glob="*.pdf", loader_cls=PyPDFLoader)
        docs = loader.load()
    else:
        docs = PyPDFLoader(DOCS_DIR).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


# ===== Embeddings & LLM =====
@st.cache_resource(show_spinner=False)
def get_embeddings():
    return SafeDashScopeEmbeddings(model="text-embedding-v1")


@st.cache_resource(show_spinner=False)
def get_llm():
    return LCTongyi(model="qwen-plus", temperature=0)


# ===== Hybrid 检索器 =====
@st.cache_resource(show_spinner=False)
def build_hybrid_retriever():
    docs = load_docs()  # 内部拿 docs，不暴露给缓存
    embeddings = get_embeddings()
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    vectordb = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vec_retriever = vectordb.as_retriever(search_kwargs={"k": K_VECTOR})

    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = K_BM25

    ensemble = EnsembleRetriever(
        retrievers=[vec_retriever, bm25_retriever],
        weights=ENSEMBLE_WEIGHTS
    )
    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=ensemble,
        llm=get_llm(),
        include_original=True
    )

    # 重排序 wrapper
    reordering = LongContextReorder()

    def _retrieve_with_reorder(query):
        # 确保 query 是字符串
        if isinstance(query, dict):
            query = query.get("input", str(query))
        elif not isinstance(query, str):
            query = str(query)

        docs = mq_retriever.get_relevant_documents(query)
        return docs

    return _retrieve_with_reorder


# ===== Streamlit UI =====
st.title("📚 增强版 RAG 知识问答系统 (可视化)")
st.sidebar.markdown("### 设置")
st.sidebar.write(f"模型提供商: {PROVIDER}")

with st.spinner("加载文档并构建检索器..."):
    # docs = load_docs()
    retriever_fn = build_hybrid_retriever()

    # 新的 prompt，兼容 0.3.x
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是严谨的助理。请仅依据上下文回答问题；没有答案就说“未在文档中找到明确答案”。"),
        ("human",
         "上下文：\n{context}\n\n问题：{input}")
    ])

    llm = get_llm()
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    # 手动把自定义 retriever 封装成 Runnable
    from langchain_core.runnables import RunnableLambda

    retrieval_chain = create_retrieval_chain(
        RunnableLambda(retriever_fn),
        combine_docs_chain
    )

query = st.text_input("请输入你的问题:")

if query:
    with st.spinner("正在生成答案..."):
        result = retrieval_chain.invoke({"input": query})
        answer = result["answer"]
        source_docs = result.get("context", [])

    # 置信度计算（基于检索分数平均）
    scores = [d.metadata.get("score", 0.5) for d in source_docs]
    confidence = round(sum(scores) / len(scores), 2) if scores else 0.0

    st.subheader("✅ 答案")
    st.write(answer)
    st.write(f"置信度: {confidence * 100:.1f}%")

    st.subheader("📄 检索贡献文档 (热力图)")
    for doc in source_docs:
        score = doc.metadata.get("score", 0.5)
        intensity = min(max(score, 0), 1)
        color = f"rgba(255,0,0,{intensity})"
        page = doc.metadata.get("page", "?")
        source = doc.metadata.get("source", "unknown")
        st.markdown(
            f"<div style='background-color:{color}; padding:5px; margin-bottom:5px;'>"
            f"<b>来源:</b> {source} 第 {page} 页<br>{doc.page_content}</div>",
            unsafe_allow_html=True
        )
