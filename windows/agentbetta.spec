# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AgentBetta (one-directory Windows build).

One-directory is deliberate: Qt, Playwright drivers and native dependencies are
more reliable and start faster than one-file extraction.
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Anchor paths at this spec's folder (the windows/ tree) regardless of CWD.
try:
    _ROOT = os.path.abspath(SPECPATH)
except NameError:  # pragma: no cover
    _ROOT = os.path.dirname(os.path.abspath(__file__))

datas = [
    (os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta.ico"), "agentbetta/desktop/resources"),
    (os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta.png"), "agentbetta/desktop/resources"),
    (os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta_logo.png"), "agentbetta/desktop/resources"),
    (os.path.join(_ROOT, "LICENSE"), "."),
    (os.path.join(_ROOT, "LICENSES"), "LICENSES"),
    (os.path.join(_ROOT, "THIRD_PARTY_NOTICES.md"), "."),
]
binaries = []
hiddenimports = []

for package in ("playwright", "keyring", "httpx", "win32ctypes"):
    try:
        package_datas, package_binaries, package_hidden = collect_all(package)
    except Exception:
        continue
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

hiddenimports += collect_submodules("keyring.backends")
# keyring's Windows backend imports win32ctypes inside a try/except; bundle it
# explicitly so API keys reach Windows Credential Manager in the frozen app.
hiddenimports += collect_submodules("win32ctypes")
hiddenimports += collect_submodules("win32ctypes.pywin32")
hiddenimports += ["keyring.backends.Windows"]
hiddenimports += collect_submodules("agentbetta.desktop")
hiddenimports += collect_submodules("agentbetta.updates")
hiddenimports += ["agentbetta.desktop.app", "agentbetta.desktop.main_window"]

block_cipher = None

a = Analysis(
    [os.path.join(_ROOT, "packaging/agentbetta_launcher.py")],
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
    icon=os.path.join(_ROOT, "src/agentbetta/desktop/resources/agentbetta.ico"),
    version=os.path.join(_ROOT, "packaging/version_info.txt"),
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
