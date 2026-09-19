# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AgentBetta (one-directory Windows build).

One-directory is deliberate: Qt, Playwright drivers and native dependencies are
more reliable and start faster than one-file extraction.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ("src/agentbetta/desktop/resources/agentbetta.ico", "agentbetta/desktop/resources"),
    ("src/agentbetta/desktop/resources/agentbetta.png", "agentbetta/desktop/resources"),
    ("src/agentbetta/desktop/resources/agentbetta_logo.png", "agentbetta/desktop/resources"),
    ("LICENSE", "."),
    ("LICENSES", "LICENSES"),
    ("docs/windows/THIRD_PARTY_NOTICES.md", "."),
]
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
    ["packaging/agentbetta_launcher.py"],
    pathex=["src"],
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
    icon="src/agentbetta/desktop/resources/agentbetta.ico",
    version="packaging/version_info.txt",
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
