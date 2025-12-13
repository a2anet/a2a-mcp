"""Main entry point for A2A MCP Server."""

import asyncio
import sys

import httpx
from loguru import logger

from a2anet_mcp import server
from a2anet_mcp.agent_manager import AgentManager
from a2anet_mcp.config import A2AMCPConfig
from a2anet_mcp.conversation_manager import ConversationManager


async def main() -> None:
    """Main entry point for A2A MCP server."""
    # Configure loguru to output to stderr
    logger.remove()  # Remove default handler
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
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {type(e).__name__}: {e}")
        sys.exit(1)

    # Create HTTP client
    httpx_client = httpx.AsyncClient(timeout=60.0)

    try:
        # Initialize agent manager
        agent_mgr = AgentManager(httpx_client)
        await agent_mgr.initialize_agents(config.agent_cards)

        if not agent_mgr.agents:
            logger.error("No agents were successfully initialized")
            sys.exit(1)

        # Initialize conversation manager
        conv_mgr = ConversationManager()

        # Set global instances in server module
        server.agent_manager = agent_mgr
        server.conversation_manager = conv_mgr

        # Run the MCP server
        logger.success("A2A MCP Server is ready")
        server.run_server()

    finally:
        # Cleanup
        await httpx_client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        sys.exit(1)
