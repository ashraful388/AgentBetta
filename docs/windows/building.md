# Building on Windows

Build from source to produce the Setup EXE and portable ZIP.

The Windows source is in the [`windows/`](https://github.com/ashraful388/AgentBetta/tree/main/windows)
folder of the repository.

## Requirements

- Windows 10/11 x64
- Python **3.11 or 3.12** (3.12 recommended for packaging)
- Inno Setup 6 (for the installer)

## Setup

```powershell
cd windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e ".[desktop,browser,http,build]"
pip install pillow pytest
```

## Build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The script:

1. runs the test suite,
2. generates the multi-size `.ico` from the logo,
3. builds the one-directory bundle with **PyInstaller** (`agentbetta.spec`),
4. creates the portable ZIP,
5. builds the installer with **Inno Setup** (`packaging\agentbetta.iss`),
6. writes `SHA256SUMS.txt`.

## Outputs

```text
windows\release\windows\0.2.0-alpha.1\
├── AgentBetta-0.2.0-alpha.1-Windows-x64-Setup.exe
├── AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip
└── SHA256SUMS.txt
```

## Test only

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Continuous integration

`.github/workflows/build-windows.yml` builds and (on a `v*` tag) publishes a
GitHub Release with the installer assets. See [Updates](../updates.md).
