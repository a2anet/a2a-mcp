"""Configuration loading for A2A MCP Server."""

import json
import os
from typing import Dict, List

from pydantic import BaseModel, Field, HttpUrl


class AgentCardConfig(BaseModel):
    """Configuration for a single agent card."""

    url: HttpUrl  # Full URL to agent-card.json
    custom_headers: Dict[str, str] = Field(default_factory=dict)  # Per-agent headers


class A2AMCPConfig(BaseModel):
    """Main configuration for the A2A MCP server."""

    agent_cards: List[AgentCardConfig]  # List of agent card configurations
    global_headers: Dict[str, str] = Field(default_factory=dict)  # Headers for all agents

    @classmethod
    def from_env(cls) -> "A2AMCPConfig":
        """Load configuration from environment variables.

        Environment variables:
            A2A_AGENT_CARDS: JSON array of agent card configs
                Example: '[{"url": "https://example.com/agent-card.json"}]'

            A2A_GLOBAL_HEADERS: Optional JSON dict of global headers
                Example: '{"User-Agent": "A2A-MCP/1.0"}'

        Returns:
            A2AMCPConfig instance

        Raises:
            ValueError: If A2A_AGENT_CARDS is not set or invalid JSON
        """
        # Load agent cards (required)
        agent_cards_json = os.getenv("A2A_AGENT_CARDS")
        if not agent_cards_json:
            raise ValueError(
                "A2A_AGENT_CARDS environment variable is required. "
                'Example: \'[{"url": "https://example.com/agent-card.json"}]\''
            )

        try:
            agent_cards_data = json.loads(agent_cards_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in A2A_AGENT_CARDS: {e}") from e

        if not isinstance(agent_cards_data, list):
            raise ValueError("A2A_AGENT_CARDS must be a JSON array")

        # Parse agent card configs
        agent_cards = [AgentCardConfig(**item) for item in agent_cards_data]

        # Load global headers (optional)
        global_headers: Dict[str, str] = {}
        global_headers_json = os.getenv("A2A_GLOBAL_HEADERS")
        if global_headers_json:
            try:
                global_headers = json.loads(global_headers_json)
                if not isinstance(global_headers, dict):
                    raise ValueError("A2A_GLOBAL_HEADERS must be a JSON object")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in A2A_GLOBAL_HEADERS: {e}") from e

        return cls(agent_cards=agent_cards, global_headers=global_headers)

    @classmethod
    def from_file(cls, path: str) -> "A2AMCPConfig":
        """Load configuration from a JSON file.

        Args:
            path: Path to JSON configuration file

        Returns:
            A2AMCPConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file contains invalid JSON or data
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)
