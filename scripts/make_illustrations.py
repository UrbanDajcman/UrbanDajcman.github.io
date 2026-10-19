"""Recolour the research illustrations into soft decorative versions for the site.

Usage:
    python scripts/make_illustrations.py

Each illustration becomes a stone duotone (dark slate to the limestone page colour) so it
reads as a quiet engraving behind text; CSS sets the final strength (opacity) and fade.
Writes static/images/illus-<name>-<width>.webp (and illus-<name>-<colour>-<width>.webp
line versions for dark backgrounds). Requires Pillow.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "photos"
OUT = ROOT / "static" / "images"
DARK = (52, 64, 63)     # stone duotone dark, #34403f
LIGHT = (255, 255, 255)  # --color-bg, white

ILLUSTRATIONS = {
    "energy": "49dfd142-fe64-4f61-b108-9dd390d22e0e.png",       # energy budget (DEB)
    "heat": "3632a033-93a3-453b-9910-14f66cd9dfe9.png",         # heat budget
    "daycycle": "254cd886-fb9f-4690-a39b-6ad5830d3415.png",     # daily sun arc, microhabitats
    "competition": "05370cc8-41d8-4f81-9dfc-d14723358a28.png",  # two lizards, sun and shade
}
WIDTHS = (800, 1400)
# Line versions for dark backgrounds: the outlines of the drawing as fine lines in this colour
# on transparency, like an engraving (the contact panel uses its text colour, --color-highlight).
INK: dict[str, tuple[str, tuple[int, int, int]]] = {}  # e.g. {"daycycle": ("gold", (236, 202, 134))}
# Kept in colour (transparent background); CSS mutes them. name -> (file, widths).
COLOUR: dict[str, tuple[str, tuple[int, ...]]] = {}  # e.g. {"snake": ("a24f2f78-….png", (1200, 2400))}


def main() -> None:
    for name, file in ILLUSTRATIONS.items():
        img = Image.open(SRC / file).convert("RGB")
        grey = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
        duo = ImageOps.colorize(grey, DARK, LIGHT)
        for w in WIDTHS:
            h = round(img.height * w / img.width)
            duo.resize((w, h), Image.LANCZOS).save(OUT / f"illus-{name}-{w}.webp", "WEBP", quality=78, method=6)
        if name in INK:
            label, colour = INK[name]
            for w in WIDTHS:
                h = round(img.height * w / img.width)
                # Edges at the output size, so lines keep the same fine weight at each width.
                g = ImageOps.grayscale(img.resize((w, h), Image.LANCZOS)).filter(ImageFilter.GaussianBlur(w / 830))
                edges = g.filter(ImageFilter.FIND_EDGES).point(lambda v: 0 if v * 2.5 < 40 else min(255, int(v * 2.5)))
                ink = Image.new("RGBA", (w, h), colour + (0,))
                ink.putalpha(edges)
                ink.save(OUT / f"illus-{name}-{label}-{w}.webp", "WEBP", quality=85, method=6)
        print(f"illus-{name}: {img.width}x{img.height}")
    for name, (file, widths) in COLOUR.items():
        img = Image.open(SRC / file).convert("RGBA")
        for w in widths:
            h = round(img.height * w / img.width)
            img.resize((w, h), Image.LANCZOS).save(OUT / f"illus-{name}-{w}.webp", "WEBP", quality=82, method=6)
        print(f"illus-{name} (colour): {img.width}x{img.height}")


if __name__ == "__main__":
    main()
