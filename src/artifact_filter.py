"""Artifact filtering utilities for A2A MCP Server."""

import json
import re
from typing import Any, Dict, List, Optional

from a2a.types import Artifact, DataPart, TextPart


class ArtifactFilter:
    """Filters artifact content based on various strategies."""

    @staticmethod
    def filter_artifact(
        artifact: Artifact,
        filter_type: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply filter to artifact and return result.

        Args:
            artifact: The artifact to filter
            filter_type: Type of filter ("regex", "json_path", "field", "none")
            filter_value: Filter value or pattern

        Returns:
            Filtered artifact dictionary

        Raises:
            ValueError: If filter_type is unknown or filter_value is missing
        """
        if not filter_type or filter_type == "none":
            return ArtifactFilter._artifact_to_dict(artifact)

        if filter_type == "regex":
            return ArtifactFilter._filter_regex(artifact, filter_value)
        elif filter_type == "json_path":
            return ArtifactFilter._filter_json_path(artifact, filter_value)
        elif filter_type == "field":
            return ArtifactFilter._filter_field(artifact, filter_value)
        else:
            raise ValueError(
                f"Unknown filter type: {filter_type}. "
                "Supported types: 'regex', 'json_path', 'field', 'none'"
            )

    @staticmethod
    def _artifact_to_dict(artifact: Artifact) -> Dict[str, Any]:
        """Convert full artifact to dictionary.

        Args:
            artifact: The artifact to convert

        Returns:
            Dictionary representation of the artifact
        """
        return {
            "artifact_id": artifact.artifact_id,
            "name": artifact.name,
            "description": artifact.description,
            "parts": [ArtifactFilter._part_to_dict(part) for part in artifact.parts],
        }

    @staticmethod
    def _part_to_dict(part: Any) -> Dict[str, Any]:
        """Convert part to dictionary.

        Args:
            part: The part to convert

        Returns:
            Dictionary representation of the part
        """
        if isinstance(part.root, TextPart):
            return {"type": "text", "text": part.root.text}
        elif isinstance(part.root, DataPart):
            return {"type": "data", "data": part.root.data}
        else:
            return {"type": "unknown"}

    @staticmethod
    def _filter_regex(artifact: Artifact, pattern: Optional[str]) -> Dict[str, Any]:
        """Filter artifact using regex pattern.

        Args:
            artifact: The artifact to filter
            pattern: The regex pattern to search for

        Returns:
            Dictionary with matching results

        Raises:
            ValueError: If pattern is not provided
        """
        if not pattern:
            raise ValueError("Regex filter requires filter_value (pattern)")

        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

        results: List[str] = []

        for part in artifact.parts:
            if isinstance(part.root, TextPart):
                # Search in text
                matches = compiled_pattern.findall(part.root.text)
                if matches:
                    results.extend(matches)
            elif isinstance(part.root, DataPart):
                # Search in stringified data
                data_str = json.dumps(part.root.data)
                matches = compiled_pattern.findall(data_str)
                if matches:
                    results.extend(matches)

        return {
            "artifact_id": artifact.artifact_id,
            "filter_type": "regex",
            "pattern": pattern,
            "matches": results,
            "match_count": len(results),
        }

    @staticmethod
    def _filter_json_path(artifact: Artifact, json_path: Optional[str]) -> Dict[str, Any]:
        """Filter artifact using JSONPath-like syntax.

        Supports simple paths like:
        - "field" - top-level field
        - "field.nested" - nested field
        - "array[0]" - array index
        - "field.array[1].nested" - combined

        Args:
            artifact: The artifact to filter
            json_path: The JSON path to extract

        Returns:
            Dictionary with extracted results

        Raises:
            ValueError: If json_path is not provided
        """
        if not json_path:
            raise ValueError("JSON path filter requires filter_value")

        results: List[Any] = []

        for part in artifact.parts:
            if isinstance(part.root, DataPart):
                try:
                    result = ArtifactFilter._evaluate_json_path(part.root.data, json_path)
                    results.append(result)
                except (KeyError, IndexError, TypeError):
                    # Path doesn't exist in this part, continue
                    pass

        return {
            "artifact_id": artifact.artifact_id,
            "filter_type": "json_path",
            "path": json_path,
            "results": results,
            "result_count": len(results),
        }

    @staticmethod
    def _evaluate_json_path(data: Any, path: str) -> Any:
        """Evaluate simple JSON path.

        Args:
            data: The data to query
            path: The JSON path (e.g., "users[0].name")

        Returns:
            The extracted value

        Raises:
            KeyError: If field doesn't exist
            IndexError: If index out of bounds
            TypeError: If path is invalid for data type
        """
        # Simple parser for paths like: "field", "field.nested", "array[0]"
        # Split on . and [ ] but keep the brackets for index detection
        parts = re.split(r"\.|\[|\]", path)
        parts = [p for p in parts if p]  # Remove empty strings

        current = data
        for part in parts:
            if part.isdigit():
                # Array index
                current = current[int(part)]
            else:
                # Object field
                current = current[part]

        return current

    @staticmethod
    def _filter_field(artifact: Artifact, field_name: Optional[str]) -> Dict[str, Any]:
        """Filter to show only specific top-level field.

        Args:
            artifact: The artifact to filter
            field_name: The field name to extract

        Returns:
            Dictionary with extracted field values

        Raises:
            ValueError: If field_name is not provided
        """
        if not field_name:
            raise ValueError("Field filter requires filter_value (field name)")

        results: List[Any] = []

        for part in artifact.parts:
            if isinstance(part.root, DataPart):
                data = part.root.data
                if isinstance(data, dict) and field_name in data:
                    results.append(data[field_name])

        return {
            "artifact_id": artifact.artifact_id,
            "filter_type": "field",
            "field": field_name,
            "values": results,
            "value_count": len(results),
        }
