"""Reusable HTML components. Every function returns an HTML string.

Conventions
- Any data value that is a string starting with "TODO" is treated as missing
  (see `is_set`) and is never rendered.
- Text fields may contain *asterisks* to mark species names; `rich()` escapes
  the text and turns them into <i class="taxon">.
"""
from __future__ import annotations

import html
import json
import re

ASTERISK = re.compile(r"\*([^*]+)\*")


def is_set(value) -> bool:
    """True when a value is present and is not a TODO placeholder."""
    if value is None:
        return False
    if isinstance(value, str):
        v = value.strip()
        return bool(v) and not v.upper().startswith("TODO")
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def rich(text: str) -> str:
    """Escape text and italicize *species names*."""
    return ASTERISK.sub(r'<i class="taxon">\1</i>', esc(text))


def plain(text: str) -> str:
    """Strip *markers* for use in attributes, <title> and meta tags."""
    return ASTERISK.sub(r"\1", text)


def ext_link(href: str, label: str, rel_me: bool = False) -> str:
    """External link; layout.new_tab_links() later makes it open in a new tab."""
    rel = ' rel="me"' if rel_me else ""
    return f'<a href="{esc(href)}"{rel}>{label}</a>'


# --------------------------------------------------------------------------
# Publications
# --------------------------------------------------------------------------

def _authors_html(authors: list[str], self_variants: list[str]) -> str:
    variants = {v.strip().lower() for v in self_variants}
    parts = []
    for a in authors:
        if a.strip().lower() in variants:
            parts.append(f'<span class="self">{esc(a)}</span>')
        else:
            parts.append(esc(a))
    return ", ".join(parts)


def publication_entry(pub: dict, self_variants: list[str], heading_level: int = 3) -> str:
    """One publication as an <li><article>. Required: authors, year, title."""
    authors = _authors_html(pub.get("authors", []), self_variants)
    venue_bits = []
    if is_set(pub.get("journal")):
        venue_bits.append(f'<cite>{esc(pub["journal"])}</cite>')
    vol = pub.get("volume")
    if is_set(vol):
        issue = f'({esc(pub["issue"])})' if is_set(pub.get("issue")) else ""
        venue_bits.append(f"{esc(vol)}{issue}")
    if is_set(pub.get("pages")):
        venue_bits.append(esc(pub["pages"]))
    venue = ", ".join(venue_bits)

    links = []
    if is_set(pub.get("doi")):
        doi = pub["doi"].strip()
        links.append(ext_link(f"https://doi.org/{doi}", f"doi:{esc(doi)}"))
    elif is_set(pub.get("url")):
        links.append(ext_link(pub["url"], "Journal page"))
    if is_set(pub.get("code_url")):
        links.append(ext_link(pub["code_url"], "Code on GitHub"))

    desc = f'<p class="pub__desc">{rich(pub["description"])}</p>' if is_set(pub.get("description")) else ""
    links_html = f'<p class="pub__links">{" · ".join(links)}</p>' if links else ""
    year = esc(pub.get("year", ""))
    h = f"h{heading_level}"
    # The title links to the paper: DOI if known, otherwise the journal page.
    target = f"https://doi.org/{pub['doi'].strip()}" if is_set(pub.get("doi")) else pub.get("url")
    title = ext_link(target, rich(pub["title"])) if is_set(target) else rich(pub["title"])
    return (
        f'<li class="pub"><article>'
        f'<{h} class="pub__title">{title}</{h}>'
        f'<p class="pub__authors">{authors} (<time datetime="{year}">{year}</time>)</p>'
        + f'<div class="pub__meta">' + (f'<p class="pub__venue">{venue}</p>' if venue else "") + links_html + "</div>"
        + desc
        + "</article></li>"
    )


def publication_list(pubs: list[dict], self_variants: list[str], empty_text: str,
                     heading_level: int = 3) -> str:
    valid = [p for p in pubs if is_set(p.get("title")) and is_set(p.get("authors"))]
    if not valid:
        return f'<p class="empty-state">{empty_text}</p>' if empty_text else ""
    valid.sort(key=lambda p: (str(p.get("year", "")), p.get("title", "")), reverse=True)
    items = "".join(publication_entry(p, self_variants, heading_level) for p in valid)
    return f'<ol class="pub-list" reversed>{items}</ol>'


