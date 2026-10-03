#!/usr/bin/env python3
"""Write the repetitive part of felt.css between its markers; everything else stays hand-written.

  grid:       Bootstrap's grid (.col-*, .row-cols-*, .offset-*, .g-*), once plain and once per breakpoint
  families:   colour helpers that take an opacity (.text-*, .bg-*, .border-*, .link-*), their subtle and
              emphasis tones, border widths, .rounded-*, overflow and position offsets
  utilities:  display, flex, order, spacing, gap, text alignment, float, object-fit and sticky, once plain
              and once per breakpoint (so `.mb-2 .mb-md-4` works like in Bootstrap), and .d-print-*

Colours are light-dark() tokens, not RGB triplets as in Bootstrap, so the opacity helpers fade a colour
with color-mix() instead of rgba(). Change the lists below and run it again.

Needs: python3.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "felt.css"

BREAKPOINTS = {"sm": 576, "md": 768, "lg": 992}   # the same as the containers and .navbar-expand-*
SPACERS = {0: "0", 1: ".25rem", 2: ".5rem", 3: "1rem", 4: "1.5rem", 5: "3rem"}
GUTTERS = {k: "0rem" if v == "0" else v for k, v in SPACERS.items()}   # unitless 0 breaks the row's calc()
COLUMNS = 12
ROW_COLS = 6

COLOURS = ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"]
TONED = COLOURS[:6]
# light and dark keep their tone in dark mode, like Bootstrap's: .bg-light .text-dark stays dark on light
FIXED = {"light": "var(--light-fixed)", "dark": "var(--dark-fixed)"}
LINK = {**{c: f"var(--{c}-text)" for c in TONED}, **FIXED}   # --*-text: the tone that reads as text on the page
TEXT = {**LINK, "black": "#000", "white": "#fff", "body": "var(--text)"}
FILL = {**{c: f"var(--{c})" for c in TONED}, **FIXED}
BG = {**FILL, "black": "#000", "white": "#fff", "body": "var(--body-bg)",
      "body-secondary": "light-dark(var(--surface-sunk), var(--surface-raised))", "body-tertiary": "var(--surface-raised)"}
BORDER = {**FILL, "black": "#000", "white": "#fff"}
HOVER_INK = {"light": "#fff", "dark": "#000"}   # links hover towards --state-ink; these two always go lighter and darker
OPACITY = {"10": ".1", "25": ".25", "50": ".5", "75": ".75", "100": "1"}
OFFSETS = {1: ".125em", 2: ".25em", 3: ".375em"}
RADII = {0: "0", 1: "var(--radius-sm)", 2: "var(--radius)", 3: "var(--radius-lg)", 4: "var(--radius-xl)",
         5: "var(--radius-xxl)", "circle": "50%", "pill": "var(--radius-pill)"}
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
    """colour at the opacity held in a custom property, as rgba() with an RGB triplet would do it"""
    return f"color-mix(in srgb, {colour} calc(var(--{opacity}{', ' + default if default else ''}) * 100%), transparent)"


def important(rules):
    return [f".{name} {{ {decl} !important; }}" for name, decl in rules]


def grid(i):
    """The grid in one breakpoint; i is the class infix ("" or "-md")."""
    out = [f".col{i} {{ flex: 1 0 0%; }}", f".row-cols{i}-auto > * {{ flex: 0 0 auto; width: auto; }}"]
    out += [f".row-cols{i}-{n} > * {{ flex: 0 0 auto; width: {pct(1, n)}; }}" for n in range(1, ROW_COLS + 1)]
    out.append(f".col{i}-auto {{ flex: 0 0 auto; width: auto; }}")
    out += [f".col{i}-{n} {{ flex: 0 0 auto; width: {pct(n, COLUMNS)}; }}" for n in range(1, COLUMNS + 1)]
    out += [f".offset{i}-{n} {{ margin-left: {pct(n, COLUMNS) if n else 0}; }}" for n in range(0 if i else 1, COLUMNS)]
    out += [f".g{i}-{k} {{ --gutter-x: {v}; --gutter-y: {v}; }} .gx{i}-{k} {{ --gutter-x: {v}; }} .gy{i}-{k} {{ --gutter-y: {v}; }}"
            for k, v in GUTTERS.items()]
    return out


def colour_family(cls, prop, colours, opacities):
    """.text-primary and friends: each resets its opacity, so .text-opacity-50 on the same element fades it"""
    var = f"{cls}-opacity"
    out = [f".{cls}-{c} {{ --{var}: 1; {prop}: {fade(v, var)} !important; }}" for c, v in colours.items()]
    return out + [f".{var}-{k} {{ --{var}: {OPACITY[k]}; }}" for k in opacities]


def links():
    names = [f"link-{c}" for c in LINK] + ["link-body-emphasis"]
    out = [f".link-{c} {{ --link-color: {v}; --link-hover-color: color-mix(in oklab, {v} 80%, {HOVER_INK.get(c, 'var(--state-ink)')}); }}"
           for c, v in LINK.items()]
    out.append(".link-body-emphasis { --link-color: var(--emphasis); --link-hover-color: color-mix(in srgb, var(--emphasis) 75%, transparent); }")
    every = ", ".join(f".{n}" for n in names)
    out.append(f":is({every}) {{ color: {fade('var(--link-color)', 'link-opacity', '1')} !important; "
               f"text-decoration-color: {fade('var(--link-color)', 'link-underline-opacity', '1')} !important; }}")
    out.append(f":is({every}):is(:hover, :focus) {{ --link-color: var(--link-hover-color); }}")
    out += [f".link-opacity-{k} {{ --link-opacity: {v}; }} .link-opacity-{k}-hover:hover {{ --link-opacity: {v}; }}"
            for k, v in OPACITY.items()]
    out += [f".link-offset-{k} {{ text-underline-offset: {v} !important; }} .link-offset-{k}-hover:hover {{ text-underline-offset: {v} !important; }}"
            for k, v in OFFSETS.items()]
    # an underline of its own, in the link's colour or another; also on a plain <a>
    out.append(':is(.link-underline, [class*="link-underline-"]) { text-decoration-color: '
               f"{fade('var(--link-underline, var(--link-color, var(--link)))', 'link-underline-opacity', '1')} !important; }}")
    out.append(".link-underline { --link-underline-opacity: 1; }")
    out += [f".link-underline-{c} {{ --link-underline: {v}; --link-underline-opacity: 1; }}" for c, v in LINK.items()]
    out += [f".link-underline-opacity-{k} {{ --link-underline-opacity: {v}; }} .link-underline-opacity-{k}-hover:hover {{ --link-underline-opacity: {v}; }}"
            for k, v in {"0": "0", **OPACITY}.items()]
    return out


def families():
    out = colour_family("text", "color", TEXT, ["25", "50", "75", "100"])
    out += important((f"text-{c}-emphasis", f"color: var(--{c}-emphasis)") for c in COLOURS)
    out += colour_family("bg", "background-color", BG, OPACITY)
    out += important((f"bg-{c}-subtle", f"background-color: var(--{c}-subtle)") for c in COLOURS)
    out += colour_family("border", "border-color", BORDER, OPACITY)
    out += important((f"border-{c}-subtle", f"border-color: var(--{c}-border-subtle)") for c in COLOURS)
    out += important((f"border-{n}", f"border-width: {n}px") for n in range(1, 6))
    out += important([("rounded", "border-radius: var(--radius)")] + [(f"rounded-{k}", f"border-radius: {v}") for k, v in RADII.items()])
    for side, (a, b) in CORNERS.items():
        for k, v in {"": "var(--radius)", **{f"-{k}": v for k, v in RADII.items()}}.items():
            out.append(f".rounded-{side}{k} {{ border-{a}-radius: {v} !important; border-{b}-radius: {v} !important; }}")
    out += links()
    out += [f".focus-ring-{c} {{ --focus-ring-color: color-mix(in oklab, {v} 50%, transparent); }}" for c, v in FILL.items()]
    out += important((f"{p}-{v}", f"{p}: {v}") for p in ("overflow", "overflow-x", "overflow-y") for v in OVERFLOW)
    out += important((f"{side}-{n}", f"{prop}: {n}{'%' if n else ''}") for side, prop in INSET.items() for n in (0, 50, 100))
    return ["  " + rule for rule in out]


def display(i):
    return important((f"d{i}-{v}", f"display: {v}") for v in DISPLAY)


def utilities(i):
    """All responsive utilities in one breakpoint, with Bootstrap's !important."""
    rules = [(name.replace("flex-", f"flex{i}-", 1), decl) for name, decl in FLEX.items()]
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


def per_breakpoint(family):
    lines = ["  " + rule for rule in family("")]
    for bp, width in BREAKPOINTS.items():
        lines.append(f"  @media (min-width: {width}px) {{")
        lines += ["    " + rule for rule in family(f"-{bp}")]
        lines.append("  }")
    return lines


def write_between(text, name, lines):
    start, end = f"/* {name}:start */", f"/* {name}:end */"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    note = f"  /* written by tools/build_utilities.py; change the script, not these {len(lines)} lines */"
    return head + start + "\n" + note + "\n" + "\n".join(lines) + "\n  " + end + tail


text = CSS.read_text()
text = write_between(text, "grid", per_breakpoint(grid))
text = write_between(text, "families", families())
text = write_between(text, "utilities", per_breakpoint(utilities)
                     + ["  @media print {"] + ["    " + rule for rule in display("-print")] + ["  }"])
CSS.write_text(text)
print(f"{CSS.name}: {len(text.splitlines())} lines")
