"""Storage paths for A2A MCP Server."""

from pathlib import Path

BASE_DIR = Path.home() / ".a2a-mcp"


def get_tasks_dir() -> Path:
    """Get the tasks storage directory.

    Returns:
        Path to ``~/.a2a-mcp/tasks/``, created if it doesn't exist.
    """
    path = BASE_DIR / "tasks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_files_dir() -> Path:
    """Get the files storage directory.

    Returns:
        Path to ``~/.a2a-mcp/files/``, created if it doesn't exist.
    """
    path = BASE_DIR / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path
