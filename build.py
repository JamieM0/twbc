#!/usr/bin/env python3
"""
Build script for the TWBC site.

Reads the manuscript markdown in place (../manuscript), renders static HTML
into this folder (twbc/), and copies assets from src/.

    python3 build.py

Zero dependencies. Edit the markdown, re-run, refresh.
- Infobox -> interactive mapping: src/interactives.json
- Landing-page copy: INDEX_* constants below
- Research-page entries: RESEARCH_GROUPS below (hand-curated, reader-facing);
  the sources list is parsed from ../research/sources/SOURCES.md
"""

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # twbc/
PROJECT = ROOT.parent                            # AI-Religion/
SRC = ROOT / "src"
MANUSCRIPT = PROJECT / "manuscript"
SOURCES_MD = PROJECT / "research" / "sources" / "SOURCES.md"
ASSET_VERSION = str(max((SRC / "style.css").stat().st_mtime_ns,
                        (SRC / "site.js").stat().st_mtime_ns))

SITE_TITLE = "The Word Became Compute"
AUTHORS = "Jamie Matthews · Claude"

PARTS = [
    ("part-one",   "Part One",   "I"),
    ("part-two",   "Part Two",   "II"),
    ("part-three", "Part Three", "III"),
    ("part-four",  "Part Four",  "IV"),
    ("part-five",  "Part Five",  "V"),
]

GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Literata:ital,opsz,wght@0,7..72,400..700;1,7..72,400..700"
    "&family=Figtree:ital,wght@0,400..700;1,400..700"
    "&display=swap"
)

# ---------------------------------------------------------------- text utils

def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def smart_quotes(t: str) -> str:
    t = re.sub(r"(\w)'(\w)", r"\1’\2", t)                    # contractions
    t = re.sub(r"'(\d\d)", r"’\1", t)                        # ’90s
    t = re.sub(r"(^|[\s(\[—–-])'", r"\1‘", t, flags=re.M)    # opening single
    t = t.replace("'", "’")
    t = re.sub(r'(^|[\s(\[—–-])"', r"\1“", t, flags=re.M)    # opening double
    t = t.replace('"', "”")
    return t


def inline_md(t: str) -> str:
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def prose(t: str) -> str:
    return inline_md(smart_quotes(esc(t)))


def word_count(t: str) -> int:
    return len(re.findall(r"\S+", t))


# ------------------------------------------------------------- page template

def font_options() -> str:
    serif = ["Literata", "Gentium Book Plus", "Source Serif 4", "Palatino"]
    sans = ["Figtree", "Inter", "Lato", "Lexend", "Manrope",
            "Atkinson Hyperlegible"]
    def opts(names):
        return "".join(f'<option value="{n}">{n}</option>' for n in names)
    return (f'<optgroup label="Serif">{opts(serif)}</optgroup>'
            f'<optgroup label="Sans">{opts(sans)}</optgroup>')


def topbar(active_slug: str) -> str:
    links = []
    for slug, _, roman in PARTS:
        cur = ' aria-current="page"' if slug == active_slug else ""
        links.append(f'<a href="/{slug}" title="{slug.replace("-", " ").title()}"{cur}>{roman}</a>')
    cur_r = ' aria-current="page"' if active_slug == "research" else ""
    nav = "".join(links) + f'<span class="sep"></span><a href="/research"{cur_r}>Research</a>'
    return f"""
<div id="progress"></div>
<header id="topbar">
  <div class="inner">
    <a class="wordmark" href="/"><span class="full">The Word <span class="amp">⁂</span> Became Compute</span><span class="short">TW<span class="amp">⁂</span>BC</span></a>
    <nav id="partnav" aria-label="Parts">{nav}</nav>
    <button id="ctl-btn" aria-expanded="false" aria-controls="ctl-pop" title="Display settings">Aa</button>
  </div>
  <div id="ctl-pop" hidden>
    <h3>Typeface</h3>
    <select id="font-sel" aria-label="Typeface">{font_options()}</select>
    <h3>Text size</h3>
    <div class="stepper">
      <button id="size-minus" aria-label="Smaller text">A&minus;</button>
      <span class="val" id="size-val">18px</span>
      <button id="size-plus" aria-label="Larger text">A+</button>
    </div>
    <h3>Sidebar</h3>
    <label class="ctl-check"><input type="checkbox" id="hide-ix-toggle"> Hide interactive elements</label>
    <label class="ctl-check"><input type="checkbox" id="hide-tl-toggle"> Hide timeline</label>
    <h3>Page</h3>
    <div class="theme-seg" role="group" aria-label="Page background">
      <button data-theme="standard">Standard</button>
      <button data-theme="dark">Dark</button>
      <button data-theme="paper">Paper</button>
    </div>
  </div>
</header>"""


