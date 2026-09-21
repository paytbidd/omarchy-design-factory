#!/usr/bin/env python3
"""Map plugin names to vendored pixelarticons (MIT). Not a generator.

Marks live in site/icons/, copied from
https://github.com/halfmage/pixelarticons (24×24, currentColor).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "site" / "icons"

# pixelarticons SVG stem → local filename
PLUGIN_MARKS = {
    "music": "apple-music-mini.svg",
    "keyboard": "macromancy.svg",
    "frame": "patina.svg",
    "sun": "redlight.svg",
    "monitor": "soundstage.svg",
    "letter-a": "type.svg",
    "layout": "default.svg",
    "copy": "copy.svg",
    "check": "check.svg",
    "moon": "moon.svg",
}


def main() -> None:
    print("Plugin marks are vendored from pixelarticons (MIT).")
    print(f"Directory: {ICONS.relative_to(ROOT)}")
    for src, dest in PLUGIN_MARKS.items():
        path = ICONS / dest
        status = "ok" if path.exists() else "MISSING"
        print(f"  {src:12} → {dest:24} {status}")


if __name__ == "__main__":
    main()
