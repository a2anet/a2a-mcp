"""Type definitions for A2A MCP Server."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from a2a.client import A2AClient
from a2a.types import AgentCard, Artifact, Message, TaskState


@dataclass
class AgentInfo:
    """Information about a registered A2A agent."""

    display_name: str  # "Twitter Agent" or "Twitter Agent (2)" if conflict
    original_name: str  # Original name from agent card
    url: str  # Full URL to agent card
    description: str  # Agent description
    skills: List[str]  # List of skill names
    agent_card: AgentCard  # Full agent card
    client: A2AClient  # A2A client instance
    custom_headers: Dict[str, str] = field(default_factory=dict)  # Custom HTTP headers


@dataclass
class ConversationState:
    """State tracking for a single conversation with an agent."""

    agent_name: str  # Display name of the agent
    context_id: str  # Conversation context ID
    task_id: Optional[str] = None  # Current task ID
    task_state: Optional[TaskState] = None  # Current task state
    messages: List[Message] = field(default_factory=list)  # Message history
    artifacts: Dict[str, Artifact] = field(default_factory=dict)  # Full artifacts by ID
    minimized_artifacts: Dict[str, Any] = field(default_factory=dict)  # Minimized for display

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        if self.task_state is None:
            return False
        return self.task_state in [
            TaskState.completed,
            TaskState.canceled,
            TaskState.rejected,
            TaskState.failed,
        ]

    @property
    def requires_task_id(self) -> bool:
        """Check if the next message should include task_id.

        Returns True if task state is input_required or auth_required.
        """
        if self.task_state is None:
            return False
        return self.task_state in [
            TaskState.input_required,
            TaskState.auth_required,
        ]
