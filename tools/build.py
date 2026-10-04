"""Pretvara ChatGPT slike (assets/src) u prave piksele: izreže frameove, makne magentu,
smanji na zajedničku mrežu, svede na zajedničku paletu i spremi PNG-ove u assets/px.

Pokretanje (iz korijena repoa): python tools/build.py
Paleta psa je zamrznuta u assets/palette.json. Iznova se računa iz svih slika samo kad
toga filea nema ili uz zastavicu: python tools/build.py --nova-paleta
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src"
OUT = ROOT / "assets" / "px"
PALETTE_FILE = ROOT / "assets" / "palette.json"

# Koliko izvornih piksela ide u jedan pravi piksel. Psi su u tri slike nacrtani u
# različitoj veličini, pa faktor izjednačava visinu psa (trčanje 240, ostali ~220).
FACTOR = {"run": 6.0, "poop": 5.5, "sleep": 5.55}
PALETTE_SIZE = 22  # samo za --nova-paleta; inače vrijedi broj boja krzna u palette.json


def background_mask(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)


def fringe_mask(rgb: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Rub psa pomiješan s magentom (ljubičasto uz pozadinu). Bez ovoga ulazi u paletu
    kao bordo boja, pa se pojavi kao točke po obrubu i preotme jezik i uši."""
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    near = ndimage.binary_dilation(bg, iterations=3)
    return (r - g > 40) & (b - g > 40) & near & ~bg


def tongue_mask(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 200) & (g < 150) & (b > 80) & (b < 170) & (r - b > 60)


def white_mask(rgb: np.ndarray) -> np.ndarray:
    """Odsjaj u oku: ChatGPT ga crta kao točkicu manju od jednog pravog piksela."""
    return rgb.min(2) > 235


def components(rgb: np.ndarray, min_area: int):
    """(okvir, maska) svakog lika, slijeva nadesno; maska pokriva samo njegove piksele."""
    fg = ndimage.binary_opening(~background_mask(rgb), iterations=1)
    lab, k = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, k + 1))
    found = []
    for i, (s, box) in enumerate(zip(sizes, ndimage.find_objects(lab)), start=1):
        if s < min_area:
            continue
        own = lab[box] == i
        # tanki rubovi koje je otvaranje odvojilo vraćaju se, tuđi likovi ne
        own = ndimage.binary_dilation(own, iterations=3) & ((lab[box] == 0) | own)
        found.append((box, own))
    return sorted(found, key=lambda t: t[0][1].start)


# Svi frameovi idu na isto platno: desni rub desnog uha na ANCHOR_X, tlo na dnu.
CANVAS_W, CANVAS_H = 76, 44
ANCHOR_X = 54


