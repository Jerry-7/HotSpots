from huggingface_hub import hf_hub_download
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr
from langchain_core.tools import tool
from pathlib import Path
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
BASE_DIR = Path("../sandbox").resolve()
BASE_DIR.mkdir(exist_ok=True)
MODEL="z-ai/glm-4.5-air:free"
SK="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"
embedding_model="text2vec-base-chinese"
BASE_URL = "https://openrouter.ai/api/v1"
persist_dir = "./chroma_db"
collection = "test_collection"

REPO_ID = "shibing624/text2vec-base-chinese"
LOCAL_DIR = "../model"
def is_model_complete(model_dir):
    required_files = [
        "config.json",
        "modules.json",
        "sentence_bert_config.json",
        "tokenizer_config.json",
        "vocab.txt"
    ]
    return all(os.path.exists(os.path.join(model_dir, f)) for f in required_files)


def download_embedding_model():
    if os.path.exists(LOCAL_DIR) and is_model_complete(LOCAL_DIR):
        print(f"✅ 本地模型已存在: {LOCAL_DIR}")
        return LOCAL_DIR

    os.makedirs(LOCAL_DIR, exist_ok=True)

    files_to_download = [
        "config.json",
        "model.safetensors",   # 推荐
        "modules.json",
        "sentence_bert_config.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "1_Pooling/config.json"
    ]

    for filename in files_to_download:
        print(f"⬇️ 下载 {filename}")
        hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=LOCAL_DIR,
            local_dir_use_symlinks=False,
            force_download=False
        )

    print("✅ 下载完成")
    return LOCAL_DIR

def get_vectorstore():
    text_data = [
        "我现在是一名分布存储后端开发工程师。",
        "我现在比较重，需要减肥。",
        "我希望未来能够养一条边牧。",
        "我喜欢吃的食物是南昌拌粉加瓦罐汤。",
    ]

    documents = [Document(page_content=t) for t in text_data]
    embeddings = HuggingFaceEmbeddings(
        model_name=f"./models/{embedding_model}"
    )
    if not os.path.exists(persist_dir):
        # 加载文档
        loader = TextLoader("./docs/knowledge.txt", encoding="utf-8")
        docs = loader.load()

        # 切片
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
        splits = splitter.split_documents(docs)

        # 写入 Chroma（自动持久化）
        vectorstore = Chroma.from_texts(
            texts=text_data,
            embedding=embeddings,
            persist_directory=persist_dir,
            collection_name="collection_name",  # 集合名称
        )
        print(f"已写入 {len(splits)} 个片段")
        return vectorstore
    else:
    # 2️⃣ 初始化 Chroma（指定持久化目录）
        vectordb = Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        return vectordb

@tool
def read_file(filename: str) -> str:
    """
    读取 sandbox 目录下的文本文件内容
    """
    path = (BASE_DIR / filename).resolve()

    if not path.exists():
        return f"文件不存在: {filename}"

    if not str(path).startswith(str(BASE_DIR)):
        return "非法路径访问"

    return path.read_text(encoding="utf-8")
@tool
def write_file(filename: str, content: str) -> str:
    """
    向 sandbox 目录写入文本文件
    """
    path = (BASE_DIR / filename).resolve()

    if not str(path).startswith(str(BASE_DIR)):
        return "非法路径访问"

    path.write_text(content, encoding="utf-8")
    return f"文件 {filename} 写入成功"

@tool
def create_directory(dir_path: str) -> str:
    """
    在 sandbox 目录下创建目录（支持多级目录）
    """
    target = (BASE_DIR / dir_path).resolve()

    # 路径安全校验
    if not str(target).startswith(str(BASE_DIR)):
        return "非法路径访问，禁止创建目录"

    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"目录创建成功: {dir_path}"
    except Exception as e:
        return f"创建目录失败: {e}"

tools = [read_file, write_file, create_directory]


llm = ChatOpenAI(
    model=MODEL,
    api_key=SecretStr(SK),
    base_url=BASE_URL,
    default_headers={
        "HTTP-Referer": "https://your-site.com",  # 标识来源（OpenRouter 推荐）
        "X-Title": "Test LLM"  # 应用名称（可选）
    },
    temperature=0.5)
prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个私人助手，有必要时可以使用工具执行。"),
        MessagesPlaceholder("chat_history"),  # 存放历史对话
        ("human", "{input}"),  # 用户输入
        MessagesPlaceholder("agent_scratchpad")  # 【关键】存放思考过程和工具结果
    ])




agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 打开这里，LangChain 会自动打印绿色的工具调用日志
    handle_parsing_errors=True  # 容错处理
)
store = {}
def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_history,
    input_messages_key="input",
    history_messages_key="chat_history" # 必须与 prompt 中的名字对应
)

def main():
    download_embedding_model()
    config = {"configurable": {"session_id": "terminal_agent"}}
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 2,
            "score_threshold": 0.5,  # 最低相似度阈值（仅 similarity_score_threshold 时生效）
            "fetch_k": 20,  # MMR 时，先取 fetch_k 条再筛选（仅 mmr 时生效）
            "lambda_mult": 0.5,  # MMR 多样性参数（仅 mmr 时生效）
        }
    )
    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    while True:
        try:
            user_input = input("\n你: ").strip()
            if not user_input or user_input.lower() in {"exit", "quit"}:
                break

            print("助手 (思考与行动中...): \n")

            # AgentExecutor 的 stream 返回的是一个个事件块
            # 这里的 chunk 主要是最终的回答片段
            final_response = ""
            for chunk in rag_chain.stream(
                    {"input": user_input},
                    config=config
            ):
                # 如果 chunk 包含 'output'，说明是最终回答的文本
                if "output" in chunk:
                    print(chunk["output"], end="", flush=True)
                    final_response += chunk["output"]

                # 如果你想自己手动处理工具日志而不是用 verbose=True，
                # 可以在这里判断 chunk 是否包含 'actions' 或 'steps'

            print("\n")

        except KeyboardInterrupt:
            print("\n👋 已退出")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()