"""Cross-platform storage paths for A2A MCP Server."""

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "a2anet-mcp"
APP_AUTHOR = "A2ANet"


def get_data_dir() -> Path:
    """Get the cross-platform data directory.

    Returns platform-specific path:
        - Linux: ~/.local/share/a2anet-mcp
        - macOS: ~/Library/Application Support/a2anet-mcp
        - Windows: C:\\Users\\<user>\\AppData\\Local\\A2ANet\\a2anet-mcp

    Returns:
        Path to the data directory
    """
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_conversations_dir() -> Path:
    """Get the conversations storage directory.

    Creates the directory if it doesn't exist.

    Returns:
        Path to the conversations directory
    """
    path = get_data_dir() / "conversations"
    path.mkdir(parents=True, exist_ok=True)
    return path
