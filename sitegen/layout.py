"""Base page layout: <head> metadata, header navigation, footer."""
from __future__ import annotations

import datetime
import re

from .components import esc, ext_link, is_set, json_ld, plain
from .icons import icon

NAV = [
    ("/research/", "Research & projects"),
    ("/publications/", "Publications"),
    ("/about/", "About & CV"),
]


def _abs_url(profile: dict, path: str) -> str | None:
    base = profile["site"].get("url")
    if not is_set(base):
        return None
    return base.rstrip("/") + path


def person_schema(profile: dict) -> dict:
    aff = profile["affiliation"]
    org = {
        "@type": "ResearchOrganization",
        "name": aff["institution"],
        "department": {"@type": "Organization", "name": aff["department"]},
        "address": {"@type": "PostalAddress", "addressCountry": "SI"},
    }
    if is_set(aff.get("url")):
        org["url"] = aff["url"]
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "honorificPrefix": profile["honorific_prefix"],
        "jobTitle": profile["current_title"],
        "worksFor": org,
        "knowsAbout": profile["knows_about"],
        "alumniOf": [
            {"@type": "CollegeOrUniversity", "name": e["institution"]}
            for e in profile["education"]
        ],
    }
    url = _abs_url(profile, "/")
    if url:
        data["url"] = url
    same_as = [
        v for k, v in profile["links"].items()
        if k != "email" and is_set(v)
    ]
    if same_as:
        data["sameAs"] = same_as
    if is_set(profile["links"].get("email")):
        data["email"] = "mailto:" + profile["links"]["email"]
    return data


def head(profile: dict, title: str, description: str, path: str, og_type: str, extra: str) -> str:
    site_name = profile["name"]
    full_title = site_name if title == site_name else f"{title} · {site_name}"
    full_title = plain(full_title)
    description = plain(description)
    canonical = _abs_url(profile, path)
    lines = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(full_title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<meta name="author" content="{esc(site_name)}">',
        '<meta name="color-scheme" content="light">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,300;1,8..60,400&display=swap">',
        '<link rel="stylesheet" href="/css/global.css">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(full_title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:site_name" content="{esc(site_name)}">',
        '<meta property="og:locale" content="en_GB">',
        '<meta name="twitter:card" content="summary">',
    ]
    if canonical:
        lines.append(f'<link rel="canonical" href="{esc(canonical)}">')
        lines.append(f'<meta property="og:url" content="{esc(canonical)}">')
    # og:image must be an absolute URL, so it is only emitted once site.url is set.
    og_image = profile["site"].get("og_image")
    img = _abs_url(profile, og_image) if is_set(og_image) else None
    if img:
        lines.append(f'<meta property="og:image" content="{esc(img)}">')
    if extra:
        lines.append(extra)
    return "\n    ".join(lines)


def header(path: str, profile: dict) -> str:
    items = []
    for href, label in NAV:
        current = ' aria-current="page"' if path.startswith(href) else ""
        items.append(f'<li><a href="{href}"{current}>{esc(label)}</a></li>')
    home_current = ' aria-current="page"' if path == "/" else ""
    # On the home page the header is laid over the hero image.
    cls = "site-header site-header--overlay" if path == "/" else "site-header"
    aff = profile["affiliation"]
    # NIB logo beside the wordmark: a single-colour mask, linked to the institute.
    inst_name = aff["institution"].replace(" (NIB)", "")
    nib = (f'<span class="nib-mark site-brand__nib" aria-hidden="true"></span>'
           f'<span class="site-brand__text">{esc(inst_name)}<br>{esc(aff["department"])}</span>')
    if is_set(aff.get("url")):
        nib = f'<a class="site-brand__inst" href="{esc(aff["url"])}">{nib}</a>'
    else:
        nib = f'<span class="site-brand__inst">{nib}</span>'
    return f"""<header class="{cls}">
  <div class="container site-header__inner">
    <div class="site-brand">
      <a class="site-title" href="/"{home_current}>{esc(profile["name"])}</a>
      {nib}
    </div>
    <nav class="site-nav" aria-label="Main">
      <ul>{"".join(items)}</ul>
    </nav>
    {profile_icons(profile["links"])}
  </div>
</header>"""


