# Build state — Whiskey & Walking-Horse Country (route guide)

**Status: built, all four formats, committed locally. This is the OPTIONAL guide in the
40th-anniversary series plan** — built fully, flagged optional for prioritization.

Route guide (three towns, driving order): **Lynchburg → Tullahoma → Shelbyville**.
Slug `tnx-whiskey-walking-horse` · built 2026-07-19 from the locked Memphis design system
(content-only clone; verified no drift vs tnx-chattanooga).

## Records → eligible, per town

| Town | Airtable records | Eligible stops | Excluded (reason) |
|---|---|---|---|
| Lynchburg (selyq098mCXF38YlQ) | 8 | 5 | Lynchburg Valley Inn, Velma's Candy Store — no permalink |
| Tullahoma (selT2IUiuZ4F0aRnW) | 9 | 3 | Sundrop Shoppe, Celtic Cup, Water's Edge Chocolates, Legacy Creamery, Shoppes at Cokers — no permalink; Beechcraft Air Museum (rec1Sxq1tJQuwXHyB) — duplicate of Beechcraft Heritage Museum, kept recIAosb1dPbtFxeb (business-named title, Talent populated; both permalinks live) |
| Shelbyville (selOwsM0Bw8VU8JHf) | 7 | 4 | Pope's Cafe, Nearest Green Distillery — no permalink; Lane Street Inn — `Business or Location` field says "Closed" (excluded as no-longer-operating; had a live permalink) |
| **Total** | **24** | **12** | |

All 12 permalinks and all 12 stop images verified 200 on tennesseecrossroads.org.
No stray city tags found — every record's ZIP matches its town (37352/37388/37160).
George Dickel is physically in Cascade Hollow near Normandy but is tagged (and marketed)
Tullahoma, ZIP 37388 — kept in the Tullahoma section, blurb says "north of town."

## Sections (driving order) and counts

1. `lynchburg` — Lynchburg — 5 stops (Jack Daniel's, Miss Mary Bobo's, Barrel House BBQ, Lynchburg Cake and Candy, Promise Manor)
2. `tullahoma` — Tullahoma — 3 stops (Beechcraft Heritage Museum, George Dickel, Emil's Bistro & Marketplace)
3. `shelbyville` — Shelbyville — 4 stops (Musgrave Pencils, Clearview Horse Farm, Flat Creek Community Center, Garland King Museum)

## Pins / geocoding

- **11 pinned, 1 unpinned** (Garland King Museum — no street address in Airtable → card only, per contract).
- Geocoded 1 record via Nominatim structured query and **wrote back** to Airtable
  (fldqCUylKRqidf2ge / fldqG6BMbukVl2h9Z): Flat Creek Community Center
  (rec6hfP8a4uVP8cFM) → 35.3890983, -86.4101841 (115 New Herman Road, Bedford Co. 37160 —
  sanity-checked ~7 mi south of Shelbyville, matching the segment description).
  Free-form Nominatim queries returned nothing; the structured street/state/postalcode
  query resolved it.
- All other included stops already had Airtable coordinates; all sanity-checked near their towns.

## Phones (10 published)

(931) 759-6357 JD · (931) 759-6154 Bobo's · (931) 759-5760 Barrel House ·
(877) 759-7441 Lynchburg Cake (toll-free — oddity, as stored) · (931) 247-4457 Promise Manor ·
(931) 455-1974 Beechcraft · (931) 857-3124 Dickel (Airtable had "x230"; extension dropped) ·
(931) 684-3611 Musgrave · (931) 684-8822 Clearview · (931) 695-5332 Flat Creek.
Omitted: Emil's (flagged uncertain, below) and Garland King (no street address).

## Flags for editorial review

- **Emil's Bistro & Marketplace (Tullahoma)** — could not verify it still operates (website
  domain is "emilsbistroandlounge.com", name drift). Included with a story-led blurb and
  **no phone**; please confirm before print.
- **Garland King Museum (Shelbyville)** — no address/website in Airtable; likely
  visit-by-arrangement. Included card-only (no pin/phone); blurb kept non-specific. Confirm.
- **Clearview Horse Farm** — old segment; no closure signal, kept with phone. Worth a call.
- **Lynchburg Cake and Candy** phone is toll-free (877) — kept as stored.
- Walking Horse National Celebration has **no record** in the filtered pull, so the route's
  namesake event isn't a stop; the walking-horse identity is carried by section intro +
  Clearview. (No seasonal stops in this guide as a result.)
- Front map shows a white "BUSINESS" route shield near Shelbyville (OSM ref on US-231
  Business) — system-rendered from map data, left as-is.

## Cover

`brochure/cache/cover-whiskey-walking-horse.jpg` — the George Dickel segment photo
(1920×1080): hand-painted "George A. Dickel & Co. — Established 1870 — Visitor Parking and
Distillery Tour" sign with willow tree, distillery, and Tennessee flag. Chosen over the JD
1988 archive frame (VHS-grainy), Clearview (cluttered stall close-up, horse in fly mask),
and Barrel House (near-black smoker interior). Caption: "Cascade Hollow, home of George
Dickel — Tullahoma".

## printTitle fit

Spec'd split ("Whiskey & Walking-Horse" / "Country · A Road Trip") **overflowed** — line 1
measures 4.45in at the locked 24pt vs ~3.83in cartouche text area and ~3.4in cover panel.
Used **"Whiskey & Walking-" / "Horse Country"** (3.45in / 2.48in — fits both proofs,
verified by eye). "A Road Trip" is carried by the web titleHTML and the eyebrow ribbon,
not the print title lines.

## Print map config

bounds west -86.642 / east -86.12 / centerLat 35.384 (lat span 0.3203 → 35.224–35.544);
every pin x ≥ 7.62in (> 7.2in requirement, boxes end at 7.1in). Lynchburg **inset**
(all 5 square-area pins; box [0.6, 4.1, 6.5, 7.96]); legend [0.6, 12.46, 6.5, 2.9];
attrib [0.6, 15.66, 6.5, 1.2] (ends 16.86 ≤ 17.4); cartouche [0.6, 0.6, 6.5, 3.1].
areaLabels: SHELBYVILLE (big), LYNCHBURG, TULLAHOMA + NORMANDY, WARTRACE (Bell Buckle is
north of the frame — omitted). Duck River: riverWide ["Duck"], riverWideIn 0.2, waterLabel
placed mid-river — all verified on proof. Overpass cached 473 ways (first attempt, no retries).

## Diff verdict vs tnx-chattanooga

8 system files (CONTENT-CONTRACT.md, DESIGN-TOKENS.md, .gitignore, .nojekyll,
brochure/build_brochure.py, brochure/export_svg.py, brochure/fetch_mapdata.py,
brochure/PRINT-SPECS.md) — **byte-identical**. index.html — identical **except exactly the
4 <head> lines** (title, description, og:title, og:description). **No leaks; no system
edits needed.**

## Formats verified

web (http://localhost:8760 curl checks: index 200, guide.json 200/parses, 12 stops) ·
home-print itinerary (derives from same data) · brochure front.tif/back.tif (CMYK 300dpi)
· front.svg — proofs reviewed by eye.
