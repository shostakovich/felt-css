"""The repetitive parts of the components: one variant per theme colour, one per breakpoint.

Each block goes between /* name:start */ and /* name:end */ in felt.css. Colour variants set the component's tokens
(like Bootstrap's .btn-primary sets --bs-btn-bg …); the component's own rules read them.
"""
from .config import BREAKPOINTS, COLOURS
from .css import media, name, refs

OPTIONAL = set()   # blocks felt.css may leave out


def tokens(cls, values):
    """.cls { --felt-x: …; } from {"x": "…"}"""
    body = " ".join(f"{name(k)}: {refs(v)};" for k, v in values.items())
    return f".{cls} {{ {body} }}"


def per_breakpoint(rules, plain=True):
    """rules(infix) once without a breakpoint (if plain) and once from each breakpoint up"""
    lines = rules("") if plain else []
    for bp, width in BREAKPOINTS.items():
        lines += media(f"(min-width: {width}px)", rules(f"-{bp}"))
    return lines


def below_breakpoint(rules, plain=True):
    """rules(infix) once without a breakpoint (if plain) and once below each breakpoint (Bootstrap's *-down)"""
    lines = rules("") if plain else []
    for bp, width in BREAKPOINTS.items():
        lines += media(f"(max-width: {width - .02:g}px)", rules(f"-{bp}"))
    return lines


# ------------------------------------------------------------------ buttons

# fill, ink and border of the solid buttons; hover and press are mixed from the fill (see .btn)
BTN = {c: {"bg": f"${c}", "color": f"${c}-ink", "border-color": "transparent"} for c in COLOURS}
BTN["warning"] |= {"hover-ink": "#fff", "press-ink": "#fff"}   # dark ink: states lighten, as in Bootstrap
BTN["light"] = {"bg": "$surface-raised", "border-color": "$border-color",
                # neutral buttons are surfaces: pressed or chosen, they take their hover a clear step further
                "btn-active-bg": "color-mix(in oklab, $btn-bg, $hover-ink $select-mix)",
                "btn-active-shadow": "inset 0 1px 3px rgb(0 0 0 / .15)"}
BTN["dark"]["border-color"] = "light-dark(transparent, $border-color)"
# outline: the colour as text and thread; chosen or pressed, the solid fill
OUTLINE_COLOR = {"primary": "light-dark($primary, $primary-text)", "secondary": "light-dark($secondary, $secondary-text)",
                 "success": "$success-emphasis", "danger": "$danger-emphasis", "warning": "$warning-emphasis",
                 "info": "$info-text", "light": "$light-emphasis", "dark": "$dark-emphasis"}
OUTLINE_FILL = {c: (f"${c}", f"${c}-ink") for c in COLOURS} | {"light": ("$light-emphasis", "$surface"),
                                                                 "dark": ("$dark-emphasis", "$surface")}


def btn_key(k):
    return k if k.startswith("btn-") or k in ("hover-ink", "press-ink") else f"btn-{k}"


def buttons():
    out = [tokens(f"btn-{c}", {btn_key(k): v for k, v in spec.items()}) for c, spec in BTN.items()]
    for c in COLOURS:
        fill, ink = OUTLINE_FILL[c]
        out.append(tokens(f"btn-outline-{c}", {
            "btn-color": OUTLINE_COLOR[c], "btn-border-color": "currentColor",
            "btn-hover-bg": "color-mix(in oklab, currentColor 10%, transparent)",
            "btn-active-bg": fill, "btn-active-color": ink, "btn-active-border-color": fill,
        }))
    return out


# ------------------------------------------------------------------ alerts, list groups, tables, text-bg

def alerts():
    out = [f".alert-{c} {{ {name('_tone')}: {refs(f'${c}')}; {name('_tone-emphasis')}: {refs(f'${c}-emphasis')}; }}"
           for c in ["primary", "secondary", "success", "warning", "danger", "info"]]
    out.append(refs(".alert-light { --_tone: $secondary-color; --_tone-emphasis: $light-emphasis; background-color: $surface-raised; "
                    "border-color: $border-color; }"))
    out.append(refs(".alert-dark { --_tone: $dark; --_tone-emphasis: $dark-emphasis; background-color: light-dark(color-mix(in oklab, $dark 16%, $surface), "
                    "color-mix(in oklab, $dark 60%, $surface)); border-color: light-dark(color-mix(in oklab, $dark 26%, $surface), $border-color); }"))
    return out


def list_group_items():
    return [refs(f".list-group-item-{c} {{ --felt-list-group-bg: ${c}-subtle; color: ${c}-emphasis; }}") for c in COLOURS]


def tables():
    out = [tokens(f"table-{c}", {"table-bg": f"${c}-subtle", "table-color": f"${c}-emphasis", "table-border-color": f"${c}-border-subtle"})
           for c in COLOURS[:6]]
    out.append(tokens("table-light", {"table-bg": "$surface-raised", "table-color": "$body-color", "table-border-color": "$border-color"}))
    out.append(tokens("table-dark", {"table-bg": "$dark", "table-color": "$dark-ink",
                                     "table-border-color": "color-mix(in oklab, $dark-ink 20%, $dark)"}))
    return out


TEXT_BG_BORDER = {"light": "transparent; box-shadow: inset 0 0 0 1px $border-color",
                  "dark": "light-dark(transparent, rgb(255 255 255 / .1))"}


