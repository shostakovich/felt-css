#!/usr/bin/env python3
"""Checks felt.css against Bootstrap's classes and tokens (pinned in tools/feltgen/bootstrap-<version>.json).

    python3 tools/check_parity.py                       # fail on gaps that aren't allowed in feltgen/parity.py
    python3 tools/check_parity.py --map                 # print every Bootstrap token and its felt counterpart
    python3 tools/check_parity.py --snapshot bootstrap.css   # re-pin from Bootstrap's dist/css/bootstrap.css

Every Bootstrap class must exist in felt.css, every --bs-* token must have a felt counterpart, each or be allowed
with a reason (feltgen/parity.py). Allowed entries that felt.css has by now fail too, so the list stays honest.
"""
import json
import sys
from pathlib import Path

from feltgen import parity


def main():
    if "--snapshot" in sys.argv:
        source = Path(sys.argv[sys.argv.index("--snapshot") + 1])
        parity.SNAPSHOT.write_text(json.dumps(parity.snapshot(source.read_text()), indent=1) + "\n")
        print(f"pinned {parity.SNAPSHOT.name}")
        return
    if "--map" in sys.argv:
        for bs, felt in parity.token_map().items():
            print(f"{bs:44} {felt or '— ' + parity.ALLOW_TOKENS.get(bs, 'MISSING')}")
        return
    r = parity.report()
    problems = [
        ("Bootstrap classes felt.css doesn't have", r["missing_classes"]),
        ("Bootstrap tokens without a felt counterpart", r["missing_tokens"]),
        ("mapped to felt tokens that don't exist", r["broken"]),
        ("allowed in feltgen/parity.py but present by now", r["stale"]),
        ("allowed in feltgen/parity.py but not in Bootstrap", r["unknown"]),
    ]
    for title, items in problems:
        if items:
            print(f"{title} ({len(items)}):\n  " + "\n  ".join(items))
    failed = sum(len(items) for _, items in problems)
    print(f"Bootstrap {parity.VERSION}: {r['classes']} classes, {r['tokens']} tokens; {failed} problems")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
