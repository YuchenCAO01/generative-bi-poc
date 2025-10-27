# DBT MCP Agents

MCP (Model Context Protocol) client implementations and LangChain-powered intelligent agents for DBT data discovery.

## Overview

This directory contains the core agent logic that enables natural language interaction with DBT metadata through the MCP protocol. The implementation bridges DBT MCP Server with LangChain to create an AI-powered data discovery assistant.

## Components

### Core Files

- **`agent.py`** - LangChain agent with OpenAI GPT-4o-mini for intelligent query routing
- **`mcp_client.py`** - Python MCP client for connecting to DBT MCP Server
- **`agent_direct_mcp.py`** - Direct MCP integration without additional abstractions
- **`test/`** - Test scripts for validating functionality

## Quick Start

### Basic Usage

```python
# Import the agent
from agents.agent import create_agent

# Create an agent instance
agent = create_agent()

# Ask questions in natural language
response = agent.invoke({
    "input": "What models are available in the staging layer?"
})
print(response["output"])
```

### Command Line Interface

```bash
# Run the interactive agent
python agents/mcp_client.py

# Example queries:
# - "List all tables in the project"
# - "Show me the schema of dim_customers"
# - "What are the fact tables?"
```

## Architecture

### Component Flow

```
User Question
    ↓
LangChain Agent (agent.py)
    ↓
MCP Client (mcp_client.py)
    ↓
DBT MCP Server (dbt-mcp)
    ↓
DBT Metadata (BigQuery/Snowflake/etc)
    ↓
Formatted Response
```

### How It Works

1. **User Input**: Natural language question about data assets
2. **Intent Analysis**: LangChain agent analyzes the query intent
3. **Tool Selection**: Agent selects appropriate MCP tools to call
4. **MCP Communication**: Client sends requests to DBT MCP Server
5. **Response Formatting**: Results are formatted into human-readable responses

## MCP Client (`mcp_client.py`)

### Features

- **Async Connection Management**: Handles stdio protocol connections
- **Singleton Pattern**: Global client instance for efficiency
- **Automatic Tool Discovery**: Dynamically discovers available MCP tools
- **Type-Safe Invocation**: Structured tool calling with validation
- **Context Manager Support**: Automatic resource cleanup
- **Error Handling**: Comprehensive error messages and recovery

### Example

```python
import asyncio
from agents.mcp_client import get_mcp_client, close_global_client

async def main():
    # Get global client instance
    client = await get_mcp_client()

    # List available tools
    tools = await client.list_tools()
    print("Available tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Call a tool
    result = await client.call_tool("list", {
        "resource_type": "model"
    })
    print(result.content[0].text)

    # Cleanup
    await close_global_client()

asyncio.run(main())
```

### Available MCP Tools

The DBT MCP Server provides these tools:

| Tool | Description |
|------|-------------|
| `list` | List DBT resources (models, sources, tests, etc.) |
| `show` | Get detailed information about a specific resource |
| `compile` | Compile DBT project to validate syntax |
| `parse` | Parse and validate project structure |
| `run` | Execute DBT models (use with caution) |
| `test` | Run DBT tests |
| `docs` | Generate documentation |

## LangChain Agent (`agent.py`)

### Features

- **Natural Language Understanding**: Processes queries in English
- **Intelligent Tool Routing**: Automatically selects the right MCP tools
- **Context Awareness**: Maintains conversation context
- **Error Recovery**: Graceful handling of tool failures
- **Streaming Support**: Real-time response streaming

### Configuration

The agent uses GPT-4o-mini by default for cost efficiency:

```python
# In agent.py
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True
)
```

To use a different model:

```python
llm = ChatOpenAI(
    model="gpt-4-turbo",  # or "gpt-4", "gpt-3.5-turbo"
    temperature=0
)
```

### System Prompt

The agent is configured with a system prompt that defines its role:

```
You are a data asset discovery assistant that helps users explore
DBT projects using natural language queries. You have access to
MCP tools that can list models, show schemas, and retrieve metadata.

Key capabilities:
- List available models and sources
- Show table schemas and column details
- Explain relationships between models
- Retrieve documentation
```

### Example Usage

```python
from agents.agent import create_agent

# Create agent
agent = create_agent()

# Single query
response = agent.invoke({
    "input": "Show me all dimension tables"
})
print(response["output"])

# Multi-turn conversation
chat_history = []
questions = [
    "List all staging models",
    "Tell me more about stg_customers",
    "What columns does it have?"
]

for question in questions:
    response = agent.invoke({
        "input": question,
        "chat_history": chat_history
    })
    print(f"Q: {question}")
    print(f"A: {response['output']}\n")

    # Update history
    chat_history.append((question, response["output"]))
```

## Direct MCP Integration (`agent_direct_mcp.py`)

A streamlined implementation that directly uses MCP tools without LangChain abstractions. Useful for:

- Custom integrations
- Performance-critical applications
- Learning MCP protocol internals

### Example

```python
from agents.agent_direct_mcp import DirectMCPAgent

async def main():
    agent = DirectMCPAgent()
    await agent.connect()

    # Direct tool call
    models = await agent.list_models()
    print(models)

    # Get model details
    details = await agent.get_model_details("dim_customers")
    print(details)

    await agent.disconnect()
```

## Testing

### Test Directory Structure

```
agents/test/
├── __init__.py
├── test_mcp.py          # MCP client connection tests
└── test_agent.py        # Agent functionality tests
```

