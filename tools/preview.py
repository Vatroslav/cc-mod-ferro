"""Uvećani pregled svih frameova iz assets/px, red po sceni, na zelenoj podlozi.

Pokretanje (iz korijena repoa): python tools/preview.py <izlazni.png> [uvećanje]
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GAP = 12


def main() -> None:
    out = sys.argv[1]
    zoom = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    rows: dict[str, list[Image.Image]] = {}
    files = sorted(
        (ROOT / "assets" / "px").glob("*-*.png"),
        key=lambda f: (f.stem.rsplit("-", 1)[0], int(f.stem.rsplit("-", 1)[1])),
    )
    for f in files:
        rows.setdefault(f.stem.rsplit("-", 1)[0], []).append(Image.open(f).convert("RGBA"))
    width = max(sum(i.width * zoom + GAP for i in r) for r in rows.values())
    height = sum(max(i.height for i in r) * zoom + GAP for r in rows.values())
    canvas = Image.new("RGBA", (width, height), (90, 160, 90, 255))
    y = 0
    for r in rows.values():
        x = 0
        for i in r:
            big = i.resize((i.width * zoom, i.height * zoom), Image.NEAREST)
            canvas.alpha_composite(big, (x, y))
            x += big.width + GAP
        y += max(i.height for i in r) * zoom + GAP
    canvas.save(out)


if __name__ == "__main__":
    main()
