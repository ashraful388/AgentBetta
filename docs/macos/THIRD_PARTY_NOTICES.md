# Third-Party Notices — AgentBetta 0.2.0-alpha.2 (macOS)

AgentBetta's own source code is licensed under the **MIT License**
(Copyright (c) 2026 Dr. Md. Ashraful Babu; see `LICENSE`). This document covers
the third-party components that AgentBetta includes or depends on; each remains
under its own license.

## Bundled components

| Component | License | Use |
|---|---|---|
| PySide6 / Qt for Python (Qt 6) | LGPL-3.0 (GPL/commercial options) | Desktop GUI |
| shiboken6 | LGPL-3.0 | PySide6 bindings |
| playwright (Python) | Apache-2.0 | Browser automation (drives Chromium; Edge optional) |
| keyring | MIT | macOS Keychain access |
| httpx | BSD-3-Clause | HTTP client |
| pypdf | BSD-3-Clause | PDF text extraction (optional) |
| PyYAML | MIT | YAML task files (optional) |
| PyInstaller | GPL-2.0 with bootloader exception | Application bundling |
| pytest | MIT | Test suite (development) |
| ruff | MIT | Linting (development) |

Chromium (via Playwright) is not redistributed with AgentBetta unless you run
`playwright install chromium`; Microsoft Edge for Mac and Ollama are used from
the user's machine or installed separately.

No large language-model weights are bundled.

## Qt / PySide6 LGPL-3.0 compliance

AgentBetta dynamically links Qt through PySide6. The LGPL-3.0 requires that:

1. The LGPL-3.0 text and the GPL-3.0 text it references are shipped with the
   application — see `LICENSES/LGPL-3.0.txt` and `LICENSES/GPL-3.0.txt`.
2. Qt remains dynamically linked (the PyInstaller bundle keeps the Qt
   `.dylib`/framework files separate from the application executable).
3. Users can replace the Qt libraries.
4. The corresponding Qt source is made available, or a written offer to provide
   it is given. Qt source: <https://www.qt.io/> and <https://code.qt.io/>.
5. Qt copyright and license notices are preserved.

If meeting these obligations is not desired, a commercial Qt license from The
Qt Company is the alternative. See `LICENSES/README.md` for details.
