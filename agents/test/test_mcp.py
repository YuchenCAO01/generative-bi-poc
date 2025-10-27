"""
Test MCP Connection

Validates the connection to DBT MCP Server and tests basic functionality.
"""

import asyncio
import sys
from typing import Any

from agents.mcp_client import get_mcp_client, close_global_client


async def test_connection() -> None:
    """
    Test the MCP Server connection

    Performs the following tests:
    1. Connect to MCP Server
    2. List all available tools
    3. Test a discovery tool call
    4. Close the connection
    """
    print("\n" + "=" * 80)
    print("  DBT MCP Server Connection Test")
    print("=" * 80 + "\n")

    client = None

    try:
        # Step 1: Connect to MCP Server
        print("[1/4] Connecting to MCP Server...")
        print("-" * 80)

        client = await get_mcp_client()

        if not client.is_connected:
            print("Failed to connect to MCP Server")
            return

        print("\n")

        # Step 2: List available tools
        print("[2/4] Listing available tools...")
        print("-" * 80)

        tools = await client.list_tools()

        if not tools:
            print("No tools available from MCP Server")
            return

        print(f"\nFound {len(tools)} tools:\n")
        for idx, tool in enumerate(tools, 1):
            print(f"{idx:2d}. {tool.name}")
            if tool.description:
                # Indent description
                desc_lines = tool.description.split('\n')
                for line in desc_lines:
                    if line.strip():
                        print(f"     {line}")
            print()

        # Step 3: Test a tool call
        print("\n[3/4] Testing tool call...")
        print("-" * 80)

        # Try to find a discovery or list tool to test
        test_tool = None
        test_args = {}

        # Look for discovery-related tools first
        for tool in tools:
            if 'discovery' in tool.name.lower() or 'list' in tool.name.lower():
                test_tool = tool.name
                break

        # If no discovery tool, try models-related tools
        if not test_tool:
            for tool in tools:
                if 'model' in tool.name.lower():
                    test_tool = tool.name
                    break

        # Fallback to first available tool
        if not test_tool and tools:
            test_tool = tools[0].name

        if test_tool:
            print(f"\nTesting tool: {test_tool}")
            print(f"Arguments: {test_args if test_args else 'None'}\n")

            try:
                result = await client.call_tool(test_tool, test_args)

                print("Tool call successful!")
                print(f"\nResult type: {type(result)}")
                print(f"\nResult:\n{result}")

            except Exception as e:
                print(f"Tool call failed: {e}")
                print("This may be expected if the tool requires specific arguments")
        else:
            print("No suitable tool found for testing")

        # Step 4: Connection info
        print("\n[4/4] Connection status")
        print("-" * 80)
        print(f"Connected: {client.is_connected}")
        print(f"Session active: {client.session is not None}")

        print("\n" + "=" * 80)
        print("  Test completed successfully!")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 80)
        print("  ERROR: Test failed!")
        print("=" * 80)
        print(f"\nError type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\nPlease ensure:")
        print("  1. DBT MCP Server is properly configured")
        print("  2. .env file exists with correct credentials")
        print("  3. Required dependencies are installed (pip install mcp)")
        print("  4. uvx is available in your PATH")
        print("\n" + "=" * 80 + "\n")
        sys.exit(1)

    finally:
        # Clean up
        if client:
            print("\nClosing connection...")
            await close_global_client()


async def test_specific_tool(tool_name: str, arguments: dict = None) -> Any:
    """
    Test a specific MCP tool

    Args:
        tool_name: Name of the tool to test
        arguments: Arguments to pass to the tool

    Returns:
        Tool execution result
    """
    print(f"\nTesting tool: {tool_name}")
    print("=" * 80)

    try:
        client = await get_mcp_client()
        result = await client.call_tool(tool_name, arguments)

        print(f"\nSuccess! Result:\n{result}\n")
        return result

    except Exception as e:
        print(f"\nError: {e}\n")
        raise
    finally:
        await close_global_client()


if __name__ == "__main__":
    """
    Run the MCP connection test

    Usage:
        python test_mcp.py              # Run full connection test
        python test_mcp.py <tool_name>  # Test specific tool
    """

    if len(sys.argv) > 1:
        # Test specific tool
        tool_name = sys.argv[1]
        args = {}

        # Parse additional arguments if provided (as key=value pairs)
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                args[key] = value

        asyncio.run(test_specific_tool(tool_name, args))
    else:
        # Run full test suite
        asyncio.run(test_connection())
