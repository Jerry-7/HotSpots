import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TONGYI_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TONGYI_MODEL = os.getenv("TONGYI_MODEL", "qwen-plus")
MODEL = os.getenv("MODEL", TONGYI_MODEL)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v1")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./storage/faiss_index")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

REDIS_URL = os.getenv("REDIS_URL", "")
AGENT_MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "6"))
