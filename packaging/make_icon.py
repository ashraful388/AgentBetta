"""Generate the AgentBetta Windows .ico from the project logo.

Reads ``src/agentbetta/desktop/resources/agentbetta.png`` (the transparent
logo), crops to the visible content, pads to a square, and writes a multi-size
``agentbetta.ico``. Requires Pillow (build-time only).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

SIZES = [16, 24, 32, 48, 64, 128, 256]


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


def build_ico(source: Path, target: Path) -> Path:
    logo = _square_logo(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    logo.save(target, format="ICO", sizes=[(size, size) for size in SIZES])
    return target


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    resources = root / "src" / "agentbetta" / "desktop" / "resources"
    print(build_ico(resources / "agentbetta.png", resources / "agentbetta.ico"))
