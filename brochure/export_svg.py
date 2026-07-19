#!/usr/bin/env python3
"""Export the brochure's MAP SIDE as a layered, live-text SVG for Illustrator.

Same data, same layout math as build_brochure.py — this is the designer's
escape hatch for the proofing process. Named top-level groups become
selectable groups/sub-layers in Illustrator; all text is real text.

Notes for editors (also in PRINT-SPECS.md):
- Install the fonts in brochure/fonts/ (Open Sans, Rubik Mono One) before
  opening in Illustrator, or AI will substitute.
- SVG is RGB. Production color remains the CMYK TIFFs from build_brochure.py;
  if you hand-edit here, export print files from Illustrator instead.
- Logos are embedded as raster; swap for the vector originals in the brand
  folders if the printer needs them.

Output: brochure/out/front.svg
"""
import base64, json, os
from PIL import Image, ImageDraw

import build_brochure as bb

ROOT = bb.ROOT
OUT = os.path.join(ROOT, "out", "front.svg")

H = lambda rgb: "#%02x%02x%02x" % rgb
_measure = ImageDraw.Draw(Image.new("RGB", (8, 8)))
def tlen(text, fnt): return _measure.textlength(text, font=fnt)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def pathd(pts, close=False):
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")

def text_el(x, y, s, family, size_px, fill, weight="normal", style="normal",
            anchor="start", spacing=None):
    """y is the TOP of the text box (PIL convention) — SVG wants baseline."""
    baseline = y + size_px * 0.8
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{baseline:.1f}" font-family="{family}" '
            f'font-size="{size_px:.0f}" font-weight="{weight}" '
            f'font-style="{style}" fill="{fill}" text-anchor="{anchor}"{sp}>'
            f'{esc(s)}</text>')

PX = lambda pt: pt / 72 * bb.DPI  # points → px at 300dpi
OS, RBF = "Open Sans", "Rubik Mono One"

def geo_layers(P, scale=1.0):
    """Return dict of SVG element lists per geometry class."""
    out = {"water": [], "river": [], "secondary": [], "primary": [],
           "trunk": [], "motorway": []}
    buckets = {k: [] for k in out}
    for el in bb.mapdata:
        t = el.get("tags", {})
        kind = t.get("highway") or ("river" if t.get("waterway") == "river" else None) \
               or ("water" if t.get("natural") == "water" else None)
        if kind not in buckets or "geometry" not in el: continue
        pts = [P(g["lat"], g["lon"]) for g in el["geometry"]]
        if len(pts) >= 2: buckets[kind].append((pts, t))
    for pts, t in buckets["water"]:
        if len(pts) >= 3:
            out["water"].append(f'<path d="{pathd(pts, True)}" fill="{H(bb.WATER)}"/>')
    for pts, t in buckets["river"]:
        wide = any(n in (t.get("name") or "") for n in bb.MAPCONF.get("riverWide", []))
        w = bb.IN(bb.MAPCONF.get("riverWideIn", 0.5))*scale if wide else bb.IN(0.07)*scale
        out["river"].append(f'<path d="{pathd(pts)}" fill="none" stroke="{H(bb.WATER)}" '
                            f'stroke-width="{max(3, w):.0f}" stroke-linejoin="round" stroke-linecap="round"/>')
    def road(cls, casew, fillw, case, fill):
        for pts, t in buckets[cls]:
            out[cls].append(f'<path d="{pathd(pts)}" fill="none" stroke="{H(case)}" '
                            f'stroke-width="{max(3, casew*scale):.0f}" stroke-linejoin="round"/>')
        for pts, t in buckets[cls]:
            out[cls].append(f'<path d="{pathd(pts)}" fill="none" stroke="{H(fill)}" '
                            f'stroke-width="{max(2, fillw*scale):.0f}" stroke-linejoin="round"/>')
    for pts, t in buckets["secondary"]:
        out["secondary"].append(f'<path d="{pathd(pts)}" fill="none" stroke="{H(bb.SECONDARY)}" '
                                f'stroke-width="{max(2, 5*scale):.0f}" stroke-linejoin="round"/>')
    road("primary", 13, 7, bb.PRIM_CASE, bb.PRIM_FILL)
    road("trunk", 15, 9, bb.TRUNK_CASE, bb.TRUNK_FILL)
    road("motorway", 19, 11, bb.MOT_CASE, bb.MOT_FILL)
    return out, buckets

