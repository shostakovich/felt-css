#!/usr/bin/env python3
"""Print the base each felt texture needs so the rendered tile has the photos' mean (grey 50 %, cream 94.6 %).
Needs the repo served on localhost:8766 and Playwright; paste the printed bases into build.py's FELT."""
import subprocess, sys, tempfile
from pathlib import Path
from build import FELT, OUT
from feltgen import felt
HERE = Path(__file__).resolve().parent
TARGET = {"felt": .5, "felt-light": .946, "felt-dark": .5}

def mean(svg):
    p = OUT / "_calib.svg"; p.write_text(svg)
    with tempfile.TemporaryDirectory() as t:
        png = f"{t}/c.png"
        subprocess.run(["node", HERE / "render.js", "http://localhost:8766/proto/svg-felt/img/_calib.svg", png, "256", "256", "1", "0", "0", "256", "256"], check=True)
        out = subprocess.run(["convert", png, "-colorspace", "Gray", "-format", "%[fx:mean]", "info:"], capture_output=True, text=True).stdout
    return float(out)

for name, kw in FELT.items():
    kw = dict(kw)
    for _ in range(4):
        m = mean(felt(**kw))
        if abs(m - TARGET[name]) < .002: break
        kw["base"] = round(kw.get("base", .5) + (TARGET[name] - m) / (kw.get("rgb") or [1])[0], 4)
    print(f"{name}: base={kw.get('base', .5)} (mean {m:.4f})")
(OUT / "_calib.svg").unlink()
