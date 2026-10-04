#!/usr/bin/env python3
"""Draw the felt textures and seams in img/ as SVG and write the matching seam tokens into felt.css
(between the stitches:start/end markers).

Textures (felt.svg, felt-light.svg, felt-dark.svg): bands of feTurbulence summed on one 256 px tile.
Fibre bands are bent by low noise (feDisplacementMap) to break up the noise's lattice and stretch its ridges
into hairs; all noise is made on the tile and repeated with feTile, so the tile stays seamless.

Seams (seam-lg/md/pill/sq.svg, seam-row.svg, seam-col.svg): drawn stitches as 9-slice images for
border-image, plus a straight row and column. The thread is near-white; felt.css tints it with
mix-blend-mode: hard-light and filter: brightness(). thread.svg is the twist that dyed thread
(.border-{colour} in the felt look) is multiplied with.

Needs: python3. tools/calibrate_felt.py re-measures the textures' bases after a change to FELT.
"""
import math
import random
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "img"
DPR = 2                          # seams are drawn for 2x screens: width/height in device px, viewBox in CSS px

# --- felt
# Felt for the web: fine, dense craft felt (like the sheets sold for crafts and the felt of Stilbag's bags), calm
# at 1x, with single light fibres up close. Photos of real felt were the reference, not a template.
# Band: [frequency, octaves, f(ractal)|t(urbulence), amplitude (negative: bright ridges), mean, bend, blur, gamma,
# (cut frequency, kept share)]. The nap's ridges brighten like fibre tips; a second noise cuts them into single
# fibres (no network of cells); a soft, blurred nap lies under the sharp one. Bases are calibrated so the tile
# has the mean of the photo textures it replaced (calibrate_felt.py); contrast per scale matches them too
# (sd at 3/8 px blur .013/.009).
FELT = {
    # grey around 50 %, soft-light on saturated colours
    "felt": dict(base=0.4857, warp=('.035', 12), bands=[['.012', 2, 'f', 0.08],
                 ['.05', 2, 'f', 0.06],
                 ['.22 .32', 2, 't', -0.26, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.32 .22', 2, 't', -0.26, 0.6, 12, 0.25, 3, ('.3', 0.5)],
                 ['.18', 2, 't', -0.08, 0.5, 10, 1.0, 2.5],
                 ['.7', 1, 'f', 0.15, 0.5, 0, 0.45],
                 ['.12', 2, 't', -0.1, 0.82, 18, 0.12, 6, ('.2', 0.3)]]),
    # cream, multiply on light surfaces: the dark felt's recipe, quieter (fine light hairs over a slightly darker
    # ground); a dense blurred nap or grain here reads as pores, like elephant skin
    "felt-light": dict(base=0.9405, rgb=(1.0084, 1.0, 0.9772), warp=('.035', 12), bands=[['.012', 2, 'f', 0.034],
                 ['.05', 2, 'f', 0.0255],
                 ['.22 .32', 2, 't', -0.0647, 0.6, 5, 0.2, 3, ('.3', 0.5)],
                 ['.32 .22', 2, 't', -0.0647, 0.6, 5, 0.2, 3, ('.3', 0.5)],
                 ['.18', 2, 't', -0.0286, 0.5, 10, 1.0, 2.5],
                 ['.7', 1, 'f', 0.0536, 0.5, 0, 0.45],
                 ['.12', 2, 't', -0.17, 0.82, 14, 0.15, 6, ('.2', 0.25)]]),
    # grey around 50 %, soft-light on charcoal: the colours' felt, a little quieter
    "felt-dark": dict(base=0.4909, warp=('.035', 12), bands=[['.012', 2, 'f', 0.068],
                 ['.05', 2, 'f', 0.051],
                 ['.22 .32', 2, 't', -0.154, 0.6, 5, 0.25, 3, ('.3', 0.5)],
                 ['.32 .22', 2, 't', -0.154, 0.6, 5, 0.25, 3, ('.3', 0.5)],
                 ['.18', 2, 't', -0.068, 0.5, 10, 1.0, 2.5],
                 ['.7', 1, 'f', 0.1275, 0.5, 0, 0.45],
                 ['.12', 2, 't', -0.1, 0.82, 14, 0.15, 6, ('.2', 0.25)]]),
}
TILE, PAD = 256, 32
SUB = f'x="0" y="0" width="{TILE}" height="{TILE}"'
GREY = '<feColorMatrix values="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 1"/>'

# --- seams (CSS px)
# Modelled on professionally sewn felt (Stilbag bags): the thread is pulled taut into a pressed groove, tone on
# tone, evenly spaced; its ends dive under the felt's fibres instead of stopping at a dot.
MARGIN = 3            # slice edge -> thread centre line
LEN, THICK = 7, 1.6   # stitch: about 2/3 of the period
PERIOD = 10           # stitch + gap
# seam radius, stitches per edge tile, groove and lip alpha (small pieces: a fainter groove, so stitch and gap read at 1x)
SHAPES = {"lg": (9, 3, .1, 0), "md": (7, 1, .1, 0), "pill": (17, 1, .1, 0), "sq": (0, 1, .1, 0)}
ROW = 3
# a machine's small irregularities: per stitch length (±4 %), angle (±1°) and offset across the seam (±0.15 px);
# every edge of a frame draws other stitches from the table, so even one-stitch tiles differ round the piece
_r = random.Random(7)
WOBBLE = [(1 + _r.uniform(-.04, .04), _r.uniform(-1, 1), _r.uniform(-.15, .15)) for _ in range(32)]

# twisted ply for dyed thread: diagonal ridges, multiplied into the dye
THREAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="6" height="6" viewBox="0 0 3 3"><rect width="3" height="3" fill="#fff"/>'
          '<path d="M-1 1L1-1M0 3L3 0M2 4L4 2" stroke="#c4c4c4" stroke-width=".75"/></svg>')


