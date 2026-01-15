"""Utility functions for artifact viewing and data analysis."""

import json
import random
import statistics
from itertools import chain
from typing import Any, Union

# Constants
MAX_OUTPUT_CHARS = 10_000
MINIMIZATION_THRESHOLD = 2_500
HALF_THRESHOLD = MINIMIZATION_THRESHOLD // 2  # 1,250
STRING_TRUNCATE_LENGTH = 100


def generate_column_summary(values: list[Any]) -> dict[str, Any]:
    """Generate a summary of a list of values (like a single column).

    Args:
        values: List of values to summarize.

    Returns:
        Dictionary with column-like statistics. Type-specific stats are
        included in each type entry within the types array.
    """
    if not values:
        return {"count": 0, "types": []}

    count = len(values)

    # Calculate unique count
    unique_values = []
    for v in values:
        if isinstance(v, (dict, list)):
            unique_values.append(json.dumps(v, sort_keys=True))
        else:
            unique_values.append(v)
    unique_count = len(set(unique_values))

    # Group values by type
    type_groups: dict[str, list[Any]] = {}
    for v in values:
        if v is None:
            type_name = "null"
        elif isinstance(v, bool):
            type_name = "bool"
        elif isinstance(v, int):
            type_name = "int"
        elif isinstance(v, float):
            type_name = "float"
        elif isinstance(v, str):
            type_name = "string"
        elif isinstance(v, list):
            type_name = "list"
        elif isinstance(v, dict):
            type_name = "object"
        else:
            type_name = type(v).__name__

        if type_name not in type_groups:
            type_groups[type_name] = []
        type_groups[type_name].append(v)

    # Build types array with stats included in each type
    types = []
    for type_name, type_values in sorted(type_groups.items(), key=lambda x: -len(x[1])):
        type_count = len(type_values)
        percentage = (type_count / count) * 100
        type_entry: dict[str, Any] = {
            "name": type_name,
            "count": type_count,
            "percentage": round(percentage, 1),
        }

        # Add sample value for this type
        type_entry["sample_value"] = random.choice(type_values)

        # Add type-specific statistics
        if type_name == "string":
            lengths = [len(s) for s in type_values]
            type_entry["length_minimum"] = min(lengths)
            type_entry["length_maximum"] = max(lengths)
            type_entry["length_average"] = round(statistics.mean(lengths), 2)
            if len(lengths) > 1:
                type_entry["length_stdev"] = round(statistics.stdev(lengths), 2)
        elif type_name in ("int", "float"):
            type_entry["minimum"] = min(type_values)
            type_entry["maximum"] = max(type_values)
            type_entry["average"] = round(statistics.mean(type_values), 2)
            if len(type_values) > 1:
                type_entry["stdev"] = round(statistics.stdev(type_values), 2)
        elif type_name == "object":
            json_lengths = [len(json.dumps(obj)) for obj in type_values]
            type_entry["json_length_minimum"] = min(json_lengths)
            type_entry["json_length_maximum"] = max(json_lengths)
            type_entry["json_length_average"] = round(statistics.mean(json_lengths), 2)
            if len(json_lengths) > 1:
                type_entry["json_length_stdev"] = round(statistics.stdev(json_lengths), 2)
        elif type_name == "list":
            list_lengths = [len(lst) for lst in type_values]
            type_entry["length_minimum"] = min(list_lengths)
            type_entry["length_maximum"] = max(list_lengths)
            type_entry["length_average"] = round(statistics.mean(list_lengths), 2)
            if len(list_lengths) > 1:
                type_entry["length_stdev"] = round(statistics.stdev(list_lengths), 2)
        types.append(type_entry)

    return {
        "count": count,
        "unique_count": unique_count,
        "types": types,
    }


