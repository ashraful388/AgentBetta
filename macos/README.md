# AgentBetta — macOS source

This folder contains the **macOS** source for AgentBetta. It is a complete,
buildable tree; the scientific core and the GUI are shared with the Windows build.

- **Documentation:** [`../docs/`](../docs/index.md) (and [`../docs/macos/`](../docs/macos))
- **Repository root:** [`..`](..)
- **Platform layer:** `src/agentbetta/platform/macos/` (paths, filesystem, login shell, processes)
- **Build spec:** `packaging/agentbetta-macos.spec` · **Icon:** `packaging/make_icns.py`
- **Preferred browser engine:** Chromium (Playwright); Edge for Mac optional

## Build (on macOS)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[desktop,browser,http,build]" pillow pytest
playwright install chromium
bash scripts/build_macos.sh
```

Output: `release/macos/<version>/` — `.zip`, `.dmg`, `SHA256SUMS.txt`.

## Test

```bash
python -m pytest
```

See [Building on macOS](../docs/macos/building.md) and
[macOS installation](../docs/macos/installation.md).