def felt(bands, base=.5, rgb=None, seed=1, warp=(".02", 10)):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{TILE}" height="{TILE}">'
         f'<filter id="f" filterUnits="userSpaceOnUse" x="{-PAD}" y="{-PAD}" width="{TILE+2*PAD}" height="{TILE+2*PAD}" color-interpolation-filters="sRGB">'
         f'<feTurbulence {SUB} type="fractalNoise" baseFrequency="{warp[0]}" numOctaves="2" seed="{seed+99}" stitchTiles="stitch"/><feTile result="w"/>'
         f'<feFlood flood-color="rgb({base*255:.1f},{base*255:.1f},{base*255:.1f})" result="a"/>']
    for i, (freq, oct, kind, amp, *opt) in enumerate(bands):
        mean = opt[0] if opt else (.5 if kind == "f" else .25)
        bend = opt[1] if len(opt) > 1 else 0
        blur = opt[2] if len(opt) > 2 else 0
        gamma = opt[3] if len(opt) > 3 else 0
        cut = opt[4] if len(opt) > 4 else None   # (frequency, keep): cut the ridges into single fibres
        # negative amplitude: invert the noise instead (bright ridges); amplitudes stay positive so alpha stays 1
        grey = GREY if amp > 0 else '<feColorMatrix values="-1 0 0 0 1 -1 0 0 0 1 -1 0 0 0 1 0 0 0 0 1"/>'
        if amp < 0: amp, mean = -amp, 1 - mean
        s.append(f'<feTurbulence {SUB} type="{"fractalNoise" if kind == "f" else "turbulence"}" baseFrequency="{freq}" '
                 f'numOctaves="{oct}" seed="{seed + 7 * i}" stitchTiles="stitch"/>{grey}'
                 + (f'<feComponentTransfer><feFuncR type="gamma" exponent="{gamma}"/><feFuncG type="gamma" exponent="{gamma}"/><feFuncB type="gamma" exponent="{gamma}"/></feComponentTransfer>' if gamma else '')
                 + '<feTile result="n"/>')
        if bend:
            s.append(f'<feDisplacementMap in2="w" scale="{bend}" xChannelSelector="R" yChannelSelector="G" in="n" result="n"/>')
        if blur:   # soft fibres: a fuzz, not a hairline
            s.append(f'<feGaussianBlur in="n" stdDeviation="{blur}" result="n"/>')
        if cut:    # keep the band only where a second noise is high: n*m + mean*(1-m), m a soft threshold
            f_, keep = cut
            t = .5 + NormalDist().inv_cdf(1 - keep) * .12          # fractalNoise R: ~N(.5, .12)
            ramp = f'type="linear" slope="10" intercept="{-10 * t:.3g}"'
            s.append(f'<feTurbulence {SUB} type="fractalNoise" baseFrequency="{f_}" numOctaves="1" seed="{seed + 50 + i}" stitchTiles="stitch"/>'
                     f'<feColorMatrix values="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 1"/>'
                     f'<feComponentTransfer><feFuncR {ramp}/><feFuncG {ramp}/><feFuncB {ramp}/></feComponentTransfer>'
                     f'<feTile result="m"/><feComposite in="n" in2="m" operator="arithmetic" k1="1" k3="{-mean:.3g}" k4="{mean:.3g}" result="n"/>')
        s.append(f'<feComposite in="a" in2="n" operator="arithmetic" k2="1" k3="{amp:.4g}" k4="{-amp * mean:.3g}" result="a"/>')
    if rgb:
        s.append(f'<feColorMatrix values="{rgb[0]} 0 0 0 0 0 {rgb[1]} 0 0 0 0 0 {rgb[2]} 0 0 0 0 0 1 0"/>')
    s.append(f'</filter><rect width="{TILE}" height="{TILE}" filter="url(#f)"/></svg>')
    return "".join(s)


