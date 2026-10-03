#!/usr/bin/env python3
"""Build all felt assets in img/ from the Codex-generated photos in raw/ and write the
matching tokens into felt.css (between the stitches:start/end markers).

Textures (Codex-generated seamless felt photos):
  felt.webp        from raw/felt-neutral.png (grey felt): mean 50 % grey, soft-light on saturated colours
  felt-light.webp  from raw/cream-a.png (cream felt): warm ~94 % with fine fibres, multiply on light colours
  felt-dark.webp   from raw/cream-a.png as well: the fibres around 50 % grey, soft-light on charcoal (dark mode)

Seams (from raw/stitch-b.png, a white running stitch on grey felt):
  Single stitches are cut out, reduced to the thread alone (no shadow, no needle holes) and laid
  along rounded rectangles as 9-slice images for border-image, plus a straight row. Long seams
  (cards, dividers) alternate three different stitches with a little hand-sewn wobble, so the
  thread doesn't read as printed; short seams (buttons) keep one stitch per tile, because
  border-image `round` would squash a longer tile on a short edge. The
  thread is near-white; CSS tints it with mix-blend-mode: hard-light and filter: brightness()
  (light thread on coloured felt, a darker tone of the same felt on light surfaces).

Needs: python3 + numpy, ImageMagick (`magick`).
"""
import math
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "img"
DPR = 2                          # assets are rendered for 2x screens

# measured in raw/stitch-b.png (1024 px): top seam line y 53..70; stitches (x from..to) on its straight part
STITCHES = [(443, 511), (257, 324), (623, 684)]   # the first is the one used for single-stitch tiles
STITCH_Y, STITCH_H, STITCH_PAD = 48, 28, 7
WOBBLE = [(0, 0), (-2.5, 0.25), (2.0, -0.2)]   # per stitch: angle in degrees, offset across the seam in CSS px
STITCH_SRC = 70                  # visible stitch length in source px (nominal)
STITCH_CSS = 6.5                 # visible stitch length in CSS px
GAP_CSS = 4
THIN = 0.85                      # squash thread thickness (18 src px -> ~1.4 CSS px)
S = STITCH_SRC / STITCH_CSS      # source px per CSS px
PERIOD = (STITCH_CSS + GAP_CSS) * S
MARGIN_CSS = 3                   # slice edge -> thread centre line
SHAPES = {"lg": (9, 3), "md": (7, 1), "pill": (17, 1)}   # seam corner radius in CSS px, stitches per edge tile
ROW_STITCHES = 3


