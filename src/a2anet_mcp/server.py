"""FastMCP Server implementation for A2A protocol."""

import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Union

import httpx
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from .core.agents import AgentManager
from .core.config import A2AMCPConfig
from .core.conversation import ConversationManager
from .tools.artifacts import (
    handle_view_data_artifact,
    handle_view_text_artifact,
)
from .tools.discovery import handle_list_available_agents
from .tools.messaging import handle_send_message_to_agent


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    agent_manager: AgentManager
    conversation_manager: ConversationManager
    httpx_client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle.

    Initializes:
    - Configuration from environment
    - HTTP client
    - Agent manager with agent cards
    - Conversation manager with persistence

    Yields:
        AppContext with all initialized dependencies
    """
    # Configure loguru to output to stderr
    logger.remove()
    logger.add(sys.stderr, format="<level>{message}</level>", level="INFO")

    # Load configuration from environment
    try:
        config = A2AMCPConfig.from_env()
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        logger.info("Please set the A2A_AGENT_CARDS environment variable.")
        logger.info(
            'Example: export A2A_AGENT_CARDS=\'[{"url": "https://example.com/agent-card.json"}]\''
        )
        raise

    # Initialize HTTP client
    httpx_client = httpx.AsyncClient(timeout=300.0)

    try:
        # Initialize agent manager
        agent_manager = AgentManager(httpx_client)
        await agent_manager.initialize_agents(config.agent_cards)

        if not agent_manager.agents:
            logger.error("No agents were successfully initialized")
            raise RuntimeError("No agents were successfully initialized")

        # Initialize conversation manager
        conversation_manager = ConversationManager()

        logger.success("A2A MCP Server is ready")

        yield AppContext(
            agent_manager=agent_manager,
            conversation_manager=conversation_manager,
            httpx_client=httpx_client,
        )
    finally:
        await httpx_client.aclose()


# Create FastMCP server with lifespan
mcp = FastMCP("a2a-mcp", lifespan=app_lifespan)


@mcp.tool()
async def send_message_to_agent(
    agent_name: str,
    message: str,
    ctx: Context[ServerSession, AppContext],
    context_id: str | None = None,
) -> str:
    """Send a message to an A2A agent and receive a structured response.

    The response includes the agent's reply and any generated artifacts
    in a structured format.

    NOTE: Artifact data in responses might have been minimised for display.
    Fields prefixed with "_" indicate metadata values for the Artifact that
    has been minimised. Use the view_*_artifact tools to access full artifact data.

    Args:
        agent_name: Name of the agent to send message to.
            Use list_available_agents to see all available agents.
        message: The message content to send to the agent.
            Can be a question, command, or request.
        ctx: MCP context (automatically injected)
        context_id: Optional context ID to continue an existing conversation.
            When provided, the agent can access previous messages.
            Omit to start a new conversation (a new context_id will be generated).

    Returns:
        JSON string with context_id, agent_message, and artifacts.

    Examples:
        Start a new conversation:
            send_message_to_agent(agent_name="Twitter Agent",
                                  message="Find tweets about AI from last week")

        Continue an existing conversation:
            send_message_to_agent(agent_name="Twitter Agent",
                                  message="Filter those to show only verified accounts",
                                  context_id="abc-123-def")
    """
    app = ctx.request_context.lifespan_context

    result = await handle_send_message_to_agent(
        agent_manager=app.agent_manager,
        conversation_manager=app.conversation_manager,
        agent_name=agent_name,
        message=message,
        context_id=context_id,
    )

    return json.dumps(result, indent=2)


@mcp.tool()
async def view_text_artifact(
    context_id: str,
    artifact_id: str,
    ctx: Context[ServerSession, AppContext],
    line_start: int | None = None,
    line_end: int | None = None,
) -> str:
    """View text content from an artifact with optional line range selection.

    Use this tool for artifacts containing text content (documents, logs, etc.).
    Use line_start/line_end to view specific sections if the content is too large.

    Args:
        context_id: Context ID of the conversation
            (obtained from send_message_to_agent response)
        artifact_id: Unique identifier of the artifact to view
            (shown in send_message_to_agent response)
        ctx: MCP context (automatically injected)
        line_start: Starting line number (1-based, inclusive).
            Use negative numbers to count from end (-1 = last line).
            Omit to start from the beginning.
        line_end: Ending line number (1-based, inclusive).
            Use negative numbers to count from end (-1 = last line).
            Omit to read to the end.

    Returns:
        JSON string with text content including artifact_id, name, total_lines,
        total_characters, line_range, and text.

    Examples:
        View full artifact:
            view_text_artifact(context_id="xyz-789", artifact_id="art-123")

        View first 10 lines:
            view_text_artifact(context_id="xyz-789", artifact_id="art-123",
                              line_start=1, line_end=10)

        View last 20 lines:
            view_text_artifact(context_id="xyz-789", artifact_id="art-123",
                              line_start=-20)
    """
    app = ctx.request_context.lifespan_context

    result = await handle_view_text_artifact(
        conversation_manager=app.conversation_manager,
        context_id=context_id,
        artifact_id=artifact_id,
        line_start=line_start,
        line_end=line_end,
    )

    return json.dumps(result, indent=2)


@mcp.tool()
async def view_data_artifact(
    context_id: str,
    artifact_id: str,
    ctx: Context[ServerSession, AppContext],
    json_path: str | None = None,
    rows: Union[int, list[int], str, None] = None,
    columns: Union[str, list[str], None] = None,
) -> str:
    """View structured data from an artifact with optional filtering.

    Use this tool for artifacts containing JSON data (objects, arrays, etc.).
    Use json_path, rows, and/or columns to access specific data if the content
    is too large.

    Args:
        context_id: Context ID of the conversation
            (obtained from send_message_to_agent response)
        artifact_id: Unique identifier of the artifact to view
            (shown in send_message_to_agent response)
        ctx: MCP context (automatically injected)
        json_path: Optional dot-separated path to extract specific fields.
            Supports nested field access only (no array indexing).
            Examples: "field", "field.nested", "data.users"
            Use the rows/columns parameters to filter list data.
        rows: Optional row selection for list data. Can be:
            - A single row index (e.g., 0 for first row, -1 for last)
            - A list of indices (e.g., [0, 1, 5])
            - A range string (e.g., "0-10" for first 10 rows)
            - "all" for all rows
        columns: Optional column selection for lists of objects. Can be:
            - A single column name (e.g., "name")
            - A list of column names (e.g., ["name", "email"])
            - "all" for all columns

    Returns:
        JSON string with data content including artifact_id, name, and data.
        For tabular data with row/column filtering, also includes total_rows,
        total_columns, selected_rows, selected_columns, and available_columns.

    Examples:
        View full data:
            view_data_artifact(context_id="xyz-789", artifact_id="art-123")

        Navigate to nested field and filter rows/columns:
            view_data_artifact(context_id="xyz-789", artifact_id="art-123",
                              json_path="data.users", rows="0-10",
                              columns=["id", "name", "email"])

        View first 5 rows of tabular data:
            view_data_artifact(context_id="xyz-789", artifact_id="art-123",
                              rows="0-5", columns="all")
    """
    app = ctx.request_context.lifespan_context

    result = await handle_view_data_artifact(
        conversation_manager=app.conversation_manager,
        context_id=context_id,
        artifact_id=artifact_id,
        json_path=json_path,
        rows=rows,
        columns=columns,
    )

    return json.dumps(result, indent=2)


@mcp.tool()
async def list_available_agents(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """List all available A2A agents with their metadata.

    Returns a structured list of agents including names, descriptions,
    and capabilities. Use this to discover what agents are available
    before sending messages.

    Args:
        ctx: MCP context (automatically injected)

    Returns:
        JSON string with agents array containing name, description, skills, and url.

    Example:
        list_available_agents()

    This is useful when you need to:
        - Find the right agent for a specific task
        - Discover what capabilities are available
        - Get the exact agent name to use in send_message_to_agent calls
    """
    app = ctx.request_context.lifespan_context

    result = await handle_list_available_agents(
        agent_manager=app.agent_manager,
    )

    return json.dumps(result, indent=2)


def main() -> None:
    """Entry point for the MCP server.

    Runs the server using stdio transport by default.
    """
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        sys.exit(1)
