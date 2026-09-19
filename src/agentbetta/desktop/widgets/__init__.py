"""Reusable desktop widgets."""

from agentbetta.desktop.widgets.approval_dialog import ApprovalDialog
from agentbetta.desktop.widgets.onboarding import OnboardingDialog
from agentbetta.desktop.widgets.report import build_details_markdown, build_result_markdown

__all__ = ["ApprovalDialog", "OnboardingDialog", "build_details_markdown", "build_result_markdown"]
