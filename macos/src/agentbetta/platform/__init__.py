"""Platform abstraction (macOS build).

Exposes the macOS platform implementation as ``agentbetta.platform.paths`` /
``filesystem`` / ``processes`` / ``credentials``. The scientific core is
platform-neutral; this is the only platform-specific package in this tree.
"""

from __future__ import annotations

import sys

from agentbetta.platform.macos import credentials, filesystem, paths, processes

PLATFORM_NAME = "macos"
PREFERRED_BROWSER_ENGINE = "chromium"

# Alias the implementation as submodules so both
# ``from agentbetta.platform import paths`` and
# ``from agentbetta.platform.paths import known_folders`` work.
for _name, _module in (
    ("credentials", credentials),
    ("filesystem", filesystem),
    ("paths", paths),
    ("processes", processes),
):
    sys.modules.setdefault(f"agentbetta.platform.{_name}", _module)
del _name, _module

__all__ = [
    "PLATFORM_NAME",
    "PREFERRED_BROWSER_ENGINE",
    "credentials",
    "filesystem",
    "paths",
    "processes",
]
