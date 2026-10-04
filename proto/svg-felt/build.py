#!/usr/bin/env python3
"""Prototype: felt textures and seams as SVG instead of photo WebPs.

Writes img/*.svg and felt.css (a copy of ../../felt.css with img/*.webp -> img/*.svg), so every
component renders exactly as in the library, only the assets differ. Seams keep the WebPs' 9-slice
geometry (same --seam-*-slice tokens): SVG width/height are device px at 2x, viewBox is CSS px.
"""
import math, random, re
from pathlib import Path
from feltgen import felt

HERE = Path(__file__).resolve().parent
OUT = HERE / "img"
DPR = 2

# --- felt: noise bands (see feltgen.py)
FELT = {
    # Dense felt: soft cloudy mottling, a short criss-cross nap (two anisotropic ridge bands, slightly bent and
    # blurred so they read as fuzz, not hairlines), fine grain and a few longer stray fibres. Compared against
    # photos of real wool and craft felt.
    # grey around 50 %, soft-light on saturated colours
    "felt": dict(warp=(".035", 12), bands=[[".012", 2, "f", 0.2], [".05", 2, "f", 0.12],
                 [".22 .32", 2, "t", -0.24, .25, 6, .25], [".32 .22", 2, "t", -0.24, .25, 6, .25],
                 [".7", 1, "f", 0.22], [".12", 2, "t", -0.16, .25, 12, .12]]),
    # warm ~94 % cream, multiply on light surfaces: the same felt, much quieter, mottling under 3 %
    "felt-light": dict(base=.95, rgb=(1.004, .996, .973), warp=(".035", 12), bands=[[".012", 2, "f", 0.05], [".05", 2, "f", 0.04],
                 [".22 .32", 2, "t", -0.0864, .25, 6, .25], [".32 .22", 2, "t", -0.0864, .25, 6, .25],
                 [".7", 1, "f", 0.0792], [".12", 2, "t", -0.0576, .25, 12, .12]]),
    # grey around 50 %, soft-light on charcoal: a little quieter than the colours
    "felt-dark": dict(warp=(".035", 12), bands=[[".012", 2, "f", 0.09], [".05", 2, "f", 0.06],
                 [".22 .32", 2, "t", -0.149, .25, 6, .25], [".32 .22", 2, "t", -0.149, .25, 6, .25],
                 [".7", 1, "f", 0.136], [".12", 2, "t", -0.0992, .25, 12, .12]]),
}

# --- seams (CSS px)
MARGIN = 3            # slice edge -> thread centre line
LEN, THICK = 7, 1.6   # stitch: about 2/3 of the period, like the photographed seam
PERIOD = 10           # stitch + gap
SHAPES = {"lg": (9, 3), "md": (7, 1), "pill": (17, 1)}   # seam radius, stitches per edge tile
ROW = 3
# a hand-sewn wobble: per stitch length factor (±8 %), angle (±2°) and offset across the seam (±0.3 px);
# every edge of a frame draws other stitches from the table, so even one-stitch tiles differ round the piece
_r = random.Random(7)
WOBBLE = [(1 + _r.uniform(-.08, .08), _r.uniform(-2, 2), _r.uniform(-.3, .3)) for _ in range(32)]

def f(x): return f"{x:.2f}".rstrip("0").rstrip(".")

def defs():
    h, l = THICK / 2, LEN / 2
    # one stitch along x: a plump body that tapers to a point where it dives into the felt
    stitch = (f'M{f(-l)} 0C{f(-l+.6)} {f(-h)} {f(-l+1.6)} {f(-h)} {f(-l+2.4)} {f(-h)}H{f(l-2.4)}'
              f'C{f(l-1.6)} {f(-h)} {f(l-.6)} {f(-h)} {f(l)} 0C{f(l-.6)} {f(h)} {f(l-1.6)} {f(h)} {f(l-2.4)} {f(h)}'
              f'H{f(-l+2.4)}C{f(-l+1.6)} {f(h)} {f(-l+.6)} {f(h)} {f(-l)} 0Z')
    return ('<defs>'
            # twisted ply: soft diagonal ridges at ~32° to the thread
            '<pattern id="t" width="1.25" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-58)">'
            '<rect width="1.25" height="4" fill="#f3f3f3"/><rect width=".5" height="4" fill="#d5d5d5"/></pattern>'
            f'<g id="s"><circle cx="{f(-l-.15)}" r=".55" opacity=".3"/><circle cx="{f(l+.15)}" r=".55" opacity=".3"/>'
            f'<path d="{stitch}" fill="url(#t)"/>'
            f'<rect x="{f(-l+1.6)}" y="{f(-h*.45)}" width="{f(LEN-3.2)}" height=".36" rx=".18" fill="#fff" opacity=".6"/></g>'
            # thread casts a soft shadow down; the stitches pull a faint groove into the felt
            '<filter id="d" x="-20%" y="-20%" width="140%" height="140%">'
            '<feGaussianBlur stdDeviation=".1" result="t"/>'
            '<feGaussianBlur in="SourceAlpha" stdDeviation=".45"/><feOffset dy=".5"/>'
            '<feComponentTransfer><feFuncA type="linear" slope=".25"/></feComponentTransfer>'
            '<feMerge><feMergeNode/><feMergeNode in="t"/></feMerge></filter>'
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
        out += [stitch(t, m, 0, k), stitch(w - m, t, 90, k + 5), stitch(w - t, w - m, 180, k + 10), stitch(m, w - t, 270, k + 15)]
    arc = math.pi / 2 * r
    na = max(1, round(arc / PERIOD))
    for j, ((cx, cy), start) in enumerate((((c, c), 180), ((w - c, c), 270), ((w - c, w - c), 0), ((c, w - c), 90))):
        for k in range(na):
            phi = math.radians(start + 90 * (k + .5) / na)
            out.append(stitch(cx + r * math.cos(phi), cy + r * math.sin(phi), math.degrees(phi) + 90, 20 + 3 * j + k,
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