def text_bg():
    return [refs(f".text-bg-{c} {{ --_tone: ${c}; background-color: ${c}; color: ${c}-ink; border-color: {TEXT_BG_BORDER.get(c, 'transparent')}; }}")
            for c in COLOURS]


# ------------------------------------------------------------------ breakpoints

def navbar_expand(i):
    """expanded, an offcanvas in the navbar is plain navbar content, laid out like .navbar-collapse"""
    n = f".navbar-expand{i}"
    return [f"{n} {{ flex-wrap: nowrap; }}", f"{n} .navbar-nav {{ flex-direction: row; }}",
            f"{n} .navbar-nav .dropdown-menu {{ position: absolute; }}", f"{n} .navbar-nav-scroll {{ overflow: visible; }}",
            f"{n} .navbar-toggler {{ display: none; }}",
            f"{n} .navbar-collapse {{ display: flex !important; flex-basis: auto; }}",
            f"{n} .offcanvas {{ position: static; z-index: auto; flex-grow: 1; width: auto !important; height: auto !important; "
            "visibility: visible !important; background-color: transparent !important; border: 0 !important; border-radius: 0; "
            "box-shadow: none; transform: none !important; transition: none; }",
            f"{n} .offcanvas .offcanvas-header {{ display: none; }}",
            refs(f"{n} .offcanvas .offcanvas-body {{ display: flex; flex-grow: 0; align-items: center; gap: $space-2 $space-3; "
                 "padding: 0; overflow-y: visible; }")]


def list_group_horizontal(i):
    n = f".list-group-horizontal{i}"
    return [f"{n} {{ flex-direction: row; width: fit-content; max-width: 100%; }}",
            refs(f"{n} > .list-group-item:first-child:not(:last-child) {{ border-end-start-radius: $radius-lg; border-start-end-radius: 0; }}"),
            refs(f"{n} > .list-group-item:last-child:not(:first-child) {{ border-start-end-radius: $radius-lg; border-end-start-radius: 0; }}"),
            f"{n} > .list-group-item + .list-group-item {{ border-width: 1px 0 1px 1px; }}",
            f"{n} > .list-group-item + .list-group-item.active {{ margin: 0 0 0 -1px; }}"]


def dropdown_align(i):
    """Bootstrap's JS (Popper) reads --bs-position to align a menu at the toggle's end"""
    return [f".dropdown-menu{i}-start {{ --bs-position: start; }}",
            f".dropdown-menu{i}-start[data-bs-popper] {{ right: auto; left: 0; }}",
            f".dropdown-menu{i}-end {{ --bs-position: end; }}",
            f".dropdown-menu{i}-end[data-bs-popper] {{ right: 0; left: auto; }}"]


def table_responsive(i):
    return [f".table-responsive{i} {{ overflow-x: auto; }}"]


def modal_fullscreen(i):
    n = f".modal-fullscreen{i}{'-down' if i else ''}"
    return [f"{n} {{ width: 100%; max-width: none; height: 100%; margin: 0; }}",
            f"{n} .modal-content {{ height: 100%; border: 0; border-radius: 0; }}",
            f"{n} :is(.modal-header, .modal-footer) {{ border-radius: 0; }}"]


def offcanvas_responsive(i):
    """.offcanvas-{bp} from its breakpoint up: the sheet becomes plain content in the page's flow"""
    n = f".offcanvas{i}"
    return [f"{n} {{ --felt-offcanvas-height: auto; --felt-offcanvas-border-width: 0; position: static; z-index: auto; display: block; "
            "width: auto; max-width: none; visibility: visible; background-color: transparent !important; color: inherit; "
            "border-radius: 0; box-shadow: none; transform: none; transition: none; }",
            f"{n} .offcanvas-header {{ display: none; }}",
            f"{n} .offcanvas-body {{ display: flex; flex-grow: 0; padding: 0; overflow-y: visible; background-color: transparent !important; }}"]


def offcanvas_inline(i):
    """the felt layer's half of offcanvas_responsive and navbar_expand: inline, an offcanvas is no piece of felt"""
    sel = ", ".join(([f".offcanvas{i}"] if i else []) + [f".navbar-expand{i} .offcanvas"])
    return [f"&:is({sel}) {{ background-image: none; box-shadow: none; overflow: visible; "
            "--felt-thread-filter: inherit; --_rule-piece: inherit; }",
            f"&:is({sel})::after {{ content: none; }}"]


def containers():
    every = ", ".join([".container", ".container-fluid"] + [f".container-{bp}" for bp in BREAKPOINTS])
    lines = [refs(f"{every} {{ width: 100%; margin-inline: auto; padding-inline: $space-3; }}"),
             refs(".container { max-width: $container-max; }")]
    return lines + [refs(f"@media (min-width: {w}px) {{ .container-{bp} {{ max-width: $container-max; }} }}") for bp, w in BREAKPOINTS.items()]


def blocks():
    return {
        "containers": containers(),
        "btn-variants": buttons(),
        "alert-variants": alerts(),
        "list-group-variants": list_group_items(),
        "table-variants": tables(),
        "text-bg": text_bg(),
        "navbar-expand": per_breakpoint(navbar_expand),
        "list-group-horizontal": per_breakpoint(list_group_horizontal),
        "dropdown-align": per_breakpoint(dropdown_align),
        "table-responsive": below_breakpoint(table_responsive),
        "modal-fullscreen": below_breakpoint(modal_fullscreen),
        "offcanvas-responsive": per_breakpoint(offcanvas_responsive, plain=False),
        "offcanvas-inline": per_breakpoint(offcanvas_inline),
    }