def magick(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def textures():
    src = RAW / "felt-neutral.png"
    mean = float(subprocess.run(["magick", src, "-colorspace", "Gray", "-format", "%[fx:mean]", "info:"],
                                check=True, capture_output=True, text=True).stdout)
    out = OUT / "felt.webp"
    magick(src, "-colorspace", "Gray", "-fx", f"(u-{mean})*1.5+0.5", "-resize", "256x256",
           "-define", "webp:method=6", "-quality", "62", out)
    print(f"{out.name}: {os.path.getsize(out)} bytes")
    # light felt: a photo of cream felt, reduced to its fibre structure around a warm ~94 %
    light_felt(RAW / "cream-a.png", OUT / "felt-light.webp")
    # dark felt: the same cream fibres around 50 % grey, soft-light on charcoal surfaces
    dark_felt(RAW / "cream-a.png", OUT / "felt-dark.webp")


def read_rgb(src, size=1024):
    with tempfile.TemporaryDirectory() as t:
        raw = Path(t) / "c.rgb"
        magick(src, "-endian", "MSB", "-depth", "16", f"rgb:{raw}")
        return np.fromfile(raw, dtype=">u2").reshape(size, size, 3).astype(float) / 65535


def light_felt(src, out, tile=512):
    rgb = read_rgb(src)
    ratio = rgb / rgb.mean(axis=(0, 1))                 # fibre structure, neutral on average
    gain = 0.029 / (ratio.mean(-1).std())               # ~1.3 % fibre variation after downscaling
    base = np.array([0.955, 0.945, 0.925])              # slightly warm, so multiply never greys
    out_rgb = np.clip(base * (1 + gain * (ratio - 1)), 0, 1)
    with tempfile.TemporaryDirectory() as t:
        raw = Path(t) / "t.rgb"
        (out_rgb * 65535).round().astype(">u2").tofile(raw)
        magick("-size", "1024x1024", "-endian", "MSB", "-depth", "16", f"rgb:{raw}", "-resize", f"{tile}x{tile}",
               "-define", "webp:method=6", "-quality", "70", out)
    print(f"{out.name}: {os.path.getsize(out)} bytes")


def dark_felt(src, out, tile=256):
    rgb = read_rgb(src)
    ratio = (rgb / rgb.mean(axis=(0, 1))).mean(-1)
    grey = np.clip(0.5 + 0.051 * (ratio - 1) / ratio.std(), 0, 1)
    with tempfile.TemporaryDirectory() as t:
        raw = Path(t) / "t.gray"
        (grey * 65535).round().astype(">u2").tofile(raw)
        magick("-size", "1024x1024", "-endian", "MSB", "-depth", "16", f"gray:{raw}", "-resize", f"{tile}x{tile}",
               "-define", "webp:method=6", "-quality", "60", out)
    print(f"{out.name}: {os.path.getsize(out)} bytes")


def make_sprites(tmp):
    return [make_sprite(tmp, i, x0, x1) for i, (x0, x1) in enumerate(STITCHES)]


def make_sprite(tmp, i, x0, x1):
    c = dict(x=x0 - STITCH_PAD, y=STITCH_Y, w=x1 - x0 + 2 * STITCH_PAD, h=STITCH_H)
    raw = tmp / f"sprite{i}.gray"
    magick(RAW / "stitch-b.png", "-crop", f"{c['w']}x{c['h']}+{c['x']}+{c['y']}", "+repage",
           "-colorspace", "Gray", "-depth", "8", f"gray:{raw}")
    g = np.fromfile(raw, dtype=np.uint8).reshape(c["h"], c["w"]).astype(float) / 255
    felt = np.median(np.concatenate([g[:3].ravel(), g[-3:].ravel()]))
    d = g - felt
    # keep only the thread: brighter than the felt by more than the fibre noise
    alpha = np.clip((d - 0.06) / 0.10, 0, 1)
    thread = g[alpha > 0.8].mean()
    grey = np.clip(0.96 + 0.5 * (g - thread), 0, 1)   # near-white, twist at half contrast
    rgba = np.stack([grey, grey, grey, alpha], -1)
    out = tmp / f"sprite{i}.rgba"
    (rgba * 255).round().astype(np.uint8).tofile(out)
    png = tmp / f"sprite{i}.png"
    magick("-size", f"{c['w']}x{c['h']}", "-depth", "8", f"rgba:{out}", png)
    return dict(png=png, w=c["w"], h=c["h"], length=x1 - x0)


def place(sprite, x, y, angle, stretch=1.0):
    cx, cy = sprite["w"] / 2, sprite["h"] / 2
    return ["(", sprite["png"], "-virtual-pixel", "transparent", "+distort", "SRT",
            f"{cx},{cy} {stretch},{THIN} {angle} {x:.2f},{y:.2f}", ")"]


def run_of(sprites, n):
    """n stitches in a row: (sprite, centre along the run, angle wobble, offset across), and the run's length.
    Each stitch keeps its own length; the gaps are equal, half a gap at either end of the run."""
    gap, at, out = PERIOD - STITCH_SRC, 0.0, []
    for k in range(n):
        sp = sprites[k % len(sprites)]
        da, dy = WOBBLE[k % len(WOBBLE)] if n > 1 else (0, 0)
        out.append((sp, at + gap / 2 + sp["length"] / 2, da, dy * S))
        at += sp["length"] + gap
    return out, at


SHADOW = dict(dy=0.7, blur=0.35, alpha=0.3)   # soft drop shadow under the thread, CSS px
GROOVE = dict(width=1.6, blur=0.8, alpha=0.12)  # the stitches pull the felt in a little, CSS px


def render(layers, w, h, out, size, groove=None):
    shadow = ["(", "+clone", "-fill", "black", "-colorize", "100",
              "-channel", "A", "-blur", f"0x{SHADOW['blur'] * S:.1f}",
              "-evaluate", "multiply", str(SHADOW["alpha"]), "+channel",
              "-roll", f"+0+{round(SHADOW['dy'] * S)}", ")", "+swap"]
    dent = []
    if groove:
        dent = ["(", "-size", f"{math.ceil(w)}x{math.ceil(h)}", "xc:none", "-fill", "none",
                "-stroke", f"rgba(0,0,0,{GROOVE['alpha']})", "-strokewidth", f"{GROOVE['width'] * S:.1f}",
                "-draw", groove, "-blur", f"0x{GROOVE['blur'] * S:.1f}", ")", "+swap"]
    magick("-size", f"{math.ceil(w)}x{math.ceil(h)}", "xc:none", *layers,
           "-background", "none", "-layers", "flatten", *shadow, "-flatten", *dent, "-flatten",
           "-resize", f"{size[0]}x{size[1]}!", "-define", "webp:lossless=true", out)


def frame(sprites, radius_css, name, stitches):
    m, r, p = MARGIN_CSS * S, radius_css * S, PERIOD
    c = m + r                     # corner slice size
    run, length = run_of(sprites, stitches)
    w = 2 * c + length            # one edge tile between the corners
    layers = []
    # straight edges, clockwise so the twist runs the same way all round
    for sp, t, da, dy in run:
        layers += place(sp, c + t, m + dy, da)
        layers += place(sp, w - m - dy, c + t, 90 + da)
        layers += place(sp, w - c - t, w - m - dy, 180 + da)
        layers += place(sp, m + dy, w - c - t, 270 + da)
    # corners: quarter arcs, stitches spread evenly, slice edges fall in the middle of a gap
    arc = math.pi / 2 * r
    n = max(1, round(arc / p))
    for j, ((cx, cy), start) in enumerate((((c, c), 180), ((w - c, c), 270), ((w - c, w - c), 0), ((c, w - c), 90))):
        for k in range(n):
            phi = math.radians(start + 90 * (k + 0.5) / n)
            sp = sprites[(j + k) % stitches]
            layers += place(sp, cx + r * math.cos(phi), cy + r * math.sin(phi),
                            math.degrees(phi) + 90, min(1.0, arc / n / p))
    size = round(w * DPR / S)
    out = OUT / f"seam-{name}.webp"
    render(layers, w, w, out, (size, size),
           groove=f"roundrectangle {m:.1f},{m:.1f} {w - m:.1f},{w - m:.1f} {r:.1f},{r:.1f}")
    slice_dev = round(c * DPR / S)
    print(f"{out.name}: {os.path.getsize(out)} bytes")
    return f"    --seam-{name}-slice: {slice_dev}; --seam-{name}-width: {slice_dev / DPR:g}px;"


def row(sprites):
    h = MARGIN_CSS * 2 * S
    run, length = run_of(sprites, ROW_STITCHES)
    layers = []
    for sp, t, da, dy in run:
        layers += place(sp, t, h / 2 + dy, da)
    out = OUT / "seam-row.webp"
    size = (round(length * DPR / S), round(h * DPR / S))
    render(layers, length, h, out, size, groove=f"line -10,{h / 2:.1f} {length + 10:.1f},{h / 2:.1f}")
    print(f"{out.name}: {os.path.getsize(out)} bytes")
    return f"    --seam-row-size: {size[0] / DPR:g}px {MARGIN_CSS * 2}px;"


def write_tokens(lines):
    css = ROOT / "felt.css"
    text = css.read_text()
    start, end = "/* stitches:start */", "/* stitches:end */"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    css.write_text(head + start + "\n" + "\n".join(lines) + "\n    " + end + tail)


textures()
with tempfile.TemporaryDirectory() as t:
    sprites = make_sprites(Path(t))
    tokens = [f"    --seam-margin: {MARGIN_CSS}px;"]
    tokens += [frame(sprites, radius, name, n) for name, (radius, n) in SHAPES.items()]
    tokens.append(row(sprites))
    write_tokens(tokens)