def f(x):   # short numbers: one decimal, no trailing or leading zeros
    v = f"{x:.1f}".rstrip("0").rstrip(".")
    return "0" if v in ("", "-0") else v.replace("0.", ".", 1) if v.startswith(("0.", "-0.")) else v


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
            # where the needle went in, the felt dips: a soft dimple, not a dot
            '<radialGradient id="h"><stop offset="0" stop-opacity=".16"/><stop offset="1" stop-opacity="0"/></radialGradient>'
            f'<g id="s"><circle cx="{f(-l+.3)}" r=".9" fill="url(#h)"/><circle cx="{f(l-.3)}" r=".9" fill="url(#h)"/>'
            f'<path d="{stitch}" fill="url(#t)"/>'
            f'<rect x="{f(-l+1.8)}" y="{f(-h*.4)}" width="{f(LEN-3.6)}" height=".34" rx=".17" fill="#fff" opacity=".7"/>'
            '</g>'
            # light from above: a soft shadow below; the light edge on top comes from felt.css's --seam-relief
            # (drawn in here, the seam filter darkens it on cream into a haze over the thread)
            '<filter id="d" x="-20%" y="-30%" width="140%" height="160%">'
            '<feGaussianBlur in="SourceAlpha" stdDeviation=".25"/><feOffset dy=".55"/>'
            '<feComponentTransfer result="s"><feFuncA type="linear" slope=".25"/></feComponentTransfer>'
            '<feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="g"><feGaussianBlur stdDeviation=".7"/></filter>'
            '</defs>')


def stitch(x, y, angle, k=0, scale=1.0):
    lf, da, dy = WOBBLE[k % len(WOBBLE)]
    s = lf * scale
    rad = math.radians(angle)
    x, y = x - dy * math.sin(rad), y + dy * math.cos(rad)
    t = f"translate({f(x)} {f(y)})" + (f" rotate({f(angle + da)})" if f(angle + da) != "0" else "") + (f" scale({f(s)} 1)" if f(s) != "1" else "")
    return f'<use href="#s" transform="{t}"/>'


