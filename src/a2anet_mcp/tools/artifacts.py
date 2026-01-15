"""Artifact viewing tools for A2A MCP Server.

Provides two specialized tools for viewing different artifact types:
- view_text_artifact: For text content with line range selection
- view_data_artifact: For structured data with JSON path, row, and column filtering
"""

import json
from itertools import chain
from typing import Any, Union

from a2a.types import Artifact, DataPart, TextPart

from ..core.conversation import ConversationManager
from .utils import (
    MAX_OUTPUT_CHARS,
    evaluate_json_path,
    filter_data_by_rows_and_columns,
    parse_column_selection,
    parse_line_range,
    parse_row_selection,
)


def _get_artifact(
    conversation_manager: ConversationManager,
    context_id: str,
    artifact_id: str,
) -> tuple[Artifact | None, dict[str, Any] | None]:
    """Get artifact from conversation, returning error dict if not found.

    Returns:
        Tuple of (artifact, error_dict). If artifact is found, error_dict is None.
        If artifact is not found, artifact is None and error_dict contains error info.
    """
    conversation = conversation_manager.get_conversation(context_id)
    if not conversation:
        return None, {
            "error": True,
            "error_message": f"No conversation found with context_id '{context_id}'",
        }

    artifact = conversation.artifacts.get(artifact_id)
    if not artifact:
        available = ", ".join(conversation.artifacts.keys()) or "(none)"
        return None, {
            "error": True,
            "error_message": f"Artifact '{artifact_id}' not found. Available: {available}",
        }

    return artifact, None


def _get_text_content(artifact: Artifact) -> str | None:
    """Extract text content from artifact parts."""
    text_parts = []
    for part in artifact.parts:
        if isinstance(part.root, TextPart):
            text_parts.append(part.root.text)
    return "\n".join(text_parts) if text_parts else None


def _get_data_content(artifact: Artifact) -> list[Any]:
    """Extract all data content from artifact parts."""
    data_parts = []
    for part in artifact.parts:
        if isinstance(part.root, DataPart):
            data_parts.append(part.root.data)
    return data_parts


async def handle_view_text_artifact(
    conversation_manager: ConversationManager,
    context_id: str,
    artifact_id: str,
    line_start: int | None = None,
    line_end: int | None = None,
) -> dict[str, Any]:
    """Handle view_text_artifact tool call.

    Args:
        conversation_manager: The conversation manager instance
        context_id: Context ID of the conversation
        artifact_id: ID of the artifact to view
        line_start: Starting line number (1-based, inclusive). None = start.
        line_end: Ending line number (1-based, inclusive). None = end.

    Returns:
        Dictionary with the text content or error. No "_" prefix on keys.
    """
    artifact, error = _get_artifact(conversation_manager, context_id, artifact_id)
    if error:
        return error

    assert artifact is not None

    # Get text content
    text_content = _get_text_content(artifact)
    if text_content is None:
        return {
            "error": True,
            "error_message": (
                f"Artifact '{artifact_id}' does not contain text content. "
                f"Use view_data_artifact instead."
            ),
        }

    try:
        # Split into lines
        lines = text_content.split("\n")
        total_lines = len(lines)

        # Parse line range
        start_idx, end_idx = parse_line_range(line_start, line_end, total_lines)

        # Extract requested lines
        selected_lines = lines[start_idx:end_idx]
        result_text = "\n".join(selected_lines)

        # Build response (no _ prefix on view tool output keys)
        response: dict[str, Any] = {
            "artifact_id": artifact_id,
            "name": artifact.name,
            "total_lines": total_lines,
            "line_range": f"{start_idx + 1}-{end_idx}",
        }

        # Check output size
        if len(result_text) > MAX_OUTPUT_CHARS:
            raise ValueError(
                f"Selected text ({len(result_text):,} characters) exceeds the maximum "
                f"output size of {MAX_OUTPUT_CHARS:,} characters. "
                f"Try selecting a smaller line range."
            )

        # Add total_characters to metadata and return full text
        response["total_characters"] = len(text_content)
        response["text"] = result_text

        return response

    except ValueError as e:
        return {
            "error": True,
            "error_message": str(e),
        }
    except Exception as e:
        return {
            "error": True,
            "error_message": f"Error viewing text artifact: {type(e).__name__}: {str(e)}",
        }


