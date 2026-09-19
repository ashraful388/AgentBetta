from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from agentbetta.core.models import PermissionSet
from agentbetta.tools.schema import validate_arguments
from agentbetta.tools.workspace import Workspace

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


@runtime_checkable
class ApprovalHook(Protocol):
    def request_tool(
        self, *, tool_name: str, arguments: dict[str, Any], permission: str | None,
        risk: str, reason: str,
    ) -> bool: ...


@dataclass
class ToolContext:
    workspace: Workspace | None = None
    permissions: PermissionSet = field(default_factory=PermissionSet)
    cancel_token: Any = None
    approvals: Any = None
    settings: Any = None
    browser: Any = None
    memory: Any = None
    cwd: str | None = None

    def require_workspace(self) -> Workspace:
        if self.workspace is None:
            raise PermissionError("This tool requires a workspace context")
        return self.workspace


@dataclass(frozen=True)
class ToolSpec:
    name: str
    permission: str | None
    risk: str
    function: Callable[..., Any]
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}},
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def spec(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def schemas(self, names: tuple[str, ...] | list[str] | None = None) -> list[dict[str, Any]]:
        selected = self._tools if names is None else {n: self._tools[n] for n in names if n in self._tools}
        return [spec.schema() for spec in selected.values()]

    def execute(
        self,
        name: str,
        args: dict[str, Any],
        *,
        workspace: Workspace | None = None,
        permissions: PermissionSet | None = None,
        ctx: ToolContext | None = None,
    ) -> Any:
        context = ctx or ToolContext(
            workspace=workspace, permissions=permissions or PermissionSet()
        )
        return self.execute_ctx(name, args, context)

    def execute_ctx(self, name: str, args: dict[str, Any], ctx: ToolContext) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        spec = self._tools[name]
        if spec.permission and not ctx.permissions.permits(spec.permission):
            raise PermissionError(f"Tool {name} requires permission {spec.permission}")
        clean = validate_arguments(spec.parameters, args)
        return spec.function(ctx=ctx, **clean)


def _list_directory(*, ctx: ToolContext, path: str = ".") -> list[str]:
    ws = ctx.require_workspace()
    p = ws.resolve(path)
    return sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir())[:500]


def _read_text_file(*, ctx: ToolContext, path: str, max_chars: int = 100_000) -> str:
    ws = ctx.require_workspace()
    p = ws.resolve(path)
    return p.read_text(encoding="utf-8", errors="replace")[:max_chars]


def _write_text_file(*, ctx: ToolContext, path: str, content: str) -> dict[str, Any]:
    ws = ctx.require_workspace()
    p = ws.resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"path": str(p.relative_to(ws.root)), "chars": len(content)}


def _calc_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_calc_node(node.left), _calc_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_calc_node(node.operand))
    raise ValueError("Unsupported calculator expression")


def _calculator(*, ctx: ToolContext, expression: str) -> float:
    return _calc_node(ast.parse(expression, mode="eval").body)


def default_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(
        ToolSpec(
            "list_directory",
            "file_read",
            "low",
            _list_directory,
            description="List files and folders inside the current workspace directory.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative directory path."}},
                "additionalProperties": False,
            },
        )
    )
    r.register(
        ToolSpec(
            "read_text_file",
            "file_read",
            "low",
            _read_text_file,
            description="Read a UTF-8 text file from the current workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        )
    )
    r.register(
        ToolSpec(
            "write_text_file",
            "file_write",
            "medium",
            _write_text_file,
            description="Create or overwrite a UTF-8 text file in the current workspace.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        )
    )
    r.register(
        ToolSpec(
            "calculator",
            None,
            "low",
            _calculator,
            description="Evaluate a basic arithmetic expression (+, -, *, /, //, %, **).",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        )
    )
    return r
