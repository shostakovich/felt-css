#!/usr/bin/env python3
"""Builds the documentation site in docs/ from the page fragments in docs-src/.

    python3 tools/build_docs.py            # plain python3, no packages
    python3 tools/build_docs.py --strict   # fail on missing pages or unknown classes
    python3 tools/build_docs.py --site _site   # the published layout: home page at the root, docs under docs/

Each fragment starts with a front-matter comment (title, description, optional layout) and holds the
page body. These tags are expanded:

    <example class="extra classes">…</example>   rendered markup followed by its highlighted source
    <codeblock lang="html|css|js|sh">…</codeblock>   highlighted source only (raw text, no escaping needed)
    <tokens group="palette theme"></tokens>      the global tokens of those groups (tools/feltgen/tokens.py)
    <cssvars name="btn"></cssvars>               a component's tokens, read from felt.css between
                                                 /* docs:btn-vars:start */ and /* docs:btn-vars:end */

--strict also fails on tokens: felt.css may only declare --felt-* and --_* tokens, every public one must be
documented (tokens.py, a <cssvars> block shown on a page, or named on a page), and every --felt-* token a page
names must exist.

Generated pages go to docs/<section>/<page>/index.html; the hand-written examples in docs/examples/*/
are left alone.
"""

import html
import os
import re
import sys
import textwrap
from pathlib import Path

from feltgen import parity
from feltgen.css import name as token_name, refs
from feltgen.tokens import GROUPS

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs-src"
OUT = ROOT / "docs"
REPO_URL = "https://github.com/shostakovich/felt-css"

NAV = [
    ("Getting started", "getting-started", [
        ("introduction", "Introduction"),
        ("looks", "Felt and clean"),
        ("felt-svg", "Felt in SVG"),
        ("color-modes", "Color modes"),
        ("javascript", "JavaScript"),
    ]),
    ("Customize", "customize", [
        ("color", "Color"),
        ("css-variables", "CSS variables"),
        ("felt", "Felt"),
    ]),
    ("Layout", "layout", [
        ("breakpoints", "Breakpoints"),
        ("containers", "Containers"),
        ("grid", "Grid"),
        ("columns", "Columns"),
        ("gutters", "Gutters"),
        ("utilities", "Utilities"),
        ("z-index", "Z-index"),
    ]),
    ("Content", "content", [
        ("reboot", "Reboot"),
        ("typography", "Typography"),
        ("images", "Images"),
        ("tables", "Tables"),
        ("figures", "Figures"),
    ]),
    ("Forms", "forms", [
        ("overview", "Overview"),
        ("form-control", "Form control"),
        ("select", "Select"),
        ("checks-radios", "Checks & radios"),
        ("range", "Range"),
        ("input-group", "Input group"),
        ("floating-labels", "Floating labels"),
        ("layout", "Layout"),
        ("validation", "Validation"),
    ]),
    ("Components", "components", [
        ("accordion", "Accordion"),
        ("alerts", "Alerts"),
        ("badge", "Badge"),
        ("breadcrumb", "Breadcrumb"),
        ("buttons", "Buttons"),
        ("button-group", "Button group"),
        ("card", "Card"),
        ("carousel", "Carousel"),
        ("close-button", "Close button"),
        ("collapse", "Collapse"),
        ("dropdowns", "Dropdowns"),
        ("list-group", "List group"),
        ("modal", "Modal"),
        ("navbar", "Navbar"),
        ("navs-tabs", "Navs & tabs"),
        ("offcanvas", "Offcanvas"),
        ("pagination", "Pagination"),
        ("placeholders", "Placeholders"),
        ("popovers", "Popovers"),
        ("progress", "Progress"),
        ("scrollspy", "Scrollspy"),
        ("spinners", "Spinners"),
        ("stat", "Stat tiles"),
        ("toasts", "Toasts"),
        ("tooltips", "Tooltips"),
    ]),
    ("Helpers", "helpers", [
        ("clearfix", "Clearfix"),
        ("color-background", "Color & background"),
        ("colored-links", "Colored links"),
        ("focus-ring", "Focus ring"),
        ("icon-link", "Icon link"),
        ("position", "Position"),
        ("ratio", "Ratio"),
        ("stacks", "Stacks"),
        ("stretched-link", "Stretched link"),
        ("text-truncation", "Text truncation"),
        ("vertical-rule", "Vertical rule"),
        ("visually-hidden", "Visually hidden"),
    ]),
    ("Utilities", "utilities", [
        ("background", "Background"),
        ("borders", "Borders"),
        ("colors", "Colors"),
        ("display", "Display"),
        ("flex", "Flex"),
        ("float", "Float"),
        ("interactions", "Interactions"),
        ("link", "Link"),
        ("object-fit", "Object fit"),
        ("opacity", "Opacity"),
        ("overflow", "Overflow"),
        ("position", "Position"),
        ("shadows", "Shadows"),
        ("sizing", "Sizing"),
        ("spacing", "Spacing"),
        ("text", "Text"),
        ("vertical-align", "Vertical align"),
        ("visibility", "Visibility"),
        ("z-index", "Z-index"),
    ]),
]

