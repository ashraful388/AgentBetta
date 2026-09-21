"""Explicit approval handling for high-risk actions.

The adaptive model can never approve its own high-risk action: an approval must
come from the user (GUI dialog) or, in headless use, from an explicit policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

HIGH_RISK = frozenset({"high", "destructive"})
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "destructive": 3}


class ApprovalDecision(str, Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_RUN = "allow_run"
    DENY = "deny"


@dataclass
class ApprovalRequest:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    permission: str | None = None
    risk: str = "low"
    reason: str = ""


ApprovalCallback = Callable[[ApprovalRequest], ApprovalDecision]


class ApprovalService:
    """Approval gate used by the tool loop.

    ``callback`` is the interactive GUI hook. When no callback is configured,
    only low/medium-risk actions are auto-approved; high/destructive actions are
    denied (fail-safe), never silently allowed.
    """

    def __init__(self, callback: ApprovalCallback | None = None, *,
                 auto_approve_max_risk: str = "medium",
                 auto_approve_all: bool = False) -> None:
        self.callback = callback
        self.auto_approve_max_risk = auto_approve_max_risk
        # When True (e.g. the Full Computer profile, or the user enabled it in
        # Settings), every action is approved without a prompt. Decisions are
        # still recorded in ``history`` for the audit trail.
        self.auto_approve_all = bool(auto_approve_all)
        self._run_allowed: set[tuple[str, str | None]] = set()
        self._run_denied: set[tuple[str, str | None]] = set()
        self.history: list[dict[str, Any]] = []

    @staticmethod
    def _key(tool_name: str, permission: str | None) -> tuple[str, str | None]:
        return (tool_name, permission)

    def requires_approval(self, risk: str) -> bool:
        return risk == "destructive" or risk == "high"

    def request_tool(self, *, tool_name: str, arguments: dict[str, Any],
                     permission: str | None, risk: str, reason: str) -> bool:
        key = self._key(tool_name, permission)
        if self.auto_approve_all:
            self.history.append({"tool_name": tool_name, "decision": "auto_all", "risk": risk})
            return True
        if key in self._run_denied:
            # A denial is a durable user decision for this run: never re-prompt
            # for the same action.
            self.history.append({"tool_name": tool_name, "decision": "deny(cached)", "risk": risk})
            return False
        if key in self._run_allowed:
            self.history.append({"tool_name": tool_name, "decision": "allow_run(cached)", "risk": risk})
            return True
        if not self.requires_approval(risk) and RISK_ORDER.get(risk, 3) <= RISK_ORDER.get(self.auto_approve_max_risk, 1):
            self.history.append({"tool_name": tool_name, "decision": "auto", "risk": risk})
            return True
        if self.callback is None:
            self.history.append({"tool_name": tool_name, "decision": "deny(no_callback)", "risk": risk})
            return False
        decision = self.callback(
            ApprovalRequest(tool_name=tool_name, arguments=arguments, permission=permission,
                            risk=risk, reason=reason)
        )
        if decision == ApprovalDecision.ALLOW_RUN:
            self._run_allowed.add(key)
            self.history.append({"tool_name": tool_name, "decision": "allow_run", "risk": risk})
            return True
        if decision == ApprovalDecision.ALLOW_ONCE:
            self.history.append({"tool_name": tool_name, "decision": "allow_once", "risk": risk})
            return True
        self._run_denied.add(key)
        self.history.append({"tool_name": tool_name, "decision": "deny", "risk": risk})
        return False
