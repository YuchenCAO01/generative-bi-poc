"""
DBT MCP Client

A Python client for connecting to the DBT MCP Server using the Model Context Protocol.
Implements singleton pattern for global client management with a persistent background
event loop to keep the server alive across Streamlit interactions.
"""

import asyncio
import atexit
import threading
from contextlib import AsyncExitStack
from typing import Optional, Any, Dict, List, Coroutine

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

MCP_TOOL_TIMEOUT_SEC = float(os.getenv("MCP_TOOL_TIMEOUT", "60"))

class DBTMCPClient:
    """
    MCP Client for DBT Server

    Manages connection to DBT MCP Server via stdio, keeping the underlying
    asyncio loop in a dedicated background thread so the server remains
    available for consecutive conversations.
    """

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._connected: bool = False

        # Background event loop management
        self._loop = asyncio.new_event_loop()
        self._loop_ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="dbt-mcp-client-loop",
            daemon=True
        )
        self._thread.start()
        self._loop_ready.wait()

    def _run_loop(self) -> None:
        """Run the asyncio loop on a dedicated thread."""
        asyncio.set_event_loop(self._loop)
        self._loop_ready.set()
        self._loop.run_forever()

    def _submit(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Future:
        """
        Schedule a coroutine on the background loop and return an awaitable
        future tied to the caller's loop.
        """
        concurrent_future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        loop = asyncio.get_running_loop()
        return asyncio.wrap_future(concurrent_future, loop=loop)

    async def connect(self) -> None:
        """Ensure the MCP server connection is established."""
        if self._connected:
            return
        await self._submit(self._connect())

    async def _connect(self) -> None:
        """Coroutine executed on the background loop to open the connection."""
        if self._connected:
            return

        try:
            server_params = StdioServerParameters(
                command="uvx",
                args=["--env-file", "./.env", "dbt-mcp"],
                env=None,
            )

            self.exit_stack = AsyncExitStack()

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            stdio, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            await self.session.initialize()
            self._connected = True
            print("Successfully connected to DBT MCP Server")

            await self._log_available_tools()

        except Exception as exc:
            print(f"Failed to connect to MCP Server: {exc}")
            if self.exit_stack:
                await self.exit_stack.aclose()
                self.exit_stack = None
            raise

    async def _log_available_tools(self) -> None:
        """Log all available tools from the MCP Server."""
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

        except Exception as exc:
            print(f"Failed to list tools: {exc}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call an MCP tool and return the result.

        Args:
            tool_name: Name of the MCP tool to call.
            arguments: Optional dictionary of arguments for the tool.
        """
        if not self._connected:
            await self.connect()
        return await self._submit(self._call_tool(tool_name, arguments or {}))

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self.session:
            raise RuntimeError("MCP session is not initialized.")
        try:
            return await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments=arguments),
                timeout=MCP_TOOL_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError as te:
            raise TimeoutError(f"Tool `{tool_name}` timed out after {MCP_TOOL_TIMEOUT_SEC}s") from te

    async def list_tools(self) -> List[Any]:
        """Return all available tools."""
        if not self._connected:
            await self.connect()
        return await self._submit(self._list_tools())

    async def _list_tools(self) -> List[Any]:
        if not self.session:
            raise RuntimeError("MCP session is not initialized.")

        response = await self.session.list_tools()
        return response.tools

    async def close(self) -> None:
        """Close the MCP connection and cleanup resources."""
        if not self._connected:
            return
        await self._submit(self._close())

    async def _close(self) -> None:
        if not self.exit_stack:
            return

        try:
            await self.exit_stack.aclose()
            print("MCP Server connection closed")
        except Exception as exc:
            print(f"Error closing connection: {exc}")
        finally:
            self.exit_stack = None
            self.session = None
            self._connected = False

    def shutdown(self) -> None:
        """Stop the background event loop and thread."""
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if not self._loop.is_closed():
            self._loop.close()

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_client_instance: Optional[DBTMCPClient] = None


async def get_mcp_client() -> DBTMCPClient:
    """
    Get or create the global MCP client instance.

    Returns:
        DBTMCPClient: Connected MCP client instance.
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = DBTMCPClient()

    if not _client_instance.is_connected:
        await _client_instance.connect()

    return _client_instance


async def close_global_client() -> None:
    """Close and dispose of the global MCP client instance."""
    global _client_instance

    client = _client_instance
    if client is None:
        return

    await client.close()
    client.shutdown()
    _client_instance = None


def close_global_client_sync() -> None:
    """Synchronous helper for closing the global client at interpreter exit."""
    try:
        asyncio.run(close_global_client())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(close_global_client())
        loop.close()


atexit.register(close_global_client_sync)
