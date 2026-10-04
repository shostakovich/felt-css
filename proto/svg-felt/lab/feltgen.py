#!/usr/bin/env python3
"""Felt as summed noise bands; fibre bands are bent by low noise (feDisplacementMap) to break up the
lattice of feTurbulence and to stretch the ridges into hairs. All noise is made on the tile and
repeated with feTile, so the displaced tile stays seamless."""
import json, sys
T, P = 256, 32
SUB = f'x="0" y="0" width="{T}" height="{T}"'
GREY = '<feColorMatrix values="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 1"/>'

def felt(bands, base=.5, rgb=None, seed=1, warp=(".02", 10)):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{T}" height="{T}">'
         f'<filter id="f" filterUnits="userSpaceOnUse" x="{-P}" y="{-P}" width="{T+2*P}" height="{T+2*P}" color-interpolation-filters="sRGB">'
         f'<feTurbulence {SUB} type="fractalNoise" baseFrequency="{warp[0]}" numOctaves="2" seed="{seed+99}" stitchTiles="stitch"/><feTile result="w"/>'
         f'<feFlood flood-color="rgb({base*255:.1f},{base*255:.1f},{base*255:.1f})" result="a"/>']
    for i, (freq, oct, kind, amp, *opt) in enumerate(bands):
        mean = opt[0] if opt else (.5 if kind == "f" else .25)
        bend = opt[1] if len(opt) > 1 else 0
        blur = opt[2] if len(opt) > 2 else 0
        # negative amplitude: invert the noise instead (bright ridges); amplitudes stay positive so alpha stays 1
        grey = GREY if amp > 0 else '<feColorMatrix values="-1 0 0 0 1 -1 0 0 0 1 -1 0 0 0 1 0 0 0 0 1"/>'
        if amp < 0: amp, mean = -amp, 1 - mean
        s.append(f'<feTurbulence {SUB} type="{"fractalNoise" if kind == "f" else "turbulence"}" baseFrequency="{freq}" '
                 f'numOctaves="{oct}" seed="{seed + 7 * i}" stitchTiles="stitch"/>{grey}<feTile result="n"/>')
        if bend:
            s.append(f'<feDisplacementMap in2="w" scale="{bend}" xChannelSelector="R" yChannelSelector="G" in="n" result="n"/>')
        if blur:   # soft fibres: a fuzz, not a hairline
            s.append(f'<feGaussianBlur in="n" stdDeviation="{blur}" result="n"/>')
        s.append(f'<feComposite in="a" in2="n" operator="arithmetic" k2="1" k3="{amp}" k4="{-amp * mean:.3g}" result="a"/>')
    if rgb:
        s.append(f'<feColorMatrix values="{rgb[0]} 0 0 0 0 0 {rgb[1]} 0 0 0 0 0 {rgb[2]} 0 0 0 0 0 1 0"/>')
    s.append(f'</filter><rect width="{T}" height="{T}" filter="url(#f)"/></svg>')
    return "".join(s)

if __name__ == "__main__":
    for name, kw in json.loads(open(sys.argv[1]).read()).items():
        open(f"{name}.svg", "w").write(felt(**kw))
