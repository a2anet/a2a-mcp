"""Message sending tool handler for A2A MCP Server."""

import uuid
from typing import Any

from a2a.types import (
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageSuccessResponse,
    Task,
    TextPart,
)

from ..core.agents import AgentManager
from ..core.conversation import ConversationManager, minimize_artifacts


async def handle_send_message_to_agent(
    agent_manager: AgentManager,
    conversation_manager: ConversationManager,
    agent_name: str,
    message: str,
    context_id: str | None = None,
) -> dict[str, Any]:
    """Handle send_message_to_agent tool call.

    Args:
        agent_manager: The agent manager instance
        conversation_manager: The conversation manager instance
        agent_name: Name of the agent to send message to
        message: The message content to send
        context_id: Optional context ID to continue a conversation

    Returns:
        Dictionary with the response data
    """
    # Get agent
    agent_info = agent_manager.get_agent(agent_name)
    if not agent_info:
        available = ", ".join(agent_manager.list_agents())
        return {
            "error": True,
            "error_message": f"Agent '{agent_name}' not found. Available agents: {available}",
        }

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
        http_kwargs: dict[str, Any] = {}
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
            error_msg: dict[str, Any] = {
                "error": True,
                "error_code": error_info.code,
                "error_message": error_info.message,
                "context_id": conversation.context_id,
            }
            if error_info.data:
                error_msg["error_data"] = error_info.data
            return error_msg

        # Handle success response
        if not isinstance(actual_response, SendMessageSuccessResponse):
            return {
                "error": True,
                "error_message": f"Unexpected response type: {type(actual_response).__name__}",
            }

        # Extract task from the response
        result = actual_response.result

        # SendMessageSuccessResponse.result can be Task or Message
        # We need a Task to update conversation state
        if not isinstance(result, Task):
            return {
                "error": True,
                "error_message": f"Expected Task response, got {type(result).__name__}",
            }

        task = result

        # Update conversation state
        conversation_manager.update_from_task(conversation, task)

        # Extract agent's message parts
        message_parts: list[dict[str, Any]] = []
        if task.history:
            for msg in reversed(task.history):
                if msg.role == "agent":
                    for part in msg.parts:
                        if isinstance(part.root, TextPart):
                            message_parts.append({"type": "text", "text": part.root.text})
                        else:
                            # Handle other part types
                            message_parts.append({"type": type(part.root).__name__})
                    break

        # Build structured response (hide task tracking - handled automatically)
        minimized_artifacts = minimize_artifacts(task.artifacts) if task.artifacts else []
        response_obj: dict[str, Any] = {
            "context_id": conversation.context_id,
            "status": {
                "state": task.status.state.value,
                "message": {
                    "parts": message_parts,
                },
            },
            "artifacts": minimized_artifacts,
        }

        return response_obj

    except Exception as e:
        return {
            "error": True,
            "error_message": f"Error sending message: {type(e).__name__}: {str(e)}",
        }
