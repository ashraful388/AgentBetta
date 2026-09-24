#!/usr/bin/env bash
# AgentBetta macOS release build script.
# Usage: bash scripts/build_macos.sh
#
# Must be run on macOS (PyInstaller cannot cross-compile a .app bundle).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
VERSION="0.2.0-alpha.3"
ARCH="$(uname -m)"
RELEASE_DIR="$ROOT/release/macos/$VERSION"
APP="$ROOT/dist/AgentBetta.app"

echo "== Environment =="
"$PY" --version
uname -m

echo "== Generate .icns =="
"$PY" packaging/make_icns.py || echo "warning: .icns generation skipped"

echo "== PyInstaller =="
"$PY" -m PyInstaller --clean --noconfirm packaging/agentbetta-macos.spec

mkdir -p "$RELEASE_DIR"

echo "== Zip the .app bundle =="
ZIP="$RELEASE_DIR/AgentBetta-$VERSION-macOS-$ARCH.zip"
rm -f "$ZIP"
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"

echo "== DMG =="
DMG="$RELEASE_DIR/AgentBetta-$VERSION-macOS-$ARCH.dmg"
rm -f "$DMG"
if command -v hdiutil >/dev/null 2>&1; then
    hdiutil create -volname "AgentBetta" -srcfolder dist/AgentBetta.app -ov -format UDZO "$DMG"
else
    echo "warning: hdiutil not found; skipping DMG"
fi

echo "== SHA-256 hashes =="
( cd "$RELEASE_DIR" && shasum -a 256 AgentBetta-*.zip AgentBetta-*.dmg > "SHA256SUMS-macOS-$ARCH.txt" )

echo "Release artifacts:"
ls -lh "$RELEASE_DIR"
