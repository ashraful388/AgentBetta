# License & notices

## AgentBetta

AgentBetta™ is released under the **MIT License**.

```
Copyright (c) 2026 Dr. Md. Ashraful Babu
```

See [`LICENSE`](https://github.com/) in the repository for the full text.

## Trademark

**AgentBetta™** and the AgentBetta logo are trademarks of Dr. Md. Ashraful Babu.
The MIT license does not grant trademark rights. See the repository's
trademark policy for permitted uses; forks must use a distinct name and not
imply official endorsement.

## Third-party components

The packaged application bundles third-party software under its own licenses:

| Component | License | Use |
|---|---|---|
| PySide6 / Qt for Python (Qt 6) | LGPL-3.0 (or GPL/commercial) | Desktop GUI |
| shiboken6 | LGPL-3.0 | PySide6 bindings |
| playwright (Python) | Apache-2.0 | Browser automation |
| keyring | MIT | OS credential store |
| httpx | BSD-3-Clause | HTTP client |
| pypdf | BSD-3-Clause | PDF extraction (optional) |
| PyYAML | MIT | YAML tasks (optional) |
| PyInstaller | GPL-2.0 with bootloader exception | Bundling |
| Inno Setup | Inno Setup License | Installer |

Microsoft Edge, Chromium and Ollama are not redistributed with AgentBetta.

### Qt / PySide6 LGPL-3.0 compliance

Because the application dynamically links Qt, distribution must satisfy the
LGPL-3.0: ship the LGPL-3.0 and GPL-3.0 texts, keep Qt dynamically linked and
replaceable, and make the corresponding Qt source available (or offer to). See
the repository's `THIRD_PARTY_NOTICES.md` and `LICENSES/`.

## Citation

If you use AgentBetta in academic work, please cite it — see `CITATION.cff`.
