"""Collaboration map: co-author institutions grouped by city, linked to the home institution.

Data: data/collaborators.json (scripts/build_collaborators.py) and data/basemap.json
(scripts/build_basemap.py, world outline in static/images/basemap-land.svg). All places
are drawn at their true position on a world map; the map opens on the whole world and
static/js/collab-map.js adds zoom and pan. The SVG is hidden from assistive technology;
the list beside it carries the same information.
"""
from __future__ import annotations

import math
import re
import unicodedata

from .components import esc, ext_link, is_set, rich

COUNTRIES = {
    "SI": "Slovenia", "PT": "Portugal", "ES": "Spain", "FR": "France", "IT": "Italy", "CZ": "Czechia",
    "GB": "United Kingdom", "NL": "Netherlands", "GR": "Greece", "US": "United States", "BR": "Brazil",
    "ZA": "South Africa", "DE": "Germany", "HR": "Croatia", "AT": "Austria",
}
# Nearby places shown as one point.
CITY_GROUPS = {"Brest": "Brest", "Plouzané": "Brest"}
# Sizes in screen pixels; the script rescales them on zoom. Static values assume the start view.
DOT_PX, HOME_PX, LABEL_PX = 4.0, 6.0, 13.0


def _norm(name: str) -> str:
    name = name.replace("‐", "-")
    return "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c)).lower()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _norm(text)).strip("-")


def group_by_city(collab: dict, home_city: str) -> tuple[dict | None, list[dict]]:
    exclude = set(collab.get("exclude", []))
    fixes = collab.get("place_fixes", {})
    nodes: dict[str, dict] = {}
    for inst in collab["institutions"]:
        if inst["id"] in exclude or inst.get("lat") is None:
            continue
        # OpenAlex sometimes places an institution at its head office; the paper's address wins.
        inst = {**inst, **{k: v for k, v in fixes.get(inst["id"], {}).items() if not k.startswith("_")}}
        city = CITY_GROUPS.get(inst.get("city") or "", inst.get("city") or inst["name"])
        key = _slug(city)
        node = nodes.setdefault(key, {
            "key": key, "city": city, "country": COUNTRIES.get(inst.get("country") or "", inst.get("country") or ""),
            "lat": inst["lat"], "lon": inst["lon"], "institutions": set(), "papers": set(),
        })
        node["institutions"].add(inst["name"])
        node["papers"].update(inst["papers"])
    home = nodes.pop(_slug(home_city), None)
    others = sorted(nodes.values(), key=lambda n: (-len(n["papers"]), n["city"]))
    return home, others


def _arc(x1: float, y1: float, x2: float, y2: float) -> str:
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy) or 1
    nx, ny = -dy / dist, dx / dist
    if ny > 0:  # bend upwards
        nx, ny = -nx, -ny
    bend = 0.22 * dist
    return f"M{x1:.1f} {y1:.1f}Q{mx + nx * bend:.1f} {my + ny * bend:.1f} {x2:.1f} {y2:.1f}"


def _first_author(pub: dict) -> str:
    authors = pub.get("authors") or []
    if not authors:
        return ""
    surname = authors[0].split(",")[0].strip()
    return surname + (" et al." if len(authors) > 2 else (f" & {authors[1].split(',')[0].strip()}" if len(authors) == 2 else ""))


def _paper_pop(key: str, place: str, ids: set[str], pubs: dict[str, dict]) -> str:
    """Pop-up listing the joint papers: title (linked to DOI), year, first author."""
    items = []
    for pub in sorted((pubs[i] for i in ids if i in pubs), key=lambda p: -int(p.get("year", 0))):
        title = rich(pub["title"])
        if is_set(pub.get("doi")):
            title = ext_link(f"https://doi.org/{pub['doi']}", title)
        items.append(f'<li><span class="collab__ptitle">{title}</span>'
                     f'<span class="collab__pmeta">{esc(pub.get("year", ""))}, {esc(_first_author(pub))}</span></li>')
    return (f'<div class="collab__pop" id="pop-{key}" role="tooltip">'
            f'<p class="collab__pop-h">Joint publications with {esc(place)}</p>'
            f'<ul>{"".join(items)}</ul></div>')


