# TWBC — the website

Static site for *The Word Became Compute*. No dependencies, no framework.

## Regenerating

Edit the manuscript markdown as usual, then:

```
cd twbc
python3 build.py
```

It reads:

- `../manuscript/part-*.md` → `part-*.html` (one page per part)
- `../research/sources/SOURCES.md` → the sources list on `research.html`
- `src/style.css`, `src/site.js` → copied to `assets/`
- `src/interactives/*.html` → inlined into the mapped infoboxes
- `src/interactives.json` → which infobox gets which interactive

Preview: `python3 -m http.server` from inside `twbc/`, or just open `index.html`.

## What the parser understands (manuscript files)

- `# Part One — The Tool` — part heading (name + era)
- `*gloss line*` — the italic subtitle
- `> "quote" — attribution` — the part epigraph
- `---` on its own line — scene break
- `[infobox: **Title.** body …]` — research aside (can span paragraphs)
- `**bold**`, `*italic*` inline; straight quotes become curly automatically

## Where things live

- **Infobox ↔ interactive mapping:** `src/interactives.json`. Keys are the start
  of the box's bold title as written in the markdown; values are filenames in
  `src/interactives/` (without `.html`). Interactives no longer render inside
  the boxes — they appear in the chronicle rail's "Try the mechanism" slot,
  anchored to the scene containing their box.
- **The chronicle rail:** the live state-of-the-story panel on part pages.
  All of its data (timeline ticks, stats, cast states, the drift chips, the
  question-shares chart) lives in `src/chronology.json`, keyed by part with
  keyframes at fractions through each part's scenes. Values carry forward
  until changed. On screens under 1200px it becomes a bottom strip that
  expands to a full overlay.
- **Landing-page copy:** the `INDEX_*` constants in `build.py`.
- **Research page:** hand-curated, reader-facing entries in `RESEARCH_GROUPS`
  in `build.py` (the raw notes in `../research/notes/` are deliberately not
  published). Sources are parsed from `SOURCES.md`.
- **Design:** `src/style.css`. Themes are the three `html[data-theme]` blocks.
- **Fonts:** the list lives in two places that must match — `FONTS` in
  `src/site.js` and `font_options()` in `build.py`.
- Never edit the generated `.html` files or `assets/` directly.

## Reader-facing behaviour

- Infoboxes render as closed one-line asides (`<details>`); a click opens the
  note and, where mapped, its interactive model. They print open, and work
  without JavaScript.
- Typeface, text size, and theme (standard / dark / paper) persist in
  localStorage via the Aa control.
- Reading position is saved per part. The index swaps "Begin Part One" for
  "Continue …" + "Start over" once there's progress; "Start over" clears
  saved positions.
