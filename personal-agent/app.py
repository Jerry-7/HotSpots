from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from config import AGENT_MAX_STEPS, REDIS_URL
from memory import ShortTermMemory
from planner import run_agent
from rag import build_or_load_vectorstore, reload_vectorstore
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载向量库
    build_or_load_vectorstore()
    yield
    # 这里可以加清理逻辑，比如关闭 DB / 清理缓存


app = FastAPI(
    title="Personal AI Agent",
    version="0.1.0",
    lifespan=lifespan
)
memory = ShortTermMemory(redis_url=REDIS_URL or None)

class ChatRequest(BaseModel):
    session_id: str = "default"
    query: str
    reset: bool = False

class ChatResponse(BaseModel):
    answer: str
    trace: Any

class IngestRequest(BaseModel):
    data_dir: str = "data"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest(req: IngestRequest):
    vs = reload_vectorstore(req.data_dir)
    return {
        "message": f"Vectorstore reloaded from {req.data_dir}",
        "documents": len(vs.index_to_docstore_id)
    }

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    if req.reset:
        memory.clear(req.session_id)

    history = memory.get(req.session_id, limit=40)
    msgs = [{"role": m["role"], "content": m["content"]} for m in history]
    msgs.append({"role": "user", "content": req.query})

    def event_generator():
        for token in run_agent(msgs, max_steps=AGENT_MAX_STEPS):
            yield token  # run_agent 要支持 yield token

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        if req.reset:
            memory.clear(req.session_id)

        history = memory.get(req.session_id, limit=40)
        msgs = [{"role": m["role"], "content": m["content"]} for m in history]
        msgs.append({"role": "user", "content": req.query})

        result = run_agent(msgs, max_steps=AGENT_MAX_STEPS)
        answer = result.get("final_answer", "")

        memory.add(req.session_id, "user", req.query)
        memory.add(req.session_id, "assistant", answer)

        return ChatResponse(answer=answer, trace=result.get("trace"))
    except Exception as e:
        return ChatResponse(answer="⚠️ 出错了，请稍后再试", trace=str(e))