def ear_right(px: np.ndarray, transparent: int) -> int:
    """Desni rub najviše četvrtine lika: to je desno uho (rep je lijevo)."""
    solid = px != transparent
    rows = np.where(solid.any(1))[0]
    top = solid[rows[0] : rows[0] + max(1, len(rows) // 4)]
    return int(np.where(top.any(0))[0].max())


def downsample(idx: np.ndarray, factor: float, transparent: int) -> np.ndarray:
    """Svaki pravi piksel dobije najčešću boju svog bloka; prozirno ako prevladava pozadina."""
    h, w = idx.shape
    th, tw = int(round(h / factor)), int(round(w / factor))
    out = np.full((th, tw), transparent, dtype=np.int16)
    for y in range(th):
        y0, y1 = int(y * factor), max(int((y + 1) * factor), int(y * factor) + 1)
        for x in range(tw):
            x0, x1 = int(x * factor), max(int((x + 1) * factor), int(x * factor) + 1)
            block = idx[y0:y1, x0:x1].ravel()
            counts = np.bincount(block, minlength=transparent + 1)
            if counts[transparent] * 2 >= block.size:
                continue
            counts[transparent] = 0
            out[y, x] = counts.argmax()
    return out


def catchlights(px: np.ndarray, white: np.ndarray, factor: float, white_i: int, dark: set) -> None:
    """Svaki odsjaj iz izvora postane jedan bijeli piksel, ako pada na tamno (oko).
    Smanjivanje ga inače izgubi jer u svom bloku nikad nije najčešća boja."""
    lab, k = ndimage.label(white)
    for cy, cx in ndimage.center_of_mass(white, lab, range(1, k + 1)):
        y, x = int(cy / factor), int(cx / factor)
        if y < px.shape[0] and x < px.shape[1] and px[y, x] in dark:
            px[y, x] = white_i


def clean_edges(px: np.ndarray, transparent: int, dark: set, protect: set, outline: int) -> None:
    """Ispegla rub: makne zalutale piksele i bočne izbočine od jednog piksela (cik-cak po rubu),
    pa zatvori obrub gdje ga je smanjivanje probilo (krzno uz pozadinu postane obrub).
    Okomite izbočine ostaju jer su to vrhovi ušiju. Jezik i odsjaj se ne diraju."""

    def sides(solid: np.ndarray) -> list[np.ndarray]:
        p = np.pad(solid, 1)  # izvan crteža je pozadina, pa i tabani dobiju obrub
        return [p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]

    solid = px != transparent
    up, down, left, right = sides(solid)
    count = up.astype(int) + down + left + right
    bump = (count == 0) | ((count == 1) & (left | right))
    px[solid & bump & ~np.isin(px, list(protect))] = transparent
    solid = px != transparent
    surrounded = np.logical_and.reduce(sides(solid))
    px[solid & ~surrounded & ~np.isin(px, list(dark | protect))] = outline


MEADOW_FX, MEADOW_FY = 10.0, 9.3  # livada nema kvadratne "piksele"
MEADOW_COLORS = 48
SKY_H = 20  # redova neba iznad brda u traci
GROUND_H = 27  # redova trave ispod grmlja u traci


def meadow() -> dict:
    """Livada u tri sloja: oblaci (presloženi u nisko nebo), brda s drvećem, trava."""
    q = Image.open(SRC / "meadow.png").convert("RGB").quantize(
        MEADOW_COLORS, method=Image.Quantize.MEDIANCUT
    )
    pal = np.array(q.getpalette()[: MEADOW_COLORS * 3]).reshape(-1, 3)
    idx = np.asarray(q).astype(np.int16)
    px = downsample_rect(idx, MEADOW_FX, MEADOW_FY, MEADOW_COLORS)
    rgb = pal[px].astype(np.uint8)
    h, w, _ = rgb.shape

    vals, counts = np.unique(rgb[2].reshape(-1, 3), axis=0, return_counts=True)
    sky = vals[counts.argmax()]
    not_sky = np.abs(rgb.astype(int) - sky).sum(2) > 30
    white = rgb.astype(int).min(2) > 190

    # početak brda: prvi red u kojem je bar trećina nečeg što nije nebo ni oblak
    hills_top = int(np.argmax((not_sky & ~white).mean(1) > 0.3)) - 3
    # početak trave: red ispod grmlja s najviše svijetlozelene
    g = rgb.astype(int)
    light_grass = (g[..., 1] > 170) & (g[..., 0] > 90) & (g[..., 2] < 90)
    grass_top = hills_top + 20 + int(np.argmax(light_grass[hills_top + 20 :].mean(1) > 0.6))

    def rgba(part: np.ndarray, mask: np.ndarray) -> Image.Image:
        out = np.zeros((*part.shape[:2], 4), dtype=np.uint8)
        out[mask, :3] = part[mask]
        out[mask, 3] = 255
        return Image.fromarray(out, "RGBA")

    # oblaci: svaki oblak zasebno, spušten u nisko nebo trake
    cloud_mask = not_sky[:hills_top] & white[:hills_top]
    cloud_mask = ndimage.binary_closing(cloud_mask, iterations=1) & not_sky[:hills_top]
    lab, k = ndimage.label(cloud_mask)
    clouds = np.zeros((SKY_H, w, 4), dtype=np.uint8)
    for i, box in enumerate(ndimage.find_objects(lab), start=1):
        ch = box[0].stop - box[0].start
        if ch > SKY_H - 2:
            continue
        y = min(max(1, box[0].start // 2), SKY_H - ch - 1)
        part = rgb[box]
        m = lab[box] == i
        tgt = clouds[y : y + ch, box[1]]
        tgt[m, :3] = part[m]
        tgt[m, 3] = 255
    Image.fromarray(clouds, "RGBA").save(OUT / "meadow-clouds.png")

    back = rgb[hills_top:grass_top]
    rgba(back, not_sky[hills_top:grass_top]).save(OUT / "meadow-back.png")
    ground = rgb[grass_top : grass_top + GROUND_H]
    rgba(ground, np.ones(ground.shape[:2], bool)).save(OUT / "meadow-ground.png")

    info = {
        "sky": "#%02x%02x%02x" % tuple(int(c) for c in sky),
        "width": w,
        "back_h": grass_top - hills_top,
        "ground_h": GROUND_H,
        "sky_h": SKY_H,
    }
    print("meadow", w, "x", h, "hills", hills_top, "grass", grass_top, info)
    return info


def downsample_rect(idx: np.ndarray, fx: float, fy: float, n: int) -> np.ndarray:
    h, w = idx.shape
    th, tw = int(round(h / fy)), int(round(w / fx))
    out = np.zeros((th, tw), dtype=np.int16)
    for y in range(th):
        y0, y1 = int(y * fy), max(int((y + 1) * fy), int(y * fy) + 1)
        for x in range(tw):
            x0, x1 = int(x * fx), max(int((x + 1) * fx), int(x * fx) + 1)
            out[y, x] = np.bincount(idx[y0:y1, x0:x1].ravel(), minlength=n).argmax()
    return out


def new_palette(sheets: dict, bgs: dict) -> np.ndarray:
    """Zajednička paleta iz svih piksela psa u svim slikama. Jezik i odsjaj imaju premalo
    piksela da bi im median cut dao boju, pa dobiju svoju povrh PALETTE_SIZE."""

    def pixels(mask_of) -> np.ndarray:
        return np.concatenate([s[mask_of(s) & ~bgs[n]] for n, s in sheets.items()])

    fg_pixels = pixels(lambda s: ~tongue_mask(s) & ~white_mask(s))
    sample = fg_pixels[:: max(1, len(fg_pixels) // 200_000)]
    # k-means dorada: bez nje median cut izgubi neutralnu tamnosivu, pa sedlo dobije smeđe mrlje
    pal_img = Image.fromarray(sample.reshape(1, -1, 3).astype(np.uint8)).quantize(
        PALETTE_SIZE, method=Image.Quantize.MEDIANCUT, kmeans=20
    )
    palette = np.array(pal_img.getpalette()[: PALETTE_SIZE * 3]).reshape(-1, 3)
    return np.vstack(
        [palette, pixels(tongue_mask).mean(0).round(), pixels(white_mask).mean(0).round()]
    ).astype(int)


def save_palette(palette: np.ndarray) -> None:
    hexes = ["#%02x%02x%02x" % tuple(int(c) for c in p) for p in palette]
    data = {"krzno": hexes[:-2], "jezik": hexes[-2], "odsjaj": hexes[-1]}
    PALETTE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("nova paleta spremljena u", PALETTE_FILE.relative_to(ROOT))


def load_palette() -> np.ndarray:
    """Boje krzna i obruba, pa jezik, pa odsjaj u oku (redoslijed određuje indekse)."""
    data = json.loads(PALETTE_FILE.read_text(encoding="utf-8"))
    hexes = data["krzno"] + [data["jezik"], data["odsjaj"]]
    return np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in hexes])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meadow.json").write_text(json.dumps(meadow()))
    sheets = {n: np.asarray(Image.open(SRC / f"{n}.png").convert("RGB")) for n in FACTOR}

    bgs = {n: background_mask(s) for n, s in sheets.items()}
    bgs = {n: bg | fringe_mask(sheets[n], bg) for n, bg in bgs.items()}

    if "--nova-paleta" in sys.argv or not PALETTE_FILE.exists():
        save_palette(new_palette(sheets, bgs))
    palette = load_palette()
    fur_n = len(palette) - 2
    tongue_i, white_i, transparent = fur_n, fur_n + 1, fur_n + 2
    dark = {i for i, p in enumerate(palette) if p.sum() < 200}  # obrub, nos, oči
    outline = int(palette[:fur_n].sum(1).argmin())

    for name, rgb in sheets.items():
        bg = bgs[name]
        flat = rgb.reshape(-1, 3).astype(int)
        # najbliža boja krzna za svaki izvorni piksel; jezik i odsjaj samo gdje su nacrtani
        best = np.zeros(len(flat), dtype=np.int16)
        best_d = np.full(len(flat), 1 << 30)
        for i, p in enumerate(palette[:fur_n]):
            d = ((flat - p) ** 2).sum(1)
            better = d < best_d
            best[better], best_d[better] = i, d[better]
        idx = best.reshape(bg.shape)
        idx[tongue_mask(rgb)] = tongue_i
        white = white_mask(rgb)
        idx[white] = white_i
        idx[bg] = transparent

        found = components(rgb, 400)
        ground = max(box[0].stop for box, _ in found)  # tlo slike: najniži lik
        parts = []
        for box, own in found:
            crop = idx[box].copy()
            crop[~own] = transparent
            px = downsample(crop, FACTOR[name], transparent)
            # uho za poravnanje se mjeri prije čišćenja, da frameovi ostanu gdje su bili
            ear = ear_right(px, transparent) if px.shape[1] >= 20 else 0
            clean_edges(px, transparent, dark, {tongue_i, white_i}, outline)
            catchlights(px, white[box] & own, FACTOR[name], white_i, dark)
            solid = px != transparent
            out = np.zeros((*px.shape, 4), dtype=np.uint8)
            out[solid, :3] = palette[px[solid]]
            out[solid, 3] = 255
            parts.append((box, px, ear, Image.fromarray(out, "RGBA")))

        dogs = []
        for box, px, ear, img in parts:
            if px.shape[1] < 20:  # hrpica, ne pas
                continue
            # poravnanje: uho na ANCHOR_X, visina prema tlu izvorne slike
            x = ANCHOR_X - ear
            y = CANVAS_H - int(round((ground - box[0].start) / FACTOR[name]))
            canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
            canvas.paste(img, (x, y), img)
            canvas.save(OUT / f"{name}-{len(dogs)}.png")
            dogs.append((box, x))
            print(name, len(dogs) - 1, "size", px.shape[1], "x", px.shape[0], "at", x, y)

        # hrpica: položaj na platnu psa koji je odmah desno od nje (taj je obavlja)
        for box, px, _, img in parts:
            if px.shape[1] >= 20:
                continue
            owner = next(i for i, (b, _) in enumerate(dogs) if b[1].start > box[1].start)
            dog_box, dog_x = dogs[owner]
            pile = {
                "frame": owner,
                "x": dog_x + int(round((box[1].start - dog_box[1].start) / FACTOR[name])),
                "y": CANVAS_H - px.shape[0],
                "w": px.shape[1],
                "h": px.shape[0],
            }
            img.save(OUT / f"{name}-pile.png")
            (OUT / f"{name}-pile.json").write_text(json.dumps(pile))
            print(name, "pile", pile)
            break


if __name__ == "__main__":
    main()
