"""Page bodies. Each function returns (path, title, description, body_html, extra_head)."""
from __future__ import annotations

import datetime

from .collab_map import collab_map
from .components import (
    credit_html, esc, ext_link, is_set, json_ld, meta_list, nib_mark, photo, photo_figure,
    publication_list, publication_years, rich,
)
from .layout import person_schema

PUB_EMPTY = "Publications will be listed here once they have been added to the publication data."

# Image `sizes` hints, matched to the CSS layout widths.
SIZES_FULL = "100vw"
SIZES_THIRD = "(min-width: 60rem) 24rem, (min-width: 40rem) 33vw, 100vw"
SIZES_PORTRAIT = "(min-width: 48rem) 22rem, 100vw"
SIZES_HALF = "(min-width: 48rem) 37rem, 100vw"
SIZES_THEME = "(min-width: 56rem) 40rem, 100vw"
SIZES_THEME_PAIR = "(min-width: 56rem) 20rem, 50vw"


# --------------------------------------------------------------------------
# Shared section builders
# --------------------------------------------------------------------------

def theme_rows(themes: list[dict], images: dict, heading_level: int = 3) -> str:
    """Research themes as quiet, equal cards: each has a soft mat of the same shape holding its
    photographs (or figure) at their own proportions, never cropped, then two thin "cantilever"
    lines (Usonian horizontals), a title and summary."""
    h = f"h{heading_level}"
    cards = []
    for i, t in enumerate(themes):
        keys = [k for k in t.get("images", []) if k in images]
        def media_html(k: str) -> str:
            img = images[k]
            if img.get("figure"):
                # Scientific figure: shown wide, linked to the full-size file for reading.
                return (f'<a class="theme-card__img theme-card__figure" href="{esc(img["full"])}" '
                        f'title="Open the full-size figure">{photo(img, "(min-width: 72rem) 18rem, (min-width: 40rem) 45vw, 90vw")}</a>')
            # --r (width / height) lets the photos of a card share one height and fill its width.
            return (f'<span class="theme-card__img" style="--r:{img["width"] / img["height"]:.3f}">'
                    f'{photo(img, "(min-width: 72rem) 10rem, (min-width: 40rem) 25vw, 45vw")}</span>')
        media = "".join(media_html(k) for k in keys)
        wide = " theme-card--figure" if any(images[k].get("figure") for k in keys) else ""
        cards.append(
            f'<article class="theme-card{wide}" id="{esc(t["slug"])}">'
            f'<div class="theme-card__media">{media}</div>'
            '<span class="theme-card__rule" aria-hidden="true"></span>'
            f'<div class="theme-card__text"><{h}>{rich(t["title"])}</{h}><p>{rich(t["summary"])}</p></div>'
            f"</article>"
        )
    return f'<div class="theme-band"><div class="theme-grid">{"".join(cards)}</div></div>'

def hero_quote(profile: dict) -> str:
    """Quotation under the name in the hero; falls back to the tagline."""
    q = profile.get("hero_quote")
    if not q:
        return f'<p class="hero__tagline">{esc(profile["tagline"])}</p>'
    return (f'<figure class="hero__quote"><blockquote><p>{esc(q["text"])}</p></blockquote>'
            f'<figcaption>{esc(q["author"])}, {esc(q["year"])}</figcaption></figure>')


# Rows of the reptile strip (keys in data/images.json). Photos keep their own proportions;
# each row is scaled to fill the width, so no animal is cropped.
# Rows have the same number of photos with similar proportions, so column edges line up
# and the colour checkerboard also holds vertically.
REPTILE_ROWS = (
    ("horvathi-karst", "reptile-moss", "muralis", "reptile-measured", "gallotia", "reptile-snake"),
    ("reptile-concrete", "algyroides", "reptile-leaves", "zootoca", "reptile-gecko", "horvathi-43"),
)