async def handle_view_data_artifact(
    conversation_manager: ConversationManager,
    context_id: str,
    artifact_id: str,
    json_path: str | None = None,
    rows: Union[int, list[int], str, None] = None,
    columns: Union[str, list[str], None] = None,
) -> dict[str, Any]:
    """Handle view_data_artifact tool call.

    Args:
        conversation_manager: The conversation manager instance
        context_id: Context ID of the conversation
        artifact_id: ID of the artifact to view
        json_path: Optional dot-separated path to extract specific fields (no array indexing)
        rows: Optional row selection - single index, list of indices, range string, or "all"
        columns: Optional column selection - single name, list of names, or "all"

    Returns:
        Dictionary with the data content or error. No "_" prefix on keys.
    """
    artifact, error = _get_artifact(conversation_manager, context_id, artifact_id)
    if error:
        return error

    assert artifact is not None

    # Get data content
    data_parts = _get_data_content(artifact)
    if not data_parts:
        return {
            "error": True,
            "error_message": (
                f"Artifact '{artifact_id}' does not contain data content. "
                f"Use view_text_artifact instead."
            ),
        }

    try:
        # If multiple data parts, combine into single response
        data = data_parts[0] if len(data_parts) == 1 else data_parts

        # Apply JSON path filter if provided (field access only, no array indexing)
        if json_path:
            try:
                data = evaluate_json_path(data, json_path)
            except (KeyError, TypeError) as e:
                return {
                    "error": True,
                    "error_message": f"JSON path '{json_path}' error: {str(e)}",
                }

        # Build response (no _ prefix on view tool output keys)
        response: dict[str, Any] = {
            "artifact_id": artifact_id,
            "name": artifact.name,
        }

        if json_path:
            response["json_path"] = json_path

        # Check if rows/columns filtering is requested
        if rows is not None or columns is not None:
            # Rows/columns filtering requires list data
            if not isinstance(data, list):
                return {
                    "error": True,
                    "error_message": (
                        "rows/columns parameters require list data. "
                        f"The data at this path is a {type(data).__name__}. "
                        "Use json_path to navigate to a list field first."
                    ),
                }

            if not data:
                return {
                    "error": True,
                    "error_message": "Cannot filter empty list.",
                }

            # Check if it's a list of objects (tabular data)
            is_tabular = isinstance(data[0], dict)

            if is_tabular:
                # Tabular data - apply row and column filtering
                table_data: list[dict[str, Any]] = data
                # Collect all unique column names from all rows (handles sparse data)
                # Uses dict.fromkeys for fast, order-preserving uniqueness
                available_columns = list(dict.fromkeys(
                    chain.from_iterable(item.keys() for item in table_data if isinstance(item, dict))
                ))

                # Parse selections
                row_indices = parse_row_selection(rows if rows is not None else "all", len(data))
                column_names = parse_column_selection(
                    columns if columns is not None else "all", available_columns
                )

                # Filter data
                filtered_data = filter_data_by_rows_and_columns(
                    table_data, row_indices, column_names
                )

                # Check output size
                output_json = json.dumps(filtered_data, indent=2)
                if len(output_json) > MAX_OUTPUT_CHARS:
                    return {
                        "error": True,
                        "error_message": (
                            f"The selection ({len(row_indices)} row(s) and "
                            f"{len(column_names)} column(s)) resulted in "
                            f"{len(output_json):,} characters, which exceeds the limit of "
                            f"{MAX_OUTPUT_CHARS:,} characters. Try selecting fewer rows or columns."
                        ),
                    }

                # Build table-specific response (no _ prefix)
                response["total_rows"] = len(table_data)
                response["total_columns"] = len(available_columns)
                response["selected_rows"] = len(row_indices)
                response["selected_columns"] = len(column_names)
                response["available_columns"] = available_columns
                response["data"] = filtered_data

                return response

            else:
                # List of basic values - only row filtering applies
                if columns is not None:
                    return {
                        "error": True,
                        "error_message": (
                            "columns parameter is only valid for lists of objects. "
                            "This list contains basic values. Use rows parameter only."
                        ),
                    }

                # Parse row selection
                row_indices = parse_row_selection(rows if rows is not None else "all", len(data))

                # Filter data
                filtered_data = [data[i] for i in row_indices]

                # Check output size
                output_json = json.dumps(filtered_data, indent=2)
                if len(output_json) > MAX_OUTPUT_CHARS:
                    return {
                        "error": True,
                        "error_message": (
                            f"The selection ({len(row_indices)} item(s)) resulted in "
                            f"{len(output_json):,} characters, which exceeds the limit of "
                            f"{MAX_OUTPUT_CHARS:,} characters. Try selecting fewer items."
                        ),
                    }

                # Build list-specific response (no _ prefix)
                response["total_items"] = len(data)
                response["selected_items"] = len(row_indices)
                response["data"] = filtered_data

                return response

        # No row/column filtering - return full data
        output_json = json.dumps(data, indent=2)
        if len(output_json) > MAX_OUTPUT_CHARS:
            return {
                "error": True,
                "error_message": (
                    f"Data output ({len(output_json):,} characters) exceeds the maximum "
                    f"size of {MAX_OUTPUT_CHARS:,} characters. "
                    "Try using json_path to access specific fields, or rows/columns "
                    "to filter list data."
                ),
            }

        # Return full data
        response["data"] = data

        return response

    except ValueError as e:
        return {
            "error": True,
            "error_message": str(e),
        }
    except Exception as e:
        return {
            "error": True,
            "error_message": f"Error viewing data artifact: {type(e).__name__}: {str(e)}",
        }
