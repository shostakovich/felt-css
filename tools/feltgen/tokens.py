"""The global tokens of felt.css: one source for the @layer tokens block and the token tables in the docs.

Each token has a value per look (clean, felt) and, where light-dark() can't hold it (images, filters, numbers,
blend modes), per colour mode. tools/build.py writes them into felt.css so that both work on any element:
data-look and data-bs-theme can be set anywhere, the nearest one wins.

    T(name, clean, felt=None, dark=None, felt_dark=None, doc="", bs=())

- name: without prefix; "_name" is internal (--_name), everything else public (--felt-name)
- clean: the value in the clean look; None for a felt-only token (it only acts in the felt look)
- felt: the value in the felt look, if it differs
- dark, felt_dark: the value in dark mode, for values that aren't colours
- doc: one line for the docs table (required for public tokens)
- bs: the Bootstrap tokens it stands for, when the name doesn't say so (--bs-X maps to --felt-X by itself)

Values refer to other tokens as $name ($primary -> var(--felt-primary), $_tone -> var(--_tone)).
Felt-only tokens carry a material word: texture, sheet, nap, wool, patch, groove, seam, thread, stitch.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import BREAKPOINTS, COLOURS, TONED


@dataclass
class Token:
    name: str
    clean: str | None
    felt: str | None = None
    dark: str | None = None
    felt_dark: str | None = None
    doc: str = ""
    bs: tuple = ()
    group: str = ""

    @property
    def public(self):
        return not self.name.startswith("_")

    @property
    def felt_only(self):
        return self.clean is None

    def values(self):
        """(clean light, clean dark, felt light, felt dark)"""
        felt = self.felt if self.felt is not None else self.clean
        if self.felt_dark is not None:
            felt_dark = self.felt_dark
        else:
            felt_dark = self.dark if self.felt is None and self.dark is not None else felt
        if self.clean is None:
            return felt, felt_dark, felt, felt_dark
        return self.clean, self.dark if self.dark is not None else self.clean, felt, felt_dark


GROUPS = []   # (key, title, intro, [Token])


def group(key, title, intro=""):
    GROUPS.append((key, title, intro, []))


def T(name, clean, felt=None, dark=None, felt_dark=None, doc="", bs=()):
    key = GROUPS[-1][0]
    GROUPS[-1][3].append(Token(name, clean, felt, dark, felt_dark, doc, tuple(bs), key))


# ------------------------------------------------------------------ palette

group("palette", "Palette", "Named felt colours, the same in both looks and both colour modes. The theme colours are "
      "made from them.")
T("mustard", "#e0a224", doc="Warning", bs=["--bs-yellow"])
T("denim", "#3d64a0", doc="Primary", bs=["--bs-blue"])
T("moss", "#5a7f33", doc="Success", bs=["--bs-green"])
T("tomato", "#c4452f", doc="Danger", bs=["--bs-red"])
T("petrol", "#2b7a80", doc="Info", bs=["--bs-teal"])
T("taupe", "#7a6e60", doc="Secondary")
T("navy", "#1e2b45", doc="Ink of the felt look")
T("indigo", "#4b4f9c", doc="Indigo felt")
T("plum", "#7b4a82", doc="Purple felt", bs=["--bs-purple"])
T("rose", "#c45a78", doc="Pink felt", bs=["--bs-pink"])
T("pumpkin", "#d6772e", doc="Orange felt", bs=["--bs-orange"])
T("lagoon", "#3a9bb2", doc="Cyan felt", bs=["--bs-cyan"])
T("black", "#000", doc="Black")
T("white", "#fff", doc="White")

group("gray", "Grays", "A neutral scale that doesn't follow the colour mode, like Bootstrap's. Clean: Bootstrap's "
      "greys; felt: warm greys from cream to charcoal, 600 is the taupe.")
CLEAN_GRAYS = ["#f8f9fa", "#e9ecef", "#dee2e6", "#ced4da", "#adb5bd", "#6c757d", "#495057", "#343a40", "#212529"]
FELT_GRAYS = ["#f5efe5", "#e9e1d3", "#d9cfbe", "#bcb09c", "#9b8f7c", "#7a6e60", "#5e554a", "#433d36", "#2b2723"]
for step, (c, f) in enumerate(zip(CLEAN_GRAYS, FELT_GRAYS), 1):
    T(f"gray-{step}00", c, f, doc=f"Gray {step}00",
      bs=[f"--bs-gray-{step}00"] + (["--bs-gray"] if step == 6 else []) + (["--bs-gray-dark"] if step == 8 else []))

# ------------------------------------------------------------------ theme colours

group("theme", "Theme colours", "Fills, the ink on them, and the tones derived from them. Dark mode mutes the fills a "
      "little: they glare less and white ink stays at 4.5:1 or more.")
FILLS = {
    "primary": ("light-dark($denim, #385c93)", None, "#fff"),
    "secondary": ("light-dark($taupe, #6a5f52)", None, "#fff"),
    "success": ("light-dark($moss, #527530)", None, "#fff"),
    "danger": ("light-dark($tomato, #b23f29)", None, "#fff"),
    "warning": ("light-dark($mustard, #cf9520)", None, "#3a2a06"),
    "info": ("light-dark($petrol, #276f75)", None, "#fff"),
    "light": ("light-dark(#f8f9fa, #3b4148)", "light-dark(#f3ece0, #4a443d)", None),
    "dark": ("light-dark(#212529, #111315)", "light-dark($navy, #202840)", "#f8f9fa"),
}
INK = {"light": ("light-dark(#1f2633, #e9ecef)", "light-dark($navy, #efe7da)")}
EMPHASIS = {
    "primary": "light-dark(#26406a, #a9c4ee)", "secondary": "light-dark(#4a4136, #d6cdbf)",
    "success": "light-dark(#36501d, #b0d18c)", "danger": "light-dark(#7d2a1b, #f3a593)",
    "warning": "light-dark(#6b4e12, #f1cb72)", "info": "light-dark(#1b4f53, #94d3d6)",
    "light": "light-dark(#495057, #dee2e6)", "dark": "light-dark(#343a40, #adb5bd)",
}
TEXT = {   # clean, felt: coloured text on the page; felt's is a shade deeper, it sits on the darker felt page too
    "primary": ("light-dark($primary, #8fb2e8)", "$link-color"),
    "secondary": ("light-dark($secondary, #c4b9aa)", "light-dark(#5c5247, #c4b9aa)"),
    "success": ("light-dark(#4e6f2c, #98c26c)", "light-dark(#46642a, #98c26c)"),
    "danger": ("light-dark($danger, #ef8c76)", "light-dark(#a33a25, #ef8c76)"),
    "warning": ("light-dark(#8a5f0c, $warning)", "light-dark(#7b560c, $warning)"),
    "info": ("light-dark($info, #6cc3c8)", "light-dark(#22666b, #6cc3c8)"),
}
SUBTLE = {c: (14, 32) for c in COLOURS} | {"warning": (18, 40)}
for c in COLOURS:
    fill, felt_fill, ink = FILLS[c]
    T(c, fill, felt_fill, doc=f"{c.capitalize()} fill")
    clean_ink, felt_ink = INK.get(c, (ink, None))
    T(f"{c}-ink", clean_ink, felt_ink, doc=f"Text and icons on the {c} fill")
for c in COLOURS:
    T(f"{c}-emphasis", EMPHASIS[c], doc=f"Text on {c} tints (.alert-{c}, .text-{c}-emphasis), 4.5:1 or more",
      bs=[f"--bs-{c}-text-emphasis"])
for c in TONED:
    T(f"{c}-text", *TEXT[c], doc=f"{c.capitalize()} as text on the page (.text-{c}, .link-{c})")
T("light-fixed", "#f8f9fa", "#f3ece0", doc="Light that keeps its tone in dark mode, like Bootstrap's (.bg-light, .text-light)")
T("dark-fixed", "#212529", "$navy", doc="Dark that keeps its tone in dark mode (.bg-dark, .text-dark)")
for c in COLOURS:
    tint, edge = SUBTLE[c]
    subtle = {"light": "color-mix(in oklab, $light 50%, $surface)", "dark": "color-mix(in oklab, $dark 20%, $surface)"}
    T(f"{c}-subtle", subtle.get(c, f"color-mix(in oklab, ${c} {tint}%, $surface)"),
      "color-mix(in oklab, $secondary 18%, $surface)" if c == "dark" else None,
      doc=f"{c.capitalize()} tint (.bg-{c}-subtle, .alert-{c})", bs=[f"--bs-{c}-bg-subtle"])
for c in COLOURS:
    tint, edge = SUBTLE[c]
    border = {"light": "$border-color", "dark": "color-mix(in oklab, $dark 40%, $surface)"}
    T(f"{c}-border-subtle", border.get(c, f"color-mix(in oklab, ${c} {edge}%, $surface)"),
      doc=f"Border of {c} tints")

# ------------------------------------------------------------------ body and surfaces

group("body", "Body and surfaces", "The page, what lies on it, and its text.")
T("body-bg", "light-dark(#f6f7f9, #212529)", "light-dark(#dbcdb7, #242220)", doc="Page background")
T("body-color", "light-dark(#1f2633, #dee2e6)", "light-dark($navy, #efe7da)", doc="Body text")
T("emphasis-color", "light-dark(#000, #fff)", "light-dark(#0e1526, #fffaf2)", doc="Strongest text (.text-body-emphasis)")
T("secondary-color", "light-dark(#677084, #a2aab4)", "light-dark(#665f50, #b8ad9c)",
  doc="Secondary text (.text-body-secondary, .text-muted, form text)")
T("tertiary-color", "light-dark(#8a92a3, #7d858f)", "light-dark(#8d8574, #8f8676)",
  doc="Tertiary text: disabled links and items, placeholders' neighbours (.text-body-tertiary)")
T("surface", "light-dark(#fff, #2b3035)", "light-dark(#faf5ee, #34312d)",
  doc="Cards, list groups, accordions, toasts")
T("surface-sunk", "light-dark(#f1f3f5, #1c1f23)", "light-dark(#ece4d4, #2d2a27)",
  doc="Wells, code blocks, readonly fields", bs=["--bs-secondary-bg"])
T("surface-raised", "light-dark(#f8f9fa, #343a40)", "light-dark(#fffcf7, #413c37)",
  doc="Slightly raised surfaces: light buttons, .alert-light, .table-light", bs=["--bs-tertiary-bg"])
T("surface-overlay", "light-dark(#fff, #343a40)", "light-dark(#fdf9f2, #48423c)",
  doc="Dropdowns, popovers, modals, offcanvas: never darker than what they lie on")
T("surface-hover", "light-dark(#eef0f3, color-mix(in oklab, $body-color 8%, $surface))",
  "light-dark(rgb(90 70 40 / .07), rgb(255 240 220 / .06))",
  doc="Hover on neutral surfaces (felt: a translucent shade, so the fibres run through)")
T("surface-pressed", "light-dark(#d4d9e0, color-mix(in oklab, $body-color 18%, $surface))",
  "light-dark(rgb(90 70 40 / .18), rgb(255 240 220 / .14))", doc="Pressed and chosen neutral surfaces")
T("field", "light-dark(#fff, #212529)", "light-dark(#fffdf8, #2b2724)", doc="Inputs and selects")
T("field-addon", "light-dark(#f1f3f5, #2b3035)", "light-dark(#f3eee4, #3a3530)",
  doc="Input-group addons and the file button: a step lighter than the field in dark mode")
T("field-disabled", "light-dark(#e9ecef, #343a40)", "light-dark(#e4dac7, #3a3631)",
  doc="Disabled fields, a step past readonly (--felt-surface-sunk)")
T("field-invalid", "$field", "light-dark(#fdf3ee, #3a2823)", doc="Invalid fields")
T("border-width", "1px", doc="Hairlines")
T("border-style", "solid", doc="Hairlines")
T("border-color", "light-dark(#e2e5ea, #41474f)", "light-dark(#c9bba3, #48423b)",
  doc="Hairlines (felt: hidden under the seams, but they keep their width)")
T("border-color-strong", "light-dark(#858f9e, #737b84)", "light-dark(#847b6a, #857a6c)",
  doc="Control outlines that reach 3:1 (checkboxes, radios)")
T("link-decoration", "underline", doc="Links")
T("link-color", "light-dark($primary, #8fb2e8)", "light-dark(#34578c, #8fb2e8)", doc="Links; .link-* set it too")
T("track", "light-dark(#e3e7ec, #3a4047)", "light-dark(rgb(90 70 40 / .16), rgb(0 0 0 / .36))",
  doc="The empty part of progress bars, ranges and the off switch; use it for tracks of your own. "
      "Felt: one groove pressed into the felt, translucent")
T("backdrop", "light-dark(rgb(16 24 40 / .45), rgb(0 0 0 / .6))", "light-dark(rgb(50 35 15 / .26), rgb(10 8 5 / .5))",
  doc="Modal and offcanvas backdrops", bs=["--bs-backdrop-bg", "--bs-modal-backdrop-bg", "--bs-offcanvas-backdrop-bg"])
T("highlight-bg", "$warning-subtle", "light-dark(#f0d8a2, color-mix(in oklab, $warning 35%, $surface))",
  doc="<mark> and .mark")
T("highlight-color", "inherit", doc="Text in <mark>")
T("code-color", "$danger-emphasis", doc="Inline <code>")

# ------------------------------------------------------------------ interaction

group("interaction", "Interaction", "States change the fill, never the text: hover mixes it towards "
      "--felt-hover-ink, pressing towards --felt-press-ink, away from the ink so it keeps its contrast.")
T("hover-ink", "light-dark(#000, #fff)", doc="What fills are mixed with on hover")
T("press-ink", "#000", doc="What fills are mixed with when pressed")
T("hover-mix", "8%", doc="How much of it a hovered fill takes")
T("active-mix", "14%", doc="How much of it a pressed fill takes")
T("select-mix", "18%", doc="A neutral button pressed or chosen: a clear step past its hover")
T("disabled-opacity", ".55", dark=".45", doc="Disabled controls in the clean look (felt pieces fade into the page instead)")
T("focus-ring-color", "light-dark(color-mix(in oklab, $primary 50%, transparent), color-mix(in oklab, $link-color 60%, transparent))",
  doc="Focus rings; .focus-ring-* set it too")
T("focus-ring-width", ".25rem", doc="Focus rings of fields and .focus-ring")
T("focus-ring-x", "0", doc=".focus-ring: horizontal offset")
T("focus-ring-y", "0", doc=".focus-ring: vertical offset")
T("focus-ring-blur", "0", doc=".focus-ring: blur")

# ------------------------------------------------------------------ type

group("type", "Type")
T("font", 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif', doc="Body font",
  bs=["--bs-font-sans-serif", "--bs-body-font-family"])
T("font-heading", "$font", doc="Headings")
T("font-mono", "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace", doc="Code", bs=["--bs-font-monospace"])
T("body-font-size", "1rem", doc="Body text")
T("body-font-weight", "400", doc="Body text")
T("body-line-height", "1.5", doc="Body text")
T("heading-color", "inherit", doc="Headings")
T("body-text-align", "start", doc="Body text")

# ------------------------------------------------------------------ layout

group("layout", "Spacing, radius and shadows")
for n, v in enumerate([".25rem", ".5rem", "1rem", "1.5rem", "3rem"], 1):
    T(f"space-{n}", v, doc=f"Spacer {n}, the same scale as the spacing utilities")
T("container-max", "1080px", doc="Width of .container")
for bp, width in {"xs": 0, **BREAKPOINTS}.items():
    T(f"breakpoint-{bp}", f"{width}px" if width else "0", doc=f"Breakpoint {bp} (for scripts; media queries can't read it)")
for size, (clean, felt) in {"sm": ("6px", "5px"), "": ("10px", "12px"), "lg": ("14px", "18px"),
                            "xl": ("20px", "24px"), "xxl": ("32px", "36px")}.items():
    T(f"radius-{size}".rstrip("-"), clean, felt, doc=f"Corner radius{' ' + size if size else ''}",
      bs=[f"--bs-border-radius{'-' + size if size else ''}"] + (["--bs-border-radius-2xl"] if size == "xxl" else []))
T("radius-pill", "999px", doc="Pills", bs=["--bs-border-radius-pill"])
T("shadow-sm", "inset 0 1px 0 light-dark(transparent, rgb(255 255 255 / .04)), 0 1px 2px light-dark(rgb(16 24 40 / .06), rgb(0 0 0 / .3))",
  doc="Clean-look shadows, darker in dark mode", bs=["--bs-box-shadow-sm"])
T("shadow", "inset 0 1px 0 light-dark(transparent, rgb(255 255 255 / .04)), 0 1px 3px light-dark(rgb(16 24 40 / .08), rgb(0 0 0 / .35)), "
  "0 1px 2px light-dark(rgb(16 24 40 / .04), rgb(0 0 0 / .2))", doc="Clean-look shadow of cards", bs=["--bs-box-shadow"])
T("shadow-lg", "0 12px 32px -8px light-dark(rgb(16 24 40 / .22), rgb(0 0 0 / .6)), 0 2px 6px light-dark(rgb(16 24 40 / .08), rgb(0 0 0 / .3))",
  doc="Clean-look shadow of what floats: menus, modals, toasts", bs=["--bs-box-shadow-lg"])
group("images", "Images")
T("gradient", "linear-gradient(180deg, rgb(255 255 255 / .15), rgb(255 255 255 / 0))", "$texture, $patch-dome",
  doc=".bg-gradient: a sheen from the top; on felt the felt keeps its texture and swells like a patch")


def chevron(colour):
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='m3.5 6 4.5 4.5L12.5 6' "
            f"fill='none' stroke='%23{colour}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\")")


T("_chevron-clean", chevron("677084"))
T("_chevron-clean-dark", chevron("a2aab4"))
T("_chevron-felt", chevron("1e2b45"))
T("_chevron-felt-dark", chevron("efe7da"))
T("select-chevron", "$_chevron-clean", "$_chevron-felt", dark="$_chevron-clean-dark", felt_dark="$_chevron-felt-dark",
  doc="The select's arrow: an image, so one per look and colour mode", bs=["--bs-form-select-bg-img"])

# ------------------------------------------------------------------ felt

group("texture", "Felt textures", "The felt itself. Light pieces (the page, cards, light buttons) are cut from the sheet: "
      "the cream felt multiplied into their colour, charcoal felt in dark mode. Coloured pieces are patches: grey felt "
      "laid over their colour in soft-light.")
T("texture", None, 'url("img/felt.svg")', doc="Felt of coloured patches (grey, blended in soft-light)")
T("texture-size", None, "256px", doc="Its tile size")
T("texture-light", None, 'url("img/felt-light.webp")', doc="Cream felt, multiplied into light pieces")
T("texture-light-size", None, "256px", doc="Its tile size")
T("texture-dark", None, 'url("img/felt-dark.webp")', doc="Charcoal felt for light pieces in dark mode")
T("texture-sheet", None, "$texture-light", felt_dark="$texture-dark", doc="The sheet light pieces are cut from in this mode")
T("texture-sheet-size", None, "$texture-light-size", doc="Its tile size")
T("texture-sheet-blend", None, "multiply", felt_dark="soft-light", doc="How the sheet is blended into a piece's colour")
T("texture-veil", None, "transparent", felt_dark="color-mix(in srgb, $body-bg 30%, transparent)",
  doc="A veil over the page's felt, so it is the quietest of all")

group("patch", "Patches and depth", "Pieces are about 2 mm thick: a darker cut edge below, edges rolling off outside "
      "the seam, a soft cast shadow.")
T("patch-shadow", None,
  "0 0 0 1px light-dark(rgb(80 60 40 / .16), transparent), 0 0 1px .5px light-dark(transparent, rgb(0 0 0 / .35)), "
  "0 0 0 .5px light-dark(transparent, rgb(255 240 220 / .06)), inset 0 -2px 0 light-dark(rgb(80 60 40 / .14), rgb(0 0 0 / .14)), "
  "inset 0 1px 0 light-dark(rgb(255 255 255 / .08), rgb(255 240 220 / .09)), 0 1px 0 light-dark(rgb(80 60 40 / .22), rgb(0 0 0 / .45)), "
  "0 1px 1.5px light-dark(rgb(70 50 30 / .32), transparent), 0 4px 12px light-dark(rgb(70 50 30 / .16), transparent), "
  "0 6px 14px -6px light-dark(transparent, rgb(0 0 0 / .6))",
  doc="Large pieces (cards, navbar, list groups, modals): in light mode a dark cut edge and a contact shadow, in the dark a soft rim and a wide halo")
T("patch-dome", None, "radial-gradient(120% 95% at 35% 10%, rgb(255 255 255 / .2), transparent 60%)",
  doc="The light on a coloured patch's swell")
T("patch-cut", None, "light-dark(#2a1a08, #000)", doc="What a patch's cut edge is darkened with")
T("patch-edge-light", None, "light-dark(#cbbca2, #1d1a17)", doc="Cut edge of light patches")
T("patch-shadow-near", None, "light-dark(rgb(60 40 15 / .26), rgb(0 0 0 / .35))", doc="Patches' short cast shadow")
T("patch-shadow-far", None, "light-dark(rgb(60 40 15 / .36), rgb(0 0 0 / .5))", doc="Patches' long cast shadow")

group("groove", "Grooves and nap", "Where the felt is pressed in: tracks, toggle groups, pagination, pockets, folds "
      "and the fields lying in it.")
T("groove-bg", None, "light-dark(rgb(90 70 40 / .13), rgb(0 0 0 / .3))",
  doc="A groove's shade: translucent, so the fibres of the piece run through")
T("groove-shade", None, "light-dark(rgb(70 50 20 / .16), rgb(0 0 0 / .45))", doc="A groove's shaded top wall")
T("groove-lip", None, "light-dark(rgb(255 255 255 / .35), rgb(255 255 255 / .06))", doc="A groove's lit lower lip")
T("groove-shadow", None, "light-dark(rgb(70 50 20 / .25), rgb(0 0 0 / .5))", doc="Inset shadow of pressed felt")
T("groove-shadow-field", None, "light-dark(rgb(60 40 20 / .08), rgb(0 0 0 / .3))", doc="Inset shadow of fields and checks")
T("nap-highlight", None, "light-dark(rgb(255 255 255 / .5), rgb(255 240 220 / .07))", doc="Light catching the nap at an edge")
T("groove-fold", None, "inset 1px 0 0 color-mix(in srgb, $groove-shadow 55%, transparent), inset 2px 0 0 color-mix(in srgb, $nap-highlight 40%, transparent)",
  doc="A fold pressed into one piece where two parts meet (left edge): button groups, horizontal lists, table columns")
T("groove-fold-y", None, "inset 0 1px 0 color-mix(in srgb, $groove-shadow 55%, transparent), inset 0 2px 0 color-mix(in srgb, $nap-highlight 28%, transparent)",
  doc="The same at the top edge")
T("wool", None, "#fff4e0", doc="Undyed wool: what white pieces (swatches, range thumbs, light dots) are dyed")
T("wool-knob", None, "light-dark(#fbf7ee, #e4dccd)", doc="The switch's knob")

group("thread", "Seams and thread", "Seams are 9-slice images of drawn thread (tools/build_assets.py), blended into the "
      "felt with hard-light and tinted by a filter: by default a darker tone of the felt underneath.")
T("thread-relief", None, "drop-shadow(0 .5px 0 rgb(255 255 255 / .3))",
  felt_dark="drop-shadow(0 1px 0 rgb(0 0 0 / .7)) drop-shadow(0 -.5px 0 rgb(255 240 220 / .12))", doc="Light and shadow along the thread")
T("thread-filter", None, "brightness(.42) sepia(.3) $thread-relief", felt_dark="brightness(.67) sepia(.22) $thread-relief",
  doc="Thread colour on light felt")
T("thread-filter-cream", None, "brightness(.4) sepia(.45) $thread-relief", doc="Thread on the lightest felt (cream pieces): a little darker")
T("thread-filter-patch", None, "brightness(1)", felt_dark="brightness(.9)", doc="Thread on coloured patches: a lighter tone of the patch")
T("thread-filter-ink", None,
  "brightness(.5) contrast(4) brightness(.5) sepia(.5) hue-rotate(180deg) saturate(1.5) drop-shadow(0 .5px 0 rgb(255 255 255 / .35))",
  felt_dark="brightness(.92) sepia(.15) drop-shadow(0 1px 0 rgb(0 0 0 / .7)) drop-shadow(0 -.5px 0 rgb(255 240 220 / .12))",
  doc="Thread in the ink's tone, for a mark sewn into any felt (a chosen swatch's ring)")
T("thread-strength", None, ".72", felt_dark=".52", doc="How strongly the thread shows on light felt (0–1)")
T("thread-strength-patch", None, ".55", felt_dark=".38", doc="… on coloured patches")
T("thread-strength-row", None, ".58", doc="Stitch rows dividing a piece, relative to its outer seam")
T("thread-strength-rule", None, ".4", doc="hr and .vr")
T("_rule-thread", None, "light-dark(color-mix(in oklab, currentColor 50%, $secondary-color), color-mix(in oklab, currentColor 75%, $secondary-color))")
T("_rule-blend", None, "multiply", felt_dark="hard-light")
T("_rule-in-piece", None, ".44", felt_dark=".4")
T("seam-inset", None, "5px", doc="How far in from the edge a seam is sewn (cards and other large pieces: 9px)")
T("_seam-img", None, 'url("img/seam-md.svg")')
T("_seam-slice", None, "$_seam-md-slice")
T("_seam-width", None, "$_seam-md-width")
STITCHES = json.loads((Path(__file__).parent / "stitches.json").read_text())
for key, value in STITCHES.items():
    docs = {"stitch-length": "Length of a stitch in SVG drawings (.stitches)", "stitch-pitch": "Stitch plus gap",
            "stitch-shadow": "The thread's shadow in SVG drawings"}
    T(key, None, value, doc=docs.get(key, ""))

group("felt-states", "Felt states")
T("_disabled-tone", None, "50%", felt_dark="35%")
T("_disabled-ink", None, "68%", felt_dark="80%")
T("_tooltip-texture", None, "$texture", felt_dark="$texture-light")
T("_tooltip-texture-blend", None, "soft-light", felt_dark="multiply")


TOKENS = [t for _, _, _, tokens in GROUPS for t in tokens]
BY_NAME = {t.name: t for t in TOKENS}
