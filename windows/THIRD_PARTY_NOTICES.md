# Third-Party Notices — AgentBetta 0.2.0-alpha.1

AgentBetta's own source code is licensed under the **MIT License**
(Copyright (c) 2026 Dr. Md. Ashraful Babu; see `LICENSE`). This document covers
the third-party components that AgentBetta includes or depends on; each remains
under its own license.

## Bundled components

| Component | License | Use |
|---|---|---|
| PySide6 / Qt for Python (Qt 6) | LGPL-3.0 (GPL/commercial options) | Desktop GUI |
| shiboken6 | LGPL-3.0 | PySide6 bindings |
| playwright (Python) | Apache-2.0 | Browser automation (drives installed Microsoft Edge) |
| keyring | MIT | Windows Credential Manager access |
| httpx | BSD-3-Clause | HTTP client |
| pypdf | BSD-3-Clause | PDF text extraction (optional) |
| PyYAML | MIT | YAML task files (optional) |
| PyInstaller | GPL-2.0 with bootloader exception | Application bundling |
| Inno Setup | Inno Setup License (freeware) | Installer |
| pytest | MIT | Test suite (development) |
| ruff | MIT | Linting (development) |

Microsoft Edge is a Microsoft product and is not redistributed with AgentBetta;
the browser layer uses the copy installed on the user's machine. Ollama is not
bundled and is installed separately by the user when desired.

No large language-model weights are bundled.

## Qt / PySide6 LGPL-3.0 compliance

AgentBetta dynamically links Qt through PySide6. The LGPL-3.0 requires that:

1. The LGPL-3.0 text and the GPL-3.0 text it references are shipped with the
   application — see `LICENSES/LGPL-3.0.txt` and `LICENSES/GPL-3.0.txt`.
2. Qt remains dynamically linked (the PyInstaller one-directory bundle keeps the
   Qt libraries as separate files, so they can be replaced).
3. Users can replace the Qt libraries; the Qt DLLs are separate from
   `AgentBetta.exe` and may be swapped.
4. The corresponding Qt source is made available, or a written offer to provide
   it is given. Qt source: <https://www.qt.io/> and <https://code.qt.io/>.
5. Qt copyright and license notices are preserved.

If meeting these obligations is not desired, a commercial Qt license from The
Qt Company is the alternative. See `LICENSES/README.md` for details.
