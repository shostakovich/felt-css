"""Bootstrap parity: which of Bootstrap's classes and --bs-* tokens felt.css has, and which it leaves out on purpose.

A Bootstrap token maps to a felt token
  1. by name: --bs-X -> --felt-X, when felt.css declares it,
  2. through tokens.py (bs=...) or MAP below, when the names differ,
or it is in ALLOW_TOKENS with the reason it has no counterpart. Classes are either in felt.css or in ALLOW_CLASSES.
The snapshot of Bootstrap's classes and tokens is bootstrap-<version>.json (tools/check_parity.py --snapshot).
"""
import json
import re
from pathlib import Path

from .config import CSS, PREFIX
from .tokens import TOKENS

VERSION = "5.3.8"
SNAPSHOT = Path(__file__).parent / f"bootstrap-{VERSION}.json"

_FOCUS = "focus shows as the global :focus-visible outline in --felt-focus-ring-color, not a box-shadow"
_RGB = "felt colours are light-dark() values, not RGB triplets; opacity utilities fade with color-mix() instead"

# Bootstrap tokens whose felt counterpart has another name (tokens.py lists the global ones itself)
MAP = {
}

# Bootstrap tokens without a felt counterpart, and why
ALLOW_TOKENS = {
    **{f"--bs-{c}-rgb": _RGB for c in ["primary", "secondary", "success", "info", "warning", "danger", "light", "dark",
                                        "white", "black"]},
    **{f"--bs-{t}-rgb": _RGB for t in ["body-color", "body-bg", "emphasis-color", "secondary-color", "secondary-bg",
                                        "tertiary-color", "tertiary-bg", "link-color", "link-hover-color"]},
    "--bs-focus-ring-opacity": "the focus ring colour carries its own transparency (--felt-focus-ring-color)",
    # btn
    "--bs-btn-font-family": "buttons inherit the font; set font-family on .btn",
    "--bs-btn-focus-box-shadow": _FOCUS,
    "--bs-btn-focus-shadow-rgb": _FOCUS,
    # btn-close
    # badge, alert, card, list-group, table, progress, spinner, placeholder
    # nav, navbar, dropdown, breadcrumb, pagination, accordion, modal, offcanvas, toast, tooltip, popover
    # carousel, forms
}

# Bootstrap classes felt.css leaves out, and why
ALLOW_CLASSES = {}


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def preludes(css):
    """the selector of every style rule (not at-rules), comments and declarations dropped"""
    css = strip_comments(css)
    css = re.sub(r'"[^"]*"|\'[^\']*\'', '""', css)
    for m in re.finditer(r"([^{};]+)\{", css):
        prelude = m.group(1).strip()
        if prelude and not prelude.startswith("@") and not re.fullmatch(r"[\d.%\s,fromto]+", prelude):
            yield prelude


def classes(css):
    found = set()
    for prelude in preludes(css):
        found |= set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", prelude))
    return found


def declared_tokens(css):
    return set(re.findall(r"(--[\w-]+)\s*:", strip_comments(css)))


def snapshot(bootstrap_css):
    css = strip_comments(bootstrap_css)
    tokens = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        scope = "global" if re.search(r":root|data-bs-theme", m.group(1)) else "component"
        for name in re.findall(r"(--bs-[\w-]+)\s*:", m.group(2)):
            if tokens.get(name) != "global":
                tokens[name] = scope
    return {"version": VERSION, "classes": sorted(classes(bootstrap_css)), "tokens": dict(sorted(tokens.items()))}


def load():
    return json.loads(SNAPSHOT.read_text())


def token_map(felt_tokens=None):
    """Bootstrap token -> felt token (None: not mapped)"""
    felt_tokens = felt_tokens if felt_tokens is not None else declared_tokens(CSS.read_text())
    out = {}
    for t in TOKENS:
        for bs in t.bs:
            out[bs] = PREFIX + t.name
    for bs in load()["tokens"]:
        if bs in out:
            continue
        if bs in MAP:
            out[bs] = MAP[bs]
        elif PREFIX + bs[len("--bs-"):] in felt_tokens:
            out[bs] = PREFIX + bs[len("--bs-"):]
        else:
            out[bs] = None
    return out


def bootstrap_names(felt_token, mapping=None):
    """the Bootstrap tokens a felt token stands for"""
    mapping = mapping if mapping is not None else token_map()
    return sorted(bs for bs, felt in mapping.items() if felt == felt_token)


def report():
    css = CSS.read_text()
    snap = load()
    felt_classes, felt_tokens = classes(css), declared_tokens(css)
    mapping = token_map(felt_tokens)
    missing_classes = sorted(c for c in snap["classes"] if c not in felt_classes and c not in ALLOW_CLASSES)
    missing_tokens = sorted(t for t in snap["tokens"] if not mapping.get(t) and t not in ALLOW_TOKENS)
    broken = sorted(f"{bs} -> {felt}" for bs, felt in mapping.items() if felt and felt not in felt_tokens)
    stale = sorted([c for c in ALLOW_CLASSES if c in felt_classes] + [t for t in ALLOW_TOKENS if mapping.get(t)])
    unknown = sorted([c for c in ALLOW_CLASSES if c not in snap["classes"]] + [t for t in ALLOW_TOKENS if t not in snap["tokens"]])
    return {"missing_classes": missing_classes, "missing_tokens": missing_tokens, "broken": broken, "stale": stale,
            "unknown": unknown, "classes": len(snap["classes"]), "tokens": len(snap["tokens"])}
