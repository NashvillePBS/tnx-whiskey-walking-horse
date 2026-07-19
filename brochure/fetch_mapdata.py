#!/usr/bin/env python3
"""Fetch road/water geometry for the brochure map from Overpass, using the
city's map bounds from data/guide.json (print.map.bounds). Caches to
cache/mapdata.json — run once per city; never re-runs automatically."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "cache", "mapdata.json")

if os.path.exists(OUT) and "--force" not in sys.argv:
    sys.exit(f"{OUT} already exists — pass --force to re-fetch")

b = json.load(open(os.path.join(REPO, "data", "guide.json")))["print"]["map"]["bounds"]
M = 0.02  # margin so geometry bleeds past the canvas
# same projection math as build_brochure.py: canvas aspect fixes the lat span
import math
ASPECT = (24.0 + 0.25) / (18.0 + 0.25)
lat_span = (b["east"] - b["west"]) * math.cos(math.radians(b["centerLat"])) / ASPECT
south = b["centerLat"] - lat_span/2 - M
north = b["centerLat"] + lat_span/2 + M
west, east = b["west"] - M, b["east"] + M
bbox = f"({south},{west},{north},{east})"

query = f"""[out:json][timeout:120];
(
  way["highway"~"^(motorway|trunk|primary|secondary)$"]{bbox};
  way["waterway"="river"]{bbox};
  way["natural"="water"]{bbox};
);
out geom;"""

print("querying Overpass for", bbox)
r = subprocess.run(
    ["curl", "-s", "-A", "NashvillePBS-CrossroadsGuide/1.0 (sburkeen@wnpt.org)",
     "--data-urlencode", f"data={query}", "https://overpass-api.de/api/interpreter",
     "-o", OUT], check=True)
n = len(json.load(open(OUT))["elements"])
print(f"cached {n} ways -> {OUT}")
