"""Crop and resize source photographs into responsive WebP files.

Usage:
    python scripts/prepare_images.py

Requires Pillow (python -m pip install --user pillow). Only needed when photos
change; the generated files in static/images/ are what the site uses.

Each entry in PHOTOS gives the source file, an output name, an optional crop box
(left, top, right, bottom) in source pixels, and the widths to generate. The
script prints the final dimensions to copy into data/images.json.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "photos"
OUT = ROOT / "static" / "images"

PHOTOS = [
    # Wide banner: the inselberg only, without the face, so the landscape leads.
    {"src": "UD_foto_spitzkope_osebniarhv.jpg", "name": "spitzkoppe-banner",
     "crop": (1060, 700, 2966, 1653), "widths": [960, 1600, 1906]},
    {"src": "UD_foto_spitzkope_osebniarhv.jpg", "name": "spitzkoppe",
     "crop": None, "widths": [800, 1400]},
    {"src": "TD__7481_foto_DavorinTome.JPG", "name": "portrait-binoculars",
     "crop": None, "widths": [600, 1000]},
    # 2:3 portrait crops for the photo row; keep the whole lizard and the face.
    {"src": "UD_lizard_foto_Osebniarhiv.jpg", "name": "lizard-field",
     "crop": (0, 200, 720, 1280), "widths": [720]},
    {"src": "UD_teren_foto_ValentinaPerc.jpg", "name": "rock-face-field",
     "crop": (0, 100, 374, 661), "widths": [374]},
    {"src": "UD_sardiniakaca_osebniarhiv.jpg", "name": "sardinia-snake",
     "crop": (45, 0, 2834, 4184), "widths": [600, 1000]},
    {"src": "UD_beach_osebniarhiv.jpg", "name": "beach",
     "crop": None, "widths": [960, 1600]},
    {"src": "UD_foto_snakes_osebniarhiv.jpg", "name": "snake-sign",
     "crop": None, "widths": [600, 1000]},
    # WETADAPT project photographs (wetadapt.si); credit "WETADAPT project".
    {"src": "wetadapt_iberolacerta-horvathi.jpg", "name": "iberolacerta-horvathi-hero",
     "crop": None, "widths": [960, 1600, 2400]},
    {"src": "wetadapt_loggers-on-rock.jpg", "name": "loggers-on-rock",
     "crop": None, "widths": [800, 1400]},
    {"src": "wetadapt_placing-logger.jpg", "name": "placing-logger",
     "crop": None, "widths": [700, 1200]},
    {"src": "wetadapt_processing-lizards.jpg", "name": "processing-lizards",
     "crop": None, "widths": [800, 1400]},
    {"src": "wetadapt_fieldwork-tenerife.jpg", "name": "fieldwork-tenerife",
     "crop": None, "widths": [960, 1600]},
    {"src": "wetadapt_sem-scales.jpg", "name": "sem-scales",
     "crop": None, "widths": [800, 1280]},
    {"src": "wetadapt_gallotia-galloti.jpg", "name": "gallotia-galloti",
     "crop": None, "widths": [800, 1400]},
    {"src": "wetadapt_urban-with-lizard.jpg", "name": "urban-with-lizard",
     "crop": None, "widths": [800, 1400, 2400]},
    # Wikimedia Commons, see data/images.json for licence and source.
    {"src": "commons_iberolacerta-horvathi_gailhampshire.jpg", "name": "iberolacerta-horvathi",
     "crop": None, "widths": [800, 1400]},
    {"src": "commons_podarcis-muralis_pinky-sl.jpg", "name": "podarcis-muralis",
     "crop": None, "widths": [800, 1400]},
    {"src": "commons_algyroides-nigropunctatus_gailhampshire.jpg", "name": "algyroides-nigropunctatus",
     "crop": None, "widths": [800, 1400]},
    {"src": "commons_zootoca-carniolica_pinky-sl.jpg", "name": "zootoca-carniolica",
     "crop": None, "widths": [800, 1400]},
    # Square crops for the round About collage (Davorin Tome).
    {"src": "TD__7484_foto_DTome.JPG", "name": "circle-portrait", "crop": (470, 0, 1595, 1125), "widths": [700]},
    {"src": "TD__7484_foto_DTome.JPG", "name": "portrait-close", "crop": (300, 0, 1800, 1125), "widths": [800]},
    {"src": "20260703_175028.jpg", "name": "circle-dunes", "crop": (500, 0, 3500, 3000), "widths": [700]},
    {"src": "TD__7319_foto_DTome.JPG", "name": "circle-net", "crop": (818, 0, 1943, 1125), "widths": [700]},
    {"src": "TD__8095_foto_DTome.JPG", "name": "circle-samples", "crop": (0, 200, 1334, 1534), "widths": [700]},
    {"src": "TD__3598.JPG", "name": "circle-karst", "crop": (0, 300, 1334, 1634), "widths": [700]},
    {"src": "TD__3598.JPG", "name": "karst", "crop": None, "widths": [800, 1334]},
    {"src": "wetadapt_urban-with-lizard.jpg", "name": "circle-lizard", "crop": (640, 0, 2560, 1920), "widths": [700]},
    # Landscapes and fieldwork (Urban's photographs), used as mood images.
    {"src": "20240711_081739.jpg", "name": "land-gorge", "crop": None, "widths": [800, 1400]},
    {"src": "20240722_181954.jpg", "name": "land-alpine", "crop": None, "widths": [700, 1200]},
    {"src": "20240726_115549.jpg", "name": "land-mountains", "crop": None, "widths": [1200, 2000]},
    {"src": "20260602_111139.jpg", "name": "land-cliffs", "crop": None, "widths": [700, 1200]},
    {"src": "20260703_175028.jpg", "name": "land-dunes", "crop": None, "widths": [800, 1400]},
    {"src": "20240520_122630.jpg", "name": "team-field", "crop": None, "widths": [800, 1400]},
    {"src": "20240520_122634.jpg", "name": "reptile-box", "crop": None, "widths": [800, 1400]},
    {"src": "commons_iberolacerta-horvathi_gailhampshire.jpg", "name": "iberolacerta-horvathi-43", "crop": (0, 390, 3592, 3084), "widths": [800, 1400]},
    {"src": "20240527_125710.jpg", "name": "reptile-snake", "crop": (0, 950, 3024, 3218), "widths": [800, 1400]},
    {"src": "TD__7319_foto_DTome.JPG", "name": "net-wide", "crop": None, "widths": [1200, 2000]},
    {"src": "UD_foto_snakes_osebniarhiv.jpg", "name": "snake-sign-43", "crop": (0, 900, 1844, 2283), "widths": [800]},
    {"src": "UD_sardiniakaca_osebniarhiv.jpg", "name": "circle-smile", "crop": (830, 250, 2630, 2050), "widths": [700]},
    # Urban's own reptile photographs for the duotone strip; never cropped so the animal stays whole.
    {"src": "20240911_132845.jpg", "name": "reptile-moss", "crop": None, "widths": [800, 1400]},
    {"src": "20250521_125426.jpg", "name": "reptile-measured", "crop": None, "widths": [800, 1400]},
    {"src": "20260425_151442.jpg", "name": "reptile-concrete", "crop": None, "widths": [800, 1400]},
    {"src": "20260502_143857.jpg", "name": "reptile-leaves", "crop": None, "widths": [800, 1400]},
    {"src": "20260701_091153.jpg", "name": "reptile-gecko", "crop": None, "widths": [800, 1400]},
]

OG = {"src": "wetadapt_iberolacerta-horvathi.jpg", "crop": (0, 180, 2560, 1524), "size": (1200, 630)}


def open_image(name: str) -> Image.Image:
    img = Image.open(SRC / name)
    return ImageOps.exif_transpose(img).convert("RGB")


def main() -> None:
    """With names as arguments (e.g. `python scripts/prepare_images.py karst`), only those are rebuilt."""
    import sys
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for p in PHOTOS:
        if only and p["name"] not in only:
            continue
        img = open_image(p["src"])
        if p["crop"]:
            img = img.crop(p["crop"])
        w, h = img.size
        for width in p["widths"]:
            width = min(width, w)
            height = round(h * width / w)
            resized = img.resize((width, height), Image.LANCZOS)
            target = OUT / f'{p["name"]}-{width}.webp'
            resized.save(target, "WEBP", quality=80, method=6)
            print(f"{target.name}: {width}x{height}, {target.stat().st_size // 1024} KB")
    og = open_image(OG["src"]).crop(OG["crop"]).resize(OG["size"], Image.LANCZOS)
    og.save(OUT / "og-default.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    print("og-default.jpg: 1200x630")


if __name__ == "__main__":
    main()
