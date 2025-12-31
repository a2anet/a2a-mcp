"""Agent discovery tool handler for A2A MCP Server."""

from typing import Any

from ..core.agents import AgentManager


async def handle_list_available_agents(
    agent_manager: AgentManager,
) -> dict[str, Any]:
    """Handle list_available_agents tool call.

    Args:
        agent_manager: The agent manager instance

    Returns:
        Dictionary with agent information
    """
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

    response_obj: dict[str, Any] = {"agents": agents_list, "count": len(agents_list)}

    # Add tips
    if agents_list:
        response_obj["tips"] = [
            "Use the agent name exactly as shown when calling send_message_to_agent",
            "Check the skills list to understand what each agent can do",
        ]

    return response_obj
