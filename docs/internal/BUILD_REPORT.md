# AgentBetta Windows Build Report

**Version:** `0.2.0-alpha.1`
**Date:** 2026-09-13
**Source revision (base):** `a4f1b4b4c1b22d0e958e0ae1edf7efc2bda46316`
**Builder:** OpenCode

## Build environment

- Windows 10/11 x64 (development host: Windows 11-class desktop)
- Python **3.12.1** (packaging target; not 3.13)
- PyInstaller **6.22.3** (one-directory bundle, `console=False`)
- Inno Setup **6.7.3** (per-user install)
- PySide6 **6.11.2**, shiboken6 6.11.2
- playwright **1.62.0**, keyring **25.7.0**, httpx **0.28.1**
- PyYAML 6.0.3, pypdf 6.18.1, pytest 9.1.1, ruff 0.16.7

## Build commands

```powershell
.\.venv\Scripts\python.exe packaging\make_icon.py
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm agentbetta.spec
# portable
Compress-Archive -Path dist\AgentBetta -DestinationPath release\...\AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip
# installer
ISCC.exe packaging\agentbetta.iss
```

Reproducible wrapper: `scripts\build_windows.ps1`.

## Artifacts and SHA-256

| Artifact | Size | SHA-256 |
|---|---|---|
| `AgentBetta-0.2.0-alpha.1-Windows-x64-Setup.exe` | 61.8 MB | `617088bcaebf4cb2e1b603937d5d45c9eff30f6467191de1e8032a91ae4b349e` |
| `AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip` | 87.9 MB | `b1dc6ce8ca9a92db2d7e27bc5d11b03e4a01e088bf7e1d5546a98d1f461edf65` |

Rebuilt with `scripts\build_windows.ps1` after the version string was set to
`0.2.0a1`; frozen smoke launch after rebuild exited 0.

Artifacts directory: `release/windows/0.2.0-alpha.1/`.

## Packaging decisions

- **One-directory bundle** (not one-file) for Qt/Playwright reliability and fast start.
- **Microsoft Edge via Playwright channel `msedge`** is preferred; no large browser binaries are bundled. If Edge is missing, the browser layer falls back to a bundled Chromium only if one is installed.
- **Ollama is not bundled**; it is detected at runtime.
- Application icon generated from `packaging/make_icon.py`; Windows file-version metadata from `packaging/version_info.txt`.
- Application files and mutable user data are separate: install under `%LOCALAPPDATA%\Programs\AgentBetta`; data under `%APPDATA%`, `%LOCALAPPDATA%`, and `Documents\AgentBetta`.
- Uninstall removes application files but **not** run history or stored credentials.

## Warnings

- The alpha installer is **unsigned** and may trigger Microsoft SmartScreen.
- First launch is slower while Qt/Playwright initialize.
- Total bundle ~224 MB uncompressed, driven by PySide6/Qt.

## Validation performed

- `pytest`: **119 passed**.
- Frozen `AgentBetta.exe` smoke launch (offscreen, `AGENTBETTA_SMOKE_EXIT=1`): exit code 0.
- Portable copy run from outside the source tree: exit code 0.
- Silent per-user install, installed-app run, and silent uninstall: all exit code 0; executable removed on uninstall.
- W7 integrated validation A–G: all PASS (see `W7_VALIDATION_RESULTS.json`).

## Known limitations

- A true **clean-machine** install test (separate VM/physical machine with no
  source tree or Python) has **not** been performed in this environment; an
  isolated-directory test is the closest equivalent performed here.
- Playwright live-browser tests require Microsoft Edge installed.
- Local model speed/instruction-following depends on the model; the validated
  model is `qwen3:1.7b`. `gpt-oss:20b` failed to load in this environment with a
  llama.cpp tensor error.
