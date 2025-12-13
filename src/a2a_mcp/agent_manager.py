"""Agent management for A2A MCP Server."""

import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from a2a.client import A2ACardResolver, A2AClient
from loguru import logger

from .config import AgentCardConfig
from .types import AgentInfo


class AgentManager:
    """Manages A2A agent cards and clients."""

    def __init__(self, httpx_client: httpx.AsyncClient):
        """Initialize the agent manager.

        Args:
            httpx_client: Async HTTP client for making requests
        """
        self.httpx_client = httpx_client
        self.agents: Dict[str, AgentInfo] = {}  # Keyed by display_name

    async def initialize_agents(self, agent_configs: List[AgentCardConfig]) -> None:
        """Fetch all agent cards in parallel and initialize clients.

        Args:
            agent_configs: List of agent card configurations

        Note:
            Logs errors but continues with successfully loaded agents.
        """
        # Fetch all agent cards in parallel
        tasks = [self._fetch_and_register_agent(config) for config in agent_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                url = str(agent_configs[i].url)
                logger.error(f"Error loading agent from {url}: {type(result).__name__}: {result}")

        # Log successfully loaded agents
        if self.agents:
            logger.success(f"Successfully initialized {len(self.agents)} agent(s):")
            for name in self.list_agents():
                agent = self.get_agent(name)
                if agent:
                    skills = ", ".join(agent.skills) if agent.skills else "No skills"
                    logger.info(f"  - {name}: {agent.description}")
                    logger.info(f"    Skills: {skills}")
        else:
            logger.warning("No agents were successfully initialized")

    async def _fetch_and_register_agent(self, config: AgentCardConfig) -> None:
        """Fetch a single agent card and create client.

        Args:
            config: Agent card configuration

        Raises:
            Exception: If agent card fetch or client creation fails
        """
        # Parse URL to extract base_url and card_path
        url_str = str(config.url)
        base_url, card_path = self._parse_agent_card_url(url_str)

        # Fetch agent card
        resolver = A2ACardResolver(
            httpx_client=self.httpx_client,
            base_url=base_url,
            agent_card_path=card_path,
        )
        agent_card = await resolver.get_agent_card()

        # Create A2A client
        client = A2AClient(httpx_client=self.httpx_client, agent_card=agent_card)

        # Resolve name conflicts
        original_name = agent_card.name
        display_name = self._resolve_name_conflict(original_name)

        # Extract skill names
        skills = [skill.name for skill in agent_card.skills] if agent_card.skills else []

        # Create AgentInfo
        agent_info = AgentInfo(
            display_name=display_name,
            original_name=original_name,
            url=url_str,
            description=agent_card.description,
            skills=skills,
            agent_card=agent_card,
            client=client,
            custom_headers=dict(config.custom_headers),
        )

        # Store in registry
        self.agents[display_name] = agent_info

    def _parse_agent_card_url(self, url: str) -> tuple[str, str]:
        """Parse agent card URL into base_url and card_path.

        Args:
            url: Full URL to agent card

        Returns:
            Tuple of (base_url, card_path)

        Example:
            "https://a2anet.com/agent/123/agent-card.json"
            -> ("https://a2anet.com", "/agent/123/agent-card.json")
        """
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        card_path = parsed.path
        return base_url, card_path

    def _resolve_name_conflict(self, desired_name: str) -> str:
        """Resolve name conflicts by adding numeric suffix.

        Args:
            desired_name: The desired display name

        Returns:
            A unique display name (possibly with suffix)

        Example:
            If "Twitter Agent" exists, returns "Twitter Agent (2)"
            If that also exists, returns "Twitter Agent (3)", etc.
        """
        if desired_name not in self.agents:
            return desired_name

        counter = 2
        while f"{desired_name} ({counter})" in self.agents:
            counter += 1

        return f"{desired_name} ({counter})"

    def get_agent(self, agent_name: str) -> Optional[AgentInfo]:
        """Retrieve agent by display name.

        Args:
            agent_name: Display name of the agent

        Returns:
            AgentInfo if found, None otherwise
        """
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """Get list of all agent display names.

        Returns:
            List of agent display names
        """
        return list(self.agents.keys())

    def get_agents_summary(self) -> str:
        """Generate formatted summary of all agents for LLM context.

        Returns:
            Formatted string with agent information
        """
        if not self.agents:
            return "No agents available."

        lines = []
        for name in sorted(self.list_agents()):
            agent = self.get_agent(name)
            if agent:
                skills_str = ", ".join(agent.skills) if agent.skills else "No skills listed"
                lines.append(
                    f"**{name}**\n  Description: {agent.description}\n  Skills: {skills_str}"
                )

        return "\n\n".join(lines)
