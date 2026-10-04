#!/usr/bin/env python3
"""calib.py file.json name... : shift each variant's base so its rendered mean hits `target` (default .5)."""
import json, subprocess, sys
from feltgen import felt
S = "/tmp/claude-0/-home-user-felt-css/eafcb1b1-4cbd-5a0e-b70b-3ea210426243/scratchpad"
def mean(name):
    subprocess.run(["node", f"{S}/shot.js", f"http://localhost:8766/proto/svg-felt/lab/{name}.svg", f"{S}/c.png", "256", "256", "1", "0", "0", "256", "256"], check=True)
    return float(subprocess.run(["convert", f"{S}/c.png", "-colorspace", "Gray", "-format", "%[fx:mean]", "info:"], capture_output=True, text=True).stdout)
v = json.load(open(sys.argv[1]))
for n in sys.argv[2:]:
    kw = v[n]; target = kw.pop("target", .5)
    for _ in range(3):
        open(f"{n}.svg", "w").write(felt(**kw)); m = mean(n)
        if abs(m - target) < .003: break
        kw["base"] = round(kw.get("base", .5) + (target - m) / (kw.get("rgb", [1])[0] if kw.get("rgb") else 1), 4)
    kw["target"] = target; print(n, "base", kw.get("base", .5), "mean", round(m, 4))
json.dump(v, open(sys.argv[1], "w"), indent=1)
