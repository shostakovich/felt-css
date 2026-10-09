"""Contrast of the token pairs felt.css puts text and marks on, in all four modes, against what is rendered.

A flat token is not what the eye sees in the felt look: the page and every light piece are multiplied with the cream
felt photo, grooves lay a translucent shade over that, and patches swell into a lighter dome. So each pair names the
place it sits on, and the background is composed the way felt.css composes it:

  page      --felt-body-bg, cut from the sheet
  surface   --felt-surface (cards, list groups), cut from the sheet
  groove    --felt-groove-bg pressed into the page (felt), the page itself in clean
  alert     an alert's tint (feltgen/variants.py; in felt the alert recipe of felt.css), cut from the sheet
  fill      a tone's fill; in felt a patch under the light of its dome
  field     --felt-field (inputs, selects), cut from the sheet

Colours are resolved from tools/feltgen/tokens.py: hex, rgb(), light-dark(), color-mix() in oklab or srgb, $tokens.
"""
import math
import re

from .config import COLOURS, TONED
from .tokens import BY_NAME
from .variants import ALERT

MODES = ("clean light", "clean dark", "felt light", "felt dark")

# mean colour of img/felt-light.webp, multiplied into light felt in light mode; measure it again if the photo changes.
# Dark mode blends the grey charcoal felt in soft-light, which leaves the mean where it is.
SHEET_LIGHT = (243.4, 241.3, 235.7)
# how much of the patch dome's white (--felt-patch-dome, .2 at its peak) lies under a label in the middle of a patch
DOME_UNDER_TEXT = .1

# the felt look's alert tints (felt.css, "alerts: a large tinted piece"): more of the tone than clean's
FELT_ALERT = {c: f"color-mix(in oklab, ${c} 20%, $surface)" for c in TONED} | {
    "secondary": "color-mix(in oklab, $secondary 14%, $surface)",
    "light": "light-dark(color-mix(in oklab, $secondary-color 6%, $surface), color-mix(in oklab, $body-color 6%, $surface-raised))",
    "dark": "light-dark(color-mix(in oklab, $dark 26%, $surface), color-mix(in oklab, $dark 55%, $surface))",
}

TEXT, NON_TEXT = 4.5, 3


def pairs():
    """(what, foreground token, place, minimum ratio)"""
    out = []
    for place in ("page", "surface"):
        for fg in ["body-color", "secondary-color", "link-color"] + [f"{c}-text" for c in TONED]:
            out.append((f"{fg} on the {place}", fg, place, TEXT))
    for fg in ["body-color"] + [f"{c}-emphasis" for c in COLOURS]:   # pagination, outline buttons in toggle groups
        out.append((f"{fg} in a groove", fg, "groove", TEXT))
    for c in COLOURS:
        out.append((f"alert-{c}", ALERT[c]["alert-color"][1:], f"alert:{c}", TEXT))
        out.append((f"{c}-ink on the {c} fill", f"{c}-ink", f"fill:{c}", TEXT))
    out.append(("focus-ring-color on the page", "focus-ring-color", "page", NON_TEXT))
    out.append(("border-color-strong on a field", "border-color-strong", "field", NON_TEXT))
    return out


# ------------------------------------------------------------------ resolving tokens

def split_args(s):
    depth, start, out = 0, 0, []
    for i, ch in enumerate(s):
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            out.append(s[start:i].strip())
            start = i + 1
    return out + [s[start:].strip()]


def value(name, mode):
    token = BY_NAME[name]
    v = token.values()[mode]
    if v is None:
        raise KeyError(f"{name} has no value in {MODES[mode]}")
    return colour(v, mode)