def svg(w, h, groove, stitches, ga=.14, la=.05):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{round(w * DPR)}" height="{round(h * DPR)}" viewBox="0 0 {f(w)} {f(h)}">{defs()}'
            + (f'<path d="{groove}" fill="none" stroke="#fff" stroke-opacity="{str(la).lstrip("0")}" stroke-width="3.4" filter="url(#g)"/>' if la else '')
            + f'<path d="{groove}" fill="none" stroke="#000" stroke-opacity="{str(ga).lstrip("0")}" stroke-width="2" filter="url(#g)"/>'
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
    body = "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts_o + pts_i[::-1]) + "Z"
    hl = "M" + "L".join(f"{f(x)} {f(y)}" for x, y in mid)
    ends = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r=".9" fill="url(#h)"/>' for x, y in (pts_o[0], pts_o[-1]))
    return (f'{ends}<path d="{body}" fill="url(#t)"/>'
            f'<path d="{hl}" fill="none" stroke="#fff" stroke-width=".32" stroke-linecap="round" opacity=".6"/>')


def frame(radius, n, ga, la):
    """A 9-slice seam frame: slice and border-image width are the margin plus the radius."""
    m, r = MARGIN, radius
    c = m + r
    w = 2 * c + n * PERIOD
    out = []
    for k in range(n):
        t = c + (k + .5) * PERIOD
        out += [stitch(t, m, 0, k), stitch(w - m, t, 90, k + 5), stitch(w - t, w - m, 180, k + 10), stitch(m, w - t, 270, k + 15)]
    arc = math.pi / 2 * r
    na = max(1, round(arc / PERIOD * 1.3)) if r else 0   # a card's corner takes two shorter stitches, so it reads as a curve
    for j, ((cx, cy), start) in enumerate((((c, c), 180), ((w - c, c), 270), ((w - c, w - c), 0), ((c, w - c), 90))):
        for k in range(na):
            phi = math.radians(start + 90 * (k + .5) / na)
            out.append(arc_stitch(cx, cy, r, phi, LEN * min(1.0, arc / na / PERIOD), 20 + 3 * j + k))
    if r:
        groove = f"M{f(m)} {f(c)}A{f(r)} {f(r)} 0 0 1 {f(c)} {f(m)}H{f(w-c)}A{f(r)} {f(r)} 0 0 1 {f(w-m)} {f(c)}V{f(w-c)}A{f(r)} {f(r)} 0 0 1 {f(w-c)} {f(w-m)}H{f(c)}A{f(r)} {f(r)} 0 0 1 {f(m)} {f(w-c)}Z"
    else:   # square corners: the stitches stop short of the corner, the groove turns sharply
        groove = f"M{f(m)} {f(m)}H{f(w-m)}V{f(w-m)}H{f(m)}Z"
    return svg(w, w, groove, out, ga, la), c


def row(vertical=False):
    h, length = 2 * MARGIN, ROW * PERIOD
    if vertical:
        st = [stitch(MARGIN, (k + .5) * PERIOD, 90, k) for k in range(ROW)]
        return svg(h, length, f"M{MARGIN} -10V{length + 10}", st)
    st = [stitch((k + .5) * PERIOD, MARGIN, 0, k) for k in range(ROW)]
    return svg(length, h, f"M-10 {MARGIN}H{length + 10}", st)


def write_tokens(lines):
    css = ROOT / "felt.css"
    text = css.read_text()
    start, end = "/* stitches:start */", "/* stitches:end */"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    css.write_text(head + start + "\n" + "\n".join(lines) + "\n    " + end + tail)


def write(name, text):
    (OUT / name).write_text(text)
    print(f"{name}: {len(text)} bytes")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, kw in FELT.items():
        write(f"{name}.svg", felt(**kw))
    tokens = [f"    --seam-margin: {MARGIN}px;"]
    for name, (r, n, ga, la) in SHAPES.items():
        s, c = frame(r, n, ga, la)
        write(f"seam-{name}.svg", s)
        tokens.append(f"    --seam-{name}-slice: {c * DPR:g}; --seam-{name}-width: {c:g}px;")
    write("seam-row.svg", row())
    write("seam-col.svg", row(True))
    write("thread.svg", THREAD)
    length = ROW * PERIOD
    tokens.append(f"    --seam-row-size: {length}px {2 * MARGIN}px;")
    # .vr: stitches 4/5 as long as the row's, so a rule only 1em tall still shows two whole ones
    tokens.append(f"    --seam-col-size: {2 * MARGIN}px {length * .8:g}px;")
    write_tokens(tokens)
