# Content Contract — Crossroads City Guides

What data drives each part of a guide, and where it comes from in the
**Tennessee Crossroads** Airtable base (`appcJ7QV9wH0ANbKd`, table `Segments`
`tblmopPUXOgtKvygF`). Every city/route guide — web, newsletter, map, brochure —
is built from this same contract. Only the values change between cities.

## Page-level (`GUIDE` object in index.html)

| Key | Drives | Source |
|---|---|---|
| `show` | wordmark in top bar | constant: "Tennessee Crossroads" |
| `eyebrow` | hero eyebrow | constant: "A Tennessee Crossroads Guide · Celebrating 40 Years" |
| `titleHTML` | hero headline (`<em>` = city name, rendered teal) | editorial, per guide |
| `sub` | hero lede | editorial, per guide |
| `metaNote` | text after computed stop count | constant unless a guide needs nuance |
| `mapLede` | one-liner beside "The Map" ribbon | editorial, per guide |
| `quote` | footer quote | constant (show sign-off) |
| `note` | viewer thank-you (web footer + print footer) | constant, evergreen — no dated/anniversary language |
| `colophonHTML` | footer colophon (carries the Nashville PBS attribution) | constant |

**No funder credits in any guide format** (Shane, 2026-07-18): funding language
changes over time and is deliberately kept out of this build. If that decision
is revisited, route the wording through Development first.

`<title>` and `<meta name="description">`/OG tags in `<head>` restate the title + lede.

Stop count and filter chips are **computed** from `SECTIONS` — never hand-edited.

## Section-level (`SECTIONS[]`)

| Key | Drives | Source |
|---|---|---|
| `key` | filter identity | editorial grouping |
| `title` | section ribbon + chip label + card category tag | editorial rollup of Airtable `Categories TNX` |
| `intro` | section lede | editorial, per guide |

Section markers ("01"), stop numbers (01–NN across all sections, shown on card
tags and map pins), chip labels, and stop counts are all **computed** at render
— never hand-edited.

Guide sections are editorial groupings; the Airtable `Categories TNX`
multi-select (Restaurants and Food, Destinations, Artists and Artisans,
Profiles, Bed and Breakfast, Events…) is the raw material they roll up from.

## Stop-level (`SECTIONS[].stops[]`)

| Key | Drives | Airtable field |
|---|---|---|
| `name` | card heading, `alt` text, no-image fallback | `Title` (fld3ub1ZfhfvuqHi1) — prefer `Business or Location` (fldGqCwLF8kQjfn1d) when the segment title isn't the place name (see `Segment Title Not Business` checkbox) |
| `host` | "as seen with …" credit; empty → "from the Crossroads archive" | `Talent` (fldOCtAfowQsKyUAu) |
| `blurb` | card body | edited from `Web Description` (fld2wUQ1AjCXbfXqd) — tighten to ~40 words, guide voice |
| `addr` | meta row | `Address` (fldhdXKru1EXTsNBW) |
| `site` / `siteUrl` | meta row outlink | `Website` (fldRwywww3GgG9Dfq) |
| `link` | photo + "Watch the segment" | `Wordpress Permalink` (fldCk1f79rMb1HFpN) — **a stop without a live permalink is excluded** |
| `img` | card photo (hotlinked, `onerror` → navy fallback) | `wordpress_img_url` (fldwMPHAEz0GHtiqv) or `Thumbnail` attachment |
| `free` | red Free badge | editorial flag (no reliable Airtable source) |
| `phone` | meta row (web: tap-to-call `tel:` link; print + brochure: text) so travelers can confirm a place is open | `Phone` (fld9ER9VXGG9QYNFz), normalized to `(XXX) XXX-XXXX`. **Only for stops with a business street address** — never publish artist-profile/personal numbers, and skip numbers for businesses that no longer operate (e.g. Inn at Hunt Phelan). |
| `lat` / `lng` | map pin position (Leaflet) | `Latitude` / `Longitude` (see below). **Omit entirely when the record has no public street address** (studio visits, P.O. boxes) — the stop keeps its card but gets no pin, and the map note reports the unpinned count automatically. Never plot ZIP/neighborhood centroids. |

## Print itinerary

The in-page printable checklist (`#print-doc`) derives entirely from `GUIDE` +
`SECTIONS`: title (tags stripped), stop count, per-stop `no · name` and
`addr · site · Free` (**no host names in print** — Shane, 2026-07-18), then the
viewer `note` and colophon. No extra fields; if a stop is on the page it is on
the itinerary. This is the home-printer format — separate from the
professionally printed brochure (phase 2).

## Brochure-only keys (`print` object in data/guide.json)

| Key | Drives | Source |
|---|---|---|
| `print.coverImage` | feature photo on the brochure cover panel | repo-relative path; pick a graphic, uncluttered segment image ≥1500px wide (≈600dpi at cover size) |
| `print.coverCaption` | italic caption under the cover photo | editorial |

Constant brochure assets (shared layer, not per-city): crew photo on the
Welcome panel (`brochure/cache/crew.jpg`) and the PBS App panel — QR to
wnpt.tv/tnx-app + "Don't miss an episode while you're on the road — stream
Tennessee Crossroads free on the PBS App." (replaced the show-quote panel,
Shane 2026-07-18).

## Map + print formats (same contract, more fields)

| Purpose | Airtable field |
|---|---|
| Map pin position | `Latitude` (fldqCUylKRqidf2ge), `Longitude` (fldqG6BMbukVl2h9Z) |
| Geocoding missing pins | geocode the street `Address` + ZIP (Nominatim; or resolve `Google Place ID` fldB3aGpYFreYciR5 / `Google Maps URL` fldYzimFVVZEkWnXn when populated) — results are **written back** to Latitude/Longitude so geocoding never re-runs. Records without a street address are never geocoded. |
| City filter | **`City List` (fldYBYOVDAXJUvsYb) single-select — the authoritative city tag (per Shane).** The older `City` field (fld3egOqHdgiL4G4A) is incomplete; don't use it. |

## Data hygiene notes (found while building Memphis)

- Use `City List`, not `City` (incomplete). But `City List` has stray tags too:
  "Bucket Man" (an Ocoee story) and "Holly Tree Manor" (Trenton, ZIP 38382) are
  tagged Memphis. Sanity-check addresses/ZIPs against the city.
- Duplicate records exist (two "National Civil Rights Museum" entries, a
  "Rendezvous Ribs FLASHBACK" beside the main Rendezvous record; "Memphis Zoo
  Pandas" beside "Memphis Zoo"). Dedupe by place, keep the record with a permalink.
- 2026-07-18: geocoded 14 Memphis records missing Latitude/Longitude (from street
  addresses via Nominatim, or copied between duplicate-place records) and wrote
  them back. Every Memphis record with a street address now has coordinates.

## Selection rules

- Include **every** segment with a live tennesseecrossroads.org permalink for the
  city — the guide runs all eligible stops, deduped by place (Memphis: 47 records
  → 30 stops; 16 lacked a live page, 1 was a duplicate).
- Skip records flagged `Do not publish to TNX` or `Closed`, unless framed historically
  (e.g. The Inn at Hunt Phelan's blurb is written in the past tense — it no longer
  takes overnight guests).
- The `Digital` checkbox is **not** a build-state signal (~1% populated). Build state lives in the project memory file, not Airtable.