def generate_table_summary(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate a comprehensive summary of tabular data (list of objects).

    Args:
        data: List of dictionaries representing table rows.

    Returns:
        List of dictionaries, each representing a column summary.
    """
    if not data:
        return []

    # Collect all unique column names (preserves order, handles sparse data)
    column_names = list(dict.fromkeys(
        chain.from_iterable(item.keys() for item in data if isinstance(item, dict))
    ))

    columns = []

    for column_name in column_names:
        # Collect all values for this column
        values = []
        for item in data:
            if isinstance(item, dict) and column_name in item:
                values.append(item[column_name])

        # Use generate_column_summary to get statistics
        column_summary = generate_column_summary(values)
        column_summary["name"] = column_name

        columns.append(column_summary)

    return columns


def check_output_size(output: str, context: str = "Output") -> None:
    """Check if output exceeds maximum size limit.

    Args:
        output: The output string to check
        context: Description of what is being checked (for error message)

    Raises:
        ValueError: If output exceeds MAX_OUTPUT_CHARS
    """
    if len(output) > MAX_OUTPUT_CHARS:
        raise ValueError(
            f"{context} exceeds the maximum size of {MAX_OUTPUT_CHARS:,} characters "
            f"(actual: {len(output):,} characters). "
            f"Try narrowing your selection (fewer rows, specific line range, or JSON path filter)."
        )


def minimize_text(text: str, total_lines: int | None = None) -> dict[str, Any]:
    """Minimize text content for display.

    If text is <= 2,500 chars, return it in full inside "text" key.
    If text is > 2,500 chars, show first 1,250 and last 1,250 with metadata.

    Args:
        text: The text content to minimize.
        total_lines: Optional total line count (for line range hints).

    Returns:
        Dict with "text" key containing the content or minimization metadata.
    """
    if len(text) <= MINIMIZATION_THRESHOLD:
        return {"text": text}

    # Calculate line ranges for the start and end sections
    lines = text.split("\n")
    line_count = len(lines)

    # Find which line the HALF_THRESHOLD char falls on for the start
    char_count = 0
    start_end_line = 1
    for i, line in enumerate(lines):
        char_count += len(line) + 1  # +1 for newline
        if char_count >= HALF_THRESHOLD:
            start_end_line = i + 1
            break

    # Find which line the end section starts on
    char_count = 0
    end_start_line = line_count
    for i in range(len(lines) - 1, -1, -1):
        char_count += len(lines[i]) + 1
        if char_count >= HALF_THRESHOLD:
            end_start_line = i + 1
            break

    missing_chars = len(text) - (2 * HALF_THRESHOLD)

    return {
        "text": {
            "_total_lines": total_lines if total_lines else line_count,
            "_total_characters": len(text),
            "_text_start": text[:HALF_THRESHOLD],
            "_text_start_line_range": f"1-{start_end_line}",
            "_truncated": f"[{missing_chars:,} characters omitted]",
            "_text_end": text[-HALF_THRESHOLD:],
            "_text_end_line_range": f"{end_start_line}-{line_count}",
            "_tip": "Use view_text_artifact to view specific sections.",
        }
    }


def minimize_object(obj: dict[str, Any]) -> dict[str, Any]:
    """Minimize an object for display.

    If JSON-stringified length is <= 2,500 chars, return it in full.
    If > 2,500 chars, show all keys but:
    - Truncate string values to 100 chars
    - Summarize lists of basic values as column statistics
    - Summarize lists of objects with table summary

    Returns dict with "data" key containing the minimized content.
    """
    json_str = json.dumps(obj, indent=2)
    if len(json_str) <= MINIMIZATION_THRESHOLD:
        return {"data": obj}

    # Process object with truncation and list summarization
    minimized = _minimize_object_values(obj)

    # Add _tip inside the data object
    minimized["_tip"] = (
        f"Object was minimized (original: {len(json_str):,} chars). "
        f"String values truncated to {STRING_TRUNCATE_LENGTH} chars. "
        f"Lists summarized. Use json_path to access specific fields, "
        f"with rows/columns for list data."
    )

    return {"data": minimized}


def _minimize_object_values(value: Any, depth: int = 0) -> Any:
    """Recursively minimize values in an object.

    - Truncate strings to STRING_TRUNCATE_LENGTH
    - Summarize lists of basic values as column statistics
    - Summarize lists of objects with table summary

    Args:
        value: The value to process
        depth: Current recursion depth

    Returns:
        Processed value with truncated strings and summarized lists
    """
    if depth > 10:  # Prevent infinite recursion
        return "..."

    if isinstance(value, str):
        if len(value) > STRING_TRUNCATE_LENGTH:
            remaining = len(value) - STRING_TRUNCATE_LENGTH
            return f"{value[:STRING_TRUNCATE_LENGTH]}... [{remaining:,} more chars]"
        return value

    elif isinstance(value, dict):
        return {k: _minimize_object_values(v, depth + 1) for k, v in value.items()}

    elif isinstance(value, list):
        if not value:
            return value

        # Check if list of objects (tabular data)
        if isinstance(value[0], dict):
            return {
                "_total_rows": len(value),
                "_columns": generate_table_summary(value),
            }

        # List of basic values - generate column summary
        return {
            "_total_items": len(value),
            "_summary": generate_column_summary(value),
        }

    else:
        return value


def minimize_list_of_objects(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Minimize a list of objects (table data) for display.

    Shows _total_rows and generates a table summary inside "data" key.

    Returns dict with "data" key containing minimization metadata.
    """
    summary = generate_table_summary(data)

    return {
        "data": {
            "_total_rows": len(data),
            "_columns": summary,
            "_tip": "Table data was minimized. Use view_data_artifact to view specific data.",
        }
    }


def minimize_data(data: Any) -> dict[str, Any]:
    """Minimize data content for display based on type.

    Args:
        data: The data to minimize

    Returns:
        Minimized representation with "data" or "text" key
    """
    json_str = json.dumps(data, indent=2) if not isinstance(data, str) else data
    str_len = len(json_str)

    # Check if minimization is needed
    if str_len <= MINIMIZATION_THRESHOLD:
        return {"data": data}

    # Handle lists
    if isinstance(data, list) and data:
        # List of objects (table data)
        if isinstance(data[0], dict):
            return minimize_list_of_objects(data)

        # List of basic values - generate column summary
        return {
            "data": {
                "_total_items": len(data),
                "_summary": generate_column_summary(data),
                "_tip": (
                    f"List was minimized (original: {str_len:,} chars, {len(data)} items). "
                    f"Use rows parameter to access specific items."
                ),
            }
        }

    # Handle objects
    if isinstance(data, dict):
        return minimize_object(data)

    # Handle empty lists
    if isinstance(data, list):
        return {"data": data}

    # Handle strings
    if isinstance(data, str):
        return minimize_text(data)

    # Fallback for other types (primitives)
    return {"data": data}


def parse_row_selection(
    rows: Union[int, list[int], str],
    total_rows: int,
) -> list[int]:
    """Parse the row selection parameter into a list of row indices.

    Args:
        rows: Can be a single row index (int), list of indices, range string ("0-10"), or "all"
        total_rows: Total number of rows in the dataset

    Returns:
        List of row indices to include
    """
    if isinstance(rows, int):
        # Single row - handle negative indices
        if rows < 0:
            rows = total_rows + rows
        if rows < 0 or rows >= total_rows:
            raise ValueError(f"Row index {rows} is out of range for dataset with {total_rows} rows")
        return [rows]
    elif isinstance(rows, list):
        # List of rows
        validated_rows = []
        for row in rows:
            if row < 0:
                row = total_rows + row
            if row < 0 or row >= total_rows:
                raise ValueError(
                    f"Row index {row} is out of range for dataset with {total_rows} rows"
                )
            validated_rows.append(row)
        return validated_rows
    elif isinstance(rows, str):
        if rows == "all":
            return list(range(total_rows))
        # Range string like "0-10" or "0:-1"
        if "-" in rows:
            parts = rows.split("-", 1)
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid range format: {rows}. Expected format: 'start-end' (e.g., '0-10')"
                )

            try:
                start_str, end_str = parts
                # Handle negative indices in string format
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else total_rows

                # Convert negative indices
                if start < 0:
                    start = total_rows + start
                if end < 0:
                    end = total_rows + end

                # Validate range
                if start < 0 or start >= total_rows:
                    raise ValueError(f"Start index {start} is out of range")
                if end < 0 or end > total_rows:
                    raise ValueError(f"End index {end} is out of range")
                if start > end:
                    raise ValueError(f"Start index {start} is greater than end index {end}")

                return list(range(start, end))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(
                        f"Invalid range format: {rows}. Expected integers in 'start-end' format."
                    ) from e
                raise
        else:
            raise ValueError(
                f"Invalid row selection: {rows}. "
                f"Must be an integer, list of integers, 'all', or a range like '0-10'"
            )
    else:
        raise ValueError(f"Invalid row selection type: {type(rows)}")