STANDALONE = ["index", "examples/index"]

# classes the docs chrome and the example frames bring along, plus Bootstrap JS hooks
DOCS_CLASSES_PREFIXES = ("bd-", "tok-", "language-")


def warn(message, problems):
    problems.append(message)
    print(f"warning: {message}", file=sys.stderr)


# ------------------------------------------------------------------ highlighting

def highlight_html(source):
    out, pos = [], 0
    token = re.compile(r"<!--.*?-->|</?[A-Za-z][^>]*>", re.S)
    for match in token.finditer(source):
        out.append(html.escape(source[pos:match.start()], quote=False))
        out.append(highlight_tag(match.group(0)))
        pos = match.end()
    out.append(html.escape(source[pos:], quote=False))
    return "".join(out)


def highlight_tag(tag):
    if tag.startswith("<!--"):
        return f'<span class="tok-com">{html.escape(tag, quote=False)}</span>'
    head = re.match(r"(</?)([A-Za-z][\w-]*)", tag)
    rest = tag[head.end():]
    parts = [f'<span class="tok-punct">{html.escape(head.group(1))}</span><span class="tok-tag">{head.group(2)}</span>']
    attr = re.compile(r'(\s+)([^\s=/>]+)(?:(=)("[^"]*"|\'[^\']*\'|[^\s>]+))?|(\s*/?>)', re.S)
    pos = 0
    for match in attr.finditer(rest):
        if match.start() != pos:
            parts.append(html.escape(rest[pos:match.start()], quote=False))
        space, name, eq, value, end = match.groups()
        if end is not None:
            parts.append(f'<span class="tok-punct">{html.escape(end, quote=False)}</span>')
        else:
            parts.append(space + f'<span class="tok-attr">{html.escape(name, quote=False)}</span>')
            if eq:
                parts.append(f'<span class="tok-punct">=</span><span class="tok-val">{html.escape(value, quote=False)}</span>')
        pos = match.end()
    parts.append(html.escape(rest[pos:], quote=False))
    return "".join(parts)


def highlight_code(source, lang):
    if lang == "html":
        return highlight_html(source)
    patterns = {
        "css": r"(?P<com>/\*.*?\*/)|(?P<val>\"[^\"]*\"|'[^']*')|(?P<attr>--[\w-]+|[\w-]+(?=\s*:(?!:)))|(?P<tag>@[\w-]+|[.#][\w-]+)",
        "js": r"(?P<com>//[^\n]*|/\*.*?\*/)|(?P<val>\"[^\"]*\"|'[^']*'|`[^`]*`)|(?P<tag>\b(?:const|let|new|function|return|if|else|for|of|document|import|export|from|async|await)\b)",
        "sh": r"(?P<com>#[^\n]*)|(?P<val>\"[^\"]*\"|'[^']*')",
    }.get(lang)
    if not patterns:
        return html.escape(source, quote=False)
    out, pos = [], 0
    for match in re.finditer(patterns, source, re.S):
        out.append(html.escape(source[pos:match.start()], quote=False))
        kind = match.lastgroup
        out.append(f'<span class="tok-{kind}">{html.escape(match.group(0), quote=False)}</span>')
        pos = match.end()
    out.append(html.escape(source[pos:], quote=False))
    return "".join(out)


def tidy(source):
    lines = source.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return textwrap.dedent("\n".join(lines))


def code_box(source, lang):
    return (f'<div class="bd-code"><button type="button" class="bd-copy btn btn-sm" aria-label="Copy to clipboard">Copy</button>'
            f'<pre><code class="language-{lang}">{highlight_code(source, lang)}</code></pre></div>')


# ------------------------------------------------------------------ fragments

def parse_attrs(text):
    return {m.group(1): html.unescape(m.group(2)) for m in re.finditer(r'([\w-]+)="([^"]*)"', text or "")}


