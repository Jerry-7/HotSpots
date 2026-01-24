from typing import List, Dict, Any
from config import MODEL, OPENAI_API_KEY
from langchain_community.llms import Tongyi
from tools import TOOLS_SPEC, call_tool
import json

SYSTEM_PLANNER = """You are a task planner for a multi-step Agent.
Break down user goals into steps. Use tools when helpful.
Prefer calling tool_rag_search for private knowledge.
Respond with a helpful final answer when ready."""

def run_agent(messages: List[Dict[str, str]], max_steps: int = 6) -> Dict[str, Any]:
    """
    ReAct-like loop with Tongyi Qianwen.
    Returns a dict with 'final_answer' and 'trace'.
    """
    client = Tongyi(model_name="qwen-plus",  dashscope_api_key=DASHSCOPE_API_KEY, model_kwargs={"temperature": 0.2} )
    trace: List[Dict[str, Any]] = []
    convo = [{"role": "system", "content": SYSTEM_PLANNER}] + messages

    for step in range(max_steps):
        # OPEN AI
        # resp = client.chat.completions.create(
        #     model=OPENAI_PLANNER_MODEL,我
        #     messages=convo,
        #     temperature=0.2
        # )
        # choice = resp.choices[0]
        # msg_content = choice.message.content or ""
        # trace.append({"assistant": msg_content})


        #Tong Yi
        resp = client.chat(messages=convo)
        msg_content = getattr(resp, "content", None) or getattr(resp, "result", "")
        trace.append({"assistant": msg_content})

        # 检查是否有工具调用指令（约定 JSON 格式：{"tool": "name", "args": {...}}）
        try:
            tool_call = json.loads(msg_content)
            if isinstance(tool_call, dict) and "tool" in tool_call and "args" in tool_call:
                name = tool_call["tool"]
                args = tool_call.get("args", {})
                result = call_tool(name, args)
                convo.append({"role": "tool", "content": result, "name": name})
                trace.append({"tool_result": {"name": name, "result": result[:500]}})
                continue
        except Exception:
            # 不是工具调用，直接作为最终答案返回
            return {"final_answer": msg_content, "trace": trace}

    return {"final_answer": "[Reached max steps]", "trace": trace}
