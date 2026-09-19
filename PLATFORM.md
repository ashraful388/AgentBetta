# AgentBetta — repository layout

Documentation is at the repository root. The **source code for each platform
lives in its own folder** so it is easy to find:

| Folder | Platform | Build output |
|---|---|---|
| [`windows/`](windows) | Windows 10/11 (x64) | `AgentBetta-<version>-Windows-x64-Setup.exe`, `...-Portable.zip` |
| [`macos/`](macos) | macOS 11+ (Intel / Apple silicon) | `AgentBetta-<version>-macOS-<arch>.dmg`, `...-<arch>.zip` |

Each folder is a **complete, buildable tree** (`src/`, `tests/`, `pyproject.toml`,
platform build files). The code is the same scientific core + GUI on both
platforms; only the platform layer and the packaging differ.

```
AgentBetta/
├── windows/                 # Windows source
│   ├── src/agentbetta/
│   │   └── platform/windows/    # Windows paths, filesystem, shell, processes
│   ├── agentbetta.spec          # PyInstaller (one-dir, console=False)
│   ├── packaging/agentbetta.iss # Inno Setup installer
│   └── scripts/build_windows.ps1
├── macos/                   # macOS source
│   ├── src/agentbetta/
│   │   └── platform/macos/      # macOS paths, filesystem, shell, processes
│   ├── packaging/agentbetta-macos.spec  # PyInstaller .app bundle
│   ├── packaging/make_icns.py
│   └── scripts/build_macos.sh
├── docs/                    # Documentation (published via mkdocs.yml)
├── website/                 # Standalone landing page
├── assets/                  # Logo / icon
├── LICENSES/                # Third-party license texts
└── .github/workflows/       # build-windows, build-macos, docs
```

## Build Windows

```powershell
cd windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop,browser,build]" pillow
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

## Build macOS

```bash
cd macos
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[desktop,browser,build]" pillow pytest
playwright install chromium
bash scripts/build_macos.sh
```

## Tests

```bash
cd windows   # or: cd macos
python -m pytest
```

The suite is platform-aware and runs on both operating systems.

## Data locations

| | Windows | macOS |
|---|---|---|
| Settings | `%APPDATA%\AgentBetta\settings.json` | `~/Library/Application Support/AgentBetta/settings.json` |
| Chats | `%LOCALAPPDATA%\AgentBetta\chats.json` | `~/Library/Application Support/AgentBetta/chats.json` |
| Logs | `%LOCALAPPDATA%\AgentBetta\logs` | `~/Library/Logs/AgentBetta` |
| Run records | `Documents\AgentBetta\runs` | `~/Documents/AgentBetta/runs` |
| Secrets | Windows Credential Manager | macOS Keychain |
