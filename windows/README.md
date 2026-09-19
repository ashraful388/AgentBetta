# AgentBetta — Windows source

This folder contains the **Windows** source for AgentBetta. It is a complete,
buildable tree; the scientific core and the GUI are shared with the macOS build.

- **Documentation:** [`../docs/`](../docs/index.md) (and [`../docs/windows/`](../docs/windows))
- **Repository root:** [`..`](..)
- **Platform layer:** `src/agentbetta/platform/windows/` (paths, filesystem, PowerShell shell, processes)
- **Build spec:** `agentbetta.spec` · **Installer:** `packaging/agentbetta.iss`
- **Preferred browser engine:** Microsoft Edge (`msedge`), Chromium fallback

## Build

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop,browser,http,build]" pillow
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Output: `release\windows\<version>\` — Setup EXE, portable ZIP, `SHA256SUMS.txt`.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

See [Building on Windows](../docs/windows/building.md) and
[Windows installation](../docs/windows/installation.md).