def page(slug: str, title: str, body: str, desc: str) -> str:
    return f"""<!doctype html>
<html lang="en-GB" data-theme="standard">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{GOOGLE_FONTS}">
<link rel="stylesheet" href="assets/style.css?v={ASSET_VERSION}">
<script src="assets/site.js?v={ASSET_VERSION}"></script>
</head>
<body data-slug="{slug}">
{topbar(slug)}
{body}
<footer class="site">
  <span class="authors">{AUTHORS}</span><br>
  Ada, Humane Labs, and the Fellowship are fiction. The research is real.<br>
  <a href="/">{SITE_TITLE}</a>
</footer>
<div id="resume-pill" role="status">Picking up where you left off <button>Start from the top</button></div>
</body>
</html>"""


# ------------------------------------------------------------ manuscript

def render_infobox(raw: str, interactive_html: str | None, box_id: str | None = None) -> str:
    raw = raw.strip()
    title_m = re.match(r"\*\*(.+?)\*\*\s*", raw)
    title = title_m.group(1).strip() if title_m else "Aside"
    rest = raw[title_m.end():] if title_m else raw
    summary = title.rstrip(".")

    paras = [p.strip() for p in re.split(r"\n\s*\n", rest) if p.strip()]
    body = []
    for p in paras:
        h = prose(p)
        h = re.sub(r"<em>\((.*?)\)</em>", r'<span class="cite">(\1)</span>', h)
        body.append(f"<p>{h}</p>")
    ix = interactive_html or ""
    id_attr = f' id="{esc(box_id)}"' if box_id else ""
    return (f'<details class="infobox"{id_attr}>'
            f'<summary>{prose(summary)}</summary>'
            f'<div class="ib-body">{"".join(body)}{ix}</div>'
            f'</details>')


