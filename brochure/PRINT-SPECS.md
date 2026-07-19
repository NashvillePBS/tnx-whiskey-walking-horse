# Print specs — Crossroads Guide brochure (Memphis)

For the local printer. Files in `brochure/out/` (regenerate with
`python3 brochure/build_brochure.py`).

## Files

| File | What |
|---|---|
| `front.tif` | Map side — CMYK TIFF, 300 dpi |
| `back.tif` | Panel side (cover, welcome, listings) — CMYK TIFF, 300 dpi |
| `front-proof.png`, `back-proof.png` | RGB proofs at 25% with trim (magenta box) and fold guides (dashes) — **not for production** |

## Dimensions

- **Trim size:** 24 × 18 in flat
- **Bleed:** 0.125 in on all sides (files are 24.25 × 18.25 in / 7275 × 5475 px)
- **No printer's marks in the files** — trim/fold per this spec
- **Fold:** map fold — vertical accordion at 4-in intervals (5 vertical folds),
  then one horizontal half fold → finished piece 4 × 9 in.
  The **cover panel** is the bottom-right panel of the back side; the panel
  grid on the back is 6 columns × 2 rows of 4 × 9 in.

## Color

- CMYK, no ICC profile embedded — printer should treat as US commercial
  defaults (SWOP/GRACoL) and proof against the supplied PNGs for intent
- Brand colors to hold: show blue ≈ C82 M69 Y0 K46 (#314289),
  show red ≈ C0 M71 Y68 K32 (#AE3238)
- Logos are embedded raster at 300 dpi. Vector originals available on request:
  Tennessee Crossroads logo + Nashville PBS horizontal white (on PBS-Blue
  #2638C4 chip) — supplied as SVG/AI by Nashville PBS if the printer prefers
  to re-place them.

## Stock suggestion

Classic road-map feel: 60–80 lb text, uncoated or matte, tolerant of
repeated folding. Final stock choice is the printer's call with Shane.

## Content notes

- Map data © OpenStreetMap contributors — attribution is printed on the map
  side and must remain.
- No funder credits appear anywhere on this piece (intentional).
- Host names ARE included on this piece (intentional; the web/home-print
  itinerary differs).

## Proofing & edits workflow

1. **Text or stop changes** (names, blurbs, phones, adding/removing stops):
   edit `data/guide.json` and re-run `python3 brochure/build_brochure.py` —
   fresh TIFFs in seconds, and the web guide + home itinerary update from the
   same file, so nothing drifts.
2. **Visual/layout tweaks or designer markup**: run
   `python3 brochure/export_svg.py` → `brochure/out/front.svg`, a layered,
   live-text vector of the map side that opens natively in Illustrator
   (named groups: water, road classes, shields, pins, labels, cartouche,
   inset, legend, attribution). Install the fonts from `brochure/fonts/`
   first or AI will substitute. SVG is RGB — if edits are finaled in AI,
   export the print file from AI; otherwise the CMYK TIFFs stay canonical.
3. The back (listings) side is intentionally not exported as SVG: it is pure
   text driven by `data/guide.json`, and editing it there keeps every format
   in sync.
