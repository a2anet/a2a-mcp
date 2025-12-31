"""Conversation persistence for A2A MCP Server.

Uses context_id as the sole key for conversations (agent_name stored internally).
"""

import json
import logging
from pathlib import Path
from typing import Any

from a2a.types import Artifact, Message, TaskState

from ..core.types import ConversationState
from .paths import get_conversations_dir

logger = logging.getLogger(__name__)


class ConversationPersistence:
    """Handles saving and loading conversation state to/from disk.

    Conversations are keyed by context_id only (which is globally unique).
    """

    def __init__(self, storage_dir: Path | None = None) -> None:
        """Initialize persistence layer.

        Args:
            storage_dir: Directory to store conversation files.
                        Defaults to platform-specific data directory.
        """
        if storage_dir is None:
            storage_dir = get_conversations_dir()

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_conversation_path(self, context_id: str) -> Path:
        """Get the file path for a conversation.

        Args:
            context_id: Conversation context ID (globally unique)

        Returns:
            Path to the conversation file
        """
        return self.storage_dir / f"{context_id}.json"

    def save_conversation(self, conversation: ConversationState) -> None:
        """Save conversation state to disk.

        Args:
            conversation: The conversation state to save
        """
        try:
            file_path = self._get_conversation_path(conversation.context_id)

            data = {
                "agent_name": conversation.agent_name,
                "context_id": conversation.context_id,
                "task_id": conversation.task_id,
                "task_state": conversation.task_state.value if conversation.task_state else None,
                "messages": [self._serialize_message(msg) for msg in conversation.messages],
                "artifacts": {
                    artifact_id: self._serialize_artifact(artifact)
                    for artifact_id, artifact in conversation.artifacts.items()
                },
                "minimized_artifacts": conversation.minimized_artifacts,
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved conversation {conversation.context_id} to {file_path}")

        except Exception as e:
            logger.error(f"Error saving conversation {conversation.context_id}: {e}")

    def load_conversation(self, context_id: str) -> ConversationState | None:
        """Load conversation state from disk.

        Args:
            context_id: Conversation context ID

        Returns:
            ConversationState if found, None otherwise
        """
        try:
            file_path = self._get_conversation_path(context_id)

            if not file_path.exists():
                return None

            with open(file_path) as f:
                data = json.load(f)

            conversation = ConversationState(
                agent_name=data["agent_name"],
                context_id=data["context_id"],
                task_id=data.get("task_id"),
                task_state=TaskState(data["task_state"]) if data.get("task_state") else None,
                messages=[self._deserialize_message(msg_data) for msg_data in data["messages"]],
                artifacts={
                    artifact_id: self._deserialize_artifact(artifact_data)
                    for artifact_id, artifact_data in data["artifacts"].items()
                },
                minimized_artifacts=data.get("minimized_artifacts", {}),
            )

            logger.debug(f"Loaded conversation {context_id} from {file_path}")
            return conversation

        except Exception as e:
            logger.error(f"Error loading conversation {context_id}: {e}")
            return None

    def load_all_conversations(self) -> dict[str, ConversationState]:
        """Load all conversations from disk.

        Returns:
            Dictionary mapping context_id to ConversationState objects
        """
        conversations: dict[str, ConversationState] = {}

        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    context_id = data["context_id"]

                    conversation = ConversationState(
                        agent_name=data["agent_name"],
                        context_id=context_id,
                        task_id=data.get("task_id"),
                        task_state=TaskState(data["task_state"])
                        if data.get("task_state")
                        else None,
                        messages=[
                            self._deserialize_message(msg_data) for msg_data in data["messages"]
                        ],
                        artifacts={
                            artifact_id: self._deserialize_artifact(artifact_data)
                            for artifact_id, artifact_data in data["artifacts"].items()
                        },
                        minimized_artifacts=data.get("minimized_artifacts", {}),
                    )

                    # Key by context_id only (not "{agent_name}:{context_id}")
                    conversations[context_id] = conversation

                except Exception as e:
                    logger.error(f"Error loading conversation from {file_path}: {e}")
                    continue

            logger.info(f"Loaded {len(conversations)} conversations from disk")

        except Exception as e:
            logger.error(f"Error loading conversations: {e}")

        return conversations

    def delete_conversation(self, context_id: str) -> bool:
        """Delete a conversation from disk.

        Args:
            context_id: Conversation context ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self._get_conversation_path(context_id)

            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted conversation {context_id} from {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting conversation {context_id}: {e}")
            return False

    def _serialize_message(self, message: Message) -> dict[str, Any]:
        """Serialize a Message object to a dictionary."""
        if hasattr(message, "model_dump"):
            return message.model_dump(mode="json")
        else:
            return dict(message)

    def _deserialize_message(self, data: dict[str, Any]) -> Message:
        """Deserialize a dictionary to a Message object."""
        if hasattr(Message, "model_validate"):
            return Message.model_validate(data)
        else:
            return Message(**data)

    def _serialize_artifact(self, artifact: Artifact) -> dict[str, Any]:
        """Serialize an Artifact object to a dictionary."""
        if hasattr(artifact, "model_dump"):
            return artifact.model_dump(mode="json")
        else:
            return dict(artifact)

    def _deserialize_artifact(self, data: dict[str, Any]) -> Artifact:
        """Deserialize a dictionary to an Artifact object."""
        if hasattr(Artifact, "model_validate"):
            return Artifact.model_validate(data)
        else:
            return Artifact(**data)
