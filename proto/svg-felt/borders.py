"""Prototype addition to felt.css: in the felt look, .border-* is the colour of the thread, not a second line.

- Pieces that are sewn already (cards, alerts, buttons, …) keep their seam; a .border-{colour} dyes its thread.
- An element with .border (or one side, .border-top …) that has no seam gets one, in that colour if given.
- The CSS border stays (same width, nothing moves when the look changes) but turns transparent.
Coloured thread is a fill masked by the seam image (as felt.css already does for outline buttons) with a
twist texture multiplied in, so it isn't a flat printed line. Without -webkit-mask-box-image (Firefox) the
border stays a plain coloured line, as today.
"""
COLOURS = {c: f"light-dark(var(--{c}), var(--{c}-text))" for c in ("primary", "secondary", "success", "danger", "warning", "info")}
# neutral threads are not dyed fills: white/light and dark/black thread is the seam itself, lightened or darkened,
# with its shadow (or light edge), so it still reads on felt of its own tone
NEUTRAL = {"white": "brightness(1.25) drop-shadow(0 0 .4px rgb(60 45 25 / .4)) drop-shadow(0 .8px .3px rgb(0 0 0 / .45))",
           "light": "brightness(1.1) sepia(.15) drop-shadow(0 0 .4px rgb(60 45 25 / .4)) drop-shadow(0 .8px .3px rgb(0 0 0 / .45))",
           "dark": "brightness(.1) drop-shadow(0 -.5px 0 rgb(255 255 255 / .3)) drop-shadow(0 .5px 0 rgb(255 255 255 / .12))",
           "black": "brightness(.03) drop-shadow(0 -.5px 0 rgb(255 255 255 / .3)) drop-shadow(0 .5px 0 rgb(255 255 255 / .12))"}
SUBTLE = ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")
SEWN = (".card, .navbar, .alert, .list-group, .accordion, .modal-content, .toast, .page-item.active .page-link, .dropdown-menu, "
        ".offcanvas, .popover, .btn-primary, .btn-secondary, .btn-success, .btn-danger, .btn-warning, .btn-info, .btn-dark, "
        ".btn-light, [class*=\"btn-outline-\"]")
NOT = "input, select, textarea, .form-control, .form-select, .form-check-input, .btn-close, hr, .vr, table, .table, img"
THICK = ".border-3, .border-4, .border-5"
ONE = ".border-top, .border-bottom, .border-start, .border-end"
SIDES = {"top": ("top", "row"), "bottom": ("bottom", "row"), "start": ("left", "col"), "end": ("right", "col")}
F = ':where([data-look="felt"])'

