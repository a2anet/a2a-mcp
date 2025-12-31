"""Conversation state management for A2A MCP Server.

Conversations are keyed by context_id only (which is globally unique).
"""

import uuid
from typing import Any

from a2a.types import Artifact, DataPart, Task, TextPart

from ..storage.persistence import ConversationPersistence
from ..tools.utils import minimize_data, minimize_text
from .types import ConversationState


def minimize_artifacts(artifacts: list[Artifact]) -> list[dict[str, Any]]:
    """Minimize artifact list for LLM display.

    Args:
        artifacts: List of artifacts to minimize

    Returns:
        List of minimized artifact dictionaries. Minimized content is inside
        "text" or "data" keys, with "_" prefixed metadata fields inside.
    """
    result: list[dict[str, Any]] = []
    for artifact in artifacts:
        minimized: dict[str, Any] = {
            "artifact_id": artifact.artifact_id,
            "name": artifact.name,
            "description": artifact.description,
            "parts": [],
        }

        parts_list: list[dict[str, Any]] = []
        for part in artifact.parts:
            if isinstance(part.root, TextPart):
                # Minimize text parts - result has "text" key
                text_content = part.root.text
                lines = text_content.split("\n")
                text_minimized = minimize_text(text_content)

                # Build part with metadata at top level
                part_dict: dict[str, Any] = {
                    "type": "text",
                    "total_lines": len(lines),
                    "total_characters": len(text_content),
                }

                # Extract text content, removing redundant metadata from inside
                text_value = text_minimized.get("text")
                if isinstance(text_value, dict):
                    # Minimized - remove redundant metadata from inside
                    text_value.pop("_total_lines", None)
                    text_value.pop("_total_characters", None)
                part_dict["text"] = text_value

                parts_list.append(part_dict)

            elif isinstance(part.root, DataPart):
                # Minimize data parts - result has "data" key
                data_minimized = minimize_data(part.root.data)
                parts_list.append({"type": "data", **data_minimized})

        minimized["parts"] = parts_list
        result.append(minimized)

    return result


class ConversationManager:
    """Manages conversation state for all active conversations.

    Conversations are keyed by context_id only (not agent_name:context_id).
    """

    def __init__(self, persistence: ConversationPersistence | None = None) -> None:
        """Initialize the conversation manager.

        Args:
            persistence: Optional persistence layer for saving/loading conversations.
                        If None, a default ConversationPersistence will be created.
        """
        # Key is just context_id (globally unique)
        self.conversations: dict[str, ConversationState] = {}
        self.persistence = persistence or ConversationPersistence()

        # Load existing conversations from disk
        self.conversations = self.persistence.load_all_conversations()

    def get_or_create_conversation(
        self, agent_name: str, context_id: str | None = None
    ) -> ConversationState:
        """Get existing conversation or create a new one.

        Args:
            agent_name: Display name of the agent
            context_id: Optional context ID. If None, a new UUID will be generated.

        Returns:
            ConversationState instance
        """
        # Generate new context_id if not provided
        if context_id is None:
            context_id = str(uuid.uuid4())

        # Return existing or create new (key is just context_id)
        if context_id not in self.conversations:
            conversation = ConversationState(agent_name=agent_name, context_id=context_id)
            self.conversations[context_id] = conversation

            # Save new conversation to disk
            self.persistence.save_conversation(conversation)

        return self.conversations[context_id]

    def update_from_task(self, conversation: ConversationState, task: Task) -> None:
        """Update conversation state from task response.

        Args:
            conversation: The conversation state to update
            task: The task result from A2A agent

        This updates:
        - task_id and task_state
        - message history
        - artifacts (both full and minimized versions)
        """
        # Update task information
        conversation.task_id = task.id
        conversation.task_state = task.status.state

        # Add new messages to history (avoid duplicates)
        if task.history:
            existing_ids = {msg.message_id for msg in conversation.messages}
            for msg in task.history:
                if msg.message_id not in existing_ids:
                    conversation.messages.append(msg)
                    existing_ids.add(msg.message_id)

        # Store artifacts
        if task.artifacts:
            for artifact in task.artifacts:
                # Store full artifact
                conversation.artifacts[artifact.artifact_id] = artifact

            # Store minimized versions
            minimized_list = minimize_artifacts(task.artifacts)
            for i, artifact in enumerate(task.artifacts):
                conversation.minimized_artifacts[artifact.artifact_id] = minimized_list[i]

        # Save updated conversation to disk
        self.persistence.save_conversation(conversation)

    def get_conversation(self, context_id: str) -> ConversationState | None:
        """Retrieve existing conversation by context_id only.

        Args:
            context_id: Context ID of the conversation

        Returns:
            ConversationState if found, None otherwise
        """
        # Check in-memory cache first
        if context_id in self.conversations:
            return self.conversations[context_id]

        # Try loading from disk if not in memory
        conversation = self.persistence.load_conversation(context_id)
        if conversation:
            # Cache it in memory
            self.conversations[context_id] = conversation

        return conversation
