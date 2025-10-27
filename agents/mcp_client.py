"""
DBT MCP Client

A Python client for connecting to the DBT MCP Server using the Model Context Protocol.
Implements singleton pattern for global client management.
"""

import asyncio
from typing import Optional, Any, Dict, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class DBTMCPClient:
    """
    MCP Client for DBT Server

    Manages connection to DBT MCP Server via stdio and provides
    methods to interact with available tools.
    """

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._connected: bool = False

    async def connect(self) -> None:
        """
        Connect to the DBT MCP Server

        Establishes stdio connection and initializes the session.
        Prints available tools after successful connection.

        Raises:
            Exception: If connection fails or server is unreachable
        """
        if self._connected:
            print("Already connected to MCP Server")
            return

        try:
            # Configure server parameters for stdio communication
            server_params = StdioServerParameters(
                command="uvx",
                args=["--env-file", "./.env", "dbt-mcp"],
                env=None
            )

            # Create exit stack for resource management
            self.exit_stack = AsyncExitStack()

            # Connect to server via stdio
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # Create and initialize session
            stdio, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize the session
            await self.session.initialize()

            self._connected = True
            print("Successfully connected to DBT MCP Server")

            # List available tools
            await self._list_available_tools()

        except Exception as e:
            print(f"Failed to connect to MCP Server: {e}")
            if self.exit_stack:
                await self.exit_stack.aclose()
                self.exit_stack = None
            raise

    async def _list_available_tools(self) -> None:
        """Print all available tools from the MCP Server"""
        if not self.session:
            return

        try:
            response = await self.session.list_tools()
            tools = response.tools

            print(f"\nAvailable Tools ({len(tools)}):")
            print("-" * 60)
            for tool in tools:
                print(f"  • {tool.name}")
                if tool.description:
                    print(f"    {tool.description}")
            print("-" * 60)

        except Exception as e:
            print(f"Failed to list tools: {e}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            RuntimeError: If not connected to server
            Exception: If tool call fails
        """
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP Server. Call connect() first.")

        try:
            result = await self.session.call_tool(
                tool_name,
                arguments=arguments or {}
            )
            return result

        except Exception as e:
            print(f"Failed to call tool '{tool_name}': {e}")
            raise

    async def list_tools(self) -> List[Any]:
        """
        Get list of available tools

        Returns:
            List of tool objects

        Raises:
            RuntimeError: If not connected to server
        """
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP Server. Call connect() first.")

        response = await self.session.list_tools()
        return response.tools

    async def close(self) -> None:
        """
        Close the MCP Server connection

        Properly cleans up resources and closes the session.
        """
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
                print("MCP Server connection closed")
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.exit_stack = None
                self.session = None
                self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected"""
        return self._connected

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Singleton instance
_client_instance: Optional[DBTMCPClient] = None


async def get_mcp_client() -> DBTMCPClient:
    """
    Get the global MCP client instance (singleton pattern)

    Creates a new client if none exists, otherwise returns the existing instance.
    Automatically connects if not already connected.

    Returns:
        DBTMCPClient: Connected MCP client instance

    Example:
        ```python
        client = await get_mcp_client()
        result = await client.call_tool("list_models")
        ```
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = DBTMCPClient()

    if not _client_instance.is_connected:
        await _client_instance.connect()

    return _client_instance


async def close_global_client() -> None:
    """
    Close the global MCP client instance

    Should be called at application shutdown to properly clean up resources.
    """
    global _client_instance

    if _client_instance is not None:
        await _client_instance.close()
        _client_instance = None
