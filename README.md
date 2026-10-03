<p align="center"><img src="docs/banner.webp" alt="felt-css, spelled in stitched felt letters" width="100%"></p>

# felt-css

**Bootstrap, but made of wool felt.** A small, dependency-free CSS toolkit with Bootstrap 5 class names
and two looks: a clean one for everyday work, and a cosy one where every card is cut from felt and every
button is sewn on by hand. One attribute switches between them, and nothing on the page moves when you do.

| Felt | Clean |
|---|---|
| ![Felt look](docs/felt.webp) | ![Clean look](docs/clean.webp) |

![Buttons and alerts in felt](docs/buttons.webp)

## A word up front

- I built this for myself, for my own little apps (a smart-home dashboard, a shared-expenses app, a
  blog). It does exactly what I need and not much more.
- I don't accept pull requests (benevolent dictator and all that), but forks are very welcome — please
  take it, change it, make it yours. If you come up with something lovely, I'll happily steal the best
  ideas back. 🧵
- Public domain ([The Unlicense](LICENSE)): no strings attached, not even a thread.

## Quick start

No build step. Copy `felt.css` and the `img/` folder next to it, then:

```html
<html data-look="felt">   <!-- leave the attribute out for the clean look -->
<head>
  <link rel="stylesheet" href="felt.css">
</head>
<body>
  <div class="card">
    <div class="card-header">Neue Ausgabe</div>
    <div class="card-body">…</div>
    <div class="card-footer">
      <button class="btn">Abbrechen</button>
      <button class="btn btn-primary">Speichern</button>
    </div>
  </div>
</body>
```

Open `index.html` for a demo of everything (`?look=clean` or `?look=felt` in the URL picks a look).

## What's in the box

Bootstrap names, Bootstrap behaviour, felt finish:

- **Layout:** `.container`, `.grid` (auto-fit, `--grid-min`), `.stack`, `.row`
- **Navbar:** `.navbar`, `.navbar-brand`, `.nav-pills` with `.nav-link.active`
- **Cards:** `.card` with `-header`, `-body`, `-footer`, `-title`, `-text`; `.stat` for KPI tiles
- **Colour helpers:** `.text-bg-primary|secondary|success|danger|warning`
- **Buttons:** `.btn-primary|secondary|success|danger|warning|light|link`, `.btn-outline-*`,
  `.btn-sm|lg|pill|icon`, `.active`, `:disabled`
- **Forms:** `.form-control`, `.form-select`, `.input-group(-text)`, `.form-check(-input)`, `.form-switch`,
  `.is-invalid|is-valid` with `.invalid-feedback|valid-feedback`
- **Badges and alerts:** `.badge.text-bg-*`, `.alert-primary|secondary|success|warning|danger`

Colours follow Bootstrap's meaning: primary is denim blue, secondary taupe, warning mustard, success
moss, danger tomato. They live in custom properties on `:root`, so overriding `--primary` and friends is
all it takes to re-dye the whole thing.

## How the felt works

- **Two felt recipes.** Saturated pieces (buttons, KPI tiles, badges) are *patches*: a grey felt photo
  blended `soft-light` onto the colour, a soft cut edge and a cast shadow. Light surfaces (page, cards,
  alerts) are quiet felt: a photo of cream felt blended `multiply`, flat, at the same fibre scale.
- **Real thread.** Seams are 9-slice images built from one photographed stitch and laid on with
  `border-image`. They're tinted with `mix-blend-mode: hard-light`, so the thread is always a tone of the
  felt underneath: lighter on colour, a shade darker on cream.
- **Never moves.** The felt layer only changes colours, textures, shadows and seams — never padding,
  borders or fonts. Toggling the look doesn't shift a single pixel.
- **Opt-out friendly.** All felt rules sit in `@layer felt` behind `:where([data-look="felt"])`, so they
  have zero specificity and your own CSS always wins.

Weight: `felt.css` is about 6 KB gzipped, all images together about 35 KB.

## Rebuilding the assets

The photos in `raw/` were drawn by an image model (OpenAI Codex image generation): grey felt, cream
felt and a single running stitch. `tools/build_assets.py` turns them into the textures and seam frames
in `img/` and writes the matching sizes into `felt.css`:

```sh
python3 tools/build_assets.py   # needs numpy and ImageMagick
```

Want chunkier stitches or rounder corners? Change `STITCH_CSS`, `GAP_CSS` or `SHAPES` at the top of the
script and run it again.

## Browser notes

- Built and checked in Chromium.
- Firefox: outline buttons fall back to tone-on-tone thread instead of thread in the button colour
  (no `-webkit-mask-box-image`).
- Safari: not tested yet.

## Status

A proof of concept that grew up a bit. Next on my list: tables, modals, dropdowns, list groups,
progress bars, and a dark mode in charcoal felt.
