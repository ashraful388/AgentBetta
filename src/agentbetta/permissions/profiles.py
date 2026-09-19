"""User-selectable permission profiles.

Every profile exposes its exact capabilities so the GUI can show the user what
they are granting. ``hard_denied`` blocks adaptive activation even when a
permission is otherwise eligible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentbetta.core.models import PermissionSet
from agentbetta.permissions.policy import (
    ALL_PERMISSIONS,
    BROWSER_DOWNLOAD,
    BROWSER_INTERACT,
    BROWSER_READ,
    DESKTOP_CONTROL,
    DESKTOP_READ,
    FILE_DELETE,
    FILE_READ,
    FILE_WRITE,
    MEMORY_READ,
    MEMORY_WRITE,
    NETWORK_HTTP,
    NETWORK_SHARE,
    PROCESS_LAUNCH,
    SHELL_EXEC,
)


@dataclass(frozen=True)
class PermissionProfile:
    key: str
    label: str
    description: str
    allowed: frozenset[str] = field(default_factory=frozenset)
    eligible: frozenset[str] = field(default_factory=frozenset)
    hard_denied: frozenset[str] = field(default_factory=frozenset)

    def to_permission_set(self) -> PermissionSet:
        return PermissionSet(allowed=self.allowed, eligible=self.eligible, hard_denied=self.hard_denied)

    def inspect(self) -> dict[str, list[str]]:
        return {
            "allowed": sorted(self.allowed),
            "eligible": sorted(self.eligible),
            "hard_denied": sorted(self.hard_denied),
        }


PROFILE_SAFE = PermissionProfile(
    key="safe",
    label="Safe / Read-Only",
    description="Read files and public web pages. No writes, deletes, shell or process launch.",
    allowed=frozenset({FILE_READ, NETWORK_HTTP, BROWSER_READ, MEMORY_READ}),
    eligible=frozenset({FILE_READ, NETWORK_HTTP, BROWSER_READ, MEMORY_READ}),
    hard_denied=frozenset(
        {
            FILE_WRITE,
            FILE_DELETE,
            SHELL_EXEC,
            PROCESS_LAUNCH,
            NETWORK_SHARE,
            BROWSER_INTERACT,
            BROWSER_DOWNLOAD,
            DESKTOP_READ,
            DESKTOP_CONTROL,
            MEMORY_WRITE,
        }
    ),
)

PROFILE_STANDARD = PermissionProfile(
    key="standard",
    label="Standard",
    description="Read and write user files, browse and interact with pages, downloads with approval.",
    allowed=frozenset(
        {
            FILE_READ,
            FILE_WRITE,
            NETWORK_HTTP,
            BROWSER_READ,
            BROWSER_INTERACT,
            MEMORY_READ,
            MEMORY_WRITE,
        }
    ),
    eligible=frozenset({FILE_DELETE, BROWSER_DOWNLOAD, NETWORK_SHARE}),
    hard_denied=frozenset({SHELL_EXEC, PROCESS_LAUNCH, DESKTOP_READ, DESKTOP_CONTROL}),
)

PROFILE_EXTENDED = PermissionProfile(
    key="extended",
    label="Extended",
    description="Read, write, move, delete, bounded shell and process launch, full browser use.",
    allowed=frozenset(
        {
            FILE_READ,
            FILE_WRITE,
            FILE_DELETE,
            NETWORK_HTTP,
            NETWORK_SHARE,
            BROWSER_READ,
            BROWSER_INTERACT,
            BROWSER_DOWNLOAD,
            PROCESS_LAUNCH,
            SHELL_EXEC,
            MEMORY_READ,
            MEMORY_WRITE,
        }
    ),
    eligible=frozenset({DESKTOP_READ, DESKTOP_CONTROL}),
    hard_denied=frozenset({DESKTOP_CONTROL}),
)

PROFILE_FULL = PermissionProfile(
    key="full",
    label="Full Computer",
    description=(
        "All supported local computer, shell, process and browser capabilities, still subject to "
        "Windows security/UAC and AgentBetta hard rules."
    ),
    allowed=ALL_PERMISSIONS,
    eligible=ALL_PERMISSIONS,
    hard_denied=frozenset(),
)

PROFILES: dict[str, PermissionProfile] = {
    PROFILE_SAFE.key: PROFILE_SAFE,
    PROFILE_STANDARD.key: PROFILE_STANDARD,
    PROFILE_EXTENDED.key: PROFILE_EXTENDED,
    PROFILE_FULL.key: PROFILE_FULL,
}

DEFAULT_PROFILE_KEY = "safe"


def get_profile(key: str) -> PermissionProfile:
    return PROFILES.get(key, PROFILE_SAFE)


def profile_permission_set(key: str) -> PermissionSet:
    return get_profile(key).to_permission_set()


def inspect_profiles() -> dict[str, dict[str, list[str]]]:
    return {key: profile.inspect() for key, profile in PROFILES.items()}