def reptile_strip(images: dict) -> str:
    """Full-width rows of duotone reptile photographs, alternating mustard and limestone grey
    in a checkerboard so tiles of the same colour never touch. Species are named in the alt text."""
    rows = []
    index = 0
    for r, keys in enumerate(REPTILE_ROWS):
        tiles = []
        for col, k in enumerate(k for k in keys if k in images):
            img = images[k]
            ratio = img["width"] / img["height"]
            tone = "mustard" if (r + col) % 2 == 0 else "stone"
            # Phone layout: two per line, checkerboard by line.
            m_tone = "mustard" if (index // 2 + index % 2) % 2 == 0 else "stone"
            tiles.append(
                # Pre-rendered duotones (scripts/make_duotones.py); phones get their own checkerboard tone.
                f'<figure class="reptile tone-{tone} m-tone-{m_tone}"><picture>'
                f'<source media="(max-width: 47.99rem)" srcset="{img["base"]}-duo-{m_tone}-800.webp">'
                f'<img src="{img["base"]}-duo-{tone}-800.webp" width="800" height="{round(800 / ratio)}" '
                f'alt="{esc(img["alt"])}" loading="{"eager" if r == 0 else "lazy"}" decoding="async"></picture></figure>'
            )
            index += 1
        rows.append(f'<div class="reptiles__row">{"".join(tiles)}</div>')
    return f'<section class="reptiles" aria-label="Study species">{"".join(rows)}</section>'

COLLAGE = ("sardinia", "urban-lizard", "circle-samples", "spitzkoppe", "snake-sign-43")


def collage(images: dict) -> str:
    """Overlapping rectangular photographs of Urban beside the About text, each on an offset
    flat colour block (mid-century collage)."""
    items = "".join(
        f'<span class="collage__item collage__item--{i} collage__item--{("mustard", "stone")[i % 2]}">'
        f'<span class="collage__photo">{photo(images[k], "(min-width: 48rem) 16rem, 45vw")}</span></span>'
        for i, k in enumerate(COLLAGE) if k in images
    )
    return f'<div class="collage">{items}</div>'


HABITATS = ("land-gorge", "land-alpine", "land-mountains", "land-cliffs", "land-dunes")


def habitat_row(images: dict) -> str:
    """Full-width row of landscape photographs (mood): karst river, alpine valley, mountains,
    limestone cliffs and desert. Landscapes only, so cropping to a common height is fine."""
    tiles = "".join(
        f'<figure class="habitat" style="--ratio:{images[k]["width"] / images[k]["height"]:.3f}">'
        f'{photo(images[k], "(min-width: 48rem) 25vw, 50vw")}</figure>'
        for k in HABITATS if k in images
    )
    return f'<div class="habitats">{tiles}</div>'


def closing_hero(img: dict, profile: dict) -> str:
    """Second full-screen photograph at the end of the page, pinned like the first hero,
    with the contact details set over it in light mustard."""
    aff, links = profile["affiliation"], profile["links"]
    inst = esc(aff["institution"])
    if is_set(aff.get("url")):
        inst = ext_link(aff["url"], inst)
    items = []
    if is_set(links.get("email")):
        items.append(f'<li><a href="mailto:{esc(links["email"])}">{esc(links["email"])}</a></li>')
    for key, label in (("orcid", "ORCID"), ("google_scholar", "Google Scholar"), ("researchgate", "ResearchGate"),
                       ("github", "GitHub"), ("inaturalist", "iNaturalist"), ("institutional_profile", "NIB profile"), ("linkedin", "LinkedIn")):
        if is_set(links.get(key)):
            items.append(f"<li>{ext_link(links[key], label, rel_me=True)}</li>")
    return f"""
<section class="hero hero--closing" aria-labelledby="contact">
  {photo(img, SIZES_FULL, cls="hero__media")}
  <div class="closing">
    <h2 id="contact" class="closing__title">Contact</h2>
    {nib_mark(aff["institution"], "closing__nib")}
    <address class="closing__address"><strong>{inst}</strong><br>{esc(aff["department"])}<br>{esc(aff["city"])}, {esc(aff["country"])}</address>
    <ul class="closing__links">{"".join(items)}</ul>
  </div>
</section>"""

def hero(profile: dict, img: dict) -> str:
    """Full-bleed opening image (or optional muted looping video) with the name over it."""
    aff = profile["affiliation"]
    media = photo(img, SIZES_FULL, eager=True, cls="hero__media")
    control = ""
    video = img.get("video")
    if is_set(video):
        poster = f'{img["base"]}-{img["sizes"][-2] if len(img["sizes"]) > 1 else img["sizes"][0]}.webp'
        sources = "".join(
            f'<source src="{esc(video[k])}" type="video/{k}">' for k in ("webm", "mp4") if is_set(video.get(k))
        )
        # No autoplay attribute: the script starts playback only when reduced motion is not requested.
        media += (f'<video class="hero__media hero__video" muted loop playsinline preload="none" '
                  f'poster="{poster}" aria-hidden="true">{sources}</video>')
        control = ('<button class="hero__toggle" type="button" hidden>Pause video</button>'
                   '<script src="/js/hero-video.js" defer></script>')
    return f"""<section class="hero" aria-labelledby="page-title">
  {media}
  <div class="hero__inner container">
    <div class="hero__head">
      <h1 id="page-title" class="hero__name">{" ".join(f"<span>{esc(part)}</span>" for part in profile["name"].split())}</h1>
    </div>
    {hero_quote(profile)}
  </div>
  {f'<p class="hero__credit">{rich(img["caption"])}</p>' if is_set(img.get("caption")) else ""}
  {control}
</section>"""


def _project_cell(r: dict, i: int, heading: str = "h3", full: bool = True) -> str:
    acr = esc(r["acronym"])
    title = rich(r["name"]) if is_set(r.get("name")) else ""
    if title and is_set(r.get("url")):
        title = ext_link(r["url"], title)
    meta = [esc(r[k]) for k in ("kind", "code") if is_set(r.get(k)) and r.get(k) != r.get("acronym")]
    if is_set(r.get("role")):
        meta.insert(0, esc(r["role"]))
    if is_set(r.get("leader")):
        meta.append(f"led by {esc(r['leader'])}")
    years = esc(r["years"]) if is_set(r.get("years")) else ""
    summary = ""
    if full and r.get("description"):
        summary = "".join(f'<p class="project__summary">{rich(x)}</p>' for x in r["description"])
    elif full and is_set(r.get("summary")):
        summary = f'<p class="project__summary">{rich(r["summary"])}</p>'
    return (
        f'<li class="project project--c{i % 4}" id="{esc(r["acronym"].lower())}">'
        f'<p class="project__acronym">{acr}</p>'
        f'<p class="project__years">{years}</p>'
        + (f'<{heading} class="project__title">{title}</{heading}>' if title else "")
        + f'<p class="project__meta">{"; ".join(meta)}</p>{summary}</li>'
    )


def _end_year(r: dict) -> int:
    """End year from '2025–2032'; open-ended ('2020–') counts as ongoing."""
    parts = str(r.get("years", "")).replace("-", "–").split("–")
    return int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 9999


def sort_projects(projects: list[dict]) -> list[dict]:
    """Ongoing projects first, then the rest; within each, latest end year first. Programme last."""
    year = datetime.date.today().year
    return sorted(projects, key=lambda r: (r.get("code") == "P1-0255", _end_year(r) < year, -_end_year(r)))


def is_ongoing(r: dict) -> bool:
    return _end_year(r) >= datetime.date.today().year and r.get("status") != "finished"


def project_list(projects: list[dict]) -> str:
    """Funded projects: acronym in a mid-century colour, then title, role, funder, code and years."""
    return f'<ul class="projects">{"".join(_project_cell(r, i) for i, r in enumerate(sort_projects(projects)))}</ul>'


def project_strip(projects: list[dict]) -> str:
    """Home page: all projects side by side across the full width, equal heights."""
    current = [r for r in sort_projects(projects) if r.get("code") != "P1-0255" and is_ongoing(r)]
    items = "".join(_project_cell(r, i, "h3", full=False) for i, r in enumerate(current))
    return f'<ul class="projects projects--strip">{items}</ul>'

def related_publications(project: dict, pubs: list[dict], variants: list[str], level: int = 3) -> str:
    ids = project.get("publications") or []
    related = [p for p in pubs if p.get("id") in ids]
    if not related:
        return ""
    return (f'<h{level} class="feature__sub">Publications</h{level}>'
            + publication_list(related, variants, "", heading_level=level + 1))


def project_feature(project: dict, heading_level: int = 3, related: str = "") -> str:
    rows = []
    if is_set(project.get("research_question")):
        rows.append(("Question", rich(project["research_question"])))
    for key, label in (("context", "Context"), ("status", "Status"), ("study_system", "Study system")):
        if is_set(project.get(key)):
            rows.append((label, rich(project[key])))
    if is_set(project.get("methods")):
        rows.append(("Methods", esc(", ".join(project["methods"]))))
    if is_set(project.get("field_sites")):
        rows.append(("Field sites", rich(project["field_sites"])))
    if is_set(project.get("collaborators")):
        rows.append(("Collaborators", rich(project["collaborators"])))
    h = f"h{heading_level}"
    return (
        f'<article class="feature">'
        f"<{h}>{rich(project['title'])}</{h}>"
        f'<div class="prose"><p>{rich(project["summary"])}</p></div>'
        f"{meta_list(rows)}{related}</article>"
    )


def section(heading: str, heading_id: str, content: str, cls: str = "", hide_heading: bool = False) -> str:
    """A page section; hide_heading keeps the heading for screen readers only."""
    h_cls = ' class="visually-hidden"' if hide_heading else ""
    return f"""<section class="section container {cls}" aria-labelledby="{heading_id}">
  <h2 id="{heading_id}"{h_cls}>{heading}</h2>
  {content}
</section>"""


def contact_block(profile: dict) -> str:
    aff = profile["affiliation"]
    links = profile["links"]
    inst = esc(aff["institution"])
    if is_set(aff.get("url")):
        inst = ext_link(aff["url"], inst)
    address = (
        f'{nib_mark(aff["institution"], "contact__nib")}'
        f"<address><strong>{inst}</strong><br>"
        f"{esc(aff['department'])}<br>{esc(aff['city'])}, {esc(aff['country'])}</address>"
    )
    items = []
    if is_set(links.get("email")):
        items.append(f'<li><a href="mailto:{esc(links["email"])}">{esc(links["email"])}</a></li>')
    labels = [
        ("institutional_profile", "Institutional profile (NIB)"),
        ("orcid", "ORCID"),
        ("google_scholar", "Google Scholar"),
        ("github", "GitHub"),
        ("researchgate", "ResearchGate"),
        ("linkedin", "LinkedIn"),
    ]
    for key, label in labels:
        if is_set(links.get(key)):
            items.append(f"<li>{ext_link(links[key], label, rel_me=True)}</li>")
    profiles = f'<ul class="link-list">{"".join(items)}</ul>' if items else ""
    return (
        f'<div class="contact"><div><h3 class="visually-hidden">Affiliation</h3>{address}</div>'
        f'<div><h3 class="visually-hidden">Academic profiles</h3>{profiles}</div></div>'
    )


def bio_paragraphs(profile: dict) -> list[str]:
    """Biography with some personality, built only from verified facts (CV, SICRIS, publications)."""
    return [
        "I am an ecologist who spends part of the year chasing lizards and the rest turning what I find into "
        "models. I currently work at the National Institute of Biology (NIB) in Ljubljana, where I keep returning "
        "to the question: what lets ecologically similar species coexist, and will they still manage it as "
        "climate and habitats change?",
        "My PhD (University of Ljubljana, cum laude, 2026) followed two lizards that meet on Slovenia's rocks: "
        '<i class="taxon">Iberolacerta horvathi</i>, a mountain specialist, and <i class="taxon">Podarcis muralis</i>, '
        "a lowland generalist. With fieldwork, physiology and Dynamic Energy Budget models I worked out where each "
        "can live, where they overlap, and how that overlap may shift as climate and habitats change. Before that, my master's "
        "thesis followed the blood parasites the two species share.",
        "I now coordinate NIB's part "
        "of LIFE4ADAPT, one of Slovenia's largest climate-adaptation projects, and work with owls and apex predators "
        "in CO-STRIX and ExtremePredator. In 2025 I spent a month in Michael Kearney's Biophysical Ecology Lab in "
        "Melbourne, bringing NicheMapR and Dynamic Energy Budget models together to study competing ectotherms.",
        "Fieldwork has taken me from the Balkans to the Canary Islands and the deserts of Namibia. Closer to home "
        "I co-supervise master's students, give occasional lectures and field courses at the University of "
        "Primorska and, after three years as its president, still volunteer with the Slovenian Herpetological Society.",
    ]

# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def home(d: dict):
    profile, themes, images = d["profile"], d["themes"], d["images"]
    variants = profile["author_name_variants"]
    # Recent publications: articles from this year and last year.
    since = datetime.date.today().year - 1
    selected = [p for p in d["publications"] if p.get("type", "article") == "article" and int(p.get("year", 0)) >= since]

    aff = profile["affiliation"]
    themes_html = theme_rows(themes, images)

    band = habitat_row(images)

    current = (project_strip(profile.get("research_participation", []))
               + '<p class="more-link"><a href="/research/#projects">Research and projects in detail</a></p>')

    collab = d["collaborators"]
    dark = f"""<div class="dark">
  <section class="section collab-section" aria-labelledby="collaborations">
    <div class="container"><h2 id="collaborations">Collaborations</h2></div>
    {collab_map(collab, d["basemap"], d["publications"], aff["city"], "National Institute of Biology")}
  </section>
</div>"""

    # Home: one short introduction (statement and biography combined), set in Jost.
    # The longer biography stays on the About & CV page (bio_paragraphs).
    intro = [
        "I'm an ecologist at the National Institute of Biology (NIB) in Ljubljana. I spend part of the year "
        "chasing lizards and the rest turning what I find into models: I combine field observations and "
        "physiological data with mechanistic models to understand where species can live and when ecologically "
        "similar species can coexist.",
        "My PhD (University of Ljubljana, cum laude, 2026) followed two lizards that meet in Slovenia's highlands, "
        '<i class="taxon">Iberolacerta horvathi</i>, a mountain specialist, and <i class="taxon">Podarcis muralis</i>, '
        "a lowland generalist, and how their overlap may shift as climate and habitats change. I now coordinate "
        "NIB's part of LIFE4ADAPT, one of Slovenia's largest climate-adaptation projects, contribute to work on "
        "owls and apex predators, and co-supervise master's students. In 2025 I spent a month in Michael "
        "Kearney's Biophysical Ecology Lab in Melbourne.",
        "Fieldwork has taken me from the Balkans to the Canary Islands and the deserts of Namibia. Closer to home, "
        "I volunteer with the Slovenian Herpetological Society, hike in the Alps, pick mushrooms, and spend a fair "
        "amount of time observing creatures of all shapes and sizes.",
    ]
    about = f"""<section class="section container about about--home" aria-labelledby="about-me">
  <div class="about__side">{collage(images)}{illus_img("heat", "about__illus", "36rem")}</div>
  <div class="about__text">
    <h2 id="about-me" class="visually-hidden">About me</h2>
    <p class="about__lead">I study how organisms interact with each other and with their physical environment, and how climate change affects these relationships and their coexistence.</p>
    <span class="about__rule" aria-hidden="true"></span>
    {"".join(f'<p class="about__p">{p}</p>' for p in intro)}
    <p class="more-link"><a href="/about/">More about me</a></p>
  </div>
</section>"""

    pub_html = publication_list(selected, variants, PUB_EMPTY)
    pub_html += '<p class="more-link"><a href="/publications/">All publications</a></p>'

    # Two "stages", each confining its pinned photograph:
    # 1) the hero stays fixed at the top while the main content (.page-over) scrolls over it;
    # 2) the closing photo stays fixed at the bottom and is revealed as the dark band scrolls off it.
    main_content = "\n".join([
        reptile_strip(images),
        about,
        section("Research themes", "themes", themes_html, hide_heading=True),
        band,
        section("Current projects", "current", current),
        section("Recent publications", "publications", illus_img("daycycle", "backdrop", "100vw") + pub_html,
                cls="tint pubs-grid backdrop-wrap"),
    ])
    body = (
        f'<div class="stage">\n{hero(profile, images["hero"])}\n<div class="page-over">\n{main_content}\n</div>\n</div>\n'
        f'<div class="stage">\n<div class="page-over">\n{dark}\n</div>\n{closing_hero(images["net-wide"], profile)}\n</div>'
    )
    extra = json_ld(person_schema(profile))
    return "/", profile["name"], profile["site"]["description"], body, extra


# Decorative illustrations beside page intros (scripts/make_illustrations.py): name -> (width, height).
ILLUS = {"energy": (1400, 1050), "heat": (1400, 1050), "daycycle": (1400, 1050), "competition": (1400, 788)}


def illus_img(name: str, cls: str, sizes: str) -> str:
    """A decorative illustration (empty alt, hidden from screen readers)."""
    w, h = ILLUS[name]
    return (f'<img class="{cls}" src="/images/illus-{name}-800.webp" '
            f'srcset="/images/illus-{name}-800.webp 800w, /images/illus-{name}-1400.webp 1400w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="" aria-hidden="true" decoding="async">')


def page_head(title: str, intro_html: str, illus: str = "") -> str:
    """Page title and intro; illus adds a soft, decorative illustration in the empty space beside it."""
    art, cls = "", ""
    if illus in ILLUS:
        art = illus_img(illus, "page-head__illus", "40rem")
        cls = " page-head--illus"
    return f"""<div class="page-head container{cls}">
  {art}<h1>{title}</h1>
  <div class="prose">{intro_html}</div>
</div>"""


def research(d: dict):
    """Research and projects on one page: themes, current projects in depth, then finished work (PhD and finished projects)."""
    profile = d["profile"]
    intro = (
        "<p>I study how organisms interact with each other and with their physical environment, and how these "
        "relationships change under climate change. Most of my work is on lizards. I measure their physiology "
        "and the microclimates they live in, in the field and in the laboratory, and use these data in "
        "mechanistic models, Dynamic Energy Budget theory and NicheMapR, that predict where species can live "
        "and when they can coexist.</p>"
        "<p>The four themes below describe what I work on. The projects that follow are the funded collaborations "
        "the work happens in, at the National Institute of Biology and with partners in Slovenia and abroad.</p>"
    )
    themes = (f'<section class="section container" aria-labelledby="themes-h">'
              f'<h2 id="themes-h" class="visually-hidden">Research themes</h2>'
              f'{theme_rows(d["themes"], d["images"])}</section>')
    projects_html = section(
        "Projects", "projects",
        project_list([r for r in profile.get("research_participation", []) if r.get("code") != "P1-0255" and is_ongoing(r)])
        + '<p class="note">All projects run within the research programme P1-0255, '
          '<i>Communities, interactions and communications in ecosystems</i> (ARIS, led by David Stanković).</p>',
    )
    # Finished work: the PhD (briefly) and finished projects.
    done = [r for r in profile.get("research_participation", []) if r.get("code") != "P1-0255" and not is_ongoing(r)]
    phd_pub = next((p for p in d["publications"] if p.get("id") == "dajcman-2025-microclimate-coexistence"), None)
    paper = (f' Main paper: {ext_link("https://doi.org/" + phd_pub["doi"], "<cite>" + rich(phd_pub["title"]) + "</cite>")}'
             f' (<cite>{esc(phd_pub["journal"])}</cite>, {esc(phd_pub["year"])}).') if phd_pub else ""
    finished = section(
        "Finished", "finished",
        '<div class="phd-brief">'
        '<p class="finished__label">PhD · University of Ljubljana · January 2026 · cum laude</p>'
        '<p class="phd-brief__title"><cite>Mechanistic understanding of ecological niche overlap in two sympatric lizard species</cite></p>'
        '<p>How <i class="taxon">Iberolacerta horvathi</i> and <i class="taxon">Podarcis muralis</i> share space along '
        f'elevation gradients, now and in a warmer climate. Supervised by Anamarija Žagar and Urtzi Enriquez-Urzelai. '
        f'Funded by an ARIS Young Researcher grant.{paper}</p>'
        '</div>' + (project_list(done) if done else ''),
    )
    return ("/research/", "Research & projects",
            "Research themes and projects of Urban Dajčman: mechanistic modelling, species interactions, thermal ecology, "
            "ecophysiology; LIFE4ADAPT, CO-STRIX, ExtremePredator and WETADAPT.",
            page_head("Research &amp; projects", intro, illus="energy") + themes + projects_html + finished, "")

def projects(d: dict):
    """Projects now live on the Research page; /projects/ forwards there so old links keep working."""
    intro = '<p>Projects are now part of the <a href="/research/#projects">Research &amp; projects</a> page.</p>'
    return ("/projects/", "Projects", "Projects of Urban Dajčman, now on the Research & projects page.",
            page_head("Projects", intro), '<meta http-equiv="refresh" content="0; url=/research/#projects">')

def publications(d: dict):
    profile = d["profile"]
    groups = [("article", "Peer-reviewed articles"), ("preprint", "Preprints"),
              ("report", "Reports and other outputs"), ("thesis", "Theses"), ("data", "Data and code")]
    blocks = []
    for key, label in groups:
        group = [p for p in d["publications"] if p.get("type", "article") == key]
        if group:
            blocks.append(
                f'<section class="section container" aria-labelledby="pub-{key}"><h2 id="pub-{key}">{label}</h2>'
                f'{publication_years(group, profile["author_name_variants"], key)}</section>'
            )
    if not blocks:
        blocks.append(f'<div class="container"><p class="empty-state">{PUB_EMPTY}</p></div>')
    # No visible title or intro: the list starts the page (the h1 stays for screen readers).
    head = '<div class="container pubs-head"><h1 class="visually-hidden">Publications</h1></div>'
    return ("/publications/", "Publications",
            "Publications by Urban Dajčman on species interactions, thermal ecology, ecophysiology, parasite ecology and mechanistic modelling.",
            ('<div class="backdrop-wrap">' + illus_img("daycycle", "backdrop", "100vw")
             + head + "\n".join(blocks) + "</div>"), "")


FIELD_GALLERY = ("team-field", "sardinia", "reptile-box", "spitzkoppe", "lizard", "sem",
                 "rock-face", "tenerife", "urban-lizard", "snake-sign", "beach")


def field_gallery(images: dict) -> str:
    """'In the field': full-width, sideways-scrolling gallery (click and drag); all photos the
    same height at their own proportions. Shown on the About & CV page."""
    items = "".join(f'<figure class="field__item">{photo(images[k], "(min-width: 48rem) 40vw, 80vw")}</figure>'
                    for k in FIELD_GALLERY if k in images)
    return f"""<div class="dark">
  <section class="section field" aria-labelledby="field">
    <div class="container field__head">
      <h2 id="field">In the field</h2>
    </div>
    <div class="field__scroller" tabindex="0" role="region" aria-label="Fieldwork photographs, scrolls sideways">
      {items}
    </div>
  </section>
</div>
<script src="/js/field-gallery.js" defer></script>"""


def cv_panels(d: dict) -> list[tuple[str, str, str]]:
    """CV content as (id, label, html) panels, shown one at a time by the selector on the About page."""
    profile = d["profile"]

    def dated(rows: list[tuple[str, str]]) -> str:
        return '<ul class="cv-list">' + "".join(
            f'<li><span class="when">{w}</span><span>{body}</span></li>' for w, body in rows) + "</ul>"

    def span(start, end) -> str:
        if not is_set(start):
            return "Current"
        return f"{esc(start)}–{esc(end)}" if is_set(end) else f"{esc(start)}–"

    emp = []
    for p in profile["positions"]:
        details = "".join(f"<li>{rich(x)}</li>" for x in p.get("details", []))
        emp.append((span(p.get("start"), p.get("end")),
                    f'<strong>{esc(p["title"])}</strong><br>{esc(p["organisation"])}'
                    + (f'<ul class="cv-details">{details}</ul>' if details else "")))
    edu = []
    for e in profile["education"]:
        detail = esc(e["institution"])
        if is_set(e.get("thesis_title")):
            detail += f"<br>Thesis: <cite>{rich(e['thesis_title'])}</cite>"
        if is_set(e.get("thesis_title_en")):
            detail += f" (English: <cite>{rich(e['thesis_title_en'])}</cite>)"
        if is_set(e.get("supervisors")):
            detail += f"<br>Supervision: {esc(e['supervisors'])}"
        edu.append((esc(e["year"]), f'<strong>{esc(e["degree"])}</strong><br>{detail}'))
    intl = [(esc(x["years"]), f'<strong>{esc(x["title"])}</strong><br>{esc(x["place"])}'
             + (f'<br>{rich(x["detail"])}' if is_set(x.get("detail")) else "")) for x in profile.get("international", [])]
    field = [(esc(x["years"]), f'<strong>{esc(x["place"])}</strong><br>{esc(x["detail"])}') for x in profile.get("fieldwork", [])]
    lead = [(esc(x["years"]), f'<strong>{esc(x["role"])}</strong><br>{esc(x["org"])}') for x in profile.get("leadership", [])]
    conf = [(esc(x["year"]), esc(x["name"]) + (f", {esc(x['place'])}" if is_set(x.get("place")) else ""))
            for x in profile.get("conferences", [])]
    talks = [(esc(x["year"]), f'{esc(x["kind"])}: <cite>{esc(x["title"])}</cite><br>{esc(x["venue"])}') for x in profile.get("talks", [])]
    teach = [(esc(x["years"]), esc(x["role"])) for x in profile.get("teaching", [])]
    grants = [(esc(x["years"]), esc(x["title"])) for x in profile.get("grants", [])]
    outreach = [(esc(x["year"]), esc(x["text"])) for x in profile.get("outreach", [])]
    skills = [(esc(x["area"]), esc(x["items"])) for x in profile.get("skills", [])]
    langs = [(esc(x["level"]), esc(x["language"])) for x in profile.get("languages", [])]
    part = []
    for r in sort_projects(profile.get("research_participation", [])):
        name = esc(r["acronym"]) + (f": {rich(r['name'])}" if is_set(r.get("name")) and r["name"] != r["acronym"] else "")
        meta = [esc(r[k]) for k in ("role", "kind", "code") if is_set(r.get(k)) and r.get(k) != r.get("acronym")]
        if is_set(r.get("leader")):
            meta.append(f"led by {esc(r['leader'])}")
        part.append((esc(r["years"]) if is_set(r.get("years")) else "", f'<strong>{name}</strong><br>{"; ".join(meta)}'))
    mem = "".join(f"<li>{esc(m)}</li>" for m in profile.get("memberships", []))
    review = ", ".join(f"<cite>{esc(j)}</cite>" for j in profile.get("reviewing", []))
    pubs = publication_list([p for p in d["publications"] if p.get("type", "article") in ("article", "thesis")],
                            profile["author_name_variants"], PUB_EMPTY, heading_level=4)
    sub = lambda t: f'<h4 class="cv-sub">{t}</h4>'
    return [
        ("cv-emp", "Employment", dated(emp)),
        ("cv-edu", "Education", dated(edu)),
        ("cv-funding", "Funding", dated(grants)),
        ("cv-proj", "Projects", dated(part)),
        ("cv-pubs", "Publications", pubs + '<p class="more-link"><a href="/publications/">All publications, data and code</a></p>'),
        ("cv-talks", "Talks & conferences", sub("Selected talks") + dated(talks) + sub("Conferences") + dated(conf)),
        ("cv-teach", "Teaching & review", dated(teach) + sub("Peer review") + f"<p>Reviewer for {review}.</p>"),
        ("cv-intl", "International & fieldwork", dated(intl) + sub("Fieldwork") + dated(field)),
        ("cv-outreach", "Outreach", dated(outreach)),
        ("cv-mem", "Memberships", dated(lead) + sub("Memberships") + f'<ul class="cv-simple">{mem}</ul>'),
        ("cv-skills", "Skills & languages", dated(skills) + sub("Languages") + dated(langs)),
    ]


def about(d: dict):
    """About and CV on one page: biography, CV with a section selector, contact, image credits."""
    profile, images = d["profile"], d["images"]
    bio = "".join(f"<p>{p}</p>" for p in bio_paragraphs(profile))
    top = f"""<div class="page-head container about">
  <div class="about__side">{collage(images)}{illus_img("heat", "about__illus", "36rem")}</div>
  <div class="about__text">
    <h1>About &amp; CV</h1>
    <div class="prose">{bio}</div>
  </div>
</div>"""
    panels = cv_panels(d)
    tabs = "".join(
        f'<button type="button" role="tab" id="tab-{pid}" aria-controls="{pid}" aria-selected="false" tabindex="-1">{esc(label)}</button>'
        for pid, label, _ in panels
    )
    bodies = "".join(
        f'<section class="cv-panel" id="{pid}" role="tabpanel" aria-labelledby="tab-{pid}">'
        f'<h3 class="cv-panel__title">{esc(label)}</h3>{html}</section>'
        for pid, label, html in panels
    )
    cv_html = f"""<section class="section container cv" aria-labelledby="cv">
  <h2 id="cv">Curriculum vitae</h2>
  <div class="cv-tabs" role="tablist" aria-label="CV sections" hidden>{tabs}</div>
  <div class="cv-panels">{bodies}</div>
</section>
<script src="/js/cv-tabs.js" defer></script>"""
    # One credits list instead of credits under every photo; reused (licensed) photos must stay listed.
    credits = []
    for img in images.values():
        if img.get("credit_on_site") is False or not is_set(img.get("credit")):
            continue
        what = rich(img["caption"]) if is_set(img.get("caption")) else esc(img["alt"].rstrip("."))
        credits.append(f"<li>{what}: {credit_html(img).replace('Photo: ', '')}</li>")
    credits_html = f'<ul class="credits">{"".join(sorted(set(credits)))}</ul>'
    rest = (
        field_gallery(images)
        + cv_html
        + section("Contact", "contact", contact_block(profile))
        + section("Image credits", "credits", credits_html, cls="small")
    )
    return ("/about/", "About & CV",
            "About Urban Dajčman, ecologist at the National Institute of Biology, Slovenia: biography and curriculum vitae (employment, education, funding, projects, publications, talks, teaching) and contact.",
            top + rest, json_ld(person_schema(profile)))


def cv(d: dict):
    """The CV now lives on the About page; /cv/ forwards there so old links keep working."""
    intro = '<p>The curriculum vitae is now part of the <a href="/about/#cv">About &amp; CV</a> page.</p>'
    return ("/cv/", "CV", "Curriculum vitae of Urban Dajčman, now on the About & CV page.",
            page_head("Curriculum vitae", intro), '<meta http-equiv="refresh" content="0; url=/about/#cv">')

def not_found(d: dict):
    intro = '<p>The page you requested does not exist. Return to the <a href="/">home page</a>.</p>'
    return ("/404.html", "Page not found", "Page not found.", page_head("Page not found", intro), "")


PAGES = [home, research, projects, publications, about, cv, not_found]
