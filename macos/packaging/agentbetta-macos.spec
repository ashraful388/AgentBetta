# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AgentBetta on macOS (a .app bundle).

Run from the repository root:

    pyinstaller --clean --noconfirm packaging/agentbetta-macos.spec

One-directory collection inside the bundle is deliberate: Qt, Playwright and
native dependencies are more reliable and start faster than one-file.
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Anchor all paths at the repository root regardless of PyInstaller's CWD
# handling (PyInstaller resolves spec-relative entries against SPECPATH).
# SPECPATH is the directory containing this spec file (i.e. <root>/packaging).
try:
    _SPEC_DIR = os.path.abspath(SPECPATH)
except NameError:
    _SPEC_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_SPEC_DIR)

_LAUNCHER = os.path.join(_ROOT, "packaging", "agentbetta_launcher.py")
_ICNS = os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta.icns")
datas = [
    (os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta.png"), "agentbetta/desktop/resources"),
    (os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta_logo.png"), "agentbetta/desktop/resources"),
    (os.path.join(_ROOT, "LICENSE"), "."),
    (os.path.join(_ROOT, "LICENSES"), "LICENSES"),
    (os.path.join(_ROOT, "THIRD_PARTY_NOTICES.md"), "."),
]
if os.path.exists(_ICNS):
    datas.append((_ICNS, "agentbetta/desktop/resources"))
binaries = []
hiddenimports = []

for package in ("playwright", "keyring", "httpx"):
    try:
        package_datas, package_binaries, package_hidden = collect_all(package)
    except Exception:
        continue
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

hiddenimports += collect_submodules("keyring.backends")
hiddenimports += collect_submodules("agentbetta.desktop")
hiddenimports += collect_submodules("agentbetta.updates")
hiddenimports += ["agentbetta.desktop.app", "agentbetta.desktop.main_window"]

block_cipher = None

a = Analysis(
    [_LAUNCHER],
    pathex=[os.path.join(_ROOT, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "scipy", "PyQt5", "PyQt6"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AgentBetta",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AgentBetta",
)

app = BUNDLE(
    coll,
    name="AgentBetta.app",
    icon=_ICNS if os.path.exists(_ICNS) else None,
    bundle_identifier="dev.agentbetta.desktop",
    info_plist={
        "CFBundleName": "AgentBetta",
        "CFBundleDisplayName": "AgentBetta",
        "CFBundleVersion": "0.2.0.1",
        "CFBundleShortVersionString": "0.2.0-alpha.1",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        "NSHumanReadableCopyright": "AgentBetta Project",
    },
)
