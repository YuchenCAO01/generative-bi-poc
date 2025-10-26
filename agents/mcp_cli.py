import os, sys, asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel

# === Configuration Section (keep it simple) ===
# Use environment variable to specify your .env path, or change to hardcoded absolute path
DBT_ENV = os.environ.get("DBT_MCP_ENV", os.path.abspath(".env"))
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")  # Your requested GPT-5 mini

# System prompt: only perform "asset discovery", no database queries/execution
SYSTEM_PROMPT = (
    "You are a dbt metadata guide. Only use MCP's Discovery tools, "
    "strictly prohibited from executing SQL or running any dbt CLI commands. "
    "For each question, output:\n"
    "1) Candidate assets (models/sources, with reasoning)\n"
    "2) Query logic sketch (fact tables/dimension tables, primary/foreign keys, time/dimension granularity)\n"
    "3) Non-executing SQL draft (only using {{ ref() }} / {{ source() }} placeholders)\n"
    "4) Assumptions and risks, metrics that need further confirmation."
)

async def main():
    # Basic checks
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set the OPENAI_API_KEY environment variable first", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(DBT_ENV):
        print(f"❌ Cannot find .env file: {DBT_ENV}\n   Please set the DBT_MCP_ENV environment variable to point to dbt-mcp's .env", file=sys.stderr)
        sys.exit(1)

    # 1) Declare dbt-mcp subprocess to be launched via stdio
    dbt_server = MCPServerStdio(
        "uvx",
        args=["--env-file", DBT_ENV, "dbt-mcp"],
        timeout=30,
    )

    # 2) Specify OpenAI model (GPT-5 mini)
    model = OpenAIModel(OPENAI_MODEL)

    # 3) Create Agent and register dbt-mcp as a toolset
    agent = Agent(model, system_prompt=SYSTEM_PROMPT, toolsets=[dbt_server])

    print("✅ Ready. Enter your question to start the conversation (type /exit to quit)\n")
    async with agent:  # Context memory is preserved within the same session
        while True:
            try:
                user = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Bye")
                break
            if not user:
                continue
            if user in ("/exit", "/quit"):
                print("👋 Bye")
                break

            # 4) Run inference once (model will call dbt-mcp's Discovery tools as needed)
            try:
                result = await agent.run(user)
                print("\nAssistant >\n" + result.output + "\n")
            except Exception as e:
                print(f"❌ Error: {e}\n", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
