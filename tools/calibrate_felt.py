#!/usr/bin/env python3
"""Print the base each felt texture in build_assets.py needs, so the rendered tile has its target mean
(grey felt 50 %). Run it after changing FELT and paste the printed bases into FELT.

Needs: python3, Node with Playwright (Chromium renders the SVG filters), ImageMagick (`convert`).
"""
import subprocess
import tempfile
from pathlib import Path

from build_assets import FELT, felt

TARGET = {"felt": .5}
RENDER = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 256, height: 256 } });
  await p.goto(process.argv[1]);
  await p.screenshot({ path: process.argv[2] });
  await b.close();
})();
"""


def mean(svg, tmp):
    src, png = Path(tmp) / "felt.svg", Path(tmp) / "felt.png"
    src.write_text(svg)
    subprocess.run(["node", "-e", RENDER, src.as_uri(), str(png)], check=True)
    out = subprocess.run(["convert", png, "-colorspace", "Gray", "-format", "%[fx:mean]", "info:"],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


with tempfile.TemporaryDirectory() as tmp:
    for name, kw in FELT.items():
        kw = dict(kw)
        for _ in range(4):
            m = mean(felt(**kw), tmp)
            if abs(m - TARGET[name]) < .002:
                break
            kw["base"] = round(kw.get("base", .5) + (TARGET[name] - m) / (kw.get("rgb") or [1])[0], 4)
        print(f"{name}: base={kw.get('base', .5)} (mean {m:.4f})")
