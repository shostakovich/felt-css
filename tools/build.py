#!/usr/bin/env python3
"""Writes the generated parts of felt.css between their markers; everything else stays hand-written.

    python3 tools/build.py           # rewrite the blocks
    python3 tools/build.py --check   # fail if felt.css isn't what the generators write (CI)

  tokens      @layer tokens, from tools/feltgen/tokens.py (feltgen/tokens_css.py says how)
  grid, families, utilities
              Bootstrap's grid and utilities per breakpoint (feltgen/utilities.py)
  variants    colour and breakpoint variants of the components (feltgen/variants.py)

Plain python3, no packages. Change the generators, not the blocks.
"""
import sys

from feltgen import utilities, variants
from feltgen.config import CSS
from feltgen.css import replace_block
from feltgen.tokens_css import token_css


def build(text):
    blocks = {"tokens": (token_css(), "tools/feltgen/tokens.py")}
    blocks |= {k: (v, "tools/feltgen/utilities.py") for k, v in utilities.blocks().items()}
    blocks |= {k: (v, "tools/feltgen/variants.py") for k, v in variants.blocks().items()}
    for block, (lines, source) in blocks.items():
        if f"/* {block}:start */" in text:
            text = replace_block(text, block, lines, source)
        elif block not in variants.OPTIONAL:
            raise SystemExit(f"felt.css: no markers for {block}")
    return text


def main():
    old = CSS.read_text()
    new = build(old)
    if "--check" in sys.argv:
        if new != old:
            raise SystemExit("felt.css is out of date: run python3 tools/build.py")
        print("felt.css is up to date")
        return
    CSS.write_text(new)
    print(f"{CSS.name}: {len(new.splitlines())} lines")


if __name__ == "__main__":
    main()