def expand(body):
    """Swaps examples and code blocks for placeholders, so headings inside examples stay out of the TOC."""
    blocks = []

    def keep(markup):
        blocks.append(markup)
        return f"\x00{len(blocks) - 1}\x00"

    def example(match):
        attrs = parse_attrs(match.group(1))
        markup = tidy(match.group(2))
        classes = " ".join(filter(None, ["bd-example", attrs.get("class")]))
        style = f' style="{attrs["style"]}"' if "style" in attrs else ""
        style += "".join(f' {k}="{attrs[k]}"' for k in ("data-look", "data-bs-theme") if k in attrs)
        rendered = f'<div class="{classes}"{style}>\n{markup}\n</div>'
        code = "" if attrs.get("code") == "false" else code_box(markup, "html")
        return keep(f'<div class="bd-example-snippet">{rendered}{code}</div>')

    def codeblock(match):
        attrs = parse_attrs(match.group(1))
        return keep(code_box(tidy(match.group(2)), attrs.get("lang", "html")))

    def tokens(match):
        return keep(token_tables(parse_attrs(match.group(1)).get("group", "").split()))

    def cssvars(match):
        return keep(cssvars_table(parse_attrs(match.group(1))["name"]))

    body = re.sub(r"<tokens\b([^>]*)>\s*</tokens>", tokens, body)
    body = re.sub(r"<cssvars\b([^>]*)>\s*</cssvars>", cssvars, body)
    body = re.sub(r"<codeblock\b([^>]*)>(.*?)</codeblock>", codeblock, body, flags=re.S)
    body = re.sub(r"<example\b([^>]*)>(.*?)</example>", example, body, flags=re.S)
    return body, blocks


# ------------------------------------------------------------------ tokens

FELT_CSS = (ROOT / "felt.css").read_text()
JS_CONTRACT = {"--bs-position"}   # Bootstrap's JS reads it
SHOWN_BLOCKS = set()   # the docs:*-vars blocks some page shows
_MAP = None


def bs_map():
    global _MAP
    if _MAP is None:
        _MAP = parity.token_map()
    return _MAP


def bs_cell(token):
    names = parity.bootstrap_names(token, bs_map())
    return "<br>".join(f"<code>{n}</code>" for n in names)


def value_cell(value):
    return f"<code>{html.escape(refs(value))}</code>"


def token_tables(keys):
    out = []
    for key, title, intro, tokens in GROUPS:
        if key not in keys:
            continue
        rows = []
        for t in (t for t in tokens if t.public):
            clean, dark, felt, felt_dark = t.values()
            value = "" if t.felt_only else value_cell(clean)
            if dark != clean and not t.felt_only:
                value += f' <span class="bd-token-mode">dark</span> {value_cell(dark)}'
            if felt != clean or t.felt_only:
                value += (f'{"<br>" if value else ""}<span class="bd-token-look">felt</span> {value_cell(felt)}')
                if felt_dark != felt:
                    value += f' <span class="bd-token-mode">dark</span> {value_cell(felt_dark)}'
            rows.append((token_name(t.name), value, bs_cell(token_name(t.name)), html.escape(t.doc)))
        with_bs = any(r[2] for r in rows)
        body = "".join(f"<tr><td><code>{n}</code></td><td>{v}</td>{f'<td>{b}</td>' if with_bs else ''}<td>{d}</td></tr>"
                       for n, v, b, d in rows)
        intro_html = f"<p>{html.escape(intro)}</p>" if intro and len(keys) > 1 else ""
        heading = f"<h3>{title}</h3>" if len(keys) > 1 else ""
        out.append(f'{heading}{intro_html}<div class="table-responsive bd-tokens"><table class="table table-sm">'
                   f"<thead><tr><th>Token</th><th>Value</th>{'<th>Bootstrap</th>' if with_bs else ''}<th>Used for</th></tr></thead>"
                   f"<tbody>{body}</tbody></table></div>")
    return "".join(out)


def css_block(name):
    m = re.search(rf"/\* docs:{re.escape(name)}-vars:start \*/(.*?)/\* docs:{re.escape(name)}-vars:end \*/", FELT_CSS, re.S)
    if not m:
        raise SystemExit(f"felt.css has no /* docs:{name}-vars:start */ block")
    return m.group(1)


