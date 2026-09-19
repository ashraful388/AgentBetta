# AgentBetta — macOS source tree

**Target platform:** macOS 11+ (Intel / Apple silicon)
**Platform layer:** `src/agentbetta/platform/macos/` (paths, filesystem, shell, processes)
**Shell tool:** the user's login shell (`zsh`/`bash`) — exposed as `run_shell`
**Preferred browser engine:** Chromium (Playwright); `msedge` selectable if Edge for Mac is installed

## Build

Must be run on macOS (PyInstaller cannot cross-compile a `.app` bundle).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[desktop,browser,build]"
pip install pillow
playwright install chromium      # browser fallback runtime

bash scripts/build_macos.sh
```

Outputs in `release/macos/0.2.0-alpha.1/`:

```text
AgentBetta-0.2.0-alpha.1-macOS.zip
AgentBetta-0.2.0-alpha.1-macOS.dmg
SHA256SUMS.txt
```

- PyInstaller spec: `packaging/agentbetta-macos.spec` (`.app` bundle)
- Icon: `packaging/make_icns.py` generates `agentbetta.icns` from
  `src/agentbetta/desktop/resources/agentbetta.png` (uses `iconutil`)
- See `docs/macos/BUILD_AND_INSTALL.md` for Gatekeeper notes (unsigned alpha)

## Test

```bash
python -m pytest
```

The suite is platform-aware; on macOS it exercises the macOS platform layer.

## Data locations

| Purpose | Path |
|---|---|
| Settings | `~/Library/Application Support/AgentBetta/settings.json` |
| Logs | `~/Library/Logs/AgentBetta/agentbetta.log` |
| Cache | `~/Library/Caches/AgentBetta/` |
| Browser profile | `~/Library/Application Support/AgentBetta/browser/profile` |
| Run records | `~/Documents/AgentBetta/runs/` |
| Secrets | macOS Keychain (via `keyring`) |

## Notes

- The Windows platform package is not included in this tree.
- The scientific core is identical to the Windows tree; only the platform layer
  and build files differ.
- `desktop_control` (UI automation) is not implemented for macOS in this alpha.
