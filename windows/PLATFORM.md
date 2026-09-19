# AgentBetta — Windows source tree

**Target platform:** Windows 10/11 x64
**Platform layer:** `src/agentbetta/platform/windows/` (paths, filesystem, shell, processes)
**Shell tool:** PowerShell (`run_powershell`)
**Preferred browser engine:** Microsoft Edge (`msedge`) via Playwright, Chromium fallback

## Build

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop,browser,build]"
pip install pillow

powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Outputs in `release\windows\0.2.0-alpha.1\`:

```text
AgentBetta-0.2.0-alpha.1-Windows-x64-Setup.exe
AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip
SHA256SUMS.txt
```

- PyInstaller spec: `agentbetta.spec` (one-directory, `console=False`)
- Installer: `packaging\agentbetta.iss` (Inno Setup 6, per-user, no admin)
- Icon: `packaging\make_icon.py` generates a multi-size `.ico` from
  `src/agentbetta/desktop/resources/agentbetta.png`

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite is platform-aware; on Windows it exercises the Windows platform layer.

## Data locations

| Purpose | Path |
|---|---|
| Settings | `%APPDATA%\AgentBetta\settings.json` |
| Chats | `%LOCALAPPDATA%\AgentBetta\chats.json` |
| Logs | `%LOCALAPPDATA%\AgentBetta\logs\` |
| Cache | `%LOCALAPPDATA%\AgentBetta\cache\` |
| Browser profile | `%LOCALAPPDATA%\AgentBetta\browser\profile` |
| Run records | `%USERPROFILE%\Documents\AgentBetta\runs\` |
| Secrets | Windows Credential Manager (via `keyring`) |

## Notes

- No provider credentials are included. API keys are stored only in the OS
  credential store; provider profiles are created by the user at runtime.
- The macOS platform package is not included in this tree.
