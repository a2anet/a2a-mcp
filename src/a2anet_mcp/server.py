"""MCP Server implementation for A2A protocol."""

import json
import uuid
from typing import Any, Optional

from a2a.types import (
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageSuccessResponse,
    TextPart,
)
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .agent_manager import AgentManager
from .artifact_filter import ArtifactFilter
from .conversation_manager import ConversationManager

# Global instances (initialized in setup)
agent_manager: Optional[AgentManager] = None
conversation_manager: Optional[ConversationManager] = None


def create_server() -> Server:
    """Create and configure the MCP server.

    Returns:
        Configured MCP Server instance
    """
    server = Server("a2a-mcp")

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_tools() -> list[Tool]:
        """List available MCP tools.

        Returns:
            List of tool definitions
        """
        return [
            Tool(
                name="send_message_to_agent",
                description=(
                    "Send a message to an A2A agent and receive a structured response with task information, "
                    "agent messages, and artifacts. The response includes task tracking (task_id, context_id, state), "
                    "the agent's reply, and any generated artifacts in a structured format.\n\n"
                    "Examples:\n"
                    "1. Start a new conversation:\n"
                    '   send_message_to_agent(agent_name="Twitter Agent", message="Find tweets about AI from last week")\n\n'
                    "2. Continue an existing conversation:\n"
                    '   send_message_to_agent(agent_name="Twitter Agent", message="Filter those to show only verified accounts", '
                    'context_id="abc-123-def")\n\n'
                    "3. Ask for data analysis:\n"
                    '   send_message_to_agent(agent_name="Analytics Agent", message="Analyze the sales data for Q4 2024")\n\n'
                    "The response will be a structured object containing:\n"
                    "- task_id: Unique identifier for this task\n"
                    "- context_id: Conversation thread identifier (use this for follow-up messages)\n"
                    "- task_state: Current state (completed, input-required, failed, etc.)\n"
                    "- agent_message: The agent's text response\n"
                    "- artifacts: List of generated artifacts (with previews for large data)\n\n"
                    "Use view_artifact to access full artifact content or apply filters."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to send message to. Use list_available_agents to see all available agents.",
                        },
                        "message": {
                            "type": "string",
                            "description": "The message content to send to the agent. Can be a question, command, or request.",
                        },
                        "context_id": {
                            "type": "string",
                            "description": (
                                "Optional context ID to continue an existing conversation. "
                                "When provided, the agent can access previous messages in the conversation. "
                                "Omit this parameter to start a new conversation (a new context_id will be generated)."
                            ),
                        },
                    },
                    "required": ["agent_name", "message"],
                },
            ),
            Tool(
                name="view_artifact",
                description=(
                    "View and filter artifacts returned by A2A agents. Artifacts are structured outputs like data tables, "
                    "documents, or analysis results. This tool supports powerful filtering to extract specific information "
                    "without retrieving the entire artifact.\n\n"
                    "Filter Types:\n"
                    "- none: Return the complete artifact without filtering\n"
                    "- regex: Apply regex pattern matching to text or JSON data\n"
                    "- json_path: Extract specific fields using JSON path notation (supports nested access)\n"
                    "- field: Extract a single top-level field from the artifact\n\n"
                    "Examples:\n"
                    "1. View full artifact:\n"
                    '   view_artifact(agent_name="Twitter Agent", context_id="xyz-789", artifact_id="art-123")\n\n'
                    "2. Extract usernames with regex:\n"
                    '   view_artifact(agent_name="Twitter Agent", context_id="xyz-789", artifact_id="art-123", '
                    'filter_type="regex", filter_value="@\\\\w+")\n\n'
                    "3. Get specific field with JSON path:\n"
                    '   view_artifact(agent_name="Analytics Agent", context_id="abc-456", artifact_id="art-789", '
                    'filter_type="json_path", filter_value="results[0].metrics.revenue")\n\n'
                    "4. Extract top-level field:\n"
                    '   view_artifact(agent_name="Data Agent", context_id="def-012", artifact_id="art-345", '
                    'filter_type="field", filter_value="summary")\n\n'
                    "5. Get all tweet texts:\n"
                    '   view_artifact(agent_name="Twitter Agent", context_id="xyz-789", artifact_id="art-123", '
                    'filter_type="json_path", filter_value="tweets[*].text")'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent that created the artifact",
                        },
                        "context_id": {
                            "type": "string",
                            "description": "Context ID of the conversation (obtained from send_message_to_agent response)",
                        },
                        "artifact_id": {
                            "type": "string",
                            "description": "Unique identifier of the artifact to view (shown in send_message_to_agent response)",
                        },
                        "filter_type": {
                            "type": "string",
                            "enum": ["none", "regex", "json_path", "field"],
                            "description": (
                                "Type of filter to apply:\n"
                                "- 'none': Return full artifact\n"
                                "- 'regex': Apply regex pattern (use for text search/extraction)\n"
                                "- 'json_path': Extract fields using path notation (e.g., 'data[0].name' or 'items[*].price')\n"
                                "- 'field': Get top-level field only"
                            ),
                        },
                        "filter_value": {
                            "type": "string",
                            "description": (
                                "The filter pattern or path to apply (required unless filter_type is 'none').\n"
                                "Examples: '@\\\\w+' for regex, 'records[0].author.name' for json_path, 'data' for field"
                            ),
                        },
                    },
                    "required": ["agent_name", "context_id", "artifact_id"],
                },
            ),
            Tool(
                name="list_available_agents",
                description=(
                    "List all available A2A agents with their metadata including names, descriptions, and capabilities. "
                    "Use this tool to discover what agents are available before sending messages.\n\n"
                    "The response returns a structured object for each agent containing:\n"
                    "- name: The agent's display name (use this with send_message_to_agent)\n"
                    "- description: What the agent does and its purpose\n"
                    "- skills: List of specific capabilities the agent provides\n\n"
                    "Example:\n"
                    "  list_available_agents()\n\n"
                    "This is useful when you need to:\n"
                    "- Find the right agent for a specific task\n"
                    "- Discover what capabilities are available\n"
                    "- Get the exact agent name to use in send_message_to_agent calls"
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool execution.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of text content results

        Raises:
            ValueError: If tool is unknown or arguments are invalid
        """
        if name == "send_message_to_agent":
            return await handle_send_message_to_agent(arguments)
        elif name == "view_artifact":
            return await handle_view_artifact(arguments)
        elif name == "list_available_agents":
            return await handle_list_available_agents()
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


async def handle_send_message_to_agent(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle send_message_to_agent tool call.

    Args:
        arguments: Tool arguments containing agent_name, message, and optional context_id

    Returns:
        List containing a single TextContent with the response
    """
    if not agent_manager or not conversation_manager:
        return [TextContent(type="text", text="Error: Server not initialized")]

    agent_name = arguments.get("agent_name")
    message = arguments.get("message")
    context_id = arguments.get("context_id")

    if not agent_name or not message:
        return [
            TextContent(
                type="text",
                text="Error: Both 'agent_name' and 'message' parameters are required",
            )
        ]

    # Get agent
    agent_info = agent_manager.get_agent(agent_name)
    if not agent_info:
        available = ", ".join(agent_manager.list_agents())
        return [
            TextContent(
                type="text",
                text=f"Error: Agent '{agent_name}' not found. Available agents: {available}",
            )
        ]

    # Get or create conversation
    conversation = conversation_manager.get_or_create_conversation(
        agent_name=agent_name, context_id=context_id
    )

    # Build message
    a2a_message = Message(
        context_id=conversation.context_id,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
        role=Role.user,
    )

    # Include task_id if needed
    if conversation.requires_task_id and conversation.task_id:
        a2a_message.task_id = conversation.task_id

    # Send message
    try:
        send_request = SendMessageRequest(
            id=str(uuid.uuid4()), params=MessageSendParams(message=a2a_message)
        )

        # Build headers
        http_kwargs = {}
        if agent_info.custom_headers:
            http_kwargs["headers"] = agent_info.custom_headers

        response = await agent_info.client.send_message(
            request=send_request, http_kwargs=http_kwargs if http_kwargs else None
        )

        # Parse response - SendMessageResponse is a RootModel wrapping the actual response
        actual_response = response.root if hasattr(response, "root") else response

        # Check if the response is an error
        if isinstance(actual_response, JSONRPCErrorResponse):
            error_info = actual_response.error
            error_msg = {
                "error": True,
                "error_code": error_info.code,
                "error_message": error_info.message,
                "context_id": conversation.context_id,
            }
            if error_info.data:
                error_msg["error_data"] = error_info.data
            return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]

        # Handle success response
        if not isinstance(actual_response, SendMessageSuccessResponse):
            return [
                TextContent(
                    type="text",
                    text=f"Error: Unexpected response type: {type(actual_response).__name__}",
                )
            ]

        # Extract task from the response
        task = actual_response.result

        # Update conversation state
        conversation_manager.update_from_task(conversation, task)

        # Extract agent's message
        agent_message = ""
        if task.history:
            for msg in reversed(task.history):
                if msg.role == "agent":
                    for part in msg.parts:
                        if isinstance(part.root, TextPart):
                            agent_message = part.root.text
                            break
                if agent_message:
                    break

        # Build structured response
        minimized_artifacts = list(conversation.minimized_artifacts.values())
        response_obj = {
            "task_id": task.id,
            "context_id": conversation.context_id,
            "task_state": task.status.state.value,
            "agent_message": agent_message,
            "artifacts": minimized_artifacts,
        }

        # Add tips section
        tips = []
        if minimized_artifacts:
            tips.append(
                "Use view_artifact to see full artifact content or apply filters (regex, json_path, field)"
            )
        if task.status.state.value == "input-required":
            tips.append(
                f"The agent needs more information. Continue the conversation using context_id: {conversation.context_id}"
            )
        elif task.status.state.value == "completed":
            tips.append(
                "Task completed successfully. You can start a new conversation or view artifacts for details."
            )

        if tips:
            response_obj["tips"] = tips

        return [TextContent(type="text", text=json.dumps(response_obj, indent=2))]

    except Exception as e:
        error_msg = f"Error sending message: {type(e).__name__}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def handle_view_artifact(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle view_artifact tool call.

    Args:
        arguments: Tool arguments containing agent_name, context_id, artifact_id, and optional filters

    Returns:
        List containing a single TextContent with the filtered artifact
    """
    if not conversation_manager:
        return [TextContent(type="text", text="Error: Server not initialized")]

    agent_name = arguments.get("agent_name")
    context_id = arguments.get("context_id")
    artifact_id = arguments.get("artifact_id")
    filter_type = arguments.get("filter_type")
    filter_value = arguments.get("filter_value")

    if not agent_name or not context_id or not artifact_id:
        return [
            TextContent(
                type="text",
                text="Error: 'agent_name', 'context_id', and 'artifact_id' are required",
            )
        ]

    # Get conversation
    conversation = conversation_manager.get_conversation(agent_name, context_id)
    if not conversation:
        return [
            TextContent(
                type="text",
                text=f"Error: No conversation found for agent '{agent_name}' with context '{context_id}'",
            )
        ]

    # Get artifact
    artifact = conversation.artifacts.get(artifact_id)
    if not artifact:
        available = ", ".join(conversation.artifacts.keys())
        return [
            TextContent(
                type="text",
                text=f"Error: Artifact '{artifact_id}' not found. Available: {available}",
            )
        ]

    # Apply filter
    try:
        filtered_result = ArtifactFilter.filter_artifact(
            artifact=artifact, filter_type=filter_type, filter_value=filter_value
        )

        # Add tips based on filter type
        tips = []
        if not filter_type or filter_type == "none":
            tips.append(
                "Use filter_type='regex' to search for patterns, 'json_path' to extract fields, or 'field' for top-level fields"
            )
        elif filter_type == "json_path":
            tips.append(
                "Try accessing nested fields with paths like 'data[0].field' or 'items[*].name'"
            )
        elif filter_type == "regex":
            tips.append(
                "Regex patterns are applied to the entire artifact. Use capturing groups to extract specific parts."
            )

        response_obj = {**filtered_result, "tips": tips} if tips else filtered_result

        return [TextContent(type="text", text=json.dumps(response_obj, indent=2))]
    except Exception as e:
        error_msg = f"Error filtering artifact: {type(e).__name__}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def handle_list_available_agents() -> list[TextContent]:
    """Handle list_available_agents tool call.

    Returns:
        List containing a single TextContent with agent information as JSON
    """
    if not agent_manager:
        return [TextContent(type="text", text="Error: Server not initialized")]

    # Build structured list of agents
    agents_list = []
    for name in sorted(agent_manager.list_agents()):
        agent = agent_manager.get_agent(name)
        if agent:
            agents_list.append(
                {
                    "name": name,
                    "description": agent.description,
                    "skills": agent.skills if agent.skills else [],
                    "url": agent.url,
                }
            )

    response_obj = {"agents": agents_list, "count": len(agents_list)}

    # Add tips
    if agents_list:
        response_obj["tips"] = [
            "Use the agent name exactly as shown when calling send_message_to_agent",
            "Check the skills list to understand what each agent can do",
        ]

    return [TextContent(type="text", text=json.dumps(response_obj, indent=2))]


def run_server() -> None:
    """Run the MCP server using stdio transport."""
    server = create_server()

    async def main() -> None:
        """Main server entry point."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    import asyncio

    asyncio.run(main())
