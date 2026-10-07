"""Ferro reference sheet for ChatGPT: three enlarged figures, the frozen palette and all frames
ChatGPT drew, from assets/px, on the magenta background that new drawings need as well. It is attached to
every message in the ChatGPT Project, so new drawings keep the same style.

Run (from the repo root): python tools/ref_sheet.py  ->  assets/ref/ferro-ref.png
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PX = ROOT / "assets" / "px"
OUT = ROOT / "assets" / "ref" / "ferro-ref.png"

W, H = 1536, 1024  # 3:2, like the images ChatGPT returns
MAGENTA = (255, 0, 255, 255)
MARGIN = 40
HERO_ZOOM, ROW_ZOOM = 6, 3
HEROES = ["poop-0", "run-4", "sit-4"]  # standing still; running with the tongue out; facing the viewer
# one row per animation, the frames ChatGPT drew (the breath and the blink are derived in code)
ROWS = [
    [f"run-{i}" for i in [4, 3, 2, 5, 0]],  # in gallop order
    [f"sleep-{i}" for i in range(6)],
    [f"poop-{i}" for i in range(6)],
    [f"poop-walk-{i}" for i in range(4)] + [f"poop-walk-drop-{i}" for i in range(3)],
    [f"sit-{i}" for i in range(6)],
]
SWATCH, SWATCH_GAP, SWATCH_COLS = 64, 8, 6


def frame(name: str) -> Image.Image:
    img = Image.open(PX / f"{name}.png").convert("RGBA")
    return img.crop(img.getbbox())


def big(img: Image.Image, zoom: int) -> Image.Image:
    return img.resize((img.width * zoom, img.height * zoom), Image.NEAREST)


def main() -> None:
    sheet = Image.new("RGBA", (W, H), MAGENTA)

    # top: enlarged figures on a shared ground line
    heroes = [big(frame(n), HERO_ZOOM) for n in HEROES]
    top_h = max(h.height for h in heroes)
    x = MARGIN
    for h in heroes:
        sheet.alpha_composite(h, (x, MARGIN + top_h - h.height))
        x += h.width + MARGIN

    # top right: the palette (fur and outline, then the tongue shades and the highlight)
    pal = json.loads((ROOT / "assets" / "palette.json").read_text(encoding="utf-8"))
    colors = pal["fur"] + pal["tongue"] + [pal["highlight"]]
    sx = W - MARGIN - SWATCH_COLS * (SWATCH + SWATCH_GAP) + SWATCH_GAP
    for i, c in enumerate(colors):
        col, row = i % SWATCH_COLS, i // SWATCH_COLS
        rgb = tuple(int(c[k : k + 2], 16) for k in (1, 3, 5))
        tile = Image.new("RGBA", (SWATCH, SWATCH), (*rgb, 255))
        sheet.alpha_composite(tile, (sx + col * (SWATCH + SWATCH_GAP), MARGIN + row * (SWATCH + SWATCH_GAP)))

    # bottom: all frames, one row per animation, aligned on the ground
    y = MARGIN + top_h + MARGIN // 2
    for names in ROWS:
        imgs = [big(frame(n), ROW_ZOOM) for n in names]
        row_h = max(i.height for i in imgs)
        x = MARGIN
        for img in imgs:
            sheet.alpha_composite(img, (x, y + row_h - img.height))
            x += img.width + MARGIN
        y += row_h + MARGIN // 2

    if y > H:
        raise SystemExit(f"sheet is too tall: {y} > {H}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUT)
    print(OUT.relative_to(ROOT), sheet.size, "last row ends at", y)


if __name__ == "__main__":
    main()