def skew_pts(x, y, w, h, skew=0.21):
    dx = h * skew
    return [(x+dx, y), (x+w+dx, y), (x+w, y+h), (x, y+h)]

def svg_ribbon(x, y, s, pt):
    fnt = bb.RB(pt)
    asc, desc = fnt.getmetrics()
    th = asc + desc
    pw, ph = int(th*0.9), int(th*0.42)
    tw = tlen(s, fnt)
    w, h = tw + 2*pw, th + 2*ph
    els = [f'<polygon points="{" ".join(f"{px:.0f},{py:.0f}" for px,py in skew_pts(x,y,w,h))}" fill="{H(bb.TNX_RED)}"/>',
           text_el(x+pw+h*0.105, y+ph, s, RBF, PX(pt), "#ffffff")]
    return els, w, h

def svg_pin(cx, cy, num, size_in=0.30):
    s = bb.IN(size_in); x, y = cx - s/2, cy - s/2; ring = 6
    fnt = bb.RB(10 if num >= 10 else 11)
    t = str(num); tw = tlen(t, fnt)
    asc, desc = fnt.getmetrics()
    return (f'<g id="pin-{num:02d}">'
            f'<polygon points="{" ".join(f"{px:.0f},{py:.0f}" for px,py in skew_pts(x-ring,y-ring,s+2*ring,s+2*ring))}" fill="#ffffff"/>'
            f'<polygon points="{" ".join(f"{px:.0f},{py:.0f}" for px,py in skew_pts(x,y,s,s))}" fill="{H(bb.TNX_RED)}"/>'
            + text_el(cx - tw/2 + s*0.10, cy - (asc+desc)/2 + 6, t,
                      RBF, PX(10 if num >= 10 else 11), "#ffffff")
            + "</g>")