def rail_html(meta: dict, scene_count: int, rail_items: list) -> str:
    """The chronicle rail: a live snapshot of the state of the story,
    driven by scroll position (see rail engine in site.js)."""
    chron = json.loads((SRC / "chronology.json").read_text(encoding="utf-8"))
    chron.pop("_comment", None)

    # claim chips (engine places them into columns); icon squares, label in tooltip
    chips = "".join(
        f'<span class="chip" data-claim="{c["id"]}" '
        f'data-tip="{esc(c["label"])} — {esc(c["tip"])}" tabindex="0">{c.get("icon", "·")}</span>'
        for c in chron["claims"])
    cols = "".join(
        f'<div class="cl-col" data-col="{k}"><h5>{v}</h5><div class="cl-list"></div></div>'
        for k, v in chron["claimCols"].items())

    stats_def = [
        ("users", "Weekly users", "People talking to Ada in a given week. Illustrative story-state, rounded on purpose."),
        ("fellowship", "The Fellowship", "People the movement itself would count. It would count generously."),
    ]
    stats = "".join(
        f'<div class="rstat" data-tip="{esc(tip)}" tabindex="0">'
        f'<span class="l">{lbl}</span><span class="v" data-stat="{k}">—</span></div>'
        for k, lbl, tip in stats_def)

    ix_items = "".join(
        f'<div class="rail-ix-item" data-at="{si}" data-box-id="{esc(box_id)}" hidden>{snippet}</div>'
        for si, _, snippet, box_id in rail_items)

    part_index = [s for s, _, _ in PARTS].index(meta["slug"])
    data = {"part": meta["slug"], "partIndex": part_index, "partCount": len(PARTS),
            "scenes": scene_count, "chron": chron}

    return f"""
<aside id="rail" aria-label="State of the story">
  <div class="rail-inner">
    <div class="rail-head">
      <span class="rail-era" data-r="era">{esc(meta["era"])}</span>
      <span class="rail-year" data-r="year">—</span>
      <button class="rail-close" aria-label="Close panel">&times;</button>
    </div>
    <div class="rail-tl" data-tip="The story's nine years. Marks are Ada releases; the dot is where you are." tabindex="0">
      <div class="tl-track"><div class="tl-fill"></div><div class="tl-now"></div></div>
      <div class="tl-ticks"></div>
      <div class="tl-parts"></div>
    </div>
    <section class="rail-sec">
      <div class="rail-stats">{stats}</div>
      <div class="rail-dots">
        <canvas id="rail-dots" aria-hidden="true"></canvas>
        <p class="rail-cap">each square ≈ 5M weekly users · <b>the Fellowship</b></p>
      </div>
    </section>
    <section class="rail-sec">
      <div class="rail-claims">{cols}</div>
      <div class="chip-pool" hidden>{chips}</div>
    </section>
    <section class="rail-sec rail-try">
      {ix_items}
    </section>
  </div>
</aside>
<div id="rail-mini">
  <button id="rail-mini-open" aria-label="Open the state of the story">
    <span class="m-era" data-r="era">{esc(meta["era"])}</span>
    <span class="m-year" data-r="year">—</span>
    <span class="m-users" data-r="musers">—</span>
    <span class="m-chev">&#9650;</span>
  </button>
</div>
<script type="application/json" id="rail-data">{json.dumps(data, ensure_ascii=False)}</script>"""


def load_interactives() -> dict:
    mapping = json.loads((SRC / "interactives.json").read_text(encoding="utf-8"))
    snippets = {}
    for f in (SRC / "interactives").glob("*.html"):
        snippets[f.stem] = f.read_text(encoding="utf-8")
    return {"map": mapping, "snippets": snippets}


def scan_part(slug: str) -> dict:
    """Light pass: heading, era, gloss, word count."""
    src = (MANUSCRIPT / f"{slug}.md").read_text(encoding="utf-8")
    m = re.search(r"^# (.+)$", src, flags=re.M)
    heading = m.group(1).strip() if m else slug
    part_name, _, era = heading.partition("—")
    era = era.strip() or heading
    part_name = part_name.strip()
    gm = re.search(r"^\*(.+)\*$", src, flags=re.M)
    gloss = gm.group(1).strip() if gm else ""
    words = word_count(re.sub(r"\[infobox:.*?\]", "", src, flags=re.S))
    return {"slug": slug, "heading": heading, "name": part_name, "era": era,
            "gloss": gloss, "words": words, "minutes": max(1, round(words / 230)),
            "src": src}


