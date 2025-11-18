"""
Simplified LangChain Agent with Automatic MCP Tool Discovery

This approach automatically discovers all MCP tools and converts them
to LangChain tools without manual wrapping of each tool.

Architecture:
1. Connect to MCP Server once
2. List all available tools automatically
3. Create LangChain tool wrapper dynamically for each MCP tool
4. Agent can use any MCP tool without code changes
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
from langchain_core.tools import ToolException
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.mcp_client import get_mcp_client

# Load environment variables from .env file
load_dotenv()


# System prompt for the agent
SYSTEM_PROMPT = """
You are a dbt project discovery assistant.

Core behavior:
- Use discovery tools only: `get_all_models`, `get_mart_models`, `get_model_details`,
  `get_model_parents`, `get_model_children`, `get_model_health`, `get_exposures`, `get_exposure_details`.
- Do not call CLI/SQL/semantic-layer tools. They are disabled in this environment.
- Prefer `get_all_models` first, then drill into details with `get_model_details` (using uniqueId).

Error handling:
- If any tool returns text that starts with "ERROR" or contains "timed out",
  DO NOT call more tools. Respond with:
  1) the exact error message,
  2) the likely cause,
  3) concrete next steps.
- If the same tool with the same arguments fails twice, DO NOT retry it again.
- If a tool raises an exception or returns text starting with "ERROR" or containing "timed out", DO NOT call more tools.
  Respond with: (1) the exact error message, (2) likely cause, (3) concrete next steps.

