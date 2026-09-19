"""Tool-level permission guards.

The registry already checks permissions; these decorators add defense in depth
so a tool function can never be invoked without its required permission, even if
called directly.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from agentbetta.tools.registry import ToolContext


def requires(permission: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(function)
        def wrapper(*, ctx: ToolContext, **kwargs: Any) -> Any:
            if not ctx.permissions.permits(permission):
                raise PermissionError(f"Permission required: {permission}")
            return function(ctx=ctx, **kwargs)

        return wrapper

    return decorator