def colour(v, mode):
    """An (r, g, b, a) in 0–255 (alpha 0–1)."""
    v = v.strip()
    if v.startswith("$"):
        return value(v[1:], mode)
    if v == "transparent":
        return (0, 0, 0, 0)
    if v.startswith("#"):
        h = v[1:]
        h = "".join(c * 2 for c in h) if len(h) in (3, 4) else h
        rgba = [int(h[i:i + 2], 16) for i in range(0, len(h), 2)]
        return (*rgba[:3], rgba[3] / 255 if len(rgba) == 4 else 1)
    m = re.fullmatch(r"rgba?\((.*)\)", v)
    if m:
        parts = re.split(r"[\s,/]+", m[1].strip())
        a = parts[3] if len(parts) > 3 else "1"
        return (*map(float, parts[:3]), float(a[:-1]) / 100 if a.endswith("%") else float(a))
    m = re.fullmatch(r"light-dark\((.*)\)", v)
    if m:
        light, dark = split_args(m[1])
        return colour(light if mode in (0, 2) else dark, mode)
    m = re.fullmatch(r"color-mix\(in (oklab|srgb), (.*)\)", v)
    if m:
        a, b = (re.fullmatch(r"(.*?)(?:\s+([\d.]+)%)?", part).groups() for part in split_args(m[2]))
        pa = float(a[1]) / 100 if a[1] else (1 - float(b[1]) / 100 if b[1] else .5)
        return mix(colour(a[0], mode), colour(b[0], mode), pa, m[1])
    raise ValueError(f"can't resolve {v!r}")


def lin(c):
    c /= 255
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def gamma(c):
    c = c * 12.92 if c <= .0031308 else 1.055 * c ** (1 / 2.4) - .055
    return min(255, max(0, c * 255))


def oklab(rgb):
    r, g, b = map(lin, rgb)
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (
        .4122214708 * r + .5363325363 * g + .0514459929 * b,
        .2119034982 * r + .6806995451 * g + .1073969566 * b,
        .0883024619 * r + .2817188376 * g + .6299787005 * b))
    return (.2104542553 * l + .7936177850 * m - .0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + .4505937099 * s,
            .0259040371 * l + .7827717662 * m - .8086757660 * s)


def from_oklab(lab):
    L, a, b = lab
    l, m, s = (x ** 3 for x in (L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b,
                                L - .0894841775 * a - 1.2914855480 * b))
    return tuple(gamma(x) for x in (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
                                    -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                                    -.0041960863 * l - .7034186147 * m + 1.7076147010 * s))


def mix(a, b, pa, space):
    """color-mix() with premultiplied alpha, as browsers do it."""
    alpha = a[3] * pa + b[3] * (1 - pa)
    if alpha == 0:
        return (0, 0, 0, 0)
    conv, back = (oklab, from_oklab) if space == "oklab" else ((lambda c: c), (lambda c: c))
    ca, cb = conv(a[:3]), conv(b[:3])
    mixed = [(x * a[3] * pa + y * b[3] * (1 - pa)) / alpha for x, y in zip(ca, cb)]
    return (*back(mixed), alpha)


def over(fg, bg):
    a = fg[3]
    return tuple(f * a + b * (1 - a) for f, b in zip(fg[:3], bg[:3])) + (1,)


def sheet(c, mode):
    return tuple(x * s / 255 for x, s in zip(c[:3], SHEET_LIGHT)) + (1,) if mode == 2 else c


def background(place, mode):
    felt = mode >= 2
    if place in ("page", "surface", "field"):
        return sheet(value({"page": "body-bg", "surface": "surface", "field": "field"}[place], mode), mode)
    if place == "groove":
        page = background("page", mode)
        return over(value("groove-bg", mode), page) if felt else page
    kind, c = place.split(":")
    if kind == "alert":
        return sheet(colour(FELT_ALERT[c] if felt else ALERT[c]["alert-bg"], mode), mode)
    fill = value(c, mode)
    if c == "light":                      # the light piece is cut from the sheet, not a patch
        return sheet(fill, mode)
    return over((255, 255, 255, DOME_UNDER_TEXT), fill) if felt else fill


def luminance(c):
    r, g, b = map(lin, c[:3])
    return .2126 * r + .7152 * g + .0722 * b


def ratio(fg, bg):
    hi, lo = sorted((luminance(over(fg, bg)), luminance(bg)), reverse=True)
    return (hi + .05) / (lo + .05)


def hex_of(c):
    return "#" + "".join(f"{round(x):02x}" for x in c[:3])


def report():
    """[(what, mode, ratio, minimum, fg hex, bg hex)]"""
    rows = []
    for what, fg, place, minimum in pairs():
        for mode in range(4):
            bg = background(place, mode)
            f = value(fg, mode)
            rows.append((what, MODES[mode], ratio(f, bg), minimum, hex_of(over(f, bg)), hex_of(bg)))
    return rows