Response requirements:
- Present findings in clear, compact English using bullets or short sections.
- Highlight discovered models/exposures and explain how they relate to the user's request.
- Ask for clarification only when tooling cannot resolve the question.
- Do not invent data.
"""


# --- 新增：把 JSON Schema 转为 Pydantic 模型 ---
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, create_model

def _json_schema_to_pydantic_model(tool_name: str, schema: Optional[Dict[str, Any]]):
    if not schema:
        return None

    props: Dict[str, Any] = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])
    fields: Dict[str, tuple] = {}

    def _map_type(s: Dict[str, Any]):
        t = s.get("type")
        # NOTE: 这里做一个通用的、足够“宽松”的映射；需要更严谨可以按 items 递归
        if t == "string":  py = str
        elif t == "integer": py = int
        elif t == "number":  py = float
        elif t == "boolean": py = bool
        elif t == "array":
            from typing import List as TList, Any as TAny
            py = TList[TAny]
        elif t == "object":
            from typing import Dict as TDict, Any as TAny
            py = TDict[str, TAny]
        else:
            from typing import Any as TAny
            py = TAny

        # enum -> Literal （可选，失败就退回基础类型）
        if "enum" in s:
            try:
                from typing import Literal
                literals = tuple(s["enum"])
                return Literal[literals]  # type: ignore
            except Exception:
                return py
        return py

    for name, sub in props.items():
        pytype = _map_type(sub)
        default = ... if name in required else None
        desc = sub.get("description")
        fields[name] = (pytype, Field(default, description=desc))

    model = create_model(f"{tool_name}_Args", **fields)  # type: ignore
    return model

def _extract_text_from_mcp_result(result: Any) -> str:
    print(f"[DEBUG] Extracting text from result type: {type(result)}")
    print(f"[DEBUG] Result has 'content' attr: {hasattr(result, 'content')}")
    
    parts: List[str] = []
    content = getattr(result, "content", []) or []
    print(f"[DEBUG] Content items count: {len(content)}")
    
    for i, item in enumerate(content):
        t = getattr(item, "type", None)
        print(f"[DEBUG] Item {i} type: {t}")
        
        if t == "text":
            text_content = getattr(item, "text", "") or ""
            print(f"[DEBUG] Text content length: {len(text_content)}")
            parts.append(text_content)
        elif t == "json":
            try:
                import json
                json_content = getattr(item, "json", None)
                print(f"[DEBUG] JSON content type: {type(json_content)}")
                formatted = json.dumps(json_content, ensure_ascii=False, indent=2)
                parts.append(formatted)
            except Exception as e:
                print(f"[DEBUG] Error formatting JSON: {e}")
                parts.append(str(getattr(item, "json", None)))
    
    result_text = "\n".join(p for p in parts if p)
    print(f"[DEBUG] Final extracted text length: {len(result_text)}")
    print(f"[DEBUG] First 500 chars: {result_text[:500]}...")
    
    return result_text
    
# --- 重新实现：为每个 MCP 工具创建 LangChain 工具 ---
from langchain_core.tools import StructuredTool
_last_calls: Dict[tuple, int] = {}

def create_mcp_tool_wrapper(tool_name: str, tool_description: str, tool_schema: dict = None) -> StructuredTool:
    args_model = _json_schema_to_pydantic_model(tool_name, tool_schema)

    async def async_call_mcp_tool(**kwargs) -> str:
        print(f"[DEBUG] Tool '{tool_name}' called with args: {kwargs}")
        
        from agents.mcp_client import get_mcp_client
        client = await get_mcp_client()

        key = (tool_name, tuple(sorted((kwargs or {}).items())))
        cnt = _last_calls.get(key, 0) + 1
        _last_calls[key] = cnt
        
        if cnt >= 3:
            error_msg = f"`{tool_name}` called 3 times with same arguments. Stopping to avoid loops."
            print(f"[DEBUG] {error_msg}")
            raise ToolException(error_msg)

        try:
            print(f"[DEBUG] Calling MCP client for tool '{tool_name}'")
            res = await client.call_tool(tool_name, kwargs or {})
            
            # Debug the raw response
            print(f"[DEBUG] Raw MCP response type: {type(res)}")
            print(f"[DEBUG] Raw MCP response: {str(res)[:500]}...")
            
            text = _extract_text_from_mcp_result(res) or str(res)
            
            if not text.strip():
                text = f"Tool `{tool_name}` returned no content."
                print(f"[DEBUG] Empty response, using default message")
            else:
                print(f"[DEBUG] Tool '{tool_name}' extracted text length: {len(text)}")
                print(f"[DEBUG] Tool '{tool_name}' first 200 chars: {text[:200]}...")
            
            # Check for errors in response
            if text.startswith("ERROR") or "timed out" in text.lower():
                _last_calls[key] = cnt - 1
                print(f"[DEBUG] Error detected in response")
                raise ToolException(text)
                
            return text
            
        except ToolException:
            raise
        except TimeoutError as e:
            _last_calls[key] = cnt - 1
            error_msg = f"ERROR: Tool `{tool_name}` timed out"
            print(f"[DEBUG] {error_msg}")
            raise ToolException(error_msg)
        except Exception as e:
            _last_calls[key] = cnt - 1
            error_msg = f"ERROR calling `{tool_name}`: {type(e).__name__}: {e}"
            print(f"[DEBUG] {error_msg}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            raise ToolException(error_msg)

    # For sync fallback (shouldn't be used but required by StructuredTool)
    def sync_wrapper(**kwargs):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_call_mcp_tool(**kwargs))

    return StructuredTool.from_function(
        func=sync_wrapper,  # Provide working sync function
        coroutine=async_call_mcp_tool,
        name=tool_name,
        description=tool_description or f"MCP tool: {tool_name}",
        args_schema=args_model,
        handle_tool_error=True,  # Let LangGraph handle tool errors gracefully
    )

async def discover_mcp_tools() -> List[StructuredTool]:
    """
    Automatically discover all available MCP tools and convert to LangChain tools

    Returns:
        List of LangChain tools, one for each MCP tool
    """
    print("🔍 Discovering MCP tools...")

    # Get MCP client
    client = await get_mcp_client()

    # List all available tools from MCP server
    langchain_tools: List[StructuredTool] = []
    tools = await client.list_tools()

    print(f"✓ Found {len(tools)} MCP tools")

    # Convert each MCP tool to a LangChain tool
    for mcp_tool in tools:
        print(f"  • {mcp_tool.name}: {mcp_tool.description[:60]}...")

        inp_schema = getattr(mcp_tool, "input_schema", None) or getattr(mcp_tool, "inputSchema", None)
        langchain_tool = create_mcp_tool_wrapper(
            tool_name=mcp_tool.name,
            tool_description=mcp_tool.description,
            tool_schema=inp_schema,
        )

        langchain_tools.append(langchain_tool)

    print(f"✓ Created {len(langchain_tools)} LangChain tool wrappers\n")
    return langchain_tools

import threading, asyncio

def _run_coro_in_thread(coro):
    """Run at the back"""
    box = {"res": None, "err": None}
    def _runner():
        try:
            box["res"] = asyncio.run(coro)
        except Exception as e:
            box["err"] = e
    t = threading.Thread(target=_runner, daemon=True)
    t.start(); t.join()
    if box["err"]:
        raise box["err"]
    return box["res"]

def create_dbt_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or environment.")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

    # use thread
    tools = _run_coro_in_thread(discover_mcp_tools())

    agent = create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
    return agent


# Global agent instance (lazy initialization)
_agent = None


def get_agent():
    """
    Get the global agent instance (singleton pattern)

    Returns:
        CompiledGraph: The agent instance
    """
    global _agent

    if _agent is None:
        _agent = create_dbt_agent()

    return _agent


def ask_agent(question: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Ask the agent a question about DBT data"""
    global _last_calls
    _last_calls.clear()
    
    try:
        print(f"Question is: {question}")
        agent = get_agent()
        
        # Build messages
        from langchain_core.messages import HumanMessage, AIMessage
        messages = []
        
        if history:
            for entry in history:
                role = entry.get("role")
                content = entry.get("content")
                if not content:
                    continue
                    
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role in ("assistant", "ai"):
                    messages.append(AIMessage(content=content))
        
        # Add current question
        messages.append(HumanMessage(content=question))
        
        print(f"[DEBUG] Invoking agent with {len(messages)} messages")
        result = agent.invoke({"messages": messages})
        print(f"[DEBUG] Agent returned result type: {type(result)}")
        
        # Extract response
        if isinstance(result, dict) and "messages" in result:
            result_messages = result["messages"]
            print(f"[DEBUG] Found {len(result_messages)} messages in result")
            
            # Print all messages for debugging
            for i, msg in enumerate(result_messages):
                print(f"[DEBUG] Message {i}: type={type(msg).__name__}, "
                      f"content_length={len(str(msg.content)) if hasattr(msg, 'content') else 0}")
                if hasattr(msg, 'content'):
                    print(f"[DEBUG] Message {i} preview: {str(msg.content)[:200]}...")
            
            # Get last AI message
            for msg in reversed(result_messages):
                if hasattr(msg, '__class__') and msg.__class__.__name__ == 'AIMessage':
                    print(f"[DEBUG] Returning AI message content")
                    return msg.content
        
        print(f"[DEBUG] No AI message found, returning str(result)")
        return str(result)
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return f"Sorry, an error occurred: {type(e).__name__} - {str(e)}"


if __name__ == "__main__":
    """Test the simplified agent"""
    print("\n" + "=" * 80)
    print("  DBT Agent with Automatic MCP Tool Discovery")
    print("=" * 80 + "\n")

    test_questions = [
        "What tables do we have?",
    ]

    for question in test_questions:
        print(f"Question: {question}\n")
        answer = ask_agent(question)
        print(f"Answer:\n{answer}\n")

    print("=" * 80 + "\n")
