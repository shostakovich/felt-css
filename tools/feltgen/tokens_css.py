"""Writes the tokens from tokens.py as CSS, so that data-look and data-bs-theme work on any element.

- Tokens that are the same everywhere go on :root.
- Tokens that differ between the looks (or are made from ones that do) go on :root (clean), [data-look="felt"] and
  [data-look="clean"]. Colours use light-dark(), which resolves where the colour is used, so they need nothing else.
- Tokens that differ by colour mode but can't use light-dark() (images, filters, numbers) are recomputed on every element
  that sets a look or a theme. They pick their value with two switches that are inherited like any token: --_dark/--_light
  and --_felt/--_clean are each either empty or invalid ("space toggles"), so `var(--_felt) var(--_dark) value` is only
  valid in felt and dark mode, and var()'s fallback takes the next case.
"""
import re

from .css import name, refs
from .tokens import BY_NAME, GROUPS, TOKENS

LOOK_SWITCHES = {"felt": "--_felt: ; --_clean: initial;", "clean": "--_felt: initial; --_clean: ;"}
THEME_SWITCHES = {"dark": "--_dark: ; --_light: initial;", "light": "--_dark: initial; --_light: ;"}
REF = re.compile(r"\$(_?[a-z0-9]+(?:-[a-z0-9]+)*)")


def deps(token):
    found = set()
    for value in token.values():
        for ref in REF.findall(value or ""):
            if ref not in BY_NAME:
                raise SystemExit(f"tokens.py: {token.name} refers to unknown token ${ref}")
            found.add(ref)
    return found


def closure(test):
    """tokens for which test holds, or which are made from one"""
    marked = {t.name for t in TOKENS if test(t)}
    changed = True
    while changed:
        changed = False
        for t in TOKENS:
            if t.name not in marked and deps(t) & marked:
                marked.add(t.name)
                changed = True
    return marked


def by_theme(t):
    cl, cd, fl, fd = t.values()
    return cl != cd or fl != fd


def by_look(t):
    cl, cd, fl, fd = t.values()
    return cl != fl or cd != fd


THEMED = closure(by_theme)
LOOKED = closure(by_look)


def declare(token, value):
    return f"{name(token.name)}: {refs(value)};"


def switched(token):
    """a token that differs by colour mode: its four cases, picked by the switches"""
    cl, cd, fl, fd = token.values()
    base = token.name.lstrip("_")
    helper = lambda case: f"--_v-{base}-{case}"   # noqa: E731
    if cl == fl and cd == fd:
        cases = [("d", "$_dark", cd)]
    elif cl == cd and fl == fd:
        cases = [("f", "$_felt", fl)]
    else:
        cases = [("fd", "$_felt $_dark", fd), ("fl", "$_felt $_light", fl), ("cd", "$_clean $_dark", cd)]
    cases = [c for c in cases if c[2] != cl]
    if not cases:
        return [declare(token, cl)]
    pick = refs(cl)
    for case, _, _ in reversed(cases):
        pick = f"var({helper(case)}, {pick})"
    lines = [f"{name(token.name)}: {pick};"]
    lines += [f"{helper(case)}: {refs(switch)} {refs(value)};" for case, switch, value in cases]
    return lines


def block(selector, lines, comment=None):
    out = [f"/* {comment} */"] if comment else []
    return out + [f"{selector} {{", *("  " + line for line in lines), "}"]


def grouped(pick, render):
    lines = []
    for _, title, _, tokens in GROUPS:
        body = [line for t in tokens if pick(t) for line in render(t)]
        if body:
            lines += [f"/* {title.lower()} */", *body]
    return lines


def token_css():
    root = grouped(lambda t: t.name not in THEMED and not t.felt_only, lambda t: [declare(t, t.values()[0])])
    felt = grouped(lambda t: t.name not in THEMED and (t.name in LOOKED or t.felt_only), lambda t: [declare(t, t.values()[2])])
    clean = grouped(lambda t: t.name not in THEMED and t.name in LOOKED and not t.felt_only, lambda t: [declare(t, t.values()[0])])
    themed = grouped(lambda t: t.name in THEMED, switched)
    return [
        *block(":root", ["color-scheme: light dark;", LOOK_SWITCHES["clean"], THEME_SWITCHES["light"], *root],
               "the clean look; colours are light-dark(light, dark) and follow color-scheme: the system's, or data-bs-theme's"),
        "@media (prefers-color-scheme: dark) {",
        *("  " + line for line in block(":root", [THEME_SWITCHES["dark"]])),
        "}",
        *block('[data-bs-theme="light"]', ["color-scheme: light;", THEME_SWITCHES["light"]]),
        *block('[data-bs-theme="dark"]', ["color-scheme: dark;", THEME_SWITCHES["dark"]]),
        *block('[data-look="felt"]', [LOOK_SWITCHES["felt"], *felt], "the felt look, on any element"),
        *block('[data-look="clean"]', [LOOK_SWITCHES["clean"], *clean], "and back to clean inside it"),
        *block(':root, [data-look], [data-bs-theme]', themed,
               "what differs by colour mode but isn't a colour: recomputed wherever the look or the theme changes"),
    ]