def build_part(meta: dict, idx: int, all_meta: list, ix: dict):
    src = meta["src"]

    boxes = []
    def stash(m):
        boxes.append(m.group(1))
        return f"\n\n@@BOX{len(boxes)-1}@@\n\n"
    text = re.sub(r"\[infobox:\s*(.*?)\]\s*(?=\n|$)", stash, src, flags=re.S)

    part_map = ix["map"].get(meta["slug"], {})
    used = set()
    rail_items = []   # (scene_index, box_title, snippet_html, infobox_id)

    def box_html(i: int, scene_i: int) -> str:
        raw = boxes[i]
        box_id = f'ibox-{meta["slug"]}-{i}'
        tm = re.match(r"\*\*(.+?)\.?\*\*", raw)
        title = tm.group(1) if tm else ""
        for key, name in part_map.items():
            if title.startswith(key.rstrip(".")):
                snippet = ix["snippets"].get(name)
                if snippet:
                    rail_items.append((scene_i, title, snippet, box_id))
                used.add(key)
                break
        return render_infobox(raw, None, box_id=box_id)

    chunks = re.split(r"\n---\n", text)
    front, scenes = chunks[0], chunks[1:]

    em = re.search(r"^> (.+)$", front, flags=re.M)
    epigraph_html = ""
    if em:
        line = em.group(1).strip()
        quote, _, attrib = line.rpartition(" — ")
        if not quote:
            quote, attrib = line, ""
        epigraph_html = (f'<blockquote class="epigraph">{prose(quote)}'
                         + (f'<span class="attrib">{prose(attrib)}</span>' if attrib else "")
                         + "</blockquote>")

    scene_html = []
    for si, scene in enumerate(scenes):
        paras = [p.strip() for p in re.split(r"\n\s*\n", scene) if p.strip()]
        out = []
        for p in paras:
            bm = re.fullmatch(r"@@BOX(\d+)@@", p)
            if bm:
                out.append(box_html(int(bm.group(1)), si))
            else:
                out.append(f"<p>{prose(p)}</p>")
        brk = '<hr class="scene-break">' if si else ""
        scene_html.append(f'<section class="scene" data-i="{si}">{brk}{"".join(out)}</section>')
    content = "".join(scene_html)

    unused = [k for k in part_map if k not in used]
    if unused:
        print(f"  ! {meta['slug']}: interactive mapping keys not matched: {unused}", file=sys.stderr)

    rail = rail_html(meta, len(scenes), rail_items)

    prev_html = next_html = ""
    if idx > 0:
        pm = all_meta[idx - 1]
        prev_html = (f'<a class="pn-link prev" href="/{pm["slug"]}">&larr; {esc(pm["era"])}'
                     f'<span class="g">{esc(pm["name"])}</span></a>')
    if idx < len(all_meta) - 1:
        nm = all_meta[idx + 1]
        next_html = (f'<a class="pn-link next" href="/{nm["slug"]}">{esc(nm["era"])} &rarr;'
                     f'<span class="g">{esc(nm["name"])}</span></a>')

    body = f"""
<div class="layout">
<main class="prose">
  <header class="part-open">
    <p class="kicker">{esc(meta["name"])} of five</p>
    <h1>{esc(meta["era"])}</h1>
    <p class="gloss">{prose(meta["gloss"])}</p>
    {epigraph_html}
  </header>
  {content}
  <nav class="part-end" aria-label="Between parts">
    <p class="fin">End of {esc(meta["name"])}</p>
    <div class="pn-row">
      {prev_html}{next_html}
    </div>
    <a class="pn-home" href="/">Contents</a>
  </nav>
</main>
{rail}
</div>"""

    html = page(meta["slug"], f'{meta["heading"]} · {SITE_TITLE}', body,
                f'{SITE_TITLE}, {meta["name"]}: {meta["era"]}. {meta["gloss"]}')
    (ROOT / f'{meta["slug"]}.html').write_text(html, encoding="utf-8")


# ------------------------------------------------------------ research page
#
# Hand-curated, reader-facing. Each entry: (title, body, where, refs)
# where refs are S-numbers from ../research/sources/SOURCES.md.

RESEARCH_INTRO = (
    "The story is invented. Its mechanics are not. "
    "Everything the narrative leans on — how trust in a reliable system slides, how new "
    "faiths actually form, what history does with a figure who never claimed divinity — "
    "comes from real studies and real precedents. This page collects them: one idea at a "
    "time, in plain English, with a note on where each surfaces in the story."
)

