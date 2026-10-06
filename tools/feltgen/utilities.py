"""Bootstrap's grid and utilities, once plain and once per breakpoint (so `.mb-2 .mb-md-4` works like in Bootstrap).

  grid:       .col-*, .row-cols-*, .offset-*, .g-*
  families:   colour helpers that take an opacity (.text-*, .bg-*, .border-*, .link-*), their subtle and emphasis tones,
              border widths, .rounded-*, overflow and position offsets
  utilities:  display, flex, order, spacing, gap, text alignment, float, object-fit and sticky, and .d-print-*

Colours are light-dark() tokens, not RGB triplets as in Bootstrap, so the opacity helpers fade a colour with
color-mix() instead of rgba().
"""
from .config import BREAKPOINTS, COLOURS, TONED
from .css import important, media, name, refs

SPACERS = {0: "0", 1: ".25rem", 2: ".5rem", 3: "1rem", 4: "1.5rem", 5: "3rem"}
GUTTERS = {k: "0rem" if v == "0" else v for k, v in SPACERS.items()}   # unitless 0 breaks the row's calc()
COLUMNS = 12
ROW_COLS = 6

# light and dark keep their tone in dark mode, like Bootstrap's: .bg-light .text-dark stays dark on light
FIXED = {"light": "$light-fixed", "dark": "$dark-fixed"}
LINK = {**{c: f"${c}-text" for c in TONED}, **FIXED}   # *-text: the tone that reads as text on the page
TEXT = {**LINK, "black": "$black", "white": "$white", "body": "$body-color"}
FILL = {**{c: f"${c}" for c in TONED}, **FIXED}
BG = {**FILL, "black": "$black", "white": "$white", "body": "$body-bg",
      "body-secondary": "light-dark($surface-sunk, $surface-raised)", "body-tertiary": "$surface-raised"}
BORDER = {**FILL, "black": "$black", "white": "$white"}
HOVER_INK = {"light": "#fff", "dark": "#000"}   # links hover towards --felt-hover-ink; these two always go lighter and darker
OPACITY = {"10": ".1", "25": ".25", "50": ".5", "75": ".75", "100": "1"}
OFFSETS = {1: ".125em", 2: ".25em", 3: ".375em"}
RADII = {0: "0", 1: "$radius-sm", 2: "$radius", 3: "$radius-lg", 4: "$radius-xl", 5: "$radius-xxl",
         "circle": "50%", "pill": "$radius-pill"}
CORNERS = {"top": ("top-left", "top-right"), "end": ("top-right", "bottom-right"),
           "bottom": ("bottom-right", "bottom-left"), "start": ("bottom-left", "top-left")}
OVERFLOW = ["auto", "hidden", "visible", "scroll"]
INSET = {"top": "top", "bottom": "bottom", "start": "inset-inline-start", "end": "inset-inline-end"}

DISPLAY = ["none", "inline", "inline-block", "block", "grid", "inline-grid", "table", "table-row",
           "table-cell", "flex", "inline-flex"]
FLEX = {
    "flex-fill": "flex: 1 1 auto", "flex-row": "flex-direction: row", "flex-column": "flex-direction: column",
    "flex-row-reverse": "flex-direction: row-reverse", "flex-column-reverse": "flex-direction: column-reverse",
    "flex-grow-0": "flex-grow: 0", "flex-grow-1": "flex-grow: 1", "flex-shrink-0": "flex-shrink: 0",
    "flex-shrink-1": "flex-shrink: 1", "flex-wrap": "flex-wrap: wrap", "flex-nowrap": "flex-wrap: nowrap",
    "flex-wrap-reverse": "flex-wrap: wrap-reverse",
}
EDGES = {"start": "flex-start", "end": "flex-end", "center": "center"}
ALIGN = {
    "justify-content": {**EDGES, "between": "space-between", "around": "space-around", "evenly": "space-evenly"},
    "align-items": {**EDGES, "baseline": "baseline", "stretch": "stretch"},
    "align-content": {**EDGES, "between": "space-between", "around": "space-around", "stretch": "stretch"},
    "align-self": {"auto": "auto", **EDGES, "baseline": "baseline", "stretch": "stretch"},
}
ORDER = {"first": -1, **{n: n for n in range(6)}, "last": 6}
SIDES = {"": "", "t": "-top", "b": "-bottom", "s": "-inline-start", "e": "-inline-end", "x": "-inline", "y": "-block"}
GAPS = {"gap": "gap", "row-gap": "row-gap", "column-gap": "column-gap"}
TEXT_ALIGN = ["start", "end", "center"]
FLOAT = {"start": "inline-start", "end": "inline-end", "none": "none"}
OBJECT_FIT = {"contain": "contain", "cover": "cover", "fill": "fill", "scale": "scale-down", "none": "none"}
STICKY = {"top": "top", "bottom": "bottom"}


