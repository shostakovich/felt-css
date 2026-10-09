#!/usr/bin/env python3
"""Checks the contrast of the token pairs felt.css sets text and marks on, in clean and felt, light and dark.

    python3 tools/check_contrast.py         # fail on pairs below 4.5:1 (text) or 3:1 (focus rings, outlines)
    python3 tools/check_contrast.py --all   # print every pair

Backgrounds are composed as rendered: the felt photo multiplied into the page and light pieces, grooves, the dome of
patches (tools/feltgen/contrast.py). Plain python3, no packages.
"""
import sys

from feltgen import contrast


def main():
    rows = contrast.report()
    failed = [r for r in rows if r[2] < r[3]]
    for what, mode, ratio, minimum, fg, bg in rows if "--all" in sys.argv else failed:
        mark = "  " if ratio >= minimum else "✗ "
        print(f"{mark}{ratio:5.2f} (≥{minimum}) {mode:11} {what:44} {fg} on {bg}")
    print(f"{len(rows) // 4} pairs in 4 modes; {len(failed)} below their minimum")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