def build():
    L = []  # top-level layer groups, in paint order
    CW, CH, BX = bb.CW, bb.CH, bb.BX
    P = lambda lat, lng: bb.proj(lat, lng)

    L.append(f'<g id="base"><rect width="{CW}" height="{CH}" fill="{H(bb.CREAM)}"/></g>')

    geo, buckets = geo_layers(P)
    L.append('<g id="water">' + "".join(geo["water"] + geo["river"]) + "</g>")
    L.append('<g id="roads-local">' + "".join(geo["secondary"]) + "</g>")
    L.append('<g id="roads-highway">' + "".join(geo["primary"] + geo["trunk"]) + "</g>")
    L.append('<g id="roads-interstate">' + "".join(geo["motorway"]) + "</g>")

    # boxes reserved (same config the raster build uses)
    def conf_box(key):
        x, y, w, h = bb.MAPCONF[key]
        return (bb.IN(x)+BX, bb.IN(y)+BX, bb.IN(x+w)+BX, bb.IN(y+h)+BX)
    cart = conf_box("cartouche"); legend = conf_box("legend"); attrib = conf_box("attrib")
    placed = [cart, legend, attrib]
    INSET = bb.MAPCONF.get("inset")
    inset_box = None
    if INSET:
        ix, iy, iw_in, ih_in = INSET["box"]
        inset_box = (bb.IN(ix)+BX, bb.IN(iy)+BX, bb.IN(ix+iw_in)+BX, bb.IN(iy+ih_in)+BX)
        placed.append(inset_box)

    # shields
    shields = []
    seen = {}
    for cls in ("motorway", "trunk"):
        for pts, t in buckets[cls]:
            ref = (t.get("ref") or "").split(";")[0].strip()
            if ref: seen.setdefault(ref, []).append(pts)
    for ref, groups in sorted(seen.items()):
        segs = max(groups, key=len)
        mx, my = segs[len(segs)//2]
        if not (0 < mx < CW and 0 < my < CH): continue
        inter = ref.upper().startswith("I")
        num = ref.split()[-1]
        fnt = bb.RB(9); tw = tlen(num, fnt)
        bw, bh = max(bb.IN(0.34), tw + bb.IN(0.14)), bb.IN(0.30)
        box = (mx-bw/2, my-bh/2, mx+bw/2, my+bh/2)
        if any(bb.rects_overlap(box, p, m=bb.IN(0.08)) for p in placed): continue
        if inter:
            shields.append(f'<g><rect x="{box[0]:.0f}" y="{box[1]:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="{bb.IN(0.06)}" fill="{H(bb.TNX_BLUE)}" stroke="#ffffff" stroke-width="5"/>'
                           f'<rect x="{box[0]:.0f}" y="{box[1]:.0f}" width="{bw:.0f}" height="{bb.IN(0.075)}" fill="{H(bb.TNX_RED)}"/>'
                           + text_el(mx - tw/2, box[1]+bb.IN(0.085), num, RBF, PX(9), "#ffffff") + "</g>")
        else:
            shields.append(f'<g><rect x="{box[0]:.0f}" y="{box[1]:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="{bb.IN(0.04)}" fill="#ffffff" stroke="{H(bb.INK)}" stroke-width="4"/>'
                           + text_el(mx - tw/2, box[1]+bb.IN(0.055), num, RBF, PX(9), H(bb.INK)) + "</g>")
        placed.append(box)
    L.append('<g id="route-shields">' + "".join(shields) + "</g>")

    # inset viewport on main map
    ib = INSET
    if INSET:
        r0 = P(ib["north"], ib["west"]); r1 = P(ib["south"], ib["east"])
        L.append(f'<g id="inset-viewport"><rect x="{r0[0]:.0f}" y="{r0[1]:.0f}" width="{r1[0]-r0[0]:.0f}" height="{r1[1]-r0[1]:.0f}" fill="none" stroke="{H(bb.TNX_BLUE)}" stroke-width="6"/>'
                 f'<rect x="{r0[0]+8:.0f}" y="{r0[1]+8:.0f}" width="{r1[0]-r0[0]-16:.0f}" height="{r1[1]-r0[1]-16:.0f}" fill="none" stroke="#ffffff" stroke-width="3"/></g>')

    # pins (same inset split + nudge as raster)
    def in_inset(s):
        if not ib: return False
        return ib["west"] < s["lng"] < ib["east"] and ib["south"] < s["lat"] < ib["north"]
    main_pins = [s for s in bb.PINNED if not in_inset(s)]
    inset_pins = [s for s in bb.PINNED if in_inset(s)]
    pin_els, pin_boxes = [], []
    for s in sorted(main_pins, key=lambda s: s["no"]):
        x, y = P(s["lat"], s["lng"]); r = bb.IN(0.36)/2
        box = (x-r, y-r, x+r, y+r)
        cands = ((0,0),(bb.IN(0.4),0),(-bb.IN(0.4),0),(0,bb.IN(0.4)),(0,-bb.IN(0.4)),(bb.IN(0.45),bb.IN(0.45)))
        for i, (dx, dy) in enumerate(cands):
            cand = (box[0]+dx, box[1]+dy, box[2]+dx, box[3]+dy)
            free = not any(bb.rects_overlap(cand, p, m=bb.IN(0.04)) for p in placed + pin_boxes)
            if free or i == len(cands)-1:
                if (dx, dy) != (0, 0):
                    pin_els.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+dx:.0f}" y2="{y+dy:.0f}" stroke="{H(bb.TNX_RED)}" stroke-width="6"/>')
                x, y, box = x+dx, y+dy, cand
                break
        pin_els.append(svg_pin(x, y, s["no"]))
        pin_boxes.append(box)
    placed += pin_boxes
    L.append('<g id="stop-pins">' + "".join(pin_els) + "</g>")

    # area labels
    lbls = []
    for lbl in bb.MAPCONF.get("areaLabels", []):
        x, y = P(lbl["lat"], lbl["lng"])
        fnt = bb.OSB(13 if lbl.get("big") else 10)
        t = " ".join(lbl["name"])
        tw = tlen(t, fnt)
        box = (x-tw/2, y, x+tw/2, y+bb.IN(0.2))
        if any(bb.rects_overlap(box, p) for p in placed): continue
        lbls.append(text_el(x-tw/2, y, t, OS, PX(13 if lbl.get("big") else 10),
                            H(bb.AREA_LBL), weight="700"))
        placed.append(box)
    wl = bb.MAPCONF.get("waterLabel")
    if wl:
        x, y = P(wl["lat"], wl["lng"])
        lbls.append(text_el(x, y, " ".join(wl["text"]), OS, PX(11), "#7898b0", style="italic"))
    L.append('<g id="area-labels">' + "".join(lbls) + "</g>")

    # cartouche
    c = []
    c.append(f'<rect x="{cart[0]}" y="{cart[1]}" width="{cart[2]-cart[0]}" height="{cart[3]-cart[1]}" fill="#ffffff" stroke="{H(bb.TNX_BLUE)}" stroke-width="8"/>')
    c.append(f'<rect x="{cart[0]+14}" y="{cart[1]+14}" width="{cart[2]-cart[0]-28}" height="{cart[3]-cart[1]-28}" fill="none" stroke="{H(bb.LINE)}" stroke-width="3"/>')
    logo = open(os.path.join(ROOT, "cache", "logo-tnx.png"), "rb").read()
    lw = bb.IN(1.9)
    from PIL import ImageChops
    li = Image.open(os.path.join(ROOT, "cache", "logo-tnx.png")).convert("RGB")
    diff = ImageChops.difference(li, Image.new("RGB", li.size, (255,255,255)))
    li = li.crop(diff.getbbox())
    lh = lw * li.height / li.width
    import io
    buf = io.BytesIO(); li.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    cx0 = cart[0] + bb.IN(0.32)
    c.append(f'<image x="{cx0:.0f}" y="{cart[1]+bb.IN(0.28):.0f}" width="{lw:.0f}" height="{lh:.0f}" href="data:image/png;base64,{b64}"/>')
    tx = cx0 + bb.IN(2.2)
    rib, rw, rh = svg_ribbon(tx, cart[1]+bb.IN(0.34), bb.GUIDE["eyebrow"].upper(), 8)
    c += rib
    c.append(text_el(tx, cart[1]+bb.IN(0.78), bb.GUIDE.get("printTitle1", "A Traveler's Guide"), OS, PX(24), H(bb.TNX_BLUE), weight="800"))
    c.append(text_el(tx, cart[1]+bb.IN(1.18), bb.GUIDE.get("printTitle2", f"to {bb.CITY}"), OS, PX(24), H(bb.TNX_RED), weight="800"))
    ry = cart[1]+bb.IN(1.85)
    dots = "".join(f'<circle cx="{tx+i*bb.IN(0.115):.0f}" cy="{ry}" r="4" fill="{H(bb.TNX_BLUE)}"/>' for i in range(28))
    c.append(f'<g>{dots}<circle cx="{tx+4}" cy="{ry}" r="14" fill="{H(bb.TNX_RED)}"/>'
             f'<polygon points="{tx+28*bb.IN(0.115):.0f},{ry-12} {tx+28*bb.IN(0.115)+22:.0f},{ry} {tx+28*bb.IN(0.115):.0f},{ry+12}" fill="{H(bb.TNX_BLUE)}"/></g>')
    c.append(text_el(tx, ry+bb.IN(0.14), f"{bb.TOTAL} STOPS · {bb.GUIDE['metaNote'].upper()}", RBF, PX(6.5), H(bb.MUTED)))
    L.append('<g id="cartouche">' + "".join(c) + "</g>")

    # inset
    if INSET:
      iw, ih = inset_box[2]-inset_box[0], inset_box[3]-inset_box[1]
      Pi = lambda lat, lng: bb.proj(lat, lng, iw, ih, ib["west"], ib["east"], ib["south"], ib["north"])
      igeo, _ = geo_layers(Pi, scale=1.7)
      inner = f'<rect width="{iw}" height="{ih}" fill="{H(bb.CREAM)}"/>' \
              + "".join(igeo["water"] + igeo["river"] + igeo["secondary"]
                        + igeo["primary"] + igeo["trunk"] + igeo["motorway"])
      ipins, ipin_boxes = [], []
      for s in sorted(inset_pins, key=lambda s: s["no"]):
          x, y = Pi(s["lat"], s["lng"]); r = bb.IN(0.38)/2
          box = (x-r, y-r, x+r, y+r)
          cands = ((0,0),(bb.IN(0.42),0),(-bb.IN(0.42),0),(0,bb.IN(0.42)),(0,-bb.IN(0.42)),(bb.IN(0.42),bb.IN(0.42)),(bb.IN(0.5),-bb.IN(0.5)))
          for i, (dx, dy) in enumerate(cands):
              cand = (box[0]+dx, box[1]+dy, box[2]+dx, box[3]+dy)
              free = not any(bb.rects_overlap(cand, p, m=bb.IN(0.05)) for p in ipin_boxes)
              if free or i == len(cands)-1:
                  if (dx, dy) != (0, 0):
                      ipins.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+dx:.0f}" y2="{y+dy:.0f}" stroke="{H(bb.TNX_RED)}" stroke-width="6"/>')
                  x, y, box = x+dx, y+dy, cand
                  break
          ipins.append(svg_pin(x, y, s["no"], size_in=0.32))
          ipin_boxes.append(box)
      rib2, _, _ = svg_ribbon(bb.IN(0.18), bb.IN(0.18), INSET["name"].upper(), 9)
      L.append(f'<g id="inset" transform="translate({inset_box[0]},{inset_box[1]})">'
               f'<clipPath id="insetclip"><rect width="{iw}" height="{ih}"/></clipPath>'
               f'<g clip-path="url(#insetclip)">{inner}{"".join(ipins)}</g>'
               f'<rect width="{iw}" height="{ih}" fill="none" stroke="{H(bb.TNX_BLUE)}" stroke-width="8"/>'
               + "".join(rib2) + "</g>")

    # legend
    lg = [f'<rect x="{legend[0]}" y="{legend[1]}" width="{legend[2]-legend[0]}" height="{legend[3]-legend[1]}" fill="#ffffff" stroke="{H(bb.TNX_BLUE)}" stroke-width="8"/>']
    lx, ly = legend[0]+bb.IN(0.3), legend[1]+bb.IN(0.25)
    rib3, _, _ = svg_ribbon(lx, ly, "READING THE MAP", 8)
    lg += rib3
    yy = ly + bb.IN(0.62)
    rows = [("pin", f"Numbered stops 01–{bb.TOTAL:02d} — details on the reverse"),
            ("mot", "Interstate"), ("prim", "US & state highways"), ("sec", "Local roads")]
    for kind, label in rows:
        cy = yy + bb.IN(0.1)
        if kind == "pin": lg.append(svg_pin(lx+bb.IN(0.17), cy, 1, size_in=0.26))
        elif kind == "mot":
            lg.append(f'<line x1="{lx}" y1="{cy}" x2="{lx+bb.IN(0.36)}" y2="{cy}" stroke="{H(bb.MOT_CASE)}" stroke-width="17"/>'
                      f'<line x1="{lx}" y1="{cy}" x2="{lx+bb.IN(0.36)}" y2="{cy}" stroke="{H(bb.MOT_FILL)}" stroke-width="10"/>')
        elif kind == "prim":
            lg.append(f'<line x1="{lx}" y1="{cy}" x2="{lx+bb.IN(0.36)}" y2="{cy}" stroke="{H(bb.PRIM_CASE)}" stroke-width="12"/>'
                      f'<line x1="{lx}" y1="{cy}" x2="{lx+bb.IN(0.36)}" y2="{cy}" stroke="{H(bb.PRIM_FILL)}" stroke-width="7"/>')
        else:
            lg.append(f'<line x1="{lx}" y1="{cy}" x2="{lx+bb.IN(0.36)}" y2="{cy}" stroke="{H(bb.SECONDARY)}" stroke-width="5"/>')
        lg.append(text_el(lx+bb.IN(0.52), yy, label, OS, PX(9.5), H(bb.INK), weight="600"))
        yy += bb.IN(0.42)
    sb_y = legend[3]-bb.IN(0.42)
    lg.append(f'<line x1="{lx}" y1="{sb_y}" x2="{lx+2*bb.PX_PER_MILE:.0f}" y2="{sb_y}" stroke="{H(bb.INK)}" stroke-width="6"/>')
    for mi in range(3):
        mx = lx+mi*bb.PX_PER_MILE
        lg.append(f'<line x1="{mx:.0f}" y1="{sb_y-bb.IN(0.05)}" x2="{mx:.0f}" y2="{sb_y+bb.IN(0.05)}" stroke="{H(bb.INK)}" stroke-width="6"/>')
        lg.append(text_el(mx-10, sb_y+bb.IN(0.07), str(mi), OS, PX(8), H(bb.INK), weight="600"))
    lg.append(text_el(lx+2*bb.PX_PER_MILE+bb.IN(0.12), sb_y-bb.IN(0.08), "miles", OS, PX(8.5), H(bb.INK), weight="600"))
    nx = legend[2]-bb.IN(0.55)
    lg.append(f'<polygon points="{nx:.0f},{sb_y-bb.IN(0.28)} {nx-bb.IN(0.11):.0f},{sb_y+bb.IN(0.05)} {nx+bb.IN(0.11):.0f},{sb_y+bb.IN(0.05)}" fill="{H(bb.TNX_BLUE)}"/>')
    lg.append(text_el(nx-bb.IN(0.05), sb_y+bb.IN(0.08), "N", OS, PX(10), H(bb.TNX_BLUE), weight="700"))
    L.append('<g id="legend">' + "".join(lg) + "</g>")

    # attribution
    at = [f'<rect x="{attrib[0]}" y="{attrib[1]}" width="{attrib[2]-attrib[0]}" height="{attrib[3]-attrib[1]}" fill="#ffffff" stroke="{H(bb.TNX_BLUE)}" stroke-width="6"/>',
          text_el(attrib[0]+bb.IN(0.3), attrib[1]+bb.IN(0.14),
                  "Every stop began as a story on Tennessee Crossroads — watch them all at tennesseecrossroads.org",
                  OS, PX(9.5), H(bb.TNX_BLUE), style="italic"),
          text_el(attrib[0]+bb.IN(0.3), attrib[1]+bb.IN(0.5),
                  "Map data © OpenStreetMap contributors · Tennessee Crossroads is a Nashville PBS production",
                  OS, PX(8), H(bb.MUTED))]
    L.append('<g id="attribution">' + "".join(at) + "</g>")

    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{bb.TRIM_W + 2*bb.BLEED}in" height="{bb.TRIM_H + 2*bb.BLEED}in" '
           f'viewBox="0 0 {bb.CW} {bb.CH}">\n'
           f'<style>@import url("https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&amp;family=Rubik+Mono+One&amp;display=swap");</style>\n'
           + "\n".join(L) + "\n</svg>\n")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    open(OUT, "w").write(svg)
    print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")

if __name__ == "__main__":
    build()