def css():
    colour_cls = [f".border-{c}" for c in COLOURS] + [f".border-{c}-subtle" for c in SUBTLE]
    neutral_cls = [f".border-{c}" for c in NEUTRAL]
    anyb = ", ".join([".border", ".border-top", ".border-bottom", ".border-start", ".border-end"] + colour_cls + neutral_cls)
    plain = f":is(.border):not({SEWN}, {NOT})"
    out = ["\n/* ---- prototype (proto/svg-felt/borders.py): .border-* in felt is the colour of the thread ---- */",
           # important in an earlier layer beats the utilities' !important
           "@layer base {\n  @supports (-webkit-mask-box-image: none) {",
           f"    {F} :is({anyb}):not({NOT}, :is({ONE}):not(.border):is({THICK})) {{ border-color: transparent !important; }}",
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
        sel = f"{F} .border-{side}:not(.border, {SEWN}, {NOT}, {THICK})::after"
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
            f"    {F} :is({ONE}):not(.border, {SEWN}, {NOT}, {THICK}):is({cols})::after {{",
            "      background: url(\"img/thread.svg\") 0 0 / 3px 3px, var(--thread); background-blend-mode: multiply;",
            "      -webkit-mask: var(--rule-img); mix-blend-mode: normal; filter: none; opacity: calc(.85 * var(--border-opacity, 1));",
            "    }",
            "  }"]
    # a thick rule on one side (a quote's bar) is a strip of felt in that colour, laid in, not a thread
    strip = {"start": "inset: 0 auto 0 calc(-1 * var(--bw)); width: var(--bw);", "end": "inset: 0 calc(-1 * var(--bw)) 0 auto; width: var(--bw);",
             "top": "inset: calc(-1 * var(--bw)) 0 auto 0; height: var(--bw);", "bottom": "inset: auto 0 calc(-1 * var(--bw)) 0; height: var(--bw);"}
    for side, pos in strip.items():
        out.append(f"  {F} .border-{side}:not(.border, {SEWN}, {NOT}):is({THICK})::after {{ content: \"\"; position: absolute; {pos}"
                   " pointer-events: none; background: var(--felt) 0 0 / var(--felt-size); mix-blend-mode: soft-light;"
                   " box-shadow: inset 0 0 1px rgb(0 0 0 / .25); }")
    for c, flt in NEUTRAL.items():
        out.append(f"  {F} :is({SEWN}, .border, {ONE}):not({NOT}).border-{c} {{ --seam-filter: {flt}; --seam-filter-cream: {flt}; "
                   "--patch-seam-filter: var(--seam-filter); --seam-strength: .9; --patch-seam-strength: .9; }")
    # square pieces get a square seam: the stitches stop short of the corner
    out.append(f"  {F} {{ --seam-sq-slice: 6; --seam-sq-width: 3px; }}")
    out.append(f"  {F} :is({SEWN}, .border):not({NOT}).rounded-0 {{ --seam-img: url(\"img/seam-sq.svg\"); "
               "--seam-slice: var(--seam-sq-slice); --seam-width: var(--seam-sq-width); }")
    # seam radius follows the piece: pills and round buttons get a stadium/circle concentric with their edge.
    # The pill image (radius 17, margin 3, slice 20) is scaled by k = (h/2 - inset) / 17 for each button size,
    # and the margin with it, so the thread keeps its distance from the edge. Heights are those of felt.css's sizes.
    for sel, k in ((":is(.btn-sm, .btn-group-sm > .btn):is(.btn-pill, .rounded-pill)", .79),
                   (".btn:is(.btn-pill, .rounded-pill):not(.btn-sm, .btn-lg, .btn-group-sm > .btn, .btn-group-lg > .btn)", .917),
                   (":is(.btn-lg, .btn-group-lg > .btn):is(.btn-pill, .rounded-pill)", 1.178),
                   (".btn-icon.btn-sm", 1.0)):   # round buttons are 44px at every size: the same seam as .btn-icon
        out.append(f"  {F} {sel} {{ --seam-img: url(\"img/seam-pill.svg\"); --seam-slice: var(--seam-pill-slice); "
                   f"--seam-width: {20 * k:.2f}px; --seam-margin: {3 * k:.2f}px;{' --seam-inset: 5px;' if 'icon' in sel else ''} }}")
    # light mode: depth and thread on a par with the dark. The patches stand higher (deeper cast shadow, darker
    # lower inner edge, a little more sheen), cards lift a little more, and the thread on colour is a crisper,
    # slightly stronger light tone. These override felt.css tokens, so they would also change the photo look.
    out += [f"  :root {{ --felt-shadow-near: light-dark(rgb(60 40 15 / .26), rgb(0 0 0 / .35)); "
            "--felt-shadow-far: light-dark(rgb(60 40 15 / .36), rgb(0 0 0 / .5)); "
            "--patch-dome: radial-gradient(120% 95% at 35% 10%, rgb(255 255 255 / .2), transparent 60%); "
            "--shadow-felt: 0 0 0 1px light-dark(rgb(80 60 40 / .16), transparent), 0 0 1px .5px light-dark(transparent, rgb(0 0 0 / .35)), "
            "0 0 0 .5px light-dark(transparent, rgb(255 240 220 / .06)), inset 0 -2px 0 light-dark(rgb(80 60 40 / .14), rgb(0 0 0 / .14)), "
            "inset 0 1px 0 light-dark(rgb(255 255 255 / .08), rgb(255 240 220 / .09)), 0 1px 0 light-dark(rgb(80 60 40 / .22), rgb(0 0 0 / .45)), "
            "0 1px 1.5px light-dark(rgb(70 50 30 / .32), transparent), 0 4px 12px light-dark(rgb(70 50 30 / .16), transparent), "
            "0 6px 14px -6px light-dark(transparent, rgb(0 0 0 / .6)); "
            "--body-bg: light-dark(#dbcdb7, #242220); --seam-filter-cream: brightness(.4) sepia(.45) var(--seam-relief); "
            "--seam-row-strength: .58; "
            "--patch-seam-filter: brightness(1); --patch-seam-strength: .55; --seam-strength: .72; }",
            # large light pieces (alerts carry their own shadow): a felt cut edge and a contact shadow instead of a light rim
            f"  {F} :where(.alert) {{ box-shadow: 0 0 0 1px light-dark(rgb(80 60 40 / .2), transparent), 0 1px 0 light-dark(rgb(80 60 40 / .24), transparent), "
            "0 0 1px .5px color-mix(in oklab, var(--tone) 20%, light-dark(transparent, rgb(0 0 0 / .3))), "
            "inset 0 1px 0 light-dark(rgb(255 255 255 / .08), color-mix(in srgb, var(--felt-highlight) 60%, transparent)), "
            "inset 0 -2px 0 light-dark(rgb(80 60 40 / .12), transparent), 0 1px 1px light-dark(transparent, var(--felt-edge)), "
            "0 1px 1.5px light-dark(rgb(70 50 30 / .3), transparent), 0 4px 12px light-dark(rgb(70 50 30 / .14), transparent), "
            "0 3px 6px -1px light-dark(transparent, color-mix(in srgb, var(--felt-shadow-near) 80%, transparent)), "
            "0 10px 18px -8px light-dark(transparent, color-mix(in srgb, var(--felt-shadow-far) 80%, transparent)); }",
            f"  {F} :where(.btn, .btn-group, .btn-group-vertical, .badge, .alert, .toast, .page-link, .progress-bar, [class*=\"text-bg-\"]) {{ "
            "--shadow-patch: 0 0 1px .5px color-mix(in oklab, color-mix(in oklab, var(--tone, light-dark(#f3ecdf, #3a3531)) 75%, var(--felt-cut)) 45%, transparent), "
            "inset 0 0 0 1px rgb(0 0 0 / .06), inset 0 1px 0 var(--patch-gloss, rgb(255 255 255 / .26)), "
            "inset 0 -3px 5px -1px light-dark(rgb(0 0 0 / .26), rgb(0 0 0 / .18)), inset 0 0 7px rgb(0 0 0 / .10), "
            "0 var(--felt-edge-y, 1.5px) 1px var(--felt-edge), 0 3px 6px -1px var(--felt-shadow-near), 0 10px 18px -8px var(--felt-shadow-far); }"]
    # dark mode: the drawn thread is finer than the photographed one, so it needs a little more light to read at 1x
    dark = ("--seam-filter: brightness(.67) sepia(.22) var(--seam-relief); --seam-strength: .52; --patch-seam-filter: brightness(.9); "
            "--patch-seam-strength: .38;")
    out += ["  @media (prefers-color-scheme: dark) {",
            f"    :root[data-look=\"felt\"]:not([data-bs-theme=\"light\"]) {{ {dark} }}", "  }",
            f"  :root[data-look=\"felt\"][data-bs-theme=\"dark\"], :root[data-look=\"felt\"] [data-bs-theme=\"dark\"] {{ {dark} }}"]
    out.append("}")
    return "\n".join(out) + "\n"

# twisted ply for coloured thread: diagonal ridges, multiplied into the dye
THREAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="6" height="6" viewBox="0 0 3 3"><rect width="3" height="3" fill="#fff"/>'
          '<path d="M-1 1L1-1M0 3L3 0M2 4L4 2" stroke="#c4c4c4" stroke-width=".75"/></svg>')
