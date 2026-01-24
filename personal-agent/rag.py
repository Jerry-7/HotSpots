from typing import List, Dict, Any
import os, glob
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.llms import Tongyi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.docstore.document import Document
from config import EMBEDDING_MODEL, VECTOR_STORE_PATH

_vectorstore = None

def _load_files(data_dir: str = "data") -> List[Document]:
    docs: List[Document] = []
    for path in glob.glob(os.path.join(data_dir, "**/*"), recursive=True):
        if os.path.isdir(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
            elif ext in [".txt", ".md", ".markdown"]:
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
        except Exception as e:
            print(f"[ingest] skip {path}: {e}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=120)
    return splitter.split_documents(docs)

def build_or_load_vectorstore(data_dir: str = "data") -> FAISS:

    global _vectorstore
    #使用全局缓存
    if _vectorstore is not None:
        return _vectorstore

    os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
    embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL)

    if os.path.exists(VECTOR_STORE_PATH):
        # 0.3版本 load_local 需要传 embeddings
        vs = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        return vs

    docs = _load_files(data_dir)
    _vectorstore = FAISS.from_documents(docs, embeddings)
    _vectorstore.save_local(VECTOR_STORE_PATH)
    return _vectorstore

def reload_vectorstore(data_dir: str = "data") -> FAISS:
    global _vectorstore
    embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL)
    docs = _load_files(data_dir)
    _vectorstore = FAISS.from_documents(docs, embeddings)
    _vectorstore.save_local(VECTOR_STORE_PATH)
    return _vectorstore

def similarity_search(query: str, k: int = 4) -> List[Dict[str, Any]]:
    vs = build_or_load_vectorstore()
    docs = vs.similarity_search(query, k=k)
    return [{"content": d.page_content, "meta": d.metadata} for d in docs]