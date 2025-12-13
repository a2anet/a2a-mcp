"""Response minimization utilities for A2A MCP Server."""

import json
from typing import Any, Dict, List

from a2a.types import Artifact, DataPart, TextPart


def minimize_artifacts(artifacts: List[Artifact]) -> List[Dict[str, Any]]:
    """Minimize artifact list for LLM display.

    Args:
        artifacts: List of artifacts to minimize

    Returns:
        List of minimized artifact dictionaries
    """
    result: List[Dict[str, Any]] = []
    for artifact in artifacts:
        minimized: Dict[str, Any] = {
            "artifact_id": artifact.artifact_id,
            "name": artifact.name,
            "description": artifact.description,
            "parts": [],
        }

        parts_list: List[Dict[str, Any]] = []
        for part in artifact.parts:
            if isinstance(part.root, TextPart):
                # Minimize text parts (truncate if too long)
                text = part.root.text
                if len(text) > 200:
                    preview = text[:200] + "..."
                else:
                    preview = text

                parts_list.append({"type": "text", "preview": preview})

            elif isinstance(part.root, DataPart):
                # Minimize data parts
                parts_list.append(minimize_data_part(part.root))

        minimized["parts"] = parts_list
        result.append(minimized)

    return result


def minimize_data_part(data_part: DataPart) -> Dict[str, Any]:
    """Minimize a DataPart by showing first/last items for large lists.

    Args:
        data_part: The data part to minimize

    Returns:
        Minimized data part dictionary
    """
    result = {"type": "data", "data": minimize_data_value(data_part.data)}
    return result


def minimize_data_value(value: Any, max_depth: int = 3) -> Any:
    """Recursively minimize data structures.

    For lists with 3+ items, shows first and last item only.
    For nested structures, recurses up to max_depth levels.

    Args:
        value: The value to minimize
        max_depth: Maximum recursion depth

    Returns:
        Minimized value
    """
    if max_depth <= 0:
        return "..."

    if isinstance(value, list):
        if len(value) <= 2:
            # Show all items for small lists
            return [minimize_data_value(item, max_depth - 1) for item in value]
        else:
            # Show first and last for large lists
            return {
                "_type": "minimized_list",
                "length": len(value),
                "first": minimize_data_value(value[0], max_depth - 1),
                "last": minimize_data_value(value[-1], max_depth - 1),
            }

    elif isinstance(value, dict):
        # Recursively minimize nested dicts
        return {k: minimize_data_value(v, max_depth - 1) for k, v in value.items()}

    else:
        # Primitives pass through unchanged
        return value


def format_minimized_response(
    task_id: str,
    context_id: str,
    task_state: str,
    agent_message: str,
    minimized_artifacts: List[Dict[str, Any]],
) -> str:
    """Format minimized response for LLM consumption.

    Args:
        task_id: The task ID
        context_id: The context ID
        task_state: The current task state
        agent_message: The text message from the agent
        minimized_artifacts: List of minimized artifacts

    Returns:
        Formatted response string
    """
    parts = [
        f"Task ID: {task_id}",
        f"Context ID: {context_id}",
        f"State: {task_state}",
    ]

    if agent_message:
        parts.append(f"\nAgent Response:\n{agent_message}")

    if minimized_artifacts:
        parts.append("\nArtifacts:")
        for artifact in minimized_artifacts:
            parts.append(f"  - {artifact['name']} ({artifact['artifact_id']})")
            if artifact.get("description"):
                parts.append(f"    {artifact['description']}")

            # Show preview of parts
            for part in artifact.get("parts", []):
                if part["type"] == "text":
                    parts.append(f"    [Text] {part.get('preview', '')}")
                elif part["type"] == "data":
                    data_str = json.dumps(part.get("data", {}), indent=2)
                    # Limit data preview to 500 chars
                    if len(data_str) > 500:
                        data_str = data_str[:500] + "\n    ..."
                    parts.append(f"    [Data] {data_str}")

        parts.append(
            "\nTip: Use view_artifact tool to see full artifact content "
            "or apply filters to specific data."
        )

    return "\n".join(parts)
