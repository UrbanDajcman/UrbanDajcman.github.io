"""Pre-render two-colour (duotone) versions of the reptile strip photos.

Usage:
    python scripts/make_duotones.py

For each image key in sitegen.pages.REPTILE_ROWS, takes the largest WebP listed in
data/images.json and writes two 800px versions next to it:
    <base>-duo-mustard-800.webp   shadows slate, highlights light mustard
    <base>-duo-stone-800.webp     shadows dark slate, highlights limestone grey
Baking the colours into the files avoids CSS blend modes, which some browsers fail to
paint reliably when many are on screen. Requires Pillow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sitegen.pages import REPTILE_ROWS  # noqa: E402

TONES = {
    "mustard": ("#4a585d", "#ecca86"),  # (shadows, highlights)
    "stone": ("#34403f", "#d2d8d9"),
}
WIDTH = 800


def main() -> None:
    images = json.load(open(ROOT / "data/images.json", encoding="utf-8"))["items"]
    for key in (k for row in REPTILE_ROWS for k in row):
        img = images[key]
        src = ROOT / "static" / (img["base"].lstrip("/") + f"-{max(img['sizes'])}.webp")
        grey = ImageOps.grayscale(Image.open(src))
        grey = ImageOps.autocontrast(grey, cutoff=1)
        grey = ImageEnhance.Brightness(grey).enhance(1.08)
        h = round(grey.height * WIDTH / grey.width)
        grey = grey.resize((WIDTH, h), Image.LANCZOS)
        for tone, (dark, light) in TONES.items():
            out = ROOT / "static" / (img["base"].lstrip("/") + f"-duo-{tone}-{WIDTH}.webp")
            ImageOps.colorize(grey, black=dark, white=light).save(out, "WEBP", quality=80, method=6)
        print(key, f"{WIDTH}x{h}")


if __name__ == "__main__":
    main()