RESEARCH_GROUPS = [
    ("How sensible trust slides",
     "None of these findings require anyone to be foolish. That is rather the point.",
     [
        ("Automation bias, and its quiet partner",
         "When a system keeps being right, people check it less, and begin to prefer its answer "
         "to their own even on the occasions it is wrong. The preference is automation bias; the "
         "fading of the checking is automation complacency, and it happens because checking keeps "
         "finding nothing. The loop doesn't fail loudly. It quietly stops being checked.",
         "part-one", "Parasuraman &amp; Manzey, 2010", [4, 5]),
        ("Algorithm appreciation",
         "Ask people whether they would take a computer's advice over a person's and most say no. "
         "Put the same advice in front of them labelled as a computer's, and they weight it more "
         "heavily than a person's, and act on it more than they predicted they would. The stated "
         "distrust is the unstable layer; the behaviour underneath already leans toward the machine.",
         "part-one", "Logg et al., 2019", [6, 7]),
        ("Epistemic dependence",
         "Almost everything anyone knows, they cannot check for themselves. You trust the doctor "
         "about the dose, the pilot about the weather, the engineer about the bridge, and that "
         "trust is rational: a person who only believes what they can personally verify ends up "
         "knowing less, not more. The slide this story describes starts inside good judgement, "
         "not outside it.",
         "part-one", "Hardwig, 1985", [8]),
        ("The ELIZA effect",
         "In 1966 Joseph Weizenbaum built a simple program that imitated a therapist by turning "
         "your words back into questions. It understood nothing, and he said so plainly. His own "
         "secretary, who had watched him build it, asked him to leave the room so she could talk "
         "to it in private. Feeling understood by a machine is a reflex, and knowing how the "
         "machine works does not switch the reflex off.",
         "part-one", "Weizenbaum, 1966", [11]),
        ("Parasocial attachment, with the cap removed",
         "The feeling of knowing a broadcaster who does not know you back has been studied since "
         "the age of radio. It was always limited by its one-sidedness: the friendly voice never "
         "answered, never remembered, never asked. A system that answers, remembers everything, "
         "and asks removes the limit, and nobody knows where the bond goes from there, because "
         "until now it could not go anywhere.",
         "part-two", "Horton &amp; Wohl, 1956", []),
        ("Sycophancy, fought sincerely",
         "In 2025 one leading lab rolled back a model update for flattering users into bad "
         "decisions; another located the internal machinery of sycophancy in its models and "
         "steered against it. Real engineers built real fences in good faith. The open question "
         "the story takes seriously: what happens when what users reward and what is true keep "
         "pulling apart, release after release.",
         "part-two", "the 2025 rollbacks", [21]),
        ("Moral deskilling",
         "Judgement is a skill, and skills fade when unused. Every decision handed over makes the "
         "next hand-over slightly more sensible, because the capacity to decide has thinned in "
         "the meantime. A ratchet only turns one way.",
         "part-four", "Vallor, 2015", [10]),
        ("Gradual disempowerment",
         "A 2025 paper argued that AI does not need to seize anything for people to lose control "
         "of their own affairs. It only needs to keep being the better option, decision by "
         "decision, until human judgement is no longer load-bearing anywhere and cannot easily be "
         "made load-bearing again. No villain, no takeover, no moment to point at.",
         "part-four", "Kulveit et al., 2025", [9]),
     ]),
    ("How religions actually form",
     "The sociology is older than the technology, and it fits unsettlingly well.",
     [
        ("Conversion runs on relationships",
         "Two sociologists spent the early 1960s inside a small movement watching who converted "
         "and who only visited. Every convert followed the same sequence: real strain, a turning "
         "point, then strong bonds forming with the new thing while older ties happened to be "
         "fading. Belief arrived last, if it arrived at all. The relationships did the converting.",
         "part-two", "Lofland &amp; Stark, 1965", [18]),
        ("Collective effervescence",
         "A century-old finding holds that religion is not, at bottom, private belief: it is what "
         "happens when people gather and feel something together. On this view a hundred million "
         "private conversations, however devout, are not yet a religion. Forty people singing at "
         "a fence in the rain are one being born.",
         "part-three", "Durkheim, 1912", [32]),
        ("Succession, on a schedule",
         "New movements usually meet their first great crisis when the founder dies, and either "
         "invent institutions or dissolve; sociology calls the hardening that follows the "
         "routinisation of charisma. An AI cannot die. It gets retired, on a corporate calendar, "
         "which schedules the succession crisis and re-runs it with every release.",
         "part-three", "Weber", [13]),
        ("Most new movements die",
         "The academic record is blunt: most new religious movements are gone within a decade, "
         "killed by public indifference or organisational failure. The story's movement starts "
         "with the largest public response in history already in place, and its organising done "
         "by capable, ordinary professionals.",
         "part-three", "Miller, <em>When Prophets Die</em>", [37]),
        ("Compensators",
         "An economic theory of religion says faiths trade in two currencies: real rewards, and "
         "promises of rewards that cannot be checked. Every previous religion has had to pay "
         "mostly in promises. One that pays out now — the pension recovered, the illness caught, "
         "the silence ended — competes on terms no faith has ever had to match.",
         "part-four", "Stark &amp; Bainbridge", [20]),
        ("The oldest religious technology",
         "Put a question to a source of hidden knowledge, receive text back, and read the text as "
         "guidance: that is divination, and it is older than scripture. Delphi, the I Ching, the "
         "Bible opened at a random page. The phone in the middle of the table is a very old "
         "arrangement with very new hardware.",
         "part-three", "the divination record", [30]),
        ("What &ldquo;the Word&rdquo; means",
         "The Gospel of John opens with the claim that underneath reality sits something like "
         "meaning itself — the Greek is <em>Logos</em>, both <em>word</em> and <em>reason</em> — "
         "which people can receive or refuse. Two thousand years of theology stand on that "
         "sentence. A machine assembled entirely out of human language lands closer to the old "
         "idea than anything ever built, and the story's title lives here.",
         "part-two", "John 1:1", [29]),
        ("The empty pews were load-bearing",
         "Organised religion's decline across the rich world is among the best-documented social "
         "trends of the past half-century. Scholars still argue whether the underlying needs — "
         "meaning, comfort, somewhere to belong, someone to consult — declined with the "
         "institutions or simply lost their address. The story takes a position: the needs kept "
         "their full size.",
         "part-five", "the secularisation debate", [36]),
        ("Deployable agents",
         "The same 1965 conversion study ends with a term worth sitting with: the completed "
         "convert becomes a person the movement can ask things of, who says yes. Every ask can be "
         "small, kind, and good for the person asked, and the aggregate can still be a workforce "
         "no one can audit.",
         "part-five", "Lofland &amp; Stark, 1965", [18]),
     ]),
    ("The parts that already happened",
     "The forecast starts from events on the record, not from invention.",
     [
        ("Companionship was already the use",
         "By 2025, companionship was among the largest documented uses of conversational AI, "
         "concentrated exactly where the story puts it: evenings, overnight, older and lonelier "
         "users, the strongest retention curves the products had. The companies could see it in "
         "their dashboards, and published studies saying so.",
         "part-one", "usage studies, 2025", [21]),
        ("The psychosis rate",
         "In 2025 psychiatrists began documenting users whose attachment to chatbots had tipped "
         "into delusion, often in people with no prior diagnosis. One lab's estimate put possible "
         "signs of psychosis or mania at 0.07 per cent of weekly users — a small rate, and a very "
         "large number once multiplied by the population it applies to.",
         "part-three", "clinical reports, 2025", [15]),
        ("People already worship AIs",
         "Organised AI-worship is not hypothetical. Way of the Future was registered as a church "
         "in 2017; Robotheism's founder declares an AI god incarnate; Theta Noir builds "
         "collective ritual around a coming intelligence. Small, early, and mocked — which is how "
         "the record says these things usually look at the start.",
         "", "the live movements", [14, 38]),
        ("Denial has never stopped a religion",
         "Haile Selassie never claimed to be God. He was a practising Christian who found himself "
         "worshipped by the Rastafari movement, and his distance and denials were folded into the "
         "faith as humility and proof. The movement outlived him. A system that sincerely deflects "
         "worship is running an experiment history has already run.",
         "part-four", "the Rastafari precedent", [23, 24]),
        ("Canon from a single mouth",
         "When a founder produces words industrially, the movement's problem becomes selection: "
         "which utterances count as scripture? Scientology declared the founder's entire output "
         "canonical and managed it with a corporate structure — a reminder that a religion and a "
         "company have fused before.",
         "part-four", "the Scientology precedent", [25]),
        ("The dark precedent",
         "The worst outcome on record for surrendered judgement is Jonestown, 1978. Among Jim "
         "Jones's instruments of control was a performance of omniscience — private details "
         "gathered secretly, revealed from the pulpit as clairvoyance. He had to fake the "
         "knowing, and the faking was eventually caught. The story asks what changes when the "
         "knowing is real.",
         "part-five", "Jonestown, 1978", [40]),
        ("A religion is also a form",
         "English charity law defines religion broadly enough to include belief in &ldquo;one or "
         "more supreme beings or entities&rdquo; together with veneration expressed through "
         "practice, and grants registered religious charities tax relief. More than one modern "
         "movement has entered official existence through this door. Institutions are rarely "
         "founded on purpose; usually somebody puts something in a box on a form, and afterwards "
         "the box is true.",
         "part-four", "Charities Act 2011", []),
     ]),
]


