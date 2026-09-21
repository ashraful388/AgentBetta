# Building on macOS

Build the `.app`, `.zip` and `.dmg` on a Mac (PyInstaller cannot cross-compile).

The macOS source is in the [`macos/`](https://github.com/ashraful388/AgentBetta/tree/main/macos)
folder of the repository.

## Requirements

- macOS 11+
- Python **3.11 or 3.12**
- Xcode Command Line Tools (`xcode-select --install`) for `iconutil`/`codesign`

## Setup

```bash
cd macos
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[desktop,browser,http,build]"
pip install pillow pytest
playwright install chromium      # browser fallback runtime
```

## Build

```bash
bash scripts/build_macos.sh
```

The script runs the tests, generates `agentbetta.icns`, builds
`dist/AgentBetta.app` (PyInstaller `packaging/agentbetta-macos.spec`), optionally
code-signs/notarizes, smoke-launches the bundle, and produces the artifacts.

## Outputs

```text
macos/release/macos/0.2.0-alpha.2/
├── AgentBetta-0.2.0-alpha.2-macOS-<arch>.zip
├── AgentBetta-0.2.0-alpha.2-macOS-<arch>.dmg
└── SHA256SUMS.txt
```

## Code signing / notarization (optional)

```bash
CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
NOTARY_PROFILE="agentbetta-notary" \
bash scripts/build_macos.sh
```

## Test only

```bash
python -m pytest
```

## Continuous integration

`.github/workflows/build-macos.yml` builds **arm64** and **x86_64** and (on a
`v*` tag) publishes a GitHub Release. See [Updates](../updates.md).
