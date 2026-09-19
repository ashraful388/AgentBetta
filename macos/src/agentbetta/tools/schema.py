"""Minimal JSON-schema argument validation for tool calls.

Model-supplied arguments are untrusted. Only declared, correctly typed
arguments reach a tool function.
"""

from __future__ import annotations

from typing import Any

_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


class ToolArgumentError(ValueError):
    pass


def validate_arguments(schema: dict[str, Any] | None, args: Any) -> dict[str, Any]:
    if args is None:
        args = {}
    if not isinstance(args, dict):
        raise ToolArgumentError("Tool arguments must be a JSON object")
    schema = schema or {"type": "object", "properties": {}}
    properties = schema.get("properties") or {}
    required = schema.get("required") or []
    for key in required:
        if key not in args:
            raise ToolArgumentError(f"Missing required argument: {key}")
    if schema.get("additionalProperties", True) is False:
        for key in args:
            if key not in properties:
                raise ToolArgumentError(f"Unexpected argument: {key}")
    for key, value in args.items():
        spec = properties.get(key)
        if not spec or value is None:
            continue
        expected = spec.get("type")
        py_type = _TYPE_MAP.get(expected) if expected else None
        if py_type is None:
            continue
        if isinstance(value, bool) and expected in ("integer", "number"):
            raise ToolArgumentError(f"Argument {key} must be {expected}")
        if not isinstance(value, py_type):
            raise ToolArgumentError(f"Argument {key} must be {expected}")
    return dict(args)