def collab_map(collab: dict, basemap: dict, publications: list[dict], home_city: str, home_label: str) -> str:
    home, nodes = group_by_city(collab, home_city)
    pubs = {p["id"]: p for p in publications}
    bbox, width, height = basemap["bbox"], basemap["width"], basemap["height"]
    k = width / (bbox["lon_max"] - bbox["lon_min"])

    def project(lon: float, lat: float) -> tuple[float, float]:
        return (lon - bbox["lon_min"]) * k, (bbox["lat_max"] - lat) * k

    # The map opens on the whole world.
    vx0, vy0, vx1, vy1 = 0, 0, width, height
    view = f"0 0 {width:.0f} {height:.0f}"
    # Map units per screen pixel in the start view, for a ~1200px wide map.
    upp = (vx1 - vx0) / 1200

    hx, hy = project(home["lon"], home["lat"])
    arcs, dots, items = [], [], []
    for n in nodes:
        x, y = project(n["lon"], n["lat"])
        weight = len(n["papers"])
        label = " / ".join(sorted(n["institutions"]))
        r_px = DOT_PX + min(weight, 6) * 0.8
        arcs.append(f'<path class="collab__arc" data-node="{n["key"]}" d="{_arc(hx, hy, x, y)}" '
                    f'style="stroke-width:{0.8 + min(weight, 6) * 0.35:.2f}px"/>')
        dots.append(
            f'<g class="collab__node" data-node="{n["key"]}" data-x="{x:.1f}" data-y="{y:.1f}" data-r="{r_px:.1f}">'
            f'<circle class="collab__halo" cx="{x:.1f}" cy="{y:.1f}" r="{(r_px + 6) * upp:.2f}"/>'
            f'<circle class="collab__dot" cx="{x:.1f}" cy="{y:.1f}" r="{r_px * upp:.2f}"/>'
            f'<text class="collab__label" x="{x + (r_px + 5) * upp:.1f}" y="{y + 4 * upp:.1f}" '
            f'font-size="{LABEL_PX * upp:.2f}">{esc(label)}</text></g>'
        )
        papers = f'{weight} joint publication{"s" if weight != 1 else ""}'
        items.append(
            f'<li class="collab__item" data-node="{n["key"]}" tabindex="0" aria-describedby="pop-{n["key"]}">'
            f'<span class="collab__place">{esc(label)}</span>'
            f'<span class="collab__count">{papers}</span>'
            f'{_paper_pop(n["key"], label, n["papers"], pubs)}</li>'
        )
    home_dot = (
        f'<g class="collab__home" data-x="{hx:.1f}" data-y="{hy:.1f}" data-r="{HOME_PX}">'
        f'<circle class="collab__home-ring" cx="{hx:.1f}" cy="{hy:.1f}" r="{(HOME_PX + 5) * upp:.2f}"/>'
        f'<circle class="collab__home-dot" cx="{hx:.1f}" cy="{hy:.1f}" r="{HOME_PX * upp:.2f}"/>'
        f'<text class="collab__label collab__label--home" x="{hx + (HOME_PX + 8) * upp:.1f}" '
        f'y="{hy - 8 * upp:.1f}" font-size="{LABEL_PX * upp:.2f}">{esc(home_label)}</text></g>'
    )
    svg = (
        f'<svg class="collab__svg" viewBox="{view}" preserveAspectRatio="xMidYMid slice" '
        f'data-world="{width:.0f} {height:.0f}" aria-hidden="true" focusable="false">'
        f'<image href="{basemap["image"]}" x="0" y="0" width="{width:.0f}" height="{height:.0f}" class="collab__land"/>'
        f'<g class="collab__arcs">{"".join(arcs)}</g>'
        f'<g class="collab__nodes">{"".join(dots)}</g>{home_dot}</svg>'
    )
    controls = (
        '<div class="collab__controls" hidden>'
        '<button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
        '<button type="button" data-zoom="out" aria-label="Zoom out">−</button>'
        "</div>"
    )
    summary = ('Point at or select an institution to see the joint papers; drag the map to move it, '
               'and use the buttons, a pinch or Ctrl + scroll to zoom.')
    home_item = ""
    if home:
        home_item = (f'<p class="collab__home-note"><span class="collab__place">{esc(" / ".join(sorted(home["institutions"])))}</span>: co-authors on '
                     f'{len(home["papers"])} publications.</p>')
    return f"""<div class="collab" data-collab>
  <div class="collab__map">{svg}{controls}<div class="collab__mappop" aria-hidden="true" hidden></div></div>
  <div class="collab__side">
    <p class="collab__summary">{summary}</p>
    <ol class="collab__list">{"".join(items)}</ol>
    {home_item}
  </div>
</div>
<script src="/js/collab-map.js" defer></script>"""
