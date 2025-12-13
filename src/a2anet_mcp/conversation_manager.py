"""Conversation state management for A2A MCP Server."""

import uuid
from typing import Dict, Optional

from a2a.types import Task

from .persistence import ConversationPersistence
from .response_minimizer import minimize_artifacts
from .types import ConversationState


class ConversationManager:
    """Manages conversation state for all active conversations."""

    def __init__(self, persistence: Optional[ConversationPersistence] = None) -> None:
        """Initialize the conversation manager.

        Args:
            persistence: Optional persistence layer for saving/loading conversations.
                        If None, a default ConversationPersistence will be created.
        """
        # Key format: "{agent_name}:{context_id}"
        self.conversations: Dict[str, ConversationState] = {}
        self.persistence = persistence or ConversationPersistence()

        # Load existing conversations from disk
        self.conversations = self.persistence.load_all_conversations()

    def get_or_create_conversation(
        self, agent_name: str, context_id: Optional[str] = None
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

        key = f"{agent_name}:{context_id}"

        # Return existing or create new
        if key not in self.conversations:
            conversation = ConversationState(agent_name=agent_name, context_id=context_id)
            self.conversations[key] = conversation

            # Save new conversation to disk
            self.persistence.save_conversation(conversation)

        return self.conversations[key]

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

    def get_conversation(self, agent_name: str, context_id: str) -> Optional[ConversationState]:
        """Retrieve existing conversation.

        Args:
            agent_name: Display name of the agent
            context_id: Context ID of the conversation

        Returns:
            ConversationState if found, None otherwise
        """
        key = f"{agent_name}:{context_id}"

        # Check in-memory cache first
        if key in self.conversations:
            return self.conversations[key]

        # Try loading from disk if not in memory
        conversation = self.persistence.load_conversation(agent_name, context_id)
        if conversation:
            # Cache it in memory
            self.conversations[key] = conversation

        return conversation
