"""Recolour a scientific figure to the site's text colour on a transparent background.

Usage:
    python scripts/recolor_figure.py photos/FIG_2_DEB_scheme.png deb-scheme

Labels and arrows of any dark colour turn solid text colour; light greys (e.g. a
background outline) stay faint; white and near-white fills become transparent. Writes WebP versions for the page and a
full-size PNG that the page links to for reading. Requires Pillow.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "images"
TEXT = (36, 40, 42)  # --color-text, #24282a


def main(src: str, name: str) -> None:
    img = Image.open(ROOT / src).convert("RGB")
    grey = ImageOps.grayscale(img)
    # Labels and arrows (any colour darker than mid-grey) become solid; light greys stay faint.
    alpha = grey.point(lambda v: 255 if v < 170 else (0 if v > 247 else min(255, round((255 - v) * 2.2))))
    out = Image.new("RGBA", img.size, TEXT + (0,))
    out.putalpha(alpha)
    out.save(OUT / f"{name}-full.png", optimize=True)
    for width in (800, 1600):
        h = round(img.height * width / img.width)
        out.resize((width, h), Image.LANCZOS).save(OUT / f"{name}-{width}.webp", "WEBP", quality=90, method=6)
        print(f"{name}-{width}.webp {width}x{h}")
    print(f"{name}-full.png {img.width}x{img.height}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
