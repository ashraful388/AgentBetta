"""Platform abstraction.

The scientific core is platform-neutral. This package selects the concrete
platform implementation (Windows or macOS) at import time and exposes it as
``agentbetta.platform.paths`` / ``filesystem`` / ``processes`` / ``credentials``.

Both platform packages are kept in the source tree; the correct one is selected
by ``sys.platform``. The non-target package is never imported.
"""

from __future__ import annotations

import sys

PLATFORM_NAME = "macos" if sys.platform == "darwin" else "windows"

if PLATFORM_NAME == "macos":
    from agentbetta.platform.macos import credentials, filesystem, paths, processes
else:
    from agentbetta.platform.windows import credentials, filesystem, paths, processes

# Alias the selected implementation as submodules so both
# ``from agentbetta.platform import paths`` and
# ``from agentbetta.platform.paths import known_folders`` work on every platform.
for _name, _module in (
    ("credentials", credentials),
    ("filesystem", filesystem),
    ("paths", paths),
    ("processes", processes),
):
    sys.modules.setdefault(f"agentbetta.platform.{_name}", _module)
del _name, _module

PREFERRED_BROWSER_ENGINE = "chromium" if PLATFORM_NAME == "macos" else "msedge"

__all__ = [
    "PLATFORM_NAME",
    "PREFERRED_BROWSER_ENGINE",
    "credentials",
    "filesystem",
    "paths",
    "processes",
]
