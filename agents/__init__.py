"""
Agents package for DBT MCP Server

Contains MCP client and related utilities for connecting to DBT MCP Server.
"""

from .mcp_client import DBTMCPClient, get_mcp_client, close_global_client

__all__ = ["DBTMCPClient", "get_mcp_client", "close_global_client"]