def pct(n, of):
    return f"{100 * n / of:.6f}".rstrip("0").rstrip(".") + "%"


def fade(colour, opacity, default=""):
    """colour at the opacity held in a token, as rgba() with an RGB triplet would do it"""
    return f"color-mix(in srgb, {colour} calc(var({name(opacity)}{', ' + default if default else ''}) * 100%), transparent)"


def grid(i):
    """The grid in one breakpoint; i is the class infix ("" or "-md")."""
    gx, gy = name("gutter-x"), name("gutter-y")
    out = [f".col{i} {{ flex: 1 0 0%; }}", f".row-cols{i}-auto > * {{ flex: 0 0 auto; width: auto; }}"]
    out += [f".row-cols{i}-{n} > * {{ flex: 0 0 auto; width: {pct(1, n)}; }}" for n in range(1, ROW_COLS + 1)]
    out.append(f".col{i}-auto {{ flex: 0 0 auto; width: auto; }}")
    out += [f".col{i}-{n} {{ flex: 0 0 auto; width: {pct(n, COLUMNS)}; }}" for n in range(1, COLUMNS + 1)]
    out += [f".offset{i}-{n} {{ margin-left: {pct(n, COLUMNS) if n else 0}; }}" for n in range(0 if i else 1, COLUMNS)]
    out += [f".g{i}-{k} {{ {gx}: {v}; {gy}: {v}; }} .gx{i}-{k} {{ {gx}: {v}; }} .gy{i}-{k} {{ {gy}: {v}; }}"
            for k, v in GUTTERS.items()]
    return out


def colour_family(cls, prop, colours, opacities):
    """.text-primary and friends: each resets its opacity, so .text-opacity-50 on the same element fades it"""
    var = f"{cls}-opacity"
    out = [f".{cls}-{c} {{ {name(var)}: 1; {prop}: {refs(fade(v, var))} !important; }}" for c, v in colours.items()]
    return out + [f".{var}-{k} {{ {name(var)}: {OPACITY[k]}; }}" for k in opacities]


def links():
    names = [f"link-{c}" for c in LINK] + ["link-body-emphasis"]
    colour, hover = name("link-color"), name("link-hover-color")
    out = [f".link-{c} {{ {colour}: {refs(v)}; {hover}: color-mix(in oklab, {refs(v)} 80%, {refs(HOVER_INK.get(c, '$hover-ink'))}); }}"
           for c, v in LINK.items()]
    out.append(refs(f".link-body-emphasis {{ {colour}: $emphasis-color; {hover}: color-mix(in srgb, $emphasis-color 75%, transparent); }}"))
    every = ", ".join(f".{n}" for n in names)
    out.append(f":is({every}) {{ color: {refs(fade('$link-color', 'link-opacity', '1'))} !important; "
               f"text-decoration-color: {refs(fade('$link-color', 'link-underline-opacity', '1'))} !important; }}")
    out.append(f":is({every}):is(:hover, :focus) {{ {colour}: var({hover}); }}")
    out += [f".link-opacity-{k} {{ {name('link-opacity')}: {v}; }} .link-opacity-{k}-hover:hover {{ {name('link-opacity')}: {v}; }}"
            for k, v in OPACITY.items()]
    out += [f".link-offset-{k} {{ text-underline-offset: {v} !important; }} .link-offset-{k}-hover:hover {{ text-underline-offset: {v} !important; }}"
            for k, v in OFFSETS.items()]
    # an underline of its own, in the link's colour or another; also on a plain <a>
    out.append(':is(.link-underline, [class*="link-underline-"]) { text-decoration-color: '
               f"{refs(fade('var(--felt-link-underline-color, $link-color)', 'link-underline-opacity', '1'))} !important; }}")
    out.append(f".link-underline {{ {name('link-underline-opacity')}: 1; }}")
    out += [f".link-underline-{c} {{ {name('link-underline-color')}: {refs(v)}; {name('link-underline-opacity')}: 1; }}"
            for c, v in LINK.items()]
    out += [f".link-underline-opacity-{k} {{ {name('link-underline-opacity')}: {v}; }} .link-underline-opacity-{k}-hover:hover {{ {name('link-underline-opacity')}: {v}; }}"
            for k, v in {"0": "0", **OPACITY}.items()]
    return out


