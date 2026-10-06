"""What the generators share: paths, the token prefix, breakpoints and the theme colours."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "felt.css"

PREFIX = "--felt-"      # every public token; internal ones are --_name, no promise
INTERNAL = "--_"

# like Bootstrap's; containers, the grid, utilities and every responsive component variant use these
BREAKPOINTS = {"sm": 576, "md": 768, "lg": 992, "xl": 1200, "xxl": 1400}

COLOURS = ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"]
TONED = COLOURS[:6]     # light and dark have no -text tone of their own