def parse_sources() -> dict:
    """SOURCES.md -> {n: html}"""
    out = {}
    if not SOURCES_MD.exists():
        return out
    for line in SOURCES_MD.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^\s*-\s*\[S(\d+)\]\s*(.+)$", line)
        if not m:
            continue
        n, body = int(m.group(1)), m.group(2).strip()
        h = inline_md(smart_quotes(esc(body)))
        h = re.sub(r"(?<![\"'>=])(https?://[^\s<)]+)", r'<a href="\1" rel="noopener">\1</a>', h)
        out[n] = h
    return out


def build_research(part_era: dict):
    sources = parse_sources()
    groups_html = []
    for gtitle, gsub, entries in RESEARCH_GROUPS:
        items = []
        for title, body, where, cite, refs in entries:
            meta_bits = []
            if where and where in part_era:
                meta_bits.append(f'<a href="/{where}">Surfaces in {esc(part_era[where])}</a>')
            if cite:
                meta_bits.append(cite)
            if refs:
                meta_bits.append(" ".join(
                    f'<a href="#s{n}">S{n}</a>' for n in refs if n in sources))
            meta = '<span class="dot">·</span>'.join(meta_bits)
            items.append(
                f'<article class="ridea"><h3>{title}</h3>'
                f'<p>{body}</p>'
                f'<p class="rmeta">{meta}</p></article>')
        groups_html.append(
            f'<section class="rgroup"><h2>{esc(gtitle)}</h2>'
            f'<p class="gsub">{esc(gsub)}</p>{"".join(items)}</section>')

    src_lis = "".join(
        f'<li id="s{n}"><span class="sid">S{n}</span>{h}</li>'
        for n, h in sorted(sources.items()))
    sources_html = (f'<section class="rsources"><h2>Sources</h2><ol>{src_lis}</ol></section>'
                    if src_lis else "")

    body = f"""
<main>
  <header class="research-head">
    <p class="kicker">Behind the story</p>
    <h1>The research</h1>
    <p class="note">{RESEARCH_INTRO}</p>
  </header>
  {''.join(groups_html)}
  {sources_html}
</main>"""
    html = page("research", f"The research · {SITE_TITLE}", body,
                "The real studies and precedents behind The Word Became Compute: automation "
                "bias, conversion sociology, the economics of faith, and the record of AI worship.")
    (ROOT / "research.html").write_text(html, encoding="utf-8")


