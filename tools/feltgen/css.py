"""Small helpers for writing CSS: token references and the generated blocks between markers in felt.css."""
import re

from .config import INTERNAL, PREFIX

REF = re.compile(r"\$(_?[a-z0-9]+(?:-[a-z0-9]+)*)")


def name(token):
    """the custom property for a token name: "primary" -> --felt-primary, "_tone" -> --_tone"""
    return INTERNAL + token[1:] if token.startswith("_") else PREFIX + token


def refs(text):
    """$primary -> var(--felt-primary), $_tone -> var(--_tone)"""
    return REF.sub(lambda m: f"var({name(m.group(1))})", text)


def important(rules):
    return [f".{cls} {{ {refs(decl)} !important; }}" for cls, decl in rules]


def indent(lines, n=2):
    return [" " * n + line if line else line for line in lines]


def media(query, lines):
    return [f"@media {query} {{", *indent(lines), "}"]


def replace_block(text, block, lines, source):
    """Swap what stands between /* block:start */ and /* block:end */ for lines, keeping the markers' indentation."""
    start, end = f"/* {block}:start */", f"/* {block}:end */"
    if start not in text or end not in text:
        raise SystemExit(f"felt.css has no {start} … {end}")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    pad = head[head.rfind("\n") + 1:]
    note = f"/* written by {source}; change it there, not these {len(lines)} lines */"
    body = "\n".join(pad + line if line else "" for line in [note, *lines])
    return head + start + "\n" + body + "\n" + pad + end + tail
