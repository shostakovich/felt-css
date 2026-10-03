<p align="center"><img src="docs/banner.webp" alt="felt-css, spelled in stitched felt letters" width="100%"></p>

# felt-css

**Bootstrap, but made of wool felt.** A small, dependency-free CSS toolkit with Bootstrap 5 class names
and two looks: a clean one for everyday work, and a cosy one where every card is cut from felt and every
button is sewn on by hand. One attribute switches between them, and nothing on the page moves when you do.

| Felt | Clean |
|---|---|
| ![Felt look](docs/felt.webp) | ![Clean look](docs/clean.webp) |

Both looks come in light and dark; dark felt is charcoal.

![Dark mode, felt and clean](docs/dark.webp)

![Colour tiles, buttons and toggle groups in felt](docs/buttons.webp)

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

Open `index.html` for a demo of everything (`?look=clean|felt` and `?theme=light|dark` in the URL pick a
look and a theme).

**Dark mode** works like Bootstrap's: `data-bs-theme="dark"` (or `"light"`) on `<html>` or on any element,
for a dark navbar on a light page and the like. Without the attribute the system setting decides.

**Behaviour** (opening dropdowns, modals, offcanvas, tooltips, tabs, collapsing, toasts) comes from
Bootstrap's own JavaScript. felt-css is CSS only and styles the classes Bootstrap's JS sets:

```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI" crossorigin="anonymous"></script>
```

Some things need no JavaScript at all: floating labels, `<details class="accordion-item">` and
`<dialog class="modal">`.

## What's in the box

Bootstrap names, Bootstrap behaviour, felt finish:

- **Layout:** `.container(-fluid|-sm|-md|-lg)`, Bootstrap's grid (`.row`, `.col-*`, `.row-cols-*`,
  `.g-*`, `.offset-*`), `.hstack`, `.vstack`
- **Utilities:** all of Bootstrap 5.3's (and `!important` like there): spacing, display, flex, text,
  colour with `*-opacity-*`, background, border, rounded, shadow, overflow, position, sizing, `z-*`, links
  (`.link-*`, `.link-underline-*`, `.link-offset-*`), `.focus-ring`, `.icon-link`, `.vr`, `.ratio`,
  `.visually-hidden`. Grid, display, flex, order, spacing, gap, text alignment, float, object-fit and
  sticky also come per breakpoint (`-sm`, `-md`, `-lg`; no `-xl`/`-xxl`), e.g. `.px-md-4`; `.d-print-*`
  for print
- **Prose:** headings, `.display-*`, `.lead`, lists, `blockquote`, `figure`, `code`/`pre`/`kbd`, `mark`, `hr`
- **Navbar and nav:** `.navbar` with `.navbar-expand-*`, `.navbar-toggler`, `.navbar-collapse`,
  `.fixed-top|bottom`; `.nav-pills`, `.nav-tabs`, `.nav-underline`, `.nav-fill|justified`, `.tab-content`
- **Cards:** header, body, footer, title, subtitle, text, links, images (top, bottom, overlay,
  horizontal), list groups and tabs in cards; `.stat` for KPI tiles
- **Buttons:** all colours, `.btn-outline-*`, `.btn-link`, sizes, `.btn-pill`, `.btn-icon`, `.btn-group`
  (horizontal and vertical, sizes), `.btn-check` toggles, `.btn-toolbar`, `.btn-close`
- **Forms:** controls, selects, sizes, plaintext, file, colour, range, checks, radios, switches, input
  groups, floating labels, validation states
- **Components:** alerts (dismissible), badges, breadcrumb, pagination, list groups (actions, colours,
  numbered, flush, horizontal), tables (striped, hover, bordered, borderless, small, colours, responsive),
  progress (stacked, striped, animated), spinners, accordion (also `<details>`), modal (also `<dialog>`),
  toasts, dropdowns (split, dropup/end/start), offcanvas (all four edges), tooltips, popovers
- **Colour helpers:** `.text-bg-*`, `.bg-*`, `.bg-*-subtle`, `.text-*`, `.text-*-emphasis`, `.border-*`

Colours follow Bootstrap's meaning: primary is denim blue, secondary taupe, warning mustard, success
moss, danger tomato, info petrol. They live in custom properties on `:root`, written as
`light-dark(light, dark)`, so overriding `--primary` and friends is all it takes to re-dye the whole thing.

### Recipe: a mobile tab bar

```html
<nav class="navbar fixed-bottom pb-safe">
  <ul class="nav nav-pills nav-fill w-100">
    <li class="nav-item">
      <a class="nav-link d-flex flex-column align-items-center active" aria-current="page" href="#"><svg>…</svg><small>Ausgaben</small></a>
    </li>
    …
  </ul>
</nav>
```

`.pb-safe` keeps the bar clear of the home indicator; in felt the bar is sewn along its inner edge and the
active tab gets a felt chip behind its icon.

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

Weight: `felt.css` is about 33 KB gzipped, all images together about 42 KB.

## Rebuilding the assets

The photos in `raw/` were drawn by an image model (OpenAI Codex image generation): grey felt, cream
felt and a single running stitch. `tools/build_assets.py` turns them into the textures and seam frames
in `img/` and writes the matching sizes into `felt.css`:

```sh
python3 tools/build_assets.py   # needs numpy and ImageMagick
```

Want chunkier stitches or rounder corners? Change `STITCH_CSS`, `GAP_CSS` or `SHAPES` at the top of the
script and run it again.

The grid and the repetitive utilities (everything per breakpoint, the colour helpers with their
opacities, rounded corners) are written the same way, by `tools/build_utilities.py` between the `grid:`,
`families:` and `utilities:` markers. Change the lists at its top (spacers, breakpoints, colours, …),
not the generated lines:

```sh
python3 tools/build_utilities.py   # plain python3, no packages
```

## Browser notes

- Needs `light-dark()` (Chrome 123, Safari 17.5, Firefox 120); also uses `:has()`, CSS nesting and
  cascade layers, which those versions all have.
- Built and checked in Chromium.
- Firefox: outline buttons fall back to tone-on-tone thread instead of thread in the button colour
  (no `-webkit-mask-box-image`).
- Safari: not tested yet.

## Upgrading from the first version

- `.grid` and `.stack` are gone, and `.row` is now Bootstrap's flex row. Use `.row` with `.row-cols-*` and
  `.g-*` instead of `.grid`, and `.vstack` with `.gap-*` instead of `.stack`.

## Status

A proof of concept that grew up: most of Bootstrap 5.3's components, light and dark, in both looks.