def cssvars_table(name):
    SHOWN_BLOCKS.add(name)
    block = re.sub(r"/\*.*?\*/", "", css_block(name), flags=re.S)
    rows = []
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]*);", block):
        token, value = m.group(1), " ".join(m.group(2).split())
        if token.startswith("--_"):
            continue
        rows.append(f"<tr><td><code>{token}</code></td><td><code>{html.escape(value)}</code></td><td>{bs_cell(token)}</td></tr>")
    return ('<div class="table-responsive bd-tokens"><table class="table table-sm">'
            "<thead><tr><th>Token</th><th>Default</th><th>Bootstrap</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def token_problems(pages_text):
    """--strict: names, documentation and existence of tokens"""
    problems = []
    css = re.sub(r"/\*.*?\*/", "", FELT_CSS, flags=re.S)
    declared = set(re.findall(r"(--[\w-]+)\s*:", css))
    for t in sorted(declared):
        if not t.startswith(("--felt-", "--_")) and t not in JS_CONTRACT:
            problems.append(f"felt.css declares {t}: tokens are --felt-* (public) or --_* (internal)")
    documented = {token_name(t.name) for _, _, _, ts in GROUPS for t in ts if t.public and t.doc}
    for block in SHOWN_BLOCKS:
        documented |= set(re.findall(r"(--felt-[\w-]+)\s*:", css_block(block)))
    named = set(re.findall(r"--felt-[\w-]*\w(?![\w*-])", pages_text))   # not a family like --felt-focus-ring-*
    public = set(re.findall(r"--felt-[\w-]*[\w]", css))   # declared, or read with a fallback (set by the page)
    for t in sorted(public - documented - named):
        problems.append(f"{t} is public but no page documents it")
    for t in sorted(named - public):
        problems.append(f"the docs name {t}, which felt.css doesn't declare")
    return problems


def restore(body, blocks):
    return re.sub(r"\x00(\d+)\x00", lambda m: blocks[int(m.group(1))], body)


def slugify(text):
    text = re.sub(r"<[^>]+>", "", html.unescape(text)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def add_heading_ids(body):
    toc, seen = [], set()

    def heading(match):
        level, attrs, inner = match.group(1), match.group(2), match.group(3)
        found = re.search(r'\bid="([^"]+)"', attrs)
        anchor = found.group(1) if found else slugify(inner)
        base, n = anchor, 2
        while anchor in seen and not found:
            anchor, n = f"{base}-{n}", n + 1
        seen.add(anchor)
        if not found:
            attrs += f' id="{anchor}"'
        toc.append((int(level), anchor, re.sub(r"<[^>]+>", "", inner)))
        link = f'<a class="bd-anchor" href="#{anchor}" aria-label="Link to this section">#</a>'
        return f"<h{level}{attrs}>{inner}{link}</h{level}>"

    body = re.sub(r"<h([23])((?:\s[^>]*)?)>(.*?)</h\1>", heading, body, flags=re.S)
    return body, toc


def toc_html(toc):
    if not toc:
        return ""
    items, open_sub = [], False
    for level, anchor, text in toc:
        if level == 3 and not open_sub and items:
            items[-1] = items[-1].removesuffix("</li>") + "<ul>"
            open_sub = True
        elif level == 2 and open_sub:
            items.append("</ul></li>")
            open_sub = False
        items.append(f'<li><a href="#{anchor}">{text}</a></li>')
    if open_sub:
        items.append("</ul></li>")
    return "<ul>" + "".join(items) + "</ul>"


def read_fragment(path):
    text = path.read_text()
    meta_match = re.match(r"\s*<!--(.*?)-->", text, re.S)
    meta = {}
    if meta_match:
        for line in meta_match.group(1).strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        text = text[meta_match.end():]
    return meta, text


# ------------------------------------------------------------------ chrome

def sidebar(current, prefix):
    groups = []
    for title, section, pages in NAV:
        links = []
        for slug, label in pages:
            active = (section, slug) == current
            attrs = ' class="nav-link active" aria-current="page"' if active else ' class="nav-link"'
            links.append(f'<li class="nav-item"><a{attrs} href="{prefix}{section}/{slug}/">{label}</a></li>')
        groups.append(f'<li class="bd-nav-group"><strong class="bd-nav-heading">{title}</strong>'
                      f'<ul class="nav nav-pills flex-column">{"".join(links)}</ul></li>')
    return '<ul class="list-unstyled mb-0">' + "".join(groups) + "</ul>"


def prev_next(current, prefix):
    flat = [(s, slug, label) for _, s, pages in NAV for slug, label in pages]
    keys = [(s, slug) for s, slug, _ in flat]
    i = keys.index(current)
    links = []
    if i > 0:
        s, slug, label = flat[i - 1]
        links.append(f'<a class="bd-pager-prev" href="{prefix}{s}/{slug}/"><small>Previous</small>{label}</a>')
    if i < len(flat) - 1:
        s, slug, label = flat[i + 1]
        links.append(f'<a class="bd-pager-next" href="{prefix}{s}/{slug}/"><small>Next</small>{label}</a>')
    return f'<nav class="bd-pager" aria-label="Pages">{"".join(links)}</nav>'


def render(layout, meta, body, prefix, repo, current=None):
    body, blocks = expand(body)
    body, toc = add_heading_ids(body)
    body = restore(body, blocks)
    toc_markup = toc_html([t for t in toc if t[0] in (2, 3)])
    section_title = next((t for t, s, _ in NAV if current and s == current[0]), "")
    replacements = {
        "title": meta.get("title", "felt-css"),
        "description": meta.get("description", ""),
        "lead": meta.get("description", ""),
        "section": section_title,
        "root": prefix,
        "repo": repo,
        "repo_url": REPO_URL,
        "sidebar": sidebar(current, prefix) if current else "",
        "toc": toc_markup,
        "pager": prev_next(current, prefix) if current else "",
        "body": body,
        "source": (f"{REPO_URL}/blob/main/docs-src/{current[0]}/{current[1]}.html" if current else ""),
        "layout": meta.get("layout", "docs"),
    }
    out = layout
    # page layout: "docs" pages get sidebar + toc, "home" pages are full width
    if replacements["layout"] != "docs":
        out = re.sub(r"<!-- docs:start -->.*?<!-- docs:end -->", "<!-- home:body -->", out, flags=re.S)
        out = out.replace("<!-- home:body -->", '<main class="bd-home" id="content">{{body}}</main>')
    else:
        out = re.sub(r"<!-- docs:start -->|<!-- docs:end -->", "", out)
    if not toc_markup:
        out = re.sub(r"<!-- toc:start -->.*?<!-- toc:end -->", "", out, flags=re.S)
    out = re.sub(r"<!-- (?:toc):(?:start|end) -->", "", out)
    for key in ("root", "repo"):
        replacements["body"] = replacements["body"].replace("{{" + key + "}}", replacements[key])
    for key, value in replacements.items():
        if key != "body":
            out = out.replace("{{" + key + "}}", value)
    return out.replace("{{body}}", replacements["body"])


# ------------------------------------------------------------------ class check

def known_classes():
    css = (ROOT / "felt.css").read_text() + (ROOT / "docs" / "assets" / "docs.css").read_text()
    return set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", css))


def unknown_classes(markup, known):
    found = set()
    markup = re.sub(r"<code>.*?</code>", "", markup, flags=re.S)
    for attr in re.findall(r'\sclass="([^"]*)"', markup):
        for name in attr.split():
            if name not in known and not name.startswith(DOCS_CLASSES_PREFIXES):
                found.add(name)
    return found


# ------------------------------------------------------------------ main

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(text)
    tmp.replace(path)


# Bootstrap's JS sets these at runtime; they are styled by felt.css under the same names
RUNTIME_CLASSES = {"show", "showing", "hiding", "collapsed", "collapsing", "fade", "active", "disabled"}


def main():
    strict = "--strict" in sys.argv
    site = Path(sys.argv[sys.argv.index("--site") + 1]).resolve() if "--site" in sys.argv else None
    out = site / "docs" if site else OUT
    layout = (SRC / "_layout.html").read_text()
    known = known_classes() | RUNTIME_CLASSES
    problems = []

    jobs = [(name, None) for name in STANDALONE]
    jobs += [(f"{section}/{slug}", (section, slug)) for _, section, pages in NAV for slug, _ in pages]

    for name, current in jobs:
        source = SRC / f"{name}.html"
        depth = name.count("/") + (1 if current else 0)
        prefix = "../" * depth
        target = out / (f"{name}.html" if not current else f"{name}/index.html")
        if not source.exists():
            warn(f"missing page {source.relative_to(ROOT)}", problems)
            title = dict(p for _, s, ps in NAV for p in ps if s == current[0]).get(current[1], name) if current else name
            meta, body = {"title": title, "description": "This page has not been written yet."}, '<p class="text-body-secondary">Coming soon.</p>'
        else:
            meta, body = read_fragment(source)
            missing = unknown_classes(body, known)
            if missing:
                warn(f"{source.relative_to(ROOT)} uses classes felt.css does not define: {' '.join(sorted(missing))}", problems)
        write(target, render(layout, meta, body, prefix, prefix + "../", current))
        if site and name == "index":
            write(site / "index.html", render(layout, meta, body, "docs/", "", current))

    if strict:
        pages_text = "".join(p.read_text() for p in SRC.rglob("*.html")) + (ROOT / "README.md").read_text()
        for problem in token_problems(pages_text):
            warn(problem, problems)
    print(f"built {len(jobs)} pages into {out}")
    if strict and problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