# Profile links shown as icons on the right of the header, in this order.
PROFILE_ICONS = [
    ("email", "E-mail"),
    ("orcid", "ORCID"),
    ("google_scholar", "Google Scholar"),
    ("researchgate", "ResearchGate"),
    ("github", "GitHub"),
    ("inaturalist", "iNaturalist"),
]


def profile_icons(links: dict) -> str:
    items = []
    for key, label in PROFILE_ICONS:
        url = links.get(key)
        if not is_set(url):
            continue
        href = f"mailto:{url}" if key == "email" else url
        name = f"E-mail {url}" if key == "email" else f"{label} profile"
        items.append(f'<li><a href="{esc(href)}" aria-label="{esc(name)}" title="{esc(label)}">{icon(key)}</a></li>')
    return f'<ul class="site-profiles" aria-label="Profiles">{"".join(items)}</ul>'


def footer(profile: dict) -> str:
    """One slim line; contact details live on the home page's closing panel and the About page."""
    year = datetime.date.today().year
    aff = profile["affiliation"]
    return f"""<footer class="site-footer">
  <div class="container site-footer__inner">
    <p>© {year} {esc(profile["name"])}, {esc(aff["institution"])}, {esc(aff["country"])}</p>
  </div>
</footer>"""

# Links that leave the site (and full-size files such as figures) open in a new tab, as the
# owner asked; links between the site's own pages stay in the same tab.
_A = re.compile(r"(<a\b[^>]*>)(.*?)(</a>)", re.S)
_NEW_TAB_NOTE = "(opens in a new tab)"


def _opens_elsewhere(href: str, site_url: str | None) -> bool:
    if href.startswith(("http://", "https://")):
        return not (site_url and href.startswith(site_url))
    return bool(re.search(r"\.(pdf|png|jpe?g|webp|svg)$", href, re.I))


def new_tab_links(html: str, site_url: str | None = None) -> str:
    def fix(m: re.Match) -> str:
        tag, inner, end = m.groups()
        href = re.search(r'href="([^"]*)"', tag)
        if not href or "target=" in tag or not _opens_elsewhere(href.group(1), site_url):
            return m.group(0)
        rel = re.search(r'rel="([^"]*)"', tag)
        if rel:
            tag = tag.replace(rel.group(0), f'rel="{rel.group(1)} noopener noreferrer"')
        else:
            tag = tag[:-1] + ' rel="noopener noreferrer">'
        tag = tag[:-1] + ' target="_blank">'
        label = re.search(r'aria-label="([^"]*)"', tag)
        if label:
            tag = tag.replace(label.group(0), f'aria-label="{label.group(1)} {_NEW_TAB_NOTE}"')
        else:
            inner += f'<span class="visually-hidden"> {_NEW_TAB_NOTE}</span>'
        return tag + inner + end
    return _A.sub(fix, html)


def page(profile: dict, *, path: str, title: str, description: str, body: str,
         og_type: str = "website", extra_head: str = "") -> str:
    site_url = profile["site"].get("url")
    return new_tab_links(_page(profile, path=path, title=title, description=description, body=body,
                               og_type=og_type, extra_head=extra_head),
                         site_url if is_set(site_url) else None)


def _page(profile: dict, *, path: str, title: str, description: str, body: str,
          og_type: str, extra_head: str) -> str:
    return f"""<!doctype html>

<html lang="en">
<head>
    {head(profile, title, description, path, og_type, extra_head)}
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
{header(path, profile)}
<main id="main">
{body}
</main>
{footer(profile)}
</body>
</html>
"""


__all__ = ["page", "person_schema", "json_ld"]