def publication_years(pubs: list[dict], self_variants: list[str], group_key: str) -> str:
    """Publications grouped under year subheadings (h3), newest first; entries are h4.
    Used on the Publications page, where entries run across the full width."""
    valid = [p for p in pubs if is_set(p.get("title")) and is_set(p.get("authors"))]
    years = sorted({str(p.get("year", "")) for p in valid}, reverse=True)
    blocks = []
    for y in years:
        group = sorted((p for p in valid if str(p.get("year", "")) == y), key=lambda p: p.get("title", ""))
        items = "".join(publication_entry(p, self_variants, 4) for p in group)
        hid = f"{group_key}-{esc(y) or 'undated'}"
        blocks.append(
            f'<section class="pub-year" aria-labelledby="{hid}">'
            f'<h3 class="pub-year__label" id="{hid}">{esc(y) or "Undated"}</h3>'
            f'<ol class="pub-list pub-list--wide">{items}</ol></section>'
        )
    return f'<div class="pub-years">{"".join(blocks)}</div>'


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def figure(img: dict, eager: bool = False) -> str:
    loading = "eager" if eager else "lazy"
    caption_bits = []
    if is_set(img.get("caption")):
        caption_bits.append(rich(img["caption"]))
    if is_set(img.get("credit")):
        caption_bits.append(f'Photo: {esc(img["credit"])}')
    cap = f"<figcaption>{' '.join(caption_bits)}</figcaption>" if caption_bits else ""
    return (
        f'<figure class="figure">'
        f'<img src="{esc(img["src"])}" width="{int(img["width"])}" height="{int(img["height"])}" '
        f'alt="{esc(img.get("alt", ""))}" loading="{loading}" decoding="async">'
        f"{cap}</figure>"
    )


def photo(img: dict, sizes: str, eager: bool = False, cls: str = "") -> str:
    """Responsive <img> from an images.json entry (WebP files at several widths)."""
    srcset = ", ".join(f'{img["base"]}-{w}.webp {w}w' for w in img["sizes"])
    smallest = f'{img["base"]}-{img["sizes"][0]}.webp'
    extra = ' fetchpriority="high"' if eager else ""
    class_attr = f' class="{cls}"' if cls else ""
    return (
        f'<img{class_attr} src="{smallest}" srcset="{srcset}" sizes="{sizes}" '
        f'width="{int(img["width"])}" height="{int(img["height"])}" alt="{esc(img.get("alt", ""))}" '
        f'loading="{"eager" if eager else "lazy"}" decoding="async"{extra}>'
    )


def credit_html(img: dict) -> str:
    """'Photo: X' with optional link, plus licence and source for reused images."""
    if not is_set(img.get("credit")):
        return ""
    who = esc(img["credit"])
    if is_set(img.get("credit_url")):
        who = ext_link(img["credit_url"], who)
    lic = ""
    if is_set(img.get("license")):
        lic_label = ext_link(img["license_url"], esc(img["license"])) if is_set(img.get("license_url")) else esc(img["license"])
        lic = f", {lic_label}"
        if is_set(img.get("source_url")):
            lic += f", via {ext_link(img['source_url'], 'Wikimedia Commons')}"
    return f'<span class="credit">Photo: {who}{lic}</span>'


def photo_figure(img: dict, sizes: str, cls: str = "photo") -> str:
    """Photo with an optional caption (Latin name). Credits are listed on the About page."""
    cap = f"<figcaption>{rich(img['caption'])}</figcaption>" if is_set(img.get("caption")) else ""
    return f'<figure class="{cls}">{photo(img, sizes)}{cap}</figure>'


def nib_mark(label: str, cls: str = "") -> str:
    """NIB logo as a single-colour mask; takes the current text colour."""
    return f'<span class="nib-mark {cls}" role="img" aria-label="{esc(label)}"></span>'


def placeholder_figure(note: str, caption: str) -> str:
    """Visible, clearly-labelled slot for an image the owner has not supplied yet."""
    return (
        f'<figure class="figure placeholder-figure" data-placeholder="true">'
        f'<div class="placeholder-figure__frame" role="img" aria-label="Image placeholder: {esc(plain(note))}">'
        f"<span>Image to be added<br>{rich(note)}</span></div>"
        f"<figcaption>{rich(caption)}</figcaption></figure>"
    )


# --------------------------------------------------------------------------
# Metadata blocks
# --------------------------------------------------------------------------

def meta_list(rows: list[tuple[str, str]]) -> str:
    """Definition list of label/value pairs; values are pre-rendered HTML."""
    if not rows:
        return ""
    body = "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<dl class="meta-list">{body}</dl>'


def json_ld(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{payload}\n</script>'
