# Personal AI Agent (RAG + Tools + Memory + Multi-step)

A minimal FastAPI backend that orchestrates:
- **Commercial LLM (OpenAI)** via function/tool calling
- **RAG** (FAISS vector store) with simple ingestion pipeline
- **Tools** (web search stub, HTTP GET, math, safe Python math eval)
- **Memory**: short-term (Redis chat history) + long-term (vector memory)
- **Multi-step planner** (ReAct-style loop)

> This is a starter kit intended for local development. Extend freely.

## 1) Setup

```bash
# Python 3.10+ recommended
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Environment variables (create .env)
cp .env.example .env
# Edit .env to put your keys (OPENAI_API_KEY, REDIS_URL, etc.)
```

## 2) Run

```bash
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs to try the API.

## 3) Endpoints

- `POST /ingest` — Ingest files from `data/` into FAISS (RAG)
- `POST /chat` — Chat with the Agent (multi-step + tools + memory)
- `GET /health` — Health check

## 4) Data

Put your PDFs/MD/TXT in `data/` then call `/ingest`.

## 5) Notes

- Web search tool is a **stub** with a pluggable interface. Wire in your provider (Tavily, SerpAPI, Bing) in `tools.py`.
- Redis is optional; if not available, an in-memory fallback is used.
- This template uses OpenAI **Chat Completions** tool-calling for broad compatibility.
- You own all integration & ops decisions (observability, auth, rate limiting, cost controls).

## 6) Extend

- Add more tools (calendar, email, spreadsheets) in `tools.py`
- Add user profiles & embeddings to personalize via `memory.py`
- Replace FAISS with Milvus/Weaviate/Pinecone for production
- Swap OpenAI for Anthropic/Gemini or an OSS model with an OpenAI-compatible server
