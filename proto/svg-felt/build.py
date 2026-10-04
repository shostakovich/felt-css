#!/usr/bin/env python3
"""Prototype: felt textures and seams as SVG instead of photo WebPs.

Writes img/*.svg and felt.css (a copy of ../../felt.css with img/*.webp -> img/*.svg), so every
component renders exactly as in the library, only the assets differ. Seams keep the WebPs' 9-slice
geometry (same --seam-*-slice tokens): SVG width/height are device px at 2x, viewBox is CSS px.
"""
import math, random, re
import borders
from pathlib import Path
from feltgen import felt

HERE = Path(__file__).resolve().parent
OUT = HERE / "img"
DPR = 2

# --- felt: noise bands (see feltgen.py)
FELT = {
    # Felt for the web: fine, dense craft felt (like the sheets sold for crafts and the felt of Stilbag's bags), calm
    # at 1x, with single light fibres up close. Photos of real felt were the reference, not a template.
    # Band: [frequency, octaves, f(ractal)|t(urbulence), amplitude (negative: bright ridges), mean, bend, blur, gamma,
    # (cut frequency, kept share)]. The nap's ridges brighten like fibre tips; a second noise cuts them into single
    # fibres (no network of cells); a soft, blurred nap lies under the sharp one. Bases are calibrated so the tile
    # has the photos' mean (calibrate.py); contrast per scale matches the old photo (sd at 3/8 px blur .013/.009).
    # grey around 50 %, soft-light on saturated colours
    "felt": dict(base=0.4857, warp=('.035', 12), bands=[['.012', 2, 'f', 0.08],
                 ['.05', 2, 'f', 0.06],
                 ['.22 .32', 2, 't', -0.26, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.32 .22', 2, 't', -0.26, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.18', 2, 't', -0.08, 0.5, 10, 1.0, 2.5],
                 ['.7', 1, 'f', 0.15, 0.5, 0, 0.45],
                 ['.12', 2, 't', -0.1, 0.82, 18, 0.12, 6, ('.2', 0.3)]]),
    # cream, multiply on light surfaces: mean colour of felt-light.webp (dE < 1), a fine blurred fluff, clouds under
    # ±1.5 %, no dark specks, no stray hairs
    "felt-light": dict(base=0.9427, rgb=(1.0084, 1.0, 0.9772), warp=('.035', 12), bands=[['.008', 2, 'f', 0.06],
                 ['.02', 2, 'f', 0.04],
                 ['.22 .32', 2, 't', -0.12, 0.6, 12, 0.6, 3, ('.3', 0.55)],
                 ['.32 .22', 2, 't', -0.12, 0.6, 12, 0.6, 3, ('.3', 0.55)],
                 ['.7', 1, 'f', 0.06, 0.5, 0, 0.6]]),
    # grey around 50 %, soft-light on charcoal: the colours' felt, a little quieter
    "felt-dark": dict(base=0.4909, warp=('.035', 12), bands=[['.012', 2, 'f', 0.068],
                 ['.05', 2, 'f', 0.051],
                 ['.22 .32', 2, 't', -0.221, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.32 .22', 2, 't', -0.221, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.18', 2, 't', -0.068, 0.5, 10, 1.0, 2.5],
                 ['.7', 1, 'f', 0.1275, 0.5, 0, 0.45],
                 ['.12', 2, 't', -0.085, 0.82, 18, 0.12, 6, ('.2', 0.3)]]),
}

# --- seams (CSS px)
# Modelled on professionally sewn felt (Stilbag bags): the thread is pulled taut into a pressed groove, tone on
# tone, evenly spaced; its ends dive under the felt's fibres instead of stopping at a dot.
MARGIN = 3            # slice edge -> thread centre line
LEN, THICK = 7, 1.6  # stitch: about 2/3 of the period
PERIOD = 10           # stitch + gap
SHAPES = {"lg": (9, 3), "md": (7, 1), "pill": (17, 1)}   # seam radius, stitches per edge tile
ROW = 3
# a machine's small irregularities: per stitch length (±4 %), angle (±1°) and offset across the seam (±0.15 px);
# every edge of a frame draws other stitches from the table, so even one-stitch tiles differ round the piece
_r = random.Random(7)
WOBBLE = [(1 + _r.uniform(-.04, .04), _r.uniform(-1, 1), _r.uniform(-.15, .15)) for _ in range(32)]

def f(x): return f"{x:.2f}".rstrip("0").rstrip(".")

