"""Prototype addition to felt.css: in the felt look, .border-* is the colour of the thread, not a second line.

- Pieces that are sewn already (cards, alerts, buttons, …) keep their seam; a .border-{colour} dyes its thread.
- An element with .border (or one side, .border-top …) that has no seam gets one, in that colour if given.
- The CSS border stays (same width, nothing moves when the look changes) but turns transparent.
Coloured thread is a fill masked by the seam image (as felt.css already does for outline buttons) with a
twist texture multiplied in, so it isn't a flat printed line. Without -webkit-mask-box-image (Firefox) the
border stays a plain coloured line, as today.
"""
COLOURS = {c: f"var(--{c})" for c in ("primary", "secondary", "success", "danger", "warning", "info")}
COLOURS |= {"light": "var(--light-fixed)", "dark": "var(--dark-fixed)", "black": "#000", "white": "#fff"}
SUBTLE = ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")
SEWN = (".card, .navbar, .alert, .list-group, .accordion, .modal-content, .toast, .page-item.active .page-link, .dropdown-menu, "
        ".offcanvas, .popover, .btn-primary, .btn-secondary, .btn-success, .btn-danger, .btn-warning, .btn-info, .btn-dark, "
        ".btn-light, [class*=\"btn-outline-\"]")
NOT = "input, select, textarea, .form-control, .form-select, .form-check-input, .btn-close, hr, .vr, table, .table, img"
SIDES = {"top": ("top", "row"), "bottom": ("bottom", "row"), "start": ("left", "col"), "end": ("right", "col")}
F = ':where([data-look="felt"])'

def css():
    colour_cls = [f".border-{c}" for c in COLOURS] + [f".border-{c}-subtle" for c in SUBTLE]
    anyb = ", ".join([".border", ".border-top", ".border-bottom", ".border-start", ".border-end"] + colour_cls)
    plain = f":is(.border):not({SEWN}, {NOT})"
    out = ["\n/* ---- prototype (proto/svg-felt/borders.py): .border-* in felt is the colour of the thread ---- */",
           # important in an earlier layer beats the utilities' !important
           "@layer base {\n  @supports (-webkit-mask-box-image: none) {",
           f"    {F} :is({anyb}):not({NOT}) {{ border-color: transparent !important; }}",
           "  }\n}", "@layer felt {"]
    out += [f"  {F} .border-{c} {{ --thread: {v}; }}" for c, v in COLOURS.items()]
    out += [f"  {F} .border-{c}-subtle {{ --thread: var(--{c}-border-subtle); }}" for c in SUBTLE]
    out += [f"  {F} .border-{n} {{ --bw: {n}px; }}" for n in range(1, 6)]
    # plain bordered elements: a seam of their own (medium seam, like a button), tone on tone by default
    out += [f"  {F} {plain}, {F} :is(.border-top, .border-bottom, .border-start, .border-end):not(.border, {SEWN}, {NOT}) {{ position: relative; }}",
            f"  {F} {plain}::after {{",
            "    content: \"\"; position: absolute; z-index: 3; pointer-events: none;",
            "    inset: calc(5px - var(--seam-margin) - var(--bw, 1px));",
            "    border: 0 solid transparent;",
            "    border-image: var(--seam-img) var(--seam-slice) / var(--seam-width) round;",
            "    mix-blend-mode: hard-light; filter: var(--seam-filter); opacity: var(--seam-strength);",
            "  }"]
    for side, (phys, kind) in SIDES.items():
        sel = f"{F} .border-{side}:not(.border, {SEWN}, {NOT})::after"
        if kind == "row":
            pos = f"left: 6px; right: 6px; {phys}: calc(3px - var(--seam-margin) - var(--bw, 1px)); height: calc(2 * var(--seam-margin));"
            img = 'url("img/seam-row.svg") left center / var(--seam-row-size) round no-repeat'
        else:
            pos = f"top: 6px; bottom: 6px; {phys}: calc(3px - var(--seam-margin) - var(--bw, 1px)); width: calc(2 * var(--seam-margin));"
            img = 'url("img/seam-col.svg") center top / var(--seam-col-size) no-repeat repeat'
        out += [f"  {sel} {{ content: \"\"; position: absolute; z-index: 3; pointer-events: none; {pos}",
                f"    --rule-img: {img}; background: var(--rule-img); mix-blend-mode: hard-light; filter: var(--seam-filter); opacity: var(--seam-strength); }}"]
    # coloured thread
    cols = ", ".join(colour_cls)
    out += ["  @supports (-webkit-mask-box-image: none) {",
            f"    {F} :is({SEWN}, .border):is({cols})::after {{",
            "      border: 0; border-image: none;",
            "      background: url(\"img/thread.svg\") 0 0 / 3px 3px, var(--thread); background-blend-mode: multiply;",
            "      -webkit-mask-box-image: var(--seam-img) var(--seam-slice) / var(--seam-width) round;",
            "      mix-blend-mode: normal; filter: none; opacity: calc(.85 * var(--border-opacity, 1));",
            "    }",
            f"    {F} :is(.border-top, .border-bottom, .border-start, .border-end):not(.border, {SEWN}, {NOT}):is({cols})::after {{",
            "      background: url(\"img/thread.svg\") 0 0 / 3px 3px, var(--thread); background-blend-mode: multiply;",
            "      -webkit-mask: var(--rule-img); mix-blend-mode: normal; filter: none; opacity: calc(.85 * var(--border-opacity, 1));",
            "    }",
            "  }", "}"]
    return "\n".join(out) + "\n"

# twisted ply for coloured thread: diagonal ridges, multiplied into the dye
THREAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="6" height="6" viewBox="0 0 3 3"><rect width="3" height="3" fill="#fff"/>'
          '<path d="M-1 1L1-1M0 3L3 0M2 4L4 2" stroke="#c4c4c4" stroke-width=".75"/></svg>')
