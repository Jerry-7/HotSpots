from typing import Any, Dict
import httpx
import math
import json

# ---------------- 工具函数 ---------------- #

def tool_web_search(query: str) -> str:
    """Stub web search (replace with real provider: SerpAPI, Bing, Tavily, etc.)."""
    return f"[search results for '{query}': (stub) integrate your provider here]"

def tool_http_get(url: str) -> str:
    """Fetch raw text content from a URL (truncated to 4000 chars)."""
    try:
        resp = httpx.get(url, timeout=15.0)
        resp.raise_for_status()
        return resp.text[:4000]
    except Exception as e:
        return f"[http_get error: {e}]"

def tool_math_eval(expression: str) -> str:
    """Evaluate a safe math expression using Python's math module."""
    try:
        allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        # 禁用内置函数
        allowed_names["__builtins__"] = {}
        result = eval(expression, allowed_names, {})
        return str(result)
    except Exception as e:
        return f"[math_eval error: {e}]"

def tool_rag_search(query: str) -> str:
    """Search local RAG knowledge base (uses similarity_search)."""
    from rag import similarity_search
    docs = similarity_search(query, k=4)
    return json.dumps(docs, ensure_ascii=False)

# ---------------- 工具注册规范 ---------------- #

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "tool_web_search",
            "description": "Search the web for up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_http_get",
            "description": "Fetch the raw text content of a URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_math_eval",
            "description": "Evaluate a safe math expression using Python math module.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_rag_search",
            "description": "Search the local RAG knowledge base for relevant chunks.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]

# ---------------- 工具调用统一接口 ---------------- #

def call_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Unified tool dispatcher."""
    if name == "tool_web_search":
        return tool_web_search(arguments.get("query", ""))
    if name == "tool_http_get":
        return tool_http_get(arguments.get("url", ""))
    if name == "tool_math_eval":
        return tool_math_eval(arguments.get("expression", ""))
    if name == "tool_rag_search":
        return tool_rag_search(arguments.get("query", ""))
    return f"[unknown tool: {name}]"