def parse_column_selection(
    columns: Union[str, list[str]],
    available_columns: list[str],
) -> list[str]:
    """Parse the column selection parameter into a list of column names.

    Args:
        columns: Can be a single column name (str), list of column names, or "all"
        available_columns: List of all available column names in the dataset

    Returns:
        List of column names to include
    """
    if isinstance(columns, str):
        if columns == "all":
            return available_columns
        # Single column
        if columns not in available_columns:
            raise ValueError(
                f"Column '{columns}' not found. Available columns: {', '.join(available_columns)}"
            )
        return [columns]
    elif isinstance(columns, list):
        # List of columns
        for col in columns:
            if col not in available_columns:
                raise ValueError(
                    f"Column '{col}' not found. Available columns: {', '.join(available_columns)}"
                )
        return columns
    else:
        raise ValueError(f"Invalid column selection type: {type(columns)}")


def filter_data_by_rows_and_columns(
    data: list[dict[str, Any]],
    row_indices: list[int],
    column_names: list[str],
) -> list[dict[str, Any]]:
    """Filter data by row indices and column names.

    Args:
        data: The full dataset
        row_indices: List of row indices to include
        column_names: List of column names to include

    Returns:
        Filtered data
    """
    filtered_data = []

    for row_idx in row_indices:
        if row_idx >= len(data):
            continue

        row = data[row_idx]
        filtered_row = {}

        for col in column_names:
            if col in row:
                filtered_row[col] = row[col]

        filtered_data.append(filtered_row)

    return filtered_data


