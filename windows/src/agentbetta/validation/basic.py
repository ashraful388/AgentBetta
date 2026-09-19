from __future__ import annotations
from agentbetta.core.models import ProviderResponse, ToolResult, VerificationResult, VerificationStatus


class BasicValidator:
    def verify(self, response: ProviderResponse, tool_results: list[ToolResult] | None = None) -> VerificationResult:
        # Tool evidence is more specific than a coarse provider failure, so it is
        # evaluated first (e.g. a denied permission must drive permission diagnosis).
        for result in tool_results or []:
            error = result.error or ""
            if "permission_denied" in error:
                name = error.split("permission_denied:", 1)[1].strip() if "permission_denied:" in error else None
                return VerificationResult(
                    VerificationStatus.FAIL,
                    f"Tool permission denied: {name or result.tool_name}",
                    {"permission_denied": True, "permission_denied_name": name},
                )
            if "Unknown tool" in error:
                return VerificationResult(
                    VerificationStatus.FAIL,
                    f"Unknown tool requested: {result.tool_name}",
                    {"missing_tool": True, "missing_tool_name": result.tool_name},
                )
            if "approval_denied" in error:
                return VerificationResult(
                    VerificationStatus.FAIL,
                    "A required action was not approved",
                    {"approval_denied": True, "approval_denied_tool": result.tool_name},
                )

        failure=response.raw.get("failure") if isinstance(response.raw,dict) else None
        if failure:
            mapping={
                "permission_denied":{"permission_denied":True},
                "missing_tool":{"missing_tool":True},
                "context_truncated":{"context_truncated":True},
                "token_limit":{"token_limit":True},
                "timeout":{"timeout":True},
                "turn_limit":{"turn_limit":True},
                "tool_limit":{"tool_limit":True},
                "model_insufficient":{"model_insufficient":True},
                "provider_error":{"provider_error":True},
            }
            detail = response.raw.get("message") if isinstance(response.raw, dict) else None
            reason = f"Structured failure: {failure}"
            evidence = dict(mapping.get(failure, {}))
            if detail:
                reason = f"{reason} — {detail}"
                evidence["provider_message"] = detail
            return VerificationResult(VerificationStatus.FAIL, reason, evidence)

        if not response.text.strip():
            return VerificationResult(VerificationStatus.INSUFFICIENT_EVIDENCE, "Provider returned no usable output", {})
        return VerificationResult(VerificationStatus.PASS, "Non-empty provider output passed the v0.1 basic validator", {"nonempty":True})
