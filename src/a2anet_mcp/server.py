"""FastMCP Server implementation for A2A protocol."""

import dataclasses
import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

from a2a_utils import (
    A2ASession,
    AgentManager,
    ArtifactSettings,
    JSONTaskStore,
    LocalFileStore,
)
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from .storage import get_files_dir, get_tasks_dir


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    agent_manager: AgentManager
    session: A2ASession


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


def _serialize_for_json(obj: Any) -> Any:
    """Recursively convert frozen dataclasses and enums to JSON-safe values."""
    if isinstance(obj, Enum):
        return obj.value
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialize_for_json(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    return obj


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

    # Initialize components
    agent_manager = AgentManager(agents=agents_config)

    task_store = (
        JSONTaskStore(get_tasks_dir()) if _parse_bool_env("A2A_MCP_TASK_STORE", True) else None
    )
    file_store = (
        LocalFileStore(get_files_dir()) if _parse_bool_env("A2A_MCP_FILE_STORE", True) else None
    )

    session = A2ASession(
        agent_manager,
        task_store=task_store,
        file_store=file_store,
        artifact_settings=artifact_settings,
    )

    logger.success("A2A MCP Server is ready")

    yield AppContext(agent_manager=agent_manager, session=session)


# Create FastMCP server with lifespan
mcp = FastMCP("a2a-mcp", lifespan=app_lifespan)


@mcp.tool()
async def send_message(
    agent_id: str,
    message: str,
    ctx: Context[ServerSession, AppContext],
    context_id: str | None = None,
    task_id: str | None = None,
) -> str:
    """Send a message to an A2A agent and receive a structured response.

    The response includes the agent's reply and any generated artifacts
    in a structured format.

    NOTE: Artifact data in responses might have been minimised for display.
    Fields prefixed with "_" indicate metadata values for the Artifact that
    has been minimised. Use the view_*_artifact tools to access full artifact data.

    Args:
        agent_id: ID of the agent to send message to.
            Use get_agents to see all available agents.
        message: The message content to send to the agent.
        ctx: MCP context (automatically injected)
        context_id: Optional context ID to continue an existing conversation.
            Omit to start a new conversation.
        task_id: Optional task ID to attach to the message.
            Use this for input_required flows.

    Returns:
        JSON string with a TaskForLLM or MessageForLLM response.
    """
    app = ctx.request_context.lifespan_context

    try:
        result = await app.session.send_message(
            agent_id, message, context_id=context_id, task_id=task_id
        )
        return json.dumps(_serialize_for_json(result), indent=2)
    except Exception as e:
        return json.dumps({"error": True, "error_message": str(e)}, indent=2)


@mcp.tool()
async def get_agents(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """List all available A2A agents with their names and descriptions.

    Use this to discover what agents are available before sending messages.

    Args:
        ctx: MCP context (automatically injected)

    Returns:
        JSON string with agents and their basic information.
    """
    app = ctx.request_context.lifespan_context

    try:
        result = await app.agent_manager.get_agents_for_llm(detail="basic")
        init_errors = app.agent_manager.initialization_errors
        if not result and init_errors:
            return json.dumps(
                {
                    "agents": result,
                    "errors": {
                        agent_id: f"Failed to load agent: {error}"
                        for agent_id, error in init_errors.items()
                    },
                },
                indent=2,
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": True, "error_message": str(e)}, indent=2)


@mcp.tool()
async def get_agent(
    agent_id: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Get detailed information about a specific A2A agent including skills.

    Args:
        agent_id: ID of the agent to get information about.
        ctx: MCP context (automatically injected)

    Returns:
        JSON string with agent name, description, and skills with descriptions.
    """
    app = ctx.request_context.lifespan_context

    try:
        result = await app.agent_manager.get_agent_for_llm(agent_id, detail="full")
        if result is None:
            return json.dumps(
                {"error": True, "error_message": f"Agent '{agent_id}' not found"},
                indent=2,
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": True, "error_message": str(e)}, indent=2)


@mcp.tool()
async def view_text_artifact(
    agent_id: str,
    task_id: str,
    artifact_id: str,
    ctx: Context[ServerSession, AppContext],
    line_start: int | None = None,
    line_end: int | None = None,
    character_start: int | None = None,
    character_end: int | None = None,
) -> str:
    """View text content from an artifact with optional line or character range.

    Use this tool for artifacts containing text content (documents, logs, etc.).
    Line and character selection are mutually exclusive.

    Args:
        agent_id: ID of the agent that produced the artifact.
        task_id: Task ID containing the artifact.
        artifact_id: Unique identifier of the artifact to view.
        ctx: MCP context (automatically injected)
        line_start: Starting line number (1-based, inclusive).
        line_end: Ending line number (1-based, inclusive).
        character_start: Starting character index (0-based, inclusive).
        character_end: Ending character index (0-based, exclusive).

    Returns:
        JSON string with ArtifactForLLM containing the text content.
    """
    app = ctx.request_context.lifespan_context

    try:
        result = await app.session.view_text_artifact(
            agent_id,
            task_id,
            artifact_id,
            line_start=line_start,
            line_end=line_end,
            character_start=character_start,
            character_end=character_end,
        )
        return json.dumps(_serialize_for_json(result), indent=2)
    except Exception as e:
        return json.dumps({"error": True, "error_message": str(e)}, indent=2)


@mcp.tool()
async def view_data_artifact(
    agent_id: str,
    task_id: str,
    artifact_id: str,
    ctx: Context[ServerSession, AppContext],
    json_path: str | None = None,
    rows: Union[int, list[int], str, None] = None,
    columns: Union[str, list[str], None] = None,
) -> str:
    """View structured data from an artifact with optional filtering.

    Use this tool for artifacts containing JSON data (objects, arrays, etc.).

    Args:
        agent_id: ID of the agent that produced the artifact.
        task_id: Task ID containing the artifact.
        artifact_id: Unique identifier of the artifact to view.
        ctx: MCP context (automatically injected)
        json_path: Dot-separated path to extract specific fields.
        rows: Row selection (index, list, range string, or "all").
        columns: Column selection (name, list, or "all").

    Returns:
        JSON string with ArtifactForLLM containing the data content.
    """
    app = ctx.request_context.lifespan_context

    try:
        result = await app.session.view_data_artifact(
            agent_id,
            task_id,
            artifact_id,
            json_path=json_path,
            rows=rows,
            columns=columns,
        )
        return json.dumps(_serialize_for_json(result), indent=2)
    except Exception as e:
        return json.dumps({"error": True, "error_message": str(e)}, indent=2)


def main() -> None:
    """Entry point for the MCP server."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        sys.exit(1)