def defs():
    h, l = THICK / 2, LEN / 2
    # one stitch along x: a taut body that narrows where it enters the felt
    stitch = (f'M{f(-l)} 0C{f(-l+.8)} {f(-h)} {f(-l+1.6)} {f(-h)} {f(-l+2.4)} {f(-h)}H{f(l-2.4)}'
              f'C{f(l-1.6)} {f(-h)} {f(l-.8)} {f(-h)} {f(l)} 0C{f(l-.8)} {f(h)} {f(l-1.6)} {f(h)} {f(l-2.4)} {f(h)}'
              f'H{f(-l+2.4)}C{f(-l+1.6)} {f(h)} {f(-l+.8)} {f(h)} {f(-l)} 0Z')
    return ('<defs>'
            # twisted ply: soft diagonal ridges at ~32° to the thread
            '<pattern id="t" width="1.25" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-58)">'
            '<rect width="1.25" height="4" fill="#fafafa"/><rect width=".5" height="4" fill="#e6e6e6"/></pattern>'
            # the ends fade into the felt over ~0.6 px
            '<linearGradient id="e"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".09" stop-color="#fff"/>'
            '<stop offset=".91" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<mask id="m" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#e)"/></mask>'
            # where the needle went in, the felt dips: a soft dimple, not a dot
            '<radialGradient id="h"><stop offset="0" stop-opacity=".16"/><stop offset="1" stop-opacity="0"/></radialGradient>'
            f'<g id="s"><circle cx="{f(-l+.3)}" r=".9" fill="url(#h)"/><circle cx="{f(l-.3)}" r=".9" fill="url(#h)"/>'
            f'<path d="{stitch}" fill="url(#t)" mask="url(#m)"/>'
            f'<rect x="{f(-l+1.8)}" y="{f(-h*.4)}" width="{f(LEN-3.6)}" height=".34" rx=".17" fill="#fff" opacity=".7"/>'
            '</g>'
            # light from above: a soft shadow below only, a faint light edge on top
            '<filter id="d" x="-20%" y="-30%" width="140%" height="160%">'
            '<feGaussianBlur in="SourceAlpha" stdDeviation=".3"/><feOffset dy=".6"/>'
            '<feComponentTransfer result="s"><feFuncA type="linear" slope=".25"/></feComponentTransfer>'
            '<feFlood flood-color="#fff" flood-opacity=".22"/><feComposite in2="SourceAlpha" operator="in"/><feOffset dy="-.35"/>'
            '<feMerge><feMergeNode in="s"/><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="g"><feGaussianBlur stdDeviation=".7"/></filter>'
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
            f'<path d="{groove}" fill="none" stroke="#fff" stroke-opacity=".05" stroke-width="3.4" filter="url(#g)"/>'
            f'<path d="{groove}" fill="none" stroke="#000" stroke-opacity=".14" stroke-width="2" filter="url(#g)"/>'
            f'<g filter="url(#d)">{"".join(stitches)}</g></svg>')

def arc_stitch(cx, cy, r, phi, length, k=0):
    """A stitch bent along the corner's arc (centre angle phi, arc length `length`), so a curve stays a curve."""
    lf = WOBBLE[k % len(WOBBLE)][0]
    span = length * lf / r
    h, n = THICK / 2, 6
    pts_o, pts_i, mid = [], [], []
    for i in range(n + 1):
        t = i / n
        a = phi - span / 2 + span * t
        p = min(1.0, 1.15 * math.sin(math.pi * t) ** .5)       # plump body, ends taper into the felt
        pts_o.append((cx + (r + h * p) * math.cos(a), cy + (r + h * p) * math.sin(a)))
        pts_i.append((cx + (r - h * p) * math.cos(a), cy + (r - h * p) * math.sin(a)))
        if .22 <= t <= .78: mid.append((cx + (r - h * .3) * math.cos(a), cy + (r - h * .3) * math.sin(a)))
    g = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    body = "M" + "L".join(f"{g(x)} {g(y)}" for x, y in pts_o + pts_i[::-1]) + "Z"
    hl = "M" + "L".join(f"{g(x)} {g(y)}" for x, y in mid)
    ends = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r=".9" fill="url(#h)"/>' for x, y in (pts_o[0], pts_o[-1]))
    return (f'{ends}<path d="{body}" fill="url(#t)"/>'
            f'<path d="{hl}" fill="none" stroke="#fff" stroke-width=".32" stroke-linecap="round" opacity=".6"/>')

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
            out.append(arc_stitch(cx, cy, r, phi, LEN * min(1.0, arc / na / PERIOD), 20 + 3 * j + k))
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
    (OUT / "thread.svg").write_text(borders.THREAD)
    (HERE / "felt.css").write_text(css + borders.css())
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size} B")
