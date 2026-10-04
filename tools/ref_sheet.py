"""Referentni sheet Ferro za ChatGPT: dva uvećana lika, zamrznuta paleta i svi frameovi
iz assets/px, na magenta podlozi kakvu traže i novi crteži. Prilaže se uz svaku poruku
u ChatGPT Projectu, da novi crteži ostanu u istom stilu.

Pokretanje (iz korijena repoa): python tools/ref_sheet.py  ->  assets/ref/ferro-ref.png
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PX = ROOT / "assets" / "px"
OUT = ROOT / "assets" / "ref" / "ferro-ref.png"

W, H = 1536, 1024  # 3:2, kao slike koje ChatGPT vraća
MAGENTA = (255, 0, 255, 255)
MARGIN = 40
HERO_ZOOM, ROW_ZOOM = 9, 3
HEROES = ["poop-0", "run-4"]  # stoji mirno; trči s isplaženim jezikom
ROWS = {"run": [4, 3, 2, 5, 0], "sleep": range(6), "poop": range(6)}  # trčanje redom galopa
SWATCH, SWATCH_GAP, SWATCH_COLS = 64, 8, 4


def frame(name: str) -> Image.Image:
    img = Image.open(PX / f"{name}.png").convert("RGBA")
    return img.crop(img.getbbox())


def big(img: Image.Image, zoom: int) -> Image.Image:
    return img.resize((img.width * zoom, img.height * zoom), Image.NEAREST)


def main() -> None:
    sheet = Image.new("RGBA", (W, H), MAGENTA)

    # gore: uvećani likovi na zajedničkom tlu
    heroes = [big(frame(n), HERO_ZOOM) for n in HEROES]
    top_h = max(h.height for h in heroes)
    x = MARGIN
    for h in heroes:
        sheet.alpha_composite(h, (x, MARGIN + top_h - h.height))
        x += h.width + MARGIN

    # gore desno: paleta (krzno i obrub, pa jezik i odsjaj)
    pal = json.loads((ROOT / "assets" / "palette.json").read_text(encoding="utf-8"))
    colors = pal["krzno"] + [pal["jezik"], pal["odsjaj"]]
    sx = W - MARGIN - SWATCH_COLS * (SWATCH + SWATCH_GAP) + SWATCH_GAP
    for i, c in enumerate(colors):
        col, row = i % SWATCH_COLS, i // SWATCH_COLS
        rgb = tuple(int(c[k : k + 2], 16) for k in (1, 3, 5))
        tile = Image.new("RGBA", (SWATCH, SWATCH), (*rgb, 255))
        sheet.alpha_composite(tile, (sx + col * (SWATCH + SWATCH_GAP), MARGIN + row * (SWATCH + SWATCH_GAP)))

    # dolje: svi frameovi, red po animaciji, poravnati po tlu
    y = MARGIN + top_h + MARGIN
    for name, order in ROWS.items():
        imgs = [big(frame(f"{name}-{i}"), ROW_ZOOM) for i in order]
        row_h = max(i.height for i in imgs)
        x = MARGIN
        for img in imgs:
            sheet.alpha_composite(img, (x, y + row_h - img.height))
            x += img.width + MARGIN
        y += row_h + MARGIN // 2

    if y > H:
        raise SystemExit(f"sheet je previsok: {y} > {H}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUT)
    print(OUT.relative_to(ROOT), sheet.size, "zadnji red završava na", y)


if __name__ == "__main__":
    main()
