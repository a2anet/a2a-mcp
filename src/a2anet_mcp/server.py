"""FastMCP Server implementation for A2A protocol."""

import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from a2a_utils import (
    A2AAgents,
    A2ASession,
    A2ATools,
    ArtifactSettings,
    JSONTaskStore,
    LocalFileStore,
)
from loguru import logger
from mcp.server.fastmcp import FastMCP

from .storage import get_files_dir, get_tasks_dir


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    session: A2ASession


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle."""
    logger.remove()
    logger.add(sys.stderr, format="<level>{message}</level>", level="INFO")

    # Parse required agent cards config
    agent_cards_raw = os.environ.get("A2A_MCP_AGENT_CARDS")
    if not agent_cards_raw:
        logger.error("A2A_MCP_AGENT_CARDS environment variable is required")
        logger.info(
            "Example: export A2A_MCP_AGENT_CARDS='"
            '{"my-agent": {"url": "https://example.com/agent-card.json"}}\''
        )
        raise ValueError("A2A_MCP_AGENT_CARDS environment variable is required")

    try:
        agents_config: dict[str, dict[str, Any]] = json.loads(agent_cards_raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"A2A_MCP_AGENT_CARDS is not valid JSON: {e}") from e

    # Parse optional artifact settings
    artifact_settings = ArtifactSettings(
        send_message_character_limit=int(
            os.environ.get("A2A_MCP_SEND_MESSAGE_CHARACTER_LIMIT", "50000")
        ),
        minimized_object_string_length=int(
            os.environ.get("A2A_MCP_MINIMIZED_OBJECT_STRING_LENGTH", "5000")
        ),
        view_artifact_character_limit=int(
            os.environ.get("A2A_MCP_VIEW_ARTIFACT_CHARACTER_LIMIT", "50000")
        ),
    )

    # Parse timeout settings
    agent_card_timeout = float(os.environ.get("A2A_MCP_AGENT_CARD_TIMEOUT", "15"))
    send_message_timeout = float(os.environ.get("A2A_MCP_SEND_MESSAGE_TIMEOUT", "60"))
    get_task_timeout = float(os.environ.get("A2A_MCP_GET_TASK_TIMEOUT", "60"))
    get_task_poll_interval = float(os.environ.get("A2A_MCP_GET_TASK_POLL_INTERVAL", "5"))

    # Initialize components
    agents = A2AAgents(agents=agents_config, timeout=agent_card_timeout)

    task_store = (
        JSONTaskStore(get_tasks_dir()) if _parse_bool_env("A2A_MCP_TASK_STORE", True) else None
    )
    file_store = (
        LocalFileStore(get_files_dir()) if _parse_bool_env("A2A_MCP_FILE_STORE", True) else None
    )

    session = A2ASession(
        agents,
        task_store=task_store,
        file_store=file_store,
        send_message_timeout=send_message_timeout,
        get_task_timeout=get_task_timeout,
        get_task_poll_interval=get_task_poll_interval,
    )

    # Register A2ATools methods directly as MCP tools
    tools = A2ATools(session, artifact_settings=artifact_settings)
    for tool in tools.tools:
        server.tool()(tool)

    logger.success("A2A MCP Server is ready")

    yield AppContext(session=session)


# Create FastMCP server with lifespan
mcp = FastMCP("a2a-mcp", lifespan=app_lifespan)


def main() -> None:
    """Entry point for the MCP server."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        sys.exit(1)
