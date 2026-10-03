#!/usr/bin/env python3
"""Build all felt assets in img/ from the Codex-generated photos in raw/ and write the
matching tokens into felt.css (between the stitches:start/end markers).

Textures (Codex-generated seamless felt photos):
  felt.webp        from raw/felt-neutral.png (grey felt): mean 50 % grey, soft-light on saturated colours
  felt-light.webp  from raw/cream-a.png (cream felt): warm ~94 % with fine fibres, multiply on light colours

Seams (from raw/stitch-b.png, a white running stitch on grey felt):
  One stitch is cut out, reduced to the thread alone (no shadow, no needle holes) and laid
  along rounded rectangles as 9-slice images for border-image, plus a straight row. The
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

# measured in raw/stitch-b.png (1024 px): top seam line y 53..70, one stitch at x 441..511
STITCH_CROP = dict(x=434, y=48, w=84, h=28)
STITCH_SRC = 70                  # visible stitch length in source px
STITCH_CSS = 6.5                 # visible stitch length in CSS px
GAP_CSS = 4
THIN = 0.85                      # squash thread thickness (18 src px -> ~1.4 CSS px)
S = STITCH_SRC / STITCH_CSS      # source px per CSS px
PERIOD = (STITCH_CSS + GAP_CSS) * S
MARGIN_CSS = 3                   # slice edge -> thread centre line
SHAPES = {"lg": 9, "md": 7, "pill": 17}   # seam corner radius in CSS px


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


def make_sprite(tmp):
    c = STITCH_CROP
    raw = tmp / "sprite.gray"
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
    out = tmp / "sprite.rgba"
    (rgba * 255).round().astype(np.uint8).tofile(out)
    png = tmp / "sprite.png"
    magick("-size", f"{c['w']}x{c['h']}", "-depth", "8", f"rgba:{out}", png)
    return png


def place(sprite, x, y, angle, stretch=1.0):
    cx, cy = STITCH_CROP["w"] / 2, STITCH_CROP["h"] / 2
    return ["(", sprite, "-virtual-pixel", "transparent", "+distort", "SRT",
            f"{cx},{cy} {stretch},{THIN} {angle} {x:.2f},{y:.2f}", ")"]


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


def frame(sprite, radius_css, name):
    m, r, p = MARGIN_CSS * S, radius_css * S, PERIOD
    c = m + r                     # corner slice size
    w = 2 * c + p                 # one edge tile between the corners
    layers = []
    # straight edges, clockwise so the twist runs the same way all round
    layers += place(sprite, w / 2, m, 0)
    layers += place(sprite, w - m, w / 2, 90)
    layers += place(sprite, w / 2, w - m, 180)
    layers += place(sprite, m, w / 2, 270)
    # corners: quarter arcs, stitches spread evenly, slice edges fall in the middle of a gap
    arc = math.pi / 2 * r
    n = max(1, round(arc / p))
    for (cx, cy), start in (((c, c), 180), ((w - c, c), 270), ((w - c, w - c), 0), ((c, w - c), 90)):
        for k in range(n):
            phi = math.radians(start + 90 * (k + 0.5) / n)
            layers += place(sprite, cx + r * math.cos(phi), cy + r * math.sin(phi),
                            math.degrees(phi) + 90, min(1.0, arc / n / p))
    size = round(w * DPR / S)
    out = OUT / f"seam-{name}.webp"
    render(layers, w, w, out, (size, size),
           groove=f"roundrectangle {m:.1f},{m:.1f} {w - m:.1f},{w - m:.1f} {r:.1f},{r:.1f}")
    slice_dev = round(c * DPR / S)
    print(f"{out.name}: {os.path.getsize(out)} bytes")
    return f"    --seam-{name}-slice: {slice_dev}; --seam-{name}-width: {slice_dev / DPR:g}px;"


def row(sprite):
    h = MARGIN_CSS * 2 * S
    out = OUT / "seam-row.webp"
    render(place(sprite, PERIOD / 2, h / 2, 0), PERIOD, h, out,
           (round(PERIOD * DPR / S), round(h * DPR / S)), groove=f"line -10,{h / 2:.1f} {PERIOD + 10:.1f},{h / 2:.1f}")
    print(f"{out.name}: {os.path.getsize(out)} bytes")
    return f"    --seam-row-size: {PERIOD / S:g}px {MARGIN_CSS * 2}px;"


def write_tokens(lines):
    css = ROOT / "felt.css"
    text = css.read_text()
    start, end = "/* stitches:start */", "/* stitches:end */"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    css.write_text(head + start + "\n" + "\n".join(lines) + "\n    " + end + tail)


textures()
with tempfile.TemporaryDirectory() as t:
    sprite = make_sprite(Path(t))
    tokens = [f"    --seam-margin: {MARGIN_CSS}px;"]
    tokens += [frame(sprite, radius, name) for name, radius in SHAPES.items()]
    tokens.append(row(sprite))
    write_tokens(tokens)