def evaluate_json_path(data: Any, path: str) -> Any:
    """Evaluate a JSONPath-like expression for field access only.

    Supports:
    - "field" - top-level field
    - "field.nested" - nested field access

    Does NOT support array indexing - use rows/columns parameters instead.

    Args:
        data: The data to query
        path: The dot-separated field path

    Returns:
        The extracted value

    Raises:
        KeyError: If field doesn't exist
        TypeError: If trying to access field on non-object
    """
    if not path:
        return data

    parts = path.split(".")
    current = data

    for part in parts:
        if not isinstance(current, dict):
            raise TypeError(
                f"Cannot access field '{part}' on {type(current).__name__}. "
                f"Use rows/columns parameters to filter list data."
            )
        if part not in current:
            available = ", ".join(current.keys()) if current else "(empty)"
            raise KeyError(f"Field '{part}' not found. Available fields: {available}")
        current = current[part]

    return current


def parse_line_range(
    line_start: int | None, line_end: int | None, total_lines: int
) -> tuple[int, int]:
    """Parse line range parameters.

    Args:
        line_start: Starting line number (1-based, inclusive). None means 1.
        line_end: Ending line number (1-based, inclusive). None means total_lines.
        total_lines: Total number of lines

    Returns:
        Tuple of (start_index, end_index) as 0-based indices

    Raises:
        ValueError: If line numbers are invalid
    """
    # Default values
    start = line_start if line_start is not None else 1
    end = line_end if line_end is not None else total_lines

    # Handle negative line numbers (count from end)
    if start < 0:
        start = total_lines + start + 1
    if end < 0:
        end = total_lines + end + 1

    # Validate range
    if start < 1:
        raise ValueError(f"line_start must be >= 1 (got {start})")
    if end > total_lines:
        raise ValueError(f"line_end ({end}) exceeds total lines ({total_lines})")
    if start > end:
        raise ValueError(f"line_start ({start}) must be <= line_end ({end})")

    # Convert to 0-based indices
    return start - 1, end
