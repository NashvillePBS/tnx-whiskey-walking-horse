# Crossroads Guide Design Tokens — v2 (show-led)

The reusable design layer for every Crossroads city/route guide. Memphis is the
reference build; other guides clone this system and change **content only**
(see [CONTENT-CONTRACT.md](CONTENT-CONTRACT.md)). Tokens live in the `:root`
block at the top of `index.html` and must be copied verbatim into each guide.

Two palette tiers:
- **Show palette (Tennessee Crossroads)** leads every guide page — matched to
  tennesseecrossroads.org (verified against the live site's computed styles).
- **Nashville PBS brand palette** carries attribution and is available to
  derivative formats (newsletter, brochure) that lead with station branding.

## Show palette

| Token | Hex | Use |
|---|---|---|
| `--tnx-blue` | `#314289` | headings, links, active chips, footer band (9.2:1 on white) |
| `--tnx-blue-deep` | `#26346E` | hover states, gradients |
| `--tnx-red` | `#AE3238` | ribbons, map pins, Free badge, accents — text-safe both ways (6.3:1 on white; white-on-red 6.3:1) |
| `--tnx-red-deep` | `#8E272C` | hover on red |

## Nashville PBS palette (attribution + derivative formats)

`--npbs-blue #2638C4 · --npbs-navy #0A145A · --npbs-teal #48D3CD ·
--npbs-coral #FE704E · --npbs-yellow #FFCF00`
Contrast rules when these lead a format: teal/yellow only on navy; coral is
decorative only on white; yellow badge always carries navy text.

## Color roles

| Token | Value | Role |
|---|---|---|
| `--c-bg` / `--c-bg-tint` | white / `#F3F4F9` | page / placeholders |
| `--c-ink` | `#20263F` | body text (14.9:1) |
| `--c-ink-soft` | `#3C4566` | secondary text (9.0:1) |
| `--c-muted` | `#5A6284` | meta text (5.6:1) |
| `--c-line` | `#E0E3EF` | hairlines |
| `--c-head` / `--c-action` / `--c-accent` | show blue / show blue / show red | headings, links, accents |
| `--c-band` + `-ink/-soft/-faint` | show blue / white / `#CBD3F0` / `#A4B0E0` | footer band text tiers (7.0:1 / 4.6:1) |

## Type

- `--f-sans`: **Open Sans** — everything, incl. 800-weight tight-tracked headlines
  (the show's heading style). Hero title: 800, `-.03em`, city name in red italic.
- `--f-label`: **Rubik Mono One** — the show's label face. Ribbons, wordmark,
  category tags, watch links, map pins, hero meta. Always uppercase; italic
  inside ribbons (synthetic oblique, matching the site).
- Scale: `--fs-hero` clamp(2.5→5.4rem) · `--fs-h3` 1.3rem · `--fs-lede`
  clamp(1.02→1.25rem) · `--fs-body` .96rem · `--fs-label` 11.5px (10px ≤640px).

## Signature elements

- **Ribbon** (`.ribbon`): show-red parallelogram, `skewX(-12deg)`, white italic
  Rubik Mono One, counter-skewed text. Used for the hero eyebrow, section heads
  ("01 / Eat & Drink"), the map label, and card category tags.
- **Route line**: dashed show-blue line, red origin dot, blue arrow (white on the
  footer band). Faint dashed "back roads" SVG behind the hero at 7% opacity.
- **Map pins**: 27px show-red rounded square, same skew, white Rubik Mono stop
  number, white ring + shadow. Popup: number · category, name, watch link.

## Space, shape, elevation

Spacing `--sp-1…8`: 4/8/14/20/28/44/64/96px. Radii: `--r-media` 12px,
`--r-pill` 40px. `--skew:-12deg`. `--shadow-card`. Container 1180px,
`--pad-x` 28px (20px ≤640px).

## Layout invariants

- **One sticky element only**: the category filter (`z-index` above Leaflet panes).
- Light editorial page; the only dark band is the show-blue footer.
- Map section sits between the filter and the first stop section; height
  `min(62vh,520px)` (52vh ≤640px). Chips filter cards **and** map pins together;
  the map re-fits bounds to visible pins.
- Card grid `auto-fill minmax(330px,1fr)`; single column ≤640px; touch targets ≥44px.
- Reduced motion: reveal/zoom transitions disabled.

## Print itinerary (home-printer format)

Every guide page carries a hidden `#print-doc` that is the only thing that
prints (`@media print` hides everything else). "Print the itinerary" button in
the hero triggers `window.print()`. Rules that make it home-printer safe:

- **No background dependence**: browsers skip backgrounds by default, so the
  layout uses only text color, borders, and SVG fills. The white Nashville PBS
  logo sits on a PBS-Blue rounded rect drawn *inside* its SVG so it always prints.
- Official logo SVGs inlined with classes converted to fill attributes (their
  internal `<style>` would otherwise leak into the page). Tennessee Crossroads
  logo header-left (its own colors #25408f/#d2232a); Nashville PBS chip in the footer.
- No photos, no map. Two-column checklist: checkbox, `NN · Name`,
  address · website · host · Free. Stop numbers match the online map pins.
  Letter size, ~1 page at 30 stops; sections break cleanly (`break-inside:avoid`).
- Content renders from the same `GUIDE` + `SECTIONS` data — nothing hand-edited.

## Dependencies (fixed)

Two Google Fonts requests (Open Sans, Rubik Mono One) + **Leaflet 1.9.4** from
unpkg with SRI hashes + OpenStreetMap standard tiles with attribution. Nothing else.

## Non-negotiables for clones

1. No new colors, fonts, shadows, or libraries — fix the token layer instead.
2. `aria-pressed` chips, alt text from stop names, focus-visible rings stay.
3. Anything you must special-case per city is a leak — report it and patch the
   shared layer.
