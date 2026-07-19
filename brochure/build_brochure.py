#!/usr/bin/env python3
"""Crossroads Guide print brochure builder — Nashville PBS.

Renders a 24x18in map-folded brochure (folds to 4x9in) from the same
data/guide.json that drives the web guide. Two sides:

  front  - stylized road map of the city with numbered stops (+ downtown inset)
  back   - 12 panels (6 cols x 2 rows of 4x9in): cover, welcome, stop listings

Output (brochure/out/):
  front.tif / back.tif   - 300dpi CMYK LZW TIFF, 0.125in bleed, no marks
  front-proof.png        - RGB proof at 25% with trim + fold guides
  back-proof.png

Content rules (per Shane): host names INCLUDED here (unlike the home-printer
itinerary), NO funder credits, evergreen viewer note included.
Map data (c) OpenStreetMap contributors - attribution printed on the map side.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)

# ---------------------------------------------------------------- geometry --
DPI = 300
TRIM_W, TRIM_H = 24.0, 18.0          # inches
BLEED = 0.125
CW, CH = int((TRIM_W + 2*BLEED)*DPI), int((TRIM_H + 2*BLEED)*DPI)
BX = int(BLEED*DPI)                  # bleed offset in px
PANEL_W, PANEL_H = int(4.0*DPI), int(9.0*DPI)

def IN(v): return int(v*DPI)

# ------------------------------------------------------------------ palette --
# Brand tint base (matches the web guide's --c-bg-tint #F3F4F9 family) —
# replaced the earlier vintage cream per Shane.
CREAM     = (242, 244, 249)
WATER     = (176, 206, 226)
SECONDARY = (213, 217, 231)
PRIM_FILL, PRIM_CASE = (244, 198, 78), (185, 138, 44)
TRUNK_FILL, TRUNK_CASE = (232, 163, 61), (166, 107, 31)
MOT_FILL, MOT_CASE = (174, 50, 56), (126, 34, 38)
TNX_BLUE  = (49, 66, 137)
TNX_BLUE_DEEP = (38, 52, 110)
TNX_RED   = (174, 50, 56)
INK       = (32, 38, 63)
INK_SOFT  = (60, 69, 102)
MUTED     = (90, 98, 132)
AREA_LBL  = (107, 120, 152)
WHITE     = (255, 255, 255)
LINE      = (224, 227, 239)

# ------------------------------------------------------------------- fonts --
F = os.path.join(ROOT, "fonts")
def font(name, pt):  # pt at 300dpi -> px = pt/72*300
    return ImageFont.truetype(os.path.join(F, name), int(round(pt/72*DPI)))
RB   = lambda pt: font("RubikMonoOne-Regular.ttf", pt)
OSR  = lambda pt: font("OpenSans-Regular.ttf", pt)
OSI  = lambda pt: font("OpenSans-Italic.ttf", pt)
OSSB = lambda pt: font("OpenSans-SemiBold.ttf", pt)
OSB  = lambda pt: font("OpenSans-Bold.ttf", pt)
OSXB = lambda pt: font("OpenSans-ExtraBold.ttf", pt)

# -------------------------------------------------------------------- data --
guide = json.load(open(os.path.join(REPO, "data", "guide.json")))
GUIDE, SECTIONS = guide["guide"], guide["sections"]
no = 0
for i, sec in enumerate(SECTIONS):
    sec["mk"] = f"{i+1:02d}"
    for s in sec["stops"]:
        no += 1
        s["no"], s["cat"] = no, sec["key"]
ALL_STOPS = [s for sec in SECTIONS for s in sec["stops"]]
TOTAL = len(ALL_STOPS)
PINNED = [s for s in ALL_STOPS if s.get("lat") is not None and s.get("lng") is not None]
CITY = GUIDE.get("city", "")

mapdata = json.load(open(os.path.join(ROOT, "cache", "mapdata.json")))["elements"]

# -------------------------------------------------------------- projection --
# All city-specific map configuration lives in data/guide.json (print.map).
MAPCONF = guide["print"]["map"]
WEST, EAST = MAPCONF["bounds"]["west"], MAPCONF["bounds"]["east"]
CLAT = MAPCONF["bounds"]["centerLat"]
ASPECT = CW / CH
PROJ_W = (EAST - WEST) * math.cos(math.radians(CLAT))
LAT_SPAN = PROJ_W / ASPECT
SOUTH, NORTH = CLAT - LAT_SPAN/2, CLAT + LAT_SPAN/2

def proj(lat, lng, w=CW, h=CH, west=WEST, east=EAST, south=SOUTH, north=NORTH):
    x = (lng - west) / (east - west) * w
    y = (north - lat) / (north - south) * h
    return x, y

PX_PER_MILE = CH / ((NORTH - SOUTH) * 69.0)

# ------------------------------------------------------------------ helpers --
def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def skew_poly(x, y, w, h, skew=0.21):
    dx = h * skew
    return [(x+dx, y), (x+w+dx, y), (x+w, y+h), (x, y+h)]

def ribbon(draw, x, y, text, fnt, pad_x=None, pad_y=None, fill=TNX_RED):
    """Skewed show ribbon; returns (width, height) consumed."""
    asc, desc = fnt.getmetrics()
    th = asc + desc
    pw = pad_x if pad_x is not None else int(th*0.9)
    ph = pad_y if pad_y is not None else int(th*0.42)
    tw = draw.textlength(text, font=fnt)
    w, h = tw + 2*pw, th + 2*ph
    draw.polygon(skew_poly(x, y, w, h), fill=fill)
    draw.text((x + pw + h*0.105, y + ph), text, font=fnt, fill=WHITE)
    return w, h

def pin(draw, cx, cy, num, size_in=0.30):
    s = IN(size_in)
    x, y = cx - s/2, cy - s/2
    ring = 6
    draw.polygon(skew_poly(x-ring, y-ring, s+2*ring, s+2*ring), fill=WHITE)
    draw.polygon(skew_poly(x, y, s, s), fill=TNX_RED)
    fnt = RB(10 if num >= 10 else 11)
    t = str(num)
    tw = draw.textlength(t, font=fnt)
    asc, desc = fnt.getmetrics()
    draw.text((cx - tw/2 + s*0.10, cy - (asc+desc)/2 + 6), t, font=fnt, fill=WHITE)

def rects_overlap(a, b, m=0):
    return not (a[2]+m < b[0] or b[2]+m < a[0] or a[3]+m < b[1] or b[3]+m < a[1])

def paste_logo(img, path, x, y, w):
    """Paste a qlmanage-rasterized logo. These come with an opaque white
    letterbox, so crop to the non-white content and paste flat — every logo
    placement in this piece sits on a white surface."""
    from PIL import ImageChops
    logo = Image.open(path).convert("RGB")
    diff = ImageChops.difference(logo, Image.new("RGB", logo.size, (255, 255, 255)))
    logo = logo.crop(diff.getbbox())
    h = int(w * logo.height / logo.width)
    logo = logo.resize((int(w), h), Image.LANCZOS)
    img.paste(logo, (int(x), int(y)))
    return h

def rounded(draw, box, r, **kw):
    draw.rounded_rectangle(box, radius=r, **kw)


def fit_font(draw, text, font_fn, start_pt, max_w, min_pt=14):
    """Largest font (<= start_pt) at which text fits max_w. Route titles
    overflowed the fixed sizes (leak confirmed by three route builds)."""
    pt = start_pt
    while pt > min_pt and draw.textlength(text, font=font_fn(pt)) > max_w:
        pt -= 0.5
    return font_fn(pt)

# ------------------------------------------------------------------- roads --
def draw_geo(img, draw, w=CW, h=CH, west=WEST, east=EAST, south=SOUTH, north=NORTH, scale=1.0):
    P = lambda lat, lng: proj(lat, lng, w, h, west, east, south, north)
    buckets = {"water": [], "river": [], "secondary": [], "primary": [], "trunk": [], "motorway": []}
    for el in mapdata:
        t = el.get("tags", {})
        kind = t.get("highway") or ("river" if t.get("waterway") == "river" else None) \
               or ("water" if t.get("natural") == "water" else None)
        if kind not in buckets or "geometry" not in el: continue
        pts = [P(g["lat"], g["lon"]) for g in el["geometry"]]
        if len(pts) >= 2: buckets[kind].append((pts, t))
    for pts, t in buckets["water"]:
        if len(pts) >= 3: draw.polygon(pts, fill=WATER)
    for pts, t in buckets["river"]:
        wide = any(n in (t.get("name") or "") for n in MAPCONF.get("riverWide", []))
        wid = int(IN(MAPCONF.get("riverWideIn", 0.5))*scale) if wide else int(IN(0.07)*scale)
        draw.line(pts, fill=WATER, width=max(3, wid), joint="curve")
    for pts, t in buckets["secondary"]:
        draw.line(pts, fill=SECONDARY, width=max(2, int(5*scale)), joint="curve")
    for cls, casew, fillw, case, fill in (
        ("primary", 13, 7, PRIM_CASE, PRIM_FILL),
        ("trunk",   15, 9, TRUNK_CASE, TRUNK_FILL),
        ("motorway",19, 11, MOT_CASE, MOT_FILL)):
        for pts, t in buckets[cls]:
            draw.line(pts, fill=case, width=max(3, int(casew*scale)), joint="curve")
        for pts, t in buckets[cls]:
            draw.line(pts, fill=fill, width=max(2, int(fillw*scale)), joint="curve")
    return buckets

def draw_shields(draw, buckets, placed, w=CW, h=CH, west=WEST, east=EAST, south=SOUTH, north=NORTH):
    P = lambda lat, lng: proj(lat, lng, w, h, west, east, south, north)
    seen = {}
    for cls in ("motorway", "trunk"):
        for pts, t in buckets[cls]:
            ref = (t.get("ref") or "").split(";")[0].strip()
            if not ref: continue
            seen.setdefault(ref, []).append(pts)
    for ref, groups in sorted(seen.items()):
        segs = max(groups, key=len)
        mx, my = segs[len(segs)//2]
        if not (0 < mx < w and 0 < my < h): continue
        inter = ref.upper().startswith("I")
        num = ref.split()[-1]
        fnt = RB(9)
        tw = draw.textlength(num, font=fnt)
        bw, bh = max(IN(0.34), tw + IN(0.14)), IN(0.30)
        box = (mx-bw/2, my-bh/2, mx+bw/2, my+bh/2)
        if any(rects_overlap(box, p, m=IN(0.08)) for p in placed): continue
        if inter:
            rounded(draw, box, IN(0.06), fill=TNX_BLUE, outline=WHITE, width=5)
            draw.rectangle((box[0], box[1], box[2], box[1]+IN(0.075)), fill=TNX_RED)
            draw.text((mx - tw/2, box[1]+IN(0.085)), num, font=fnt, fill=WHITE)
        else:
            rounded(draw, box, IN(0.04), fill=WHITE, outline=INK, width=4)
            draw.text((mx - tw/2, box[1]+IN(0.055)), num, font=fnt, fill=INK)
        placed.append(box)

# ------------------------------------------------------------------- front --
def render_front():
    img = Image.new("RGB", (CW, CH), CREAM)
    d = ImageDraw.Draw(img)
    buckets = draw_geo(img, d)
    placed = []   # occupied rects (boxes added first so pins/shields avoid them)

    # ---- reserved boxes placed over the map's quiet zone (per-city config) ----
    def conf_box(key):
        x, y, w, h = MAPCONF[key]
        return (IN(x)+BX, IN(y)+BX, IN(x+w)+BX, IN(y+h)+BX)
    cart = conf_box("cartouche")
    legend = conf_box("legend")
    attrib = conf_box("attrib")
    placed += [cart, legend, attrib]
    INSET = MAPCONF.get("inset")
    inset_box = None
    if INSET:
        ix, iy, iw_in, ih_in = INSET["box"]
        inset_box = (IN(ix)+BX, IN(iy)+BX, IN(ix+iw_in)+BX, IN(iy+ih_in)+BX)
        placed.append(inset_box)

    draw_shields(d, buckets, placed)

    # ---- pins (dense-cluster pins live in the inset, when one is configured) ----
    ib = INSET
    def in_inset(s):
        if not ib: return False
        return ib["west"] < s["lng"] < ib["east"] and ib["south"] < s["lat"] < ib["north"]
    main_pins = [s for s in PINNED if not in_inset(s)]
    inset_pins = [s for s in PINNED if in_inset(s)]

    if INSET:
        # inset viewport rectangle on the main map
        r0 = proj(ib["north"], ib["west"]); r1 = proj(ib["south"], ib["east"])
        d.rectangle((r0[0], r0[1], r1[0], r1[1]), outline=TNX_BLUE, width=6)
        d.rectangle((r0[0]+8, r0[1]+8, r1[0]-8, r1[1]-8), outline=WHITE, width=3)

    pin_boxes = []
    for s in sorted(main_pins, key=lambda s: s["no"]):
        x, y = proj(s["lat"], s["lng"])
        r = IN(0.36)/2
        box = (x-r, y-r, x+r, y+r)
        # last candidate is a forced fallback so co-located pins never stamp
        # over each other (leak found during the Columbia build)
        cands = ((0,0),(IN(0.4),0),(-IN(0.4),0),(0,IN(0.4)),(0,-IN(0.4)),(IN(0.45),IN(0.45)))
        for i, (dx, dy) in enumerate(cands):
            cand = (box[0]+dx, box[1]+dy, box[2]+dx, box[3]+dy)
            free = not any(rects_overlap(cand, p, m=IN(0.04)) for p in placed + pin_boxes)
            if free or i == len(cands)-1:
                if (dx, dy) != (0, 0):
                    d.line((x, y, x+dx, y+dy), fill=TNX_RED, width=6)
                x, y, box = x+dx, y+dy, cand
                break
        pin(d, x, y, s["no"])
        pin_boxes.append(box)
    placed += pin_boxes

    # ---- area labels (per-city config) ----
    for lbl in MAPCONF.get("areaLabels", []):
        x, y = proj(lbl["lat"], lbl["lng"])
        fnt = OSB(13 if lbl.get("big") else 10)
        t = " ".join(lbl["name"])  # letterspacing
        tw = d.textlength(t, font=fnt)
        box = (x-tw/2, y, x+tw/2, y+IN(0.2))
        if any(rects_overlap(box, p) for p in placed): continue
        d.text((x-tw/2, y), t, font=fnt, fill=AREA_LBL)
        placed.append(box)
    wl = MAPCONF.get("waterLabel")
    if wl:
        x, y = proj(wl["lat"], wl["lng"])
        d.text((x, y), " ".join(wl["text"]), font=OSI(11), fill=(120, 152, 176))

    # ---- cartouche ----
    d.rectangle(cart, fill=WHITE, outline=TNX_BLUE, width=8)
    d.rectangle((cart[0]+14, cart[1]+14, cart[2]-14, cart[3]-14), outline=LINE, width=3)
    cx0 = cart[0] + IN(0.32)
    lh = paste_logo(img, os.path.join(ROOT, "cache", "logo-tnx.png"), cx0, cart[1]+IN(0.28), IN(1.9))
    tx = cx0 + IN(2.2)
    ribbon(d, tx, cart[1]+IN(0.34), GUIDE["eyebrow"].upper(), RB(8))
    pt1 = GUIDE.get("printTitle1", "A Traveler's Guide")
    pt2 = GUIDE.get("printTitle2", f"to {CITY}")
    cart_w = cart[2] - tx - IN(0.25)
    d.text((tx, cart[1]+IN(0.78)), pt1, font=fit_font(d, pt1, OSXB, 24, cart_w), fill=TNX_BLUE)
    d.text((tx, cart[1]+IN(1.18)), pt2, font=fit_font(d, pt2, OSXB, 24, cart_w), fill=TNX_RED)
    # route motif
    ry = cart[1]+IN(1.85)
    for i in range(28):
        d.ellipse((tx+i*IN(0.115)-4, ry-4, tx+i*IN(0.115)+4, ry+4), fill=TNX_BLUE)
    d.ellipse((tx-10, ry-14, tx+18, ry+14), fill=TNX_RED)
    d.polygon([(tx+28*IN(0.115), ry-12), (tx+28*IN(0.115)+22, ry), (tx+28*IN(0.115), ry+12)], fill=TNX_BLUE)
    d.text((tx, ry+IN(0.14)), f"{TOTAL} STOPS · {GUIDE['metaNote'].upper()}", font=RB(6.5), fill=MUTED)

    # ---- inset ----
    if not INSET:
        return _finish_front(img, d, cart, legend, attrib)
    iw, ih = inset_box[2]-inset_box[0], inset_box[3]-inset_box[1]
    sub = Image.new("RGB", (iw, ih), CREAM)
    sd = ImageDraw.Draw(sub)
    ib_buckets = draw_geo(sub, sd, iw, ih, ib["west"], ib["east"], ib["south"], ib["north"], scale=1.7)
    sub_pin_boxes = []
    for s in sorted(inset_pins, key=lambda s: s["no"]):
        x, y = proj(s["lat"], s["lng"], iw, ih, ib["west"], ib["east"], ib["south"], ib["north"])
        r = IN(0.38)/2
        box = (x-r, y-r, x+r, y+r)
        cands = ((0,0),(IN(0.42),0),(-IN(0.42),0),(0,IN(0.42)),(0,-IN(0.42)),
                 (IN(0.42),IN(0.42)),(IN(0.5),-IN(0.5)))
        for i, (dx, dy) in enumerate(cands):
            cand = (box[0]+dx, box[1]+dy, box[2]+dx, box[3]+dy)
            free = not any(rects_overlap(cand, p, m=IN(0.05)) for p in sub_pin_boxes)
            if free or i == len(cands)-1:
                if (dx, dy) != (0, 0):
                    sd.line((x, y, x+dx, y+dy), fill=TNX_RED, width=6)
                x, y, box = x+dx, y+dy, cand
                break
        pin(sd, x, y, s["no"], size_in=0.32)
        sub_pin_boxes.append(box)
    img.paste(sub, (inset_box[0], inset_box[1]))
    d.rectangle(inset_box, outline=TNX_BLUE, width=8)
    rw, rh = ribbon(d, inset_box[0]+IN(0.18), inset_box[1]+IN(0.18),
                    INSET["name"].upper(), RB(9))
    return _finish_front(img, d, cart, legend, attrib)

def _finish_front(img, d, cart, legend, attrib):
    # ---- legend ----
    d.rectangle(legend, fill=WHITE, outline=TNX_BLUE, width=8)
    lx, ly = legend[0]+IN(0.3), legend[1]+IN(0.25)
    ribbon(d, lx, ly, "READING THE MAP", RB(8))
    rows = [
        ("pin",   f"Numbered stops 01–{TOTAL:02d} — details on the reverse"),
        ("mot",   "Interstate"),
        ("prim",  "US & state highways"),
        ("sec",   "Local roads"),
    ]
    yy = ly + IN(0.62)
    for kind, label in rows:
        if kind == "pin":
            pin(d, lx+IN(0.17), yy+IN(0.1), 1, size_in=0.26)
        elif kind == "mot":
            d.line((lx, yy+IN(0.1), lx+IN(0.36), yy+IN(0.1)), fill=MOT_CASE, width=17)
            d.line((lx, yy+IN(0.1), lx+IN(0.36), yy+IN(0.1)), fill=MOT_FILL, width=10)
        elif kind == "prim":
            d.line((lx, yy+IN(0.1), lx+IN(0.36), yy+IN(0.1)), fill=PRIM_CASE, width=12)
            d.line((lx, yy+IN(0.1), lx+IN(0.36), yy+IN(0.1)), fill=PRIM_FILL, width=7)
        elif kind == "sec":
            d.line((lx, yy+IN(0.1), lx+IN(0.36), yy+IN(0.1)), fill=SECONDARY, width=5)
        d.text((lx+IN(0.52), yy), label, font=OSSB(9.5), fill=INK)
        yy += IN(0.42)
    # scale bar + north arrow
    sb_y = legend[3]-IN(0.42)
    d.line((lx, sb_y, lx+2*PX_PER_MILE, sb_y), fill=INK, width=6)
    for mi in range(3):
        d.line((lx+mi*PX_PER_MILE, sb_y-IN(0.05), lx+mi*PX_PER_MILE, sb_y+IN(0.05)), fill=INK, width=6)
        d.text((lx+mi*PX_PER_MILE-10, sb_y+IN(0.07)), str(mi), font=OSSB(8), fill=INK)
    d.text((lx+2*PX_PER_MILE+IN(0.12), sb_y-IN(0.08)), "miles", font=OSSB(8.5), fill=INK)
    nx = legend[2]-IN(0.55)
    d.polygon([(nx, sb_y-IN(0.28)), (nx-IN(0.11), sb_y+IN(0.05)), (nx+IN(0.11), sb_y+IN(0.05))], fill=TNX_BLUE)
    d.text((nx-IN(0.05), sb_y+IN(0.08)), "N", font=OSB(10), fill=TNX_BLUE)

    # ---- attribution strip ----
    d.rectangle(attrib, fill=WHITE, outline=TNX_BLUE, width=6)
    d.text((attrib[0]+IN(0.3), attrib[1]+IN(0.14)),
           "Every stop began as a story on Tennessee Crossroads — watch them all at tennesseecrossroads.org",
           font=OSI(9.5), fill=TNX_BLUE)
    d.text((attrib[0]+IN(0.3), attrib[1]+IN(0.5)),
           "Map data © OpenStreetMap contributors · Tennessee Crossroads is a Nashville PBS production",
           font=OSR(8), fill=MUTED)
    return img

# -------------------------------------------------------------------- back --
def panel_xy(col, row):
    return BX + col*PANEL_W, BX + row*PANEL_H

def render_back():
    img = Image.new("RGB", (CW, CH), WHITE)
    d = ImageDraw.Draw(img)
    M = IN(0.42)                                  # panel inner margin

    # ---------- listing panels: top row c0..c5, bottom row c0..c3 ----------
    order = [(c, 0) for c in range(6)] + [(c, 1) for c in range(4)]
    pi = 0
    px, py = panel_xy(*order[pi])
    cur_y = py + M

    def next_panel():
        nonlocal pi, px, py, cur_y
        pi += 1
        if pi >= len(order):
            raise SystemExit("stop listings overflow the available panels")
        px, py = panel_xy(*order[pi])
        cur_y = py + M

    def ensure(hpx):
        nonlocal cur_y
        if cur_y + hpx > py + PANEL_H - M:
            next_panel()

    maxw = PANEL_W - 2*M
    name_f, cred_f, blurb_f, meta_f = OSB(12.5), OSI(9.5), OSR(10), OSSB(8.5)

    def meta_text(s):
        return " · ".join(b for b in (s.get("addr"), s.get("phone"),
                          s.get("site"), "Free" if s.get("free") else "") if b)

    def stop_height(s):
        name_lines = wrap(d, f"{s['no']:02d} · {s['name']}", name_f, maxw)
        blurb_lines = wrap(d, s["blurb"], blurb_f, maxw)
        meta_lines = wrap(d, meta_text(s), meta_f, maxw)
        return (len(name_lines)*IN(0.215) + IN(0.19)
                + len(blurb_lines)*IN(0.175)
                + len(meta_lines)*IN(0.155) + IN(0.05) + IN(0.34))

    for sec in SECTIONS:
        # keep the section ribbon attached to its first stop
        ensure(IN(0.75) + stop_height(sec["stops"][0]))
        rw, rh = ribbon(d, px+M, cur_y, f"{sec['mk']} / {sec['title'].upper()}", RB(10))
        cur_y += rh + IN(0.22)
        for s in sec["stops"]:
            name_lines = wrap(d, f"{s['no']:02d} · {s['name']}", name_f, maxw)
            blurb_lines = wrap(d, s["blurb"], blurb_f, maxw)
            meta_lines = wrap(d, meta_text(s), meta_f, maxw)
            hh = stop_height(s)
            ensure(hh)
            yy = cur_y
            for ln in name_lines:
                d.text((px+M, yy), ln, font=name_f, fill=TNX_BLUE); yy += IN(0.215)
            credit = f"as seen with {s['host']}" if s.get("host") else "from the Crossroads archive"
            d.text((px+M, yy), credit, font=cred_f, fill=MUTED)
            yy += IN(0.19)
            for ln in blurb_lines:
                d.text((px+M, yy), ln, font=blurb_f, fill=INK_SOFT); yy += IN(0.175)
            yy += IN(0.02)
            for ln in meta_lines:
                d.text((px+M, yy), ln, font=meta_f, fill=MUTED); yy += IN(0.155)
            yy += IN(0.05)
            d.line((px+M, yy+IN(0.07), px+PANEL_W-M, yy+IN(0.07)), fill=LINE, width=3)
            cur_y = yy + IN(0.21)

    # ---------- filler panels: quote, then ruled notes ----------
    fill_i = 0
    while pi + 1 < len(order):
        next_panel()
        fx, fy = px, py
        if fill_i == 0:
            # PBS App panel — take the show along on the road
            d.rectangle((fx, fy, fx+PANEL_W, fy+PANEL_H), fill=CREAM)
            qy = fy + IN(0.9)
            rw, rh = ribbon(d, fx+M, qy, "TAKE THE SHOW ALONG", RB(9.5))
            qy += rh + IN(0.4)
            appf = OSSB(12.5)
            for ln in wrap(d, "Don't miss an episode while you're on the road — stream "
                              "Tennessee Crossroads free on the PBS App.", appf,
                           PANEL_W-2*M):
                d.text((fx+M, qy), ln, font=appf, fill=TNX_BLUE); qy += IN(0.26)
            qy += IN(0.45)
            qr_s = IN(2.3)
            qbx = fx+(PANEL_W-qr_s-IN(0.4))/2
            rounded(d, (qbx, qy, qbx+qr_s+IN(0.4), qy+qr_s+IN(0.4)), IN(0.1),
                    fill=WHITE, outline=TNX_BLUE, width=6)
            qr = Image.open(os.path.join(ROOT, "cache", "qr-pbs-app.png")).convert("RGB")
            qr = qr.resize((int(qr_s), int(qr_s)), Image.LANCZOS)
            img.paste(qr, (int(qbx+IN(0.2)), int(qy+IN(0.2))))
            qy += qr_s + IN(0.4) + IN(0.3)
            sc = "SCAN TO DOWNLOAD"
            scf = RB(7.5)
            d.text((fx+(PANEL_W-d.textlength(sc, font=scf))/2, qy), sc, font=scf, fill=TNX_RED)
            qy += IN(0.28)
            ur = "wnpt.tv/tnx-app"
            urf = OSB(11)
            d.text((fx+(PANEL_W-d.textlength(ur, font=urf))/2, qy), ur, font=urf, fill=TNX_BLUE)
        else:
            rw, rh = ribbon(d, fx+M, fy+M, "NOTES FROM THE ROAD", RB(9))
            ny = fy + M + rh + IN(0.45)
            while ny < fy + PANEL_H - M:
                d.line((fx+M, ny, fx+PANEL_W-M, ny), fill=LINE, width=3)
                ny += IN(0.42)
        fill_i += 1

    # ------------------------------- welcome panel (bottom row, col 4) -----
    wx, wy = panel_xy(4, 1)
    d.rectangle((wx, wy, wx+PANEL_W, wy+PANEL_H), fill=CREAM)
    yy = wy + IN(0.55)
    rw, rh = ribbon(d, wx+M, yy, "WELCOME", RB(10)); yy += rh + IN(0.28)
    for ln in wrap(d, GUIDE["note"], OSI(11.5), PANEL_W-2*M):
        d.text((wx+M, yy), ln, font=OSI(11.5), fill=TNX_BLUE); yy += IN(0.23)
    yy += IN(0.28)
    # the current Crossroads crew
    crew = Image.open(os.path.join(ROOT, "cache", "crew.jpg")).convert("RGB")
    cw_px = PANEL_W - 2*M
    crew = crew.resize((int(cw_px), int(cw_px)), Image.LANCZOS)
    img.paste(crew, (int(wx+M), int(yy)))
    d.rectangle((wx+M, yy, wx+M+cw_px, yy+cw_px), outline=TNX_BLUE, width=5)
    yy += cw_px + IN(0.25)
    for ln in wrap(d, "Every numbered pin on the map matches a stop listed on this side — and "
                      "every stop is a real segment from the show.", OSR(9.5), PANEL_W-2*M):
        d.text((wx+M, yy), ln, font=OSR(9.5), fill=INK_SOFT); yy += IN(0.17)
    d.text((wx+M, wy+PANEL_H-IN(0.62)), "Map data © OpenStreetMap contributors",
           font=OSR(7.5), fill=MUTED)

    # ------------------------------- cover panel (bottom row, col 5) -------
    cx, cy = panel_xy(5, 1)
    d.rectangle((cx, cy, cx+PANEL_W, cy+PANEL_H), fill=WHITE)
    d.rectangle((cx+IN(0.22), cy+IN(0.22), cx+PANEL_W-IN(0.22), cy+PANEL_H-IN(0.22)),
                outline=TNX_BLUE, width=6)
    lw = IN(2.2)
    lh = paste_logo(img, os.path.join(ROOT, "cache", "logo-tnx.png"),
                    cx+(PANEL_W-lw)/2, cy+IN(0.55), lw)
    yy = cy + IN(0.55) + lh + IN(0.32)
    eb_f = RB(7.5)
    tw = d.textlength(GUIDE["eyebrow"].upper(), font=eb_f)
    ribbon(d, cx+(PANEL_W-tw-IN(0.5))/2, yy, GUIDE["eyebrow"].upper(), eb_f)
    yy += IN(0.62)
    t1 = GUIDE.get("printTitle1", "A Traveler's Guide")
    t2 = GUIDE.get("printTitle2", f"to {CITY}")
    cover_w = PANEL_W - 2*IN(0.5)
    f1a = fit_font(d, t1, OSXB, 22, cover_w)
    f1b = fit_font(d, t2, OSXB, 22, cover_w)
    d.text((cx+(PANEL_W-d.textlength(t1, font=f1a))/2, yy), t1, font=f1a, fill=TNX_BLUE)
    yy += IN(0.42)
    d.text((cx+(PANEL_W-d.textlength(t2, font=f1b))/2, yy), t2, font=f1b, fill=TNX_RED)
    yy += IN(0.62)
    ry = yy
    n_dots, dot_span = 16, IN(0.115)
    rx = cx+(PANEL_W-n_dots*dot_span)/2
    for i in range(n_dots):
        d.ellipse((rx+i*dot_span-4, ry-4, rx+i*dot_span+4, ry+4), fill=TNX_BLUE)
    d.ellipse((rx-12, ry-13, rx+14, ry+13), fill=TNX_RED)
    d.polygon([(rx+n_dots*dot_span, ry-11), (rx+n_dots*dot_span+20, ry), (rx+n_dots*dot_span, ry+11)], fill=TNX_BLUE)
    yy += IN(0.28)
    mt = f"{TOTAL} STOPS · FOUR DECADES OF STORIES"
    mf = RB(6.5)
    d.text((cx+(PANEL_W-d.textlength(mt, font=mf))/2, yy), mt, font=mf, fill=MUTED)
    yy += IN(0.42)
    # feature photo (from data/guide.json print.coverImage)
    pconf = guide.get("print", {})
    if pconf.get("coverImage"):
        ph = Image.open(os.path.join(REPO, pconf["coverImage"])).convert("RGB")
        fw = PANEL_W - 2*IN(0.42)
        fh = int(IN(2.15))
        scale = max(fw/ph.width, fh/ph.height)
        ph = ph.resize((int(ph.width*scale)+1, int(ph.height*scale)+1), Image.LANCZOS)
        left = (ph.width - fw)//2; top = (ph.height - fh)//2
        ph = ph.crop((left, top, left+int(fw), top+fh))
        img.paste(ph, (int(cx+IN(0.42)), int(yy)))
        d.rectangle((cx+IN(0.42), yy, cx+IN(0.42)+int(fw), yy+fh), outline=TNX_BLUE, width=5)
        if pconf.get("coverCaption"):
            capf = OSI(7.5)
            d.text((cx+(PANEL_W-d.textlength(pconf["coverCaption"], font=capf))/2, yy+fh+IN(0.09)),
                   pconf["coverCaption"], font=capf, fill=MUTED)
    # NPBS chip bottom (blue box is part of the rasterized art)
    chip_w = IN(1.85)
    chip_h = paste_logo(img, os.path.join(ROOT, "cache", "logo-npbs-chip.png"),
                        cx+(PANEL_W-chip_w)/2, cy+PANEL_H-IN(1.2), chip_w)
    cl = "A NASHVILLE PBS PRODUCTION"
    clf = OSSB(7)
    d.text((cx+(PANEL_W-d.textlength(cl, font=clf))/2, cy+PANEL_H-IN(1.2)+chip_h+IN(0.1)), cl,
           font=clf, fill=MUTED)
    return img

# ------------------------------------------------------------------ output --
def save(img, name):
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    img.convert("CMYK").save(os.path.join(out, f"{name}.tif"), compression="tiff_lzw",
                             dpi=(DPI, DPI))
    # proof at 25% with trim + fold guides
    proof = img.copy()
    pd = ImageDraw.Draw(proof)
    pd.rectangle((BX, BX, CW-BX, CH-BX), outline=(255, 0, 255), width=4)
    if name == "back":
        for c in range(1, 6):
            x = BX + c*PANEL_W
            for y in range(BX, CH-BX, 60):
                pd.line((x, y, x, y+28), fill=(255, 0, 255), width=3)
        y = BX + PANEL_H
        for x in range(BX, CW-BX, 60):
            pd.line((x, y, x+28, y), fill=(255, 0, 255), width=3)
    proof = proof.resize((CW//4, CH//4), Image.LANCZOS)
    proof.save(os.path.join(out, f"{name}-proof.png"))

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("front", "both"):
        save(render_front(), "front"); print("front done")
    if which in ("back", "both"):
        save(render_back(), "back"); print("back done")
