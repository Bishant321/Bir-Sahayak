import json
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator


def definition(name, description, properties=None, required=None):
    return {"name": name, "description": description, "input_schema": {
        "type": "object", "properties": properties or {}, "required": required or [],
        "additionalProperties": False}}


COLUMNS = {"type": "array", "items": {"type": "string"}, "minItems": 1, "uniqueItems": True}
TOOLS = [
    definition("dataset_info", "Get verified row count, column names and types, missing cells and duplicate count."),
    definition("find_nulls", "Count missing values and their percentages in every column. Does not change data."),
    definition("find_duplicates", "Count duplicate rows after their first occurrence, optionally using specific columns.", {"columns": COLUMNS}),
    definition("remove_duplicates", "Remove duplicate rows, keeping the first. Only use when the user asks to remove duplicates.", {"columns": COLUMNS}),
    definition("fill_missing", "Fill nulls in selected columns. Auto uses numeric median or categorical mode. Ask for clarification if the user's target columns or intent are unclear.", {
        "columns": COLUMNS, "strategy": {"type": "string", "enum": ["auto", "mean", "median", "mode", "constant"]},
        "value": {"type": ["string", "number", "boolean"]}}, ["columns", "strategy"]),
    definition("create_chart", "Render a local Plotly chart. For category counts use bar and count; sum/mean require numeric y. Raw charts are sampled above 5,000 rows; aggregates use all complete rows.", {
        "kind": {"type": "string", "enum": ["bar", "line", "scatter", "histogram"]},
        "x": {"type": "string"}, "y": {"type": "string"},
        "aggregation": {"type": "string", "enum": ["none", "count", "sum", "mean"]}}, ["kind", "x"]),
    definition("query_sql", "Answer analytical questions using one read-only DuckDB SELECT over dataset. Quote column names with double quotes. No files, network, extensions, recursive queries or write operations. At most 50 result rows are returned.", {
        "query": {"type": "string", "maxLength": 10000}}, ["query"]),
    definition("undo", "Reverse the most recent data change. Only use when requested."),
    definition("change_history", "Show the most recent 20 dataset changes and available undo steps."),
]
SCHEMAS = {tool["name"]: Draft202012Validator(tool["input_schema"]) for tool in TOOLS}


@dataclass
class ToolResult:
    name: str
    arguments: dict
    data: dict
    figure: Any = None
    error: bool = False

    def for_model(self):
        # Keep tool payloads bounded, including very long text returned by SQL.
        encoded = json.dumps(self.data, ensure_ascii=False, default=str)
        if len(encoded) > 16000:
            return json.dumps({"error": "Result exceeds the 16,000-character model limit. Use an aggregate or a narrower query.",
                               "result_withheld": True})
        return encoded


def execute(dataset, name, arguments):
    try:
        if name not in SCHEMAS:
            raise ValueError("Unknown tool. Use one of the declared tools.")
        errors = list(SCHEMAS[name].iter_errors(arguments))
        if errors:
            raise ValueError(f"Invalid tool arguments: {errors[0].message[:300]}")
        method = dataset.info if name == "dataset_info" else getattr(dataset, name)
        value = method(**arguments)
        if name == "create_chart":
            return ToolResult(name, arguments, value[0], figure=value[1])
        return ToolResult(name, arguments, value)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return ToolResult(name, arguments, {"error": str(exc)[:600]}, error=True)
