# Licensing

## AgentBetta (first-party code)

AgentBetta's own source code is licensed under the **MIT License**.
See [`../LICENSE`](../LICENSE).

Copyright (c) 2026 Dr. Md. Ashraful Babu.

## Bundled third-party components

AgentBetta's packaged application includes or depends on third-party software
that remains under its own license. The MIT license above applies only to
AgentBetta's own code.

| Component | License | Notes |
|---|---|---|
| PySide6 / Qt for Python (Qt 6) | LGPL-3.0 (or GPL-3.0 / commercial) | Bundled GUI toolkit |
| shiboken6 | LGPL-3.0 | PySide6 bindings |
| playwright (Python) | Apache-2.0 | Browser automation |
| keyring | MIT | OS credential store |
| httpx | BSD-3-Clause | HTTP client |
| pypdf | BSD-3-Clause | PDF extraction (optional) |
| PyYAML | MIT | YAML tasks (optional) |
| PyInstaller | GPL-2.0 with bootloader exception | Bundling (build tool) |
| Inno Setup | Inno Setup License (freeware) | Installer (build tool) |

Microsoft Edge, Chromium, and Ollama are **not redistributed** with AgentBetta;
they are used from the user's machine or installed separately.

## Qt / PySide6 LGPL-3.0 compliance

Because the packaged application dynamically links Qt (PySide6), distributing it
requires satisfying the LGPL-3.0. In practice, for this project:

1. Ship the LGPL-3.0 text (`LGPL-3.0.txt`) and the GPL-3.0 text (`GPL-3.0.txt`)
   with the application and reference them in `THIRD_PARTY_NOTICES.md`.
2. Keep Qt dynamically linked (the PyInstaller one-directory bundle does this).
3. Allow the user to replace the Qt libraries (the DLLs/`.so`/`.dylib` files are
   separate from the application executable, so they can be swapped).
4. Provide the corresponding Qt source, or a written offer to provide it, as the
   LGPL requires. The Qt source is available from <https://www.qt.io/> and
   <https://code.qt.io/>.
5. Do not statically link Qt into a proprietary binary, and do not remove Qt
   license notices.

If you prefer not to meet the LGPL obligations, the alternative is to purchase a
commercial Qt license from The Qt Company.

## Trademark

The "AgentBetta" name and logo are brand assets of the project owner and are not
covered by the MIT license. Using the name to endorse or promote derived products
requires permission. Consider registering the mark if you commercialize it.
