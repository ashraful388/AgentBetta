# AgentBetta — repository layout

This single repository contains the **Windows and macOS** source for AgentBetta.
The scientific core and the desktop GUI are shared; only the platform layer and
the packaging differ.

```
src/agentbetta/
  core/            # runtime, characterization, tool loop, models, events
  policy/          # initial policy, diagnosis, selective expansion, contraction
  providers/       # Fake, Ollama, OpenAI-compatible, Tiered, Fallback
  tools/           # registry, filesystem, shell, processes, browser, web, memory
  permissions/     # profiles, approvals, policy
  memory/          # governed long-term memory
  settings/        # settings store, secrets, provider/model profiles
  updates/         # GitHub-Releases updater
  platform/
    windows/       # Windows paths, filesystem, shell, processes
    macos/         # macOS paths, filesystem, shell, processes
  desktop/         # PySide6 GUI (shared by both platforms)
```

## Windows

- Platform layer: `src/agentbetta/platform/windows/`
- Shell tool: PowerShell (`run_powershell`)
- Preferred browser: Microsoft Edge (`msedge`), Chromium fallback
- Spec: `agentbetta.spec` · Installer: `packaging/agentbetta.iss`
- Build: `scripts/build_windows.ps1`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop,browser,build]" pillow
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Outputs in `release\windows\<version>\` (Setup EXE, portable ZIP, SHA256SUMS).

## macOS

- Platform layer: `src/agentbetta/platform/macos/`
- Shell tool: the user's login shell (`run_shell`)
- Preferred browser: Chromium (Playwright); Edge for Mac optional
- Spec: `packaging/agentbetta-macos.spec` · Icon: `packaging/make_icns.py`
- Build: `scripts/build_macos.sh`

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[desktop,browser,build]" pillow pytest
playwright install chromium
bash scripts/build_macos.sh
```

Outputs in `release/macos/<version>/` (`.zip`, `.dmg`, SHA256SUMS).

## Tests

```bash
python -m pytest
```

The suite is platform-aware and runs on both operating systems.

## Documentation & website

- `docs/` — documentation (also published with MkDocs: `mkdocs.yml`)
- `website/` — standalone landing page
- `.github/workflows/` — Windows build, macOS build, docs site

## Data locations

| | Windows | macOS |
|---|---|---|
| Settings | `%APPDATA%\AgentBetta\settings.json` | `~/Library/Application Support/AgentBetta/settings.json` |
| Chats | `%LOCALAPPDATA%\AgentBetta\chats.json` | `~/Library/Application Support/AgentBetta/chats.json` |
| Logs | `%LOCALAPPDATA%\AgentBetta\logs` | `~/Library/Logs/AgentBetta` |
| Run records | `Documents\AgentBetta\runs` | `~/Documents/AgentBetta/runs` |
| Secrets | Windows Credential Manager | macOS Keychain |
