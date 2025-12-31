"""A2A MCP Server - Model Context Protocol server for Agent2Agent protocol."""

from .__about__ import __version__
from .server import main, mcp

__all__ = ["__version__", "main", "mcp"]
