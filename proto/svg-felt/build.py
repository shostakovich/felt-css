#!/usr/bin/env python3
"""Prototype: felt textures and seams as SVG instead of photo WebPs.

Writes img/*.svg and felt.css (a copy of ../../felt.css with img/*.webp -> img/*.svg), so every
component renders exactly as in the library, only the assets differ. Seams keep the WebPs' 9-slice
geometry (same --seam-*-slice tokens): SVG width/height are device px at 2x, viewBox is CSS px.
"""
import math, re
from pathlib import Path
from feltgen import felt

HERE = Path(__file__).resolve().parent
OUT = HERE / "img"
DPR = 2

# --- felt: noise bands fitted to the photos' contrast at 0/1/3/8 px blur (see lab/)
FELT = {
    # grey around 50 %, soft-light on saturated colours
    "felt": dict(warp=(".035", 16), bands=[[".03", 2, "f", .038], [".08", 2, "f", .097],
                 [".15", 2, "t", -.273, .25, 16], [".5", 1, "t", -.313, .145, 14]]),
    # warm ~94 % cream, multiply on light surfaces
    "felt-light": dict(base=.95, rgb=(1.004, .996, .973), warp=(".035", 16), bands=[[".03", 2, "f", .059], [".08", 2, "f", .054],
                 [".15", 2, "t", -.092, .25, 16], [".3", 2, "t", -.056, .25, 14]]),
    # grey around 50 %, quieter, soft-light on charcoal
    "felt-dark": dict(warp=(".035", 16), bands=[[".03", 2, "f", .067], [".08", 2, "f", .056],
                 [".15", 2, "t", -.157, .25, 16], [".3", 2, "t", -.139, .25, 14]]),
}

# --- seams (CSS px)
MARGIN = 3            # slice edge -> thread centre line
LEN, THICK = 6.5, 1.4 # stitch
PERIOD = 10           # stitch + gap
SHAPES = {"lg": (9, 3), "md": (7, 1), "pill": (17, 1)}   # seam radius, stitches per edge tile
ROW = 3
# per stitch: length factor, angle (deg), offset across the seam: a hand-sewn wobble
WOBBLE = [(1, 0, 0), (.97, -2.5, .25), (.9, 2, -.2)]

def f(x): return f"{x:.2f}".rstrip("0").rstrip(".")

def defs():
    h, l = THICK / 2, LEN / 2
    # one stitch along x: a lens-ended capsule, twisted ply (stripes), a highlight along its top
    stitch = (f'M{f(-l)} 0Q{f(-l+.3)} {f(-h)} {f(-l+1.2)} {f(-h)}H{f(l-1.2)}Q{f(l-.3)} {f(-h)} {f(l)} 0'
              f'Q{f(l-.3)} {f(h)} {f(l-1.2)} {f(h)}H{f(-l+1.2)}Q{f(-l+.3)} {f(h)} {f(-l)} 0Z')
    return ('<defs>'
            '<pattern id="t" width="1.1" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-58)">'
            '<rect width="1.1" height="4" fill="#f4f4f4"/><rect width=".42" height="4" fill="#c9c9c9"/></pattern>'
            f'<g id="s"><path d="{stitch}" fill="url(#t)"/>'
            f'<rect x="{f(-l+1.1)}" y="{f(-h+.2)}" width="{f(LEN-2.2)}" height=".38" rx=".19" fill="#fff" opacity=".7"/></g>'
            # thread casts a soft shadow down; the stitches pull a faint groove into the felt
            '<filter id="d" x="-20%" y="-20%" width="140%" height="140%">'
            '<feGaussianBlur in="SourceAlpha" stdDeviation=".35"/><feOffset dy=".7"/>'
            '<feComponentTransfer><feFuncA type="linear" slope=".3"/></feComponentTransfer>'
            '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="g"><feGaussianBlur stdDeviation=".8"/></filter>'
            '</defs>')

def stitch(x, y, angle, k=0, scale=1.0):
    lf, da, dy = WOBBLE[k % len(WOBBLE)]
    s = lf * scale
    rad = math.radians(angle)
    x, y = x - dy * math.sin(rad), y + dy * math.cos(rad)
    t = f"translate({f(x)} {f(y)}) rotate({f(angle + da)})" + (f" scale({f(s)} 1)" if s != 1 else "")
    return f'<use href="#s" transform="{t}"/>'

def svg(w, h, groove, stitches):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{round(w * DPR)}" height="{round(h * DPR)}" viewBox="0 0 {f(w)} {f(h)}">{defs()}'
            f'<path d="{groove}" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="1.6" filter="url(#g)"/>'
            f'<g filter="url(#d)">{"".join(stitches)}</g></svg>')

def frame(radius, n):
    m, r = MARGIN, radius
    c = m + r
    w = 2 * c + n * PERIOD
    out = []
    for k in range(n):
        t = c + (k + .5) * PERIOD
        out += [stitch(t, m, 0, k), stitch(w - m, t, 90, k), stitch(w - t, w - m, 180, k), stitch(m, w - t, 270, k)]
    arc = math.pi / 2 * r
    na = max(1, round(arc / PERIOD))
    for j, ((cx, cy), start) in enumerate((((c, c), 180), ((w - c, c), 270), ((w - c, w - c), 0), ((c, w - c), 90))):
        for k in range(na):
            phi = math.radians(start + 90 * (k + .5) / na)
            out.append(stitch(cx + r * math.cos(phi), cy + r * math.sin(phi), math.degrees(phi) + 90, j + k,
                              min(1.0, arc / na / PERIOD)))
    groove = f"M{f(m)} {f(c)}A{f(r)} {f(r)} 0 0 1 {f(c)} {f(m)}H{f(w-c)}A{f(r)} {f(r)} 0 0 1 {f(w-m)} {f(c)}V{f(w-c)}A{f(r)} {f(r)} 0 0 1 {f(w-c)} {f(w-m)}H{f(c)}A{f(r)} {f(r)} 0 0 1 {f(m)} {f(w-c)}Z"
    return svg(w, w, groove, out), c * DPR

def row(vertical=False):
    h, length = 2 * MARGIN, ROW * PERIOD
    if vertical:
        st = [stitch(MARGIN, (k + .5) * PERIOD, 90, k) for k in range(ROW)]
        return svg(h, length, f"M{MARGIN} -10V{length + 10}", st)
    st = [stitch((k + .5) * PERIOD, MARGIN, 0, k) for k in range(ROW)]
    return svg(length, h, f"M-10 {MARGIN}H{length + 10}", st)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, kw in FELT.items():
        (OUT / f"{name}.svg").write_text(felt(**kw))
    for name, (r, n) in SHAPES.items():
        s, sl = frame(r, n)
        (OUT / f"seam-{name}.svg").write_text(s)
        print(f"seam-{name}: slice {sl:g}")
    (OUT / "seam-row.svg").write_text(row())
    (OUT / "seam-col.svg").write_text(row(True))
    css = (HERE.parent.parent / "felt.css").read_text()
    css = re.sub(r'img/((?:felt|seam)[\w-]*)\.webp', r'img/\1.svg', css)
    (HERE / "felt.css").write_text(css)
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size} B")