def families():
    out = colour_family("text", "color", TEXT, ["25", "50", "75", "100"])
    out += important((f"text-{c}-emphasis", f"color: ${c}-emphasis") for c in COLOURS)
    out += colour_family("bg", "background-color", BG, OPACITY)
    out += important((f"bg-{c}-subtle", f"background-color: ${c}-subtle") for c in COLOURS)
    out += colour_family("border", "border-color", BORDER, OPACITY)
    out += important((f"border-{c}-subtle", f"border-color: ${c}-border-subtle") for c in COLOURS)
    out += important((f"border-{n}", f"border-width: {n}px") for n in range(1, 6))
    out += important([("rounded", "border-radius: $radius")] + [(f"rounded-{k}", f"border-radius: {v}") for k, v in RADII.items()])
    for side, (a, b) in CORNERS.items():
        for k, v in {"": "$radius", **{f"-{k}": v for k, v in RADII.items()}}.items():
            out.append(refs(f".rounded-{side}{k} {{ border-{a}-radius: {v} !important; border-{b}-radius: {v} !important; }}"))
    out += links()
    out += [f".focus-ring-{c} {{ {name('focus-ring-color')}: color-mix(in oklab, {refs(v)} 50%, transparent); }}" for c, v in FILL.items()]
    out += important((f"{p}-{v}", f"{p}: {v}") for p in ("overflow", "overflow-x", "overflow-y") for v in OVERFLOW)
    out += important((f"{side}-{n}", f"{prop}: {n}{'%' if n else ''}") for side, prop in INSET.items() for n in (0, 50, 100))
    return out


def display(i):
    return important((f"d{i}-{v}", f"display: {v}") for v in DISPLAY)


def utilities(i):
    """All responsive utilities in one breakpoint, with Bootstrap's !important."""
    rules = [(cls.replace("flex-", f"flex{i}-", 1), decl) for cls, decl in FLEX.items()]
    rules += [(f"{prop}{i}-{k}", f"{prop}: {v}") for prop, values in ALIGN.items() for k, v in values.items()]
    rules += [(f"order{i}-{k}", f"order: {v}") for k, v in ORDER.items()]
    for letter, prop in (("m", "margin"), ("p", "padding")):
        for side, suffix in SIDES.items():
            values = {**SPACERS, **({"auto": "auto"} if letter == "m" else {})}
            rules += [(f"{letter}{side}{i}-{k}", f"{prop}{suffix}: {v}") for k, v in values.items()]
    rules += [(f"{cls}{i}-{k}", f"{prop}: {v}") for cls, prop in GAPS.items() for k, v in SPACERS.items()]
    rules += [(f"text{i}-{v}", f"text-align: {v}") for v in TEXT_ALIGN]
    rules += [(f"float{i}-{k}", f"float: {v}") for k, v in FLOAT.items()]
    rules += [(f"object-fit{i}-{k}", f"object-fit: {v}") for k, v in OBJECT_FIT.items()]
    sticky = [f".sticky{i}-{k} {{ position: sticky !important; {edge}: 0 !important; z-index: 1020 !important; }}"
              for k, edge in STICKY.items()]
    return display(i) + important(rules) + sticky


def per_breakpoint(family, breakpoints=BREAKPOINTS):
    lines = family("")
    for bp, width in breakpoints.items():
        lines += media(f"(min-width: {width}px)", family(f"-{bp}"))
    return lines


def blocks():
    return {
        "grid": per_breakpoint(grid),
        "families": families(),
        "utilities": per_breakpoint(utilities) + media("print", display("-print")),
    }