### Running Tests

```bash
# Test MCP connection
python -m agents.test.test_mcp

# Test agent responses
python -m agents.test.test_agent

# Run all tests
python -m pytest agents/test/
```

### Writing Tests

```python
# agents/test/test_custom.py
import asyncio
from agents.mcp_client import get_mcp_client, close_global_client

async def test_list_models():
    client = await get_mcp_client()
    result = await client.call_tool("list", {"resource_type": "model"})
    assert result.content[0].text
    await close_global_client()

if __name__ == "__main__":
    asyncio.run(test_list_models())
```

## Configuration

### Environment Variables

Required variables in `.env`:

```bash
# DBT Configuration
DBT_PROJECT_DIR=/path/to/your/dbt/project
DBT_PATH=/path/to/dbt/executable

# Google Cloud (if using BigQuery)
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-credentials.json
GCP_PROJECT=your-project-id
BIGQUERY_DATASET=your_dataset

# OpenAI (for LangChain Agent)
OPENAI_API_KEY=sk-your-openai-api-key
```

### MCP Server Launch

The client automatically launches DBT MCP Server via:

```bash
uvx --env-file .env dbt-mcp
```

This requires `uv` to be installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Best Practices

### Connection Management

```python
# Use context manager for automatic cleanup
async with DBTMCPClient() as client:
    result = await client.call_tool("list", {})

# Or use singleton pattern
client = await get_mcp_client()
try:
    result = await client.call_tool("list", {})
finally:
    await close_global_client()
```

### Error Handling

```python
from agents.agent import create_agent

agent = create_agent()

try:
    response = agent.invoke({
        "input": "Show me non_existent_model"
    })
    print(response["output"])
except Exception as e:
    print(f"Agent error: {e}")
    # Implement fallback logic
```

### Resource Management

```python
import asyncio
from agents.mcp_client import get_mcp_client, close_global_client

async def query_models():
    try:
        client = await get_mcp_client()
        # Your queries here
        result = await client.call_tool("list", {})
        return result
    finally:
        # Always cleanup
        await close_global_client()

# Run with timeout
asyncio.wait_for(query_models(), timeout=30.0)
```

## Advanced Usage

### Custom Tool Creation

Extend the agent with custom tools:

```python
from langchain.tools import tool
from agents.mcp_client import get_mcp_client

@tool
def get_model_lineage(model_name: str) -> str:
    """Get the lineage of a DBT model."""
    async def _execute():
        client = await get_mcp_client()
        # Custom logic using MCP tools
        result = await client.call_tool("show", {
            "resource_type": "model",
            "name": model_name
        })
        # Process and return lineage
        return process_lineage(result)

    return asyncio.run(_execute())

# Add to agent
from agents.agent import create_agent
agent = create_agent(extra_tools=[get_model_lineage])
```

### Streaming Responses

```python
from agents.agent import create_agent

agent = create_agent()

# Stream response chunks
for chunk in agent.stream({"input": "List all models"}):
    if "output" in chunk:
        print(chunk["output"], end="", flush=True)
```

### Multi-Agent Setup

```python
from agents.agent import create_agent

# Discovery agent
discovery_agent = create_agent()

# Analysis agent with different config
analysis_agent = create_agent(
    model="gpt-4",
    temperature=0.3
)

# Use different agents for different tasks
models = discovery_agent.invoke({
    "input": "List dimension tables"
})

analysis = analysis_agent.invoke({
    "input": f"Analyze these models: {models['output']}"
})
```

## Troubleshooting

### Common Issues

**"Failed to connect to MCP Server"**
- Check `.env` file exists with correct `DBT_PROJECT_DIR`
- Verify `uvx` is installed: `which uvx`
- Ensure DBT project is valid: `dbt parse`

**"OPENAI_API_KEY not set"**
- Add key to `.env`: `OPENAI_API_KEY=sk-...`
- Or export: `export OPENAI_API_KEY=sk-...`

**"No module named 'mcp'"**
```bash
pip install mcp
# or
uv pip install mcp
```

**Agent Timeout**
- Increase timeout in agent configuration
- Use simpler queries
- Check MCP server responsiveness

**Tool Not Found**
- Verify MCP server is running
- Check tool name spelling
- List available tools: `client.list_tools()`

## Performance Tips

1. **Reuse Client**: Use singleton pattern to avoid reconnecting
2. **Batch Queries**: Combine multiple questions in one prompt
3. **Cache Results**: Store frequently accessed metadata
4. **Async Operations**: Use `asyncio` for concurrent requests
5. **Model Selection**: Use `gpt-4o-mini` for cost/speed balance

## Development

### Adding New Features

1. **New MCP Tool Wrapper**:
   - Add function in `agent.py` or create new file
   - Decorate with `@tool`
   - Register with agent

2. **Custom Agent Behavior**:
   - Modify system prompt in `agent.py`
   - Adjust temperature/model parameters
   - Add custom prompt templates

3. **Integration with UI**:
   - Import agent in `app.py`
   - Add to Streamlit callbacks
   - Handle streaming responses

## Resources

- [MCP Protocol Docs](https://modelcontextprotocol.io/)
- [DBT MCP Server](https://github.com/jonnycrunch/dbt-mcp)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [OpenAI API Reference](https://platform.openai.com/docs/)

## License

Same as parent project (MIT License)
