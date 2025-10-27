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
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool

from agents.mcp_client import get_mcp_client, close_global_client

# Load environment variables from .env file
load_dotenv()


# System prompt for the agent
SYSTEM_PROMPT = """You are a data asset discovery assistant that helps users understand the tables and fields in their DBT project.

Your tasks:
1. Understand user questions about data tables
2. Use the available DBT tools to query project metadata
3. Provide clear, concise, and friendly responses in English

Response requirements:
- Present information in a clear format (use lists, sections, etc.)
- If uncertain, ask for more information
- Keep responses concise and highlight key information
- Focus on discovery - execution tools are disabled for safety

You have access to DBT metadata tools. Use them to answer questions about:
- Available tables and models
- Table structures and schemas
- Data lineage and dependencies
- Documentation and descriptions
"""


def create_mcp_tool_wrapper(tool_name: str, tool_description: str, tool_schema: dict = None):
    """
    Create a LangChain tool wrapper for an MCP tool

    Args:
        tool_name: Name of the MCP tool
        tool_description: Description of what the tool does
        tool_schema: JSON schema for tool parameters

    Returns:
        StructuredTool: LangChain tool that calls the MCP tool
    """

    def sync_call_mcp_tool(**kwargs) -> str:
        """Synchronous wrapper that calls MCP tool"""
        async def _call():
            client = await get_mcp_client()
            result = await client.call_tool(tool_name, kwargs)

            # Extract text content from result
            if result.content:
                return result.content[0].text
            return str(result)

        # Run async function synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            elif loop.is_running():
                # Create new loop for nested async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(_call())
        except Exception as e:
            return f"Error calling MCP tool '{tool_name}': {str(e)}"

    # Create the LangChain tool
    return StructuredTool.from_function(
        func=sync_call_mcp_tool,
        name=tool_name,
        description=tool_description or f"MCP tool: {tool_name}",
        # If we have a schema, we could parse it to add args_schema
        # For now, keep it simple
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
    tools = await client.list_tools()

    print(f"✓ Found {len(tools)} MCP tools")

    # Convert each MCP tool to a LangChain tool
    langchain_tools = []

    for mcp_tool in tools:
        print(f"  • {mcp_tool.name}: {mcp_tool.description[:60]}...")

        langchain_tool = create_mcp_tool_wrapper(
            tool_name=mcp_tool.name,
            tool_description=mcp_tool.description,
            tool_schema=mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') else None
        )

        langchain_tools.append(langchain_tool)

    print(f"✓ Created {len(langchain_tools)} LangChain tool wrappers\n")

    return langchain_tools


def create_dbt_agent():
    """
    Create a DBT data discovery agent with automatic MCP tool discovery

    Returns:
        CompiledGraph: Configured agent ready to answer questions

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )

    # Discover MCP tools automatically
    tools = asyncio.run(discover_mcp_tools())

    # Create the agent using LangGraph
    agent = create_react_agent(
        model=llm,
        tools=tools,  # All MCP tools automatically available
        prompt=SYSTEM_PROMPT
    )

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


def ask_agent(question: str) -> str:
    """
    Ask the agent a question about DBT data

    Args:
        question: The question to ask in natural language

    Returns:
        str: The agent's answer
    """
    try:
        agent = get_agent()
        result = agent.invoke({"messages": [("user", question)]})

        # Extract response
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                return msg.content
            elif hasattr(msg, 'content') and isinstance(msg.content, str):
                return msg.content

        return str(result)

    except KeyboardInterrupt:
        return "Query interrupted by user."
    except TimeoutError:
        return "Query timed out."
    except Exception as e:
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
