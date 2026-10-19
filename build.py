"""Static site build for urban-dajcman site. Python 3.10+, standard library only.

Usage:
    python build.py            build into dist/
    python build.py --check    build, then validate the output (exit 1 on problems)
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

from sitegen.layout import page
from sitegen.pages import PAGES

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

BANNED = [
    "delve", "leverage", "cutting-edge", "cutting edge", "groundbreaking", "transformative",
    "multifaceted", "dynamic landscape", "at the intersection of", "unlock insights", "tapestry",
    "journey", "pushing boundaries", "world-leading", "visionary", "revolutionary", "thought leader",
]


def load(name: str):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def load_data() -> dict:
    return {
        "profile": load("profile.json"),
        "publications": load("publications.json")["items"],
        "projects": load("projects.json")["items"],
        "themes": load("research-themes.json")["items"],
        "images": load("images.json")["items"],
        "collaborators": load("collaborators.json"),
        "basemap": load("basemap.json"),
    }


def out_path(path: str) -> Path:
    if path.endswith(".html"):
        return DIST / path.lstrip("/")
    return DIST / path.lstrip("/") / "index.html"


def build() -> list[Path]:
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)
    data = load_data()
    written = []
    for fn in PAGES:
        path, title, description, body, extra = fn(data)
        html = page(data["profile"], path=path, title=title, description=description,
                    body=body, extra_head=extra)
        target = out_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)
    return written


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self._skip = 0
        self.meta = {}
        self.headings: list[int] = []
        self.imgs_without_alt = 0
        self.hrefs: list[str] = []
        self.landmarks: set[str] = set()
        self.text: list[str] = []
        self.html_lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "title":
            self._in_title = True
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if tag in ("header", "nav", "main", "footer"):
            self.landmarks.add(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if not self._skip:
            self.text.append(data)


def check(files: list[Path]) -> list[str]:
    problems = []
    for f in files:
        rel = f.relative_to(DIST).as_posix()
        a = Audit()
        a.feed(f.read_text(encoding="utf-8"))
        text = " ".join(a.text)
        if not a.title.strip():
            problems.append(f"{rel}: missing <title>")
        if a.html_lang != "en":
            problems.append(f"{rel}: missing lang attribute")
        for key in ("description", "og:title", "og:description", "og:type"):
            if not a.meta.get(key):
                problems.append(f"{rel}: missing meta {key}")
        if a.headings.count(1) != 1:
            problems.append(f"{rel}: expected exactly one h1, found {a.headings.count(1)}")
        for prev, cur in zip(a.headings, a.headings[1:]):
            if cur > prev + 1:
                problems.append(f"{rel}: heading level skips from h{prev} to h{cur}")
                break
        if a.imgs_without_alt:
            problems.append(f"{rel}: {a.imgs_without_alt} <img> without alt")
        missing = {"header", "nav", "main", "footer"} - a.landmarks
        if missing:
            problems.append(f"{rel}: missing landmarks {sorted(missing)}")
        if "TODO" in text or any("TODO" in v for v in a.meta.values()):
            problems.append(f"{rel}: TODO placeholder leaked into rendered output")
        if "*" in text:
            problems.append(f"{rel}: literal '*' in rendered text (unconverted species markup?)")
        low = text.lower()
        for w in BANNED:
            if w in low:
                problems.append(f"{rel}: banned phrase '{w}'")
        for href in a.hrefs:
            if href.startswith("/") and not href.startswith("//"):
                p = href.split("#")[0]
                target = DIST / p.lstrip("/")
                if p.endswith("/") or p == "":
                    target = target / "index.html"
                if not target.exists():
                    problems.append(f"{rel}: broken internal link {href}")
    return problems


def main() -> int:
    files = build()
    print(f"Built {len(files)} pages into {DIST}")
    if "--check" in sys.argv:
        problems = check(files)
        if problems:
            print("Check failed:")
            for p in problems:
                print("  - " + p)
            return 1
        print("Check passed: titles, meta/OG tags, headings, landmarks, alt text, internal links, placeholders, banned phrases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
