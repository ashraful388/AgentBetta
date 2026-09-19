"""Generate the AgentBetta macOS ``.icns`` from the project logo.

Preferred path uses ``iconutil`` (present on macOS). Falls back to Pillow's
ICNS writer when ``iconutil`` is unavailable. Requires Pillow (build-time only).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ICONSET_SIZES = [16, 32, 64, 128, 256, 512, 1024]


def _square_logo(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    side = max(image.size)
    pad = int(side * 0.08)
    canvas = Image.new("RGBA", (side + 2 * pad, side + 2 * pad), (0, 0, 0, 0))
    canvas.paste(image, ((canvas.width - image.width) // 2, (canvas.height - image.height) // 2), image)
    return canvas


def _write_iconset(logo: Image.Image, iconset: Path) -> None:
    iconset.mkdir(parents=True, exist_ok=True)
    for size in ICONSET_SIZES:
        logo.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
        if size <= 512:
            logo.resize((size * 2, size * 2), Image.LANCZOS).save(
                iconset / f"icon_{size}x{size}@2x.png"
            )


def build_icns(source: Path, target: Path) -> Path:
    logo = _square_logo(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    iconutil = shutil.which("iconutil")
    if iconutil:
        with tempfile.TemporaryDirectory() as tmp:
            iconset = Path(tmp) / "AgentBetta.iconset"
            _write_iconset(logo, iconset)
            subprocess.run(
                [iconutil, "-c", "icns", str(iconset), "-o", str(target)],
                check=True,
            )
    else:
        logo.save(target, format="ICNS")
    return target


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    resources = root / "src" / "agentbetta" / "desktop" / "resources"
    try:
        print(build_icns(resources / "agentbetta.png", resources / "agentbetta.icns"))
    except Exception as exc:  # pragma: no cover - build environment dependent
        print(f"Could not generate .icns: {exc}", file=sys.stderr)
        raise SystemExit(1)