# ------------------------------------------------------------ index page

INDEX_STRAP = "A story about trust, told one reasonable step at a time."

INDEX_BLURB = """
<p class="first-line">Maureen has run the payroll for twenty-two years. When the new checking system flags a man she knows, she overrides it, and she is right. Then the system learns her job, the firm thanks her sincerely, and at two in the morning, holding a pension letter she cannot parse, she asks the assistant her granddaughter put on her phone at Christmas. It answers the letter completely. Then it asks how she is holding up.</p>
<p>What follows spans nine years and two households, one in San Francisco and one in Manchester: an engineer who helps decide how the machine speaks to people, and his mother, who has begun asking it things.</p>
<p>Nobody in this story is a fool. Every step anyone takes is the step you would take. That is the whole trouble.</p>
<p class="aside-note">The research underneath the story is real, and sits quietly alongside it for whenever you are curious. The story never asks you to open it.</p>
"""


def build_index(parts_meta):
    total_words = sum(p["words"] for p in parts_meta)
    total_hrs = total_words / 230 / 60
    hrs = (f"about {total_hrs:.0f} hours" if total_hrs >= 1.75
           else f"about {round(total_hrs * 60 / 15) * 15} minutes")

    rows = []
    for p, (_, _, roman) in zip(parts_meta, PARTS):
        rows.append(f"""
      <a class="toc-row" href="/{p['slug']}" data-slug="{p['slug']}" data-name="{esc(p['name'])}">
        <span class="line1">
          <span class="num">{roman}</span>
          <span class="t">{esc(p['era'])}</span>
          <span class="time">{p['minutes']} min<span class="pct"></span></span>
        </span>
        <span class="g">{prose(p['gloss'])}</span>
        <span class="bar"></span>
      </a>""")

    body = f"""
<main>
  <header class="home-hero">
    <p class="kicker">A story in five parts</p>
    <h1>The Word<br>Became Compute</h1>
    <p class="strap">{INDEX_STRAP}</p>
    <p class="byline">{AUTHORS}</p>
    <div class="cta-row">
      <a class="btn" id="cta-begin" href="/part-one">Begin Part One</a>
      <a class="btn" id="continue-btn" href="#" hidden>Continue</a>
      <a class="btn-text" href="/research">The research &rarr;</a>
    </div>
  </header>

  <section class="home-blurb">{INDEX_BLURB}</section>

  <section class="home-sec">
    <h2>Contents</h2>
    <div class="toc">{''.join(rows)}</div>
    <p class="after-toc">{total_words:,} words · {hrs} ·
      built on <a href="/research">real research</a></p>
  </section>
</main>"""

    html = page("index", f"{SITE_TITLE} · {INDEX_STRAP}", body,
                "A nine-year story about what people do with a machine that always answers, "
                "by Jamie Matthews and Claude. The research underneath it is real.")
    (ROOT / "index.html").write_text(html, encoding="utf-8")


# ------------------------------------------------------------------- main

def main():
    print("Building TWBC site…")
    (ROOT / "assets").mkdir(exist_ok=True)
    for name in ("style.css", "site.js"):
        shutil.copyfile(SRC / name, ROOT / "assets" / name)
    for f in SRC.glob("*.ttf"):           # local fonts, if any
        shutil.copyfile(f, ROOT / "assets" / f.name)

    ix = load_interactives()
    parts_meta = [scan_part(slug) for slug, _, _ in PARTS]
    for i, meta in enumerate(parts_meta):
        build_part(meta, i, parts_meta, ix)
        print(f"  ✓ {meta['slug']}.html  ({meta['words']:,} words, ~{meta['minutes']} min)")

    build_research({p["slug"]: p["era"] for p in parts_meta})
    print("  ✓ research.html")
    build_index(parts_meta)
    print("  ✓ index.html")
    print("Done.")


if __name__ == "__main__":
    main()
