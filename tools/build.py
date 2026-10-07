"""Turns the ChatGPT images (assets/src) into real pixels: cuts the frames, removes the magenta,
downsamples to a shared grid, maps to a shared palette and saves the PNGs to assets/px.

Run (from the repo root): python tools/build.py
The dog palette is frozen in assets/palette.json. It is recomputed from all images only when
that file is missing or with the flag: python tools/build.py --new-palette
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
# Frames fixed by hand in a pixel editor (same 76x44 canvas, same position): a file here replaces
# the built frame of the same name, before the breathing, blink and sniff frames are derived.
FIX = ROOT / "assets" / "fix"

# How many source pixels make one real pixel. The dog is drawn at a different size in each
# image, so the factor evens out the dog's height from ear tip to ground (run ~240, poop and
# sleep ~220, poop-walk ~236). sit.png is drawn bigger still, with a bigger head: 9.0 makes
# the head the size of the other frames. In sniff.png her head is down, so its factor evens out
# the length instead: the walking frames come out 51-55 pixels long, like standing (poop-0, 51)
# and running (56).
# drink.png is drawn a little bigger again (standing 343-359 source pixels long): 6.5 makes her
# 53-55 pixels long, like standing. Not yet checked by eye.
FACTOR = {"run": 6.0, "poop": 5.5, "sleep": 5.55, "poop-walk": 6.8, "sit": 9.0, "sniff": 6.0, "drink": 6.5}
# Sheets whose small figures are a row of droppings: each one is saved on its own as
# <name>-drop-<i>.png. In poop.png the small figure is the pile next to the frame making it.
# ChatGPT drew them bigger than asked (the largest as wide as a third of the dog), so they get
# a larger factor of their own: the largest comes out 9 pixels wide, like the old pile.
DROPPINGS = {"poop-walk": 10.5}
PALETTE_SIZE = 22  # only for --new-palette; otherwise the number of fur colours in palette.json


def background_mask(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)


def fringe_mask(rgb: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """The dog's edge blended with the magenta (purple next to the background). Without this
    it enters the palette as a maroon colour, shows up as dots along the outline and takes
    over the tongue and the ears."""
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    near = ndimage.binary_dilation(bg, iterations=3)
    return (r - g > 40) & (b - g > 40) & near & ~bg


def tongue_mask(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 200) & (g < 150) & (b > 80) & (b < 170) & (r - b > 60)


# The tongue has three shades of the same pink (palette.json "tongue", dark to light), so it keeps
# the texture ChatGPT draws (Vatra, 7.10.2026). With one colour, only its brighter pixels passed
# tongue_mask and the darker ones went to brown fur. A tongue is a patch of pink of at least
# TONGUE_MIN_AREA source pixels: blue about as strong as green, where tan fur and orange ears have
# far less blue than green. Each of its pixels gets the shade nearest to its brightness relative
# to the patch's average, so every tongue averages to the middle shade whatever pink ChatGPT used.
TONGUE_MIN_AREA = 60
TONGUE_SHADES = (0.78, 1.2)  # dark and light, times the middle shade; only for --new-palette
LUMA = np.array([0.299, 0.587, 0.114])


def tongue_shades(rgb: np.ndarray, bg: np.ndarray, tongue: np.ndarray) -> np.ndarray:
    """Index into the tongue shades for each source pixel of a tongue, -1 elsewhere. Pink pixels
    of tongue_mask outside a big enough patch (a stray speck on an ear) get the middle shade."""
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    pink = (r > 140) & (r - g > 45) & (b > g - 30) & ~bg
    lab, k = ndimage.label(pink)
    out = np.full(bg.shape, -1, dtype=np.int16)
    out[tongue_mask(rgb) & ~bg] = len(tongue) // 2
    sizes = ndimage.sum(pink, lab, range(1, k + 1))
    ratios = (tongue @ LUMA) / (tongue[len(tongue) // 2] @ LUMA)
    luma = rgb @ LUMA
    for i in [i + 1 for i, s in enumerate(sizes) if s >= TONGUE_MIN_AREA]:
        m = lab == i
        rel = luma[m] / luma[m].mean()
        out[m] = np.abs(rel[:, None] - ratios[None]).argmin(1)
    return out


def white_mask(rgb: np.ndarray) -> np.ndarray:
    """Eye highlight: ChatGPT draws it as a dot smaller than one real pixel."""
    return rgb.min(2) > 235


def components(rgb: np.ndarray, min_area: int):
    """(box, mask) of each figure, left to right; the mask covers only its own pixels."""
    fg = ndimage.binary_opening(~background_mask(rgb), iterations=1)
    lab, k = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, k + 1))
    found = []
    for i, (s, box) in enumerate(zip(sizes, ndimage.find_objects(lab)), start=1):
        if s < min_area:
            continue
        own = lab[box] == i
        # thin edges cut off by the opening come back, other figures do not
        own = ndimage.binary_dilation(own, iterations=3) & ((lab[box] == 0) | own)
        found.append((box, own))
    return sorted(found, key=lambda t: t[0][1].start)


# All frames go on the same canvas: the right edge of the right ear at ANCHOR_X, ground at the bottom.
CANVAS_W, CANVAS_H = 76, 44
ANCHOR_X = 54
# Sheets where the head turns, so the ear moves: their frames are aligned on the front toes
# (the rightmost pixel of the bottom rows) instead, which stay planted.
# drink: she stands in the same spot from frame 2 on while only her head moves.
TOES_X = {"sit": 54, "drink": 54}
# Sheets where the head is down, so the top quarter of the figure is the tail and the back, not
# the ear: their frames are aligned on the nose (the rightmost pixel), at the x of the nose of a
# running frame, so she keeps her place when she drops her nose out of a run.
NOSE_X = {"sniff": 58}


def ear_right(px: np.ndarray, transparent: int) -> int:
    """Right edge of the top quarter of the figure: that is the right ear (the tail is left)."""
    solid = px != transparent
    rows = np.where(solid.any(1))[0]
    top = solid[rows[0] : rows[0] + max(1, len(rows) // 4)]
    return int(np.where(top.any(0))[0].max())


def downsample(idx: np.ndarray, factor: float, transparent: int, group: tuple = ()) -> np.ndarray:
    """Each real pixel gets the most common colour of its block; transparent if background wins.
    The colours of a group (the tongue shades) vote together, and a block they win gets the
    group's most common colour: split into shades, the tongue would lose blocks to the fur."""
    group = list(group)
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
            if group:
                total, best = counts[group].sum(), group[int(counts[group].argmax())]
                counts[group] = 0
                counts[best] = total
            out[y, x] = counts.argmax()
    return out


def catchlights(px: np.ndarray, white: np.ndarray, factor: float, white_i: int, dark: set,
                transparent: int) -> None:
    """Each eye highlight in the source becomes one white pixel, if it lands on a dark eye.
    Downsampling would lose it otherwise, because it is never the most common colour in its block.
    Only specks on the head count (the right 65% and top 60% of the figure, which also takes in
    the head of a sitting dog facing the viewer), only on a dark patch that does not touch the
    background (an eye, not the outline), and only the largest speck per eye: stray specks also
    land on dark pixels, and one on the outline of a hind leg looked like a hole in the outline.
    A dog facing the viewer gets one highlight in each eye."""
    # a big highlight can also win its block in downsampling: it takes its neighbours' colour,
    # so the eye keeps exactly one white pixel
    for y, x in zip(*np.where(px == white_i)):
        around = [px[j, i] for j, i in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                  if 0 <= j < px.shape[0] and 0 <= i < px.shape[1] and px[j, i] != white_i]
        px[y, x] = max(set(around), key=around.count)
    lab, k = ndimage.label(white)
    if k == 0:
        return
    eyes, _ = ndimage.label(np.isin(px, list(dark)))
    by_background = set(np.unique(eyes[ndimage.binary_dilation(px == transparent)])) | {0}
    areas = ndimage.sum(white, lab, range(1, k + 1))
    best = {}  # eye: (area, y, x)
    for area, (cy, cx) in zip(areas, ndimage.center_of_mass(white, lab, range(1, k + 1))):
        y, x = int(cy / factor), int(cx / factor)
        on_head = x >= px.shape[1] * 0.35 and y <= px.shape[0] * 0.6
        if not (on_head and y < px.shape[0] and x < px.shape[1]):
            continue
        eye = eyes[y, x]
        if eye not in by_background and (eye not in best or area > best[eye][0]):
            best[eye] = (area, y, x)
    for _, y, x in best.values():
        px[y, x] = white_i


def clean_edges(px: np.ndarray, transparent: int, dark: set, protect: set, outline: int) -> None:
    """Smooths the edge: removes stray pixels and one-pixel side bumps (zigzag along the edge),
    then closes the outline where downsampling broke it (fur next to the background becomes
    outline). Vertical bumps stay, because they are the ear tips. Tongue and highlight are kept."""

    def sides(solid: np.ndarray) -> list[np.ndarray]:
        p = np.pad(solid, 1)  # outside the drawing is background, so the paw pads get an outline too
        return [p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]

    solid = px != transparent
    up, down, left, right = sides(solid)
    count = up.astype(int) + down + left + right
    bump = (count == 0) | ((count == 1) & (left | right))
    px[solid & bump & ~np.isin(px, list(protect))] = transparent
    solid = px != transparent
    surrounded = np.logical_and.reduce(sides(solid))
    px[solid & ~surrounded & ~np.isin(px, list(dark | protect))] = outline


MEADOW_FX, MEADOW_FY = 10.0, 9.3  # the meadow's "pixels" are not square
MEADOW_COLORS = 48
CLOUD_COLORS = 2  # white and the light-blue shading, on top of the sky colour
# Backgrounds: assets/src/<name>.png -> assets/px/<name>-clouds/back/ground.png and <name>.json.
# The mod picks one at random on every turn.
BACKGROUNDS = ["meadow", "autumn", "winter"]
# Extra colours for a background whose rare colours median cut loses: in the winter meadow
# the brown trunks and twigs (under 1% of the pixels) turned near black.
EXTRA_COLORS = {"winter": 4}
SKY_H = 20  # rows of sky above the hills in the band
GROUND_H = 27  # rows of grass below the bushes in the band


def meadow(name: str) -> dict:
    """Background in three layers: clouds (moved into a low sky), hills with trees, grass."""
    img = Image.open(SRC / f"{name}.png").convert("RGB")
    q = img.quantize(MEADOW_COLORS, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[: MEADOW_COLORS * 3]).reshape(-1, 3)
    if EXTRA_COLORS.get(name):
        # colours the palette misses by far (more than 60 in the sum of channel differences)
        # get their own, and every pixel is mapped to the nearest colour of the larger palette
        flat = np.asarray(img).reshape(-1, 3).astype(int)
        missed = flat[np.abs(flat - pal[np.asarray(q).ravel()]).sum(1) > 60]
        extra = Image.fromarray(missed.reshape(1, -1, 3).astype(np.uint8)).quantize(
            EXTRA_COLORS[name], method=Image.Quantize.MEDIANCUT, kmeans=10
        )
        pal = np.vstack([pal, np.array(extra.getpalette()[: EXTRA_COLORS[name] * 3]).reshape(-1, 3)])
        pal_img = Image.new("P", (1, 1))
        pal_img.putpalette([int(c) for c in pal.ravel()] + [int(c) for c in pal[0]] * (256 - len(pal)))
        q = img.quantize(palette=pal_img, dither=Image.Dither.NONE)
    idx = np.asarray(q).astype(np.int16)
    px = downsample_rect(idx, MEADOW_FX, MEADOW_FY, len(pal))
    rgb = pal[px].astype(np.uint8)
    h, w, _ = rgb.shape

    vals, counts = np.unique(rgb[2].reshape(-1, 3), axis=0, return_counts=True)
    sky = vals[counts.argmax()]
    not_sky = np.abs(rgb.astype(int) - sky).sum(2) > 30

    # top of the hills: the block of rows that are at least a third not sky and run unbroken
    # down to the bottom, plus 3 rows for the peaks. Cloud rows sit above a gap of clear sky.
    # White counts as not sky, because snowy hills are white too.
    solid_rows = not_sky.mean(1) > 0.3
    hills_top = h
    while hills_top > 0 and solid_rows[hills_top - 1]:
        hills_top -= 1
    hills_top -= 3
    # top of the grass: row below the bushes with the most light green. A ground that is not
    # green (snow) starts on the row after the dark line under the bushes.
    g = rgb.astype(int)
    light_grass = (g[..., 1] > 170) & (g[..., 0] > 90) & (g[..., 2] < 90)
    green_rows = light_grass[hills_top + 20 :].mean(1) > 0.6
    if green_rows.any():
        grass_top = hills_top + 20 + int(np.argmax(green_rows))
    else:
        grass_top = hills_top + 21 + int(g[hills_top + 20 : hills_top + 40].sum(2).mean(1).argmin())

    def rgba(part: np.ndarray, mask: np.ndarray) -> Image.Image:
        out = np.zeros((*part.shape[:2], 4), dtype=np.uint8)
        out[mask, :3] = part[mask]
        out[mask, 3] = 255
        return Image.fromarray(out, "RGBA")

    # clouds get their own small palette from the sky above the hills: in the shared palette
    # their light-blue shading merges into the sky or a grey-green and they turn into flat blobs
    # (the sky is most of the pixels, so the cloud colours come from the cloud pixels alone)
    top = np.asarray(Image.open(SRC / f"{name}.png").convert("RGB"))[: int(hills_top * MEADOW_FY)]
    flat = top.reshape(-1, 3).astype(int)
    vals, counts = np.unique(flat, axis=0, return_counts=True)
    src_sky = vals[counts.argmax()]
    cloudy = flat[np.abs(flat - src_sky).sum(1) > 30]
    cloud_q = Image.fromarray(cloudy.reshape(1, -1, 3).astype(np.uint8)).quantize(
        CLOUD_COLORS, method=Image.Quantize.MEDIANCUT
    )
    cloud_pal = np.vstack([src_sky, np.array(cloud_q.getpalette()[: CLOUD_COLORS * 3]).reshape(-1, 3)])
    nearest = ((flat[:, None, :] - cloud_pal[None]) ** 2).sum(2).argmin(1)
    cloud_px = downsample_rect(
        nearest.reshape(top.shape[:2]).astype(np.int16), MEADOW_FX, MEADOW_FY, len(cloud_pal)
    )[:hills_top]
    sky_rgb = cloud_pal[cloud_px].astype(np.uint8)
    cloud_mask = cloud_px > 0

    # clouds: each cloud on its own, lowered into the band's low sky
    lab, k = ndimage.label(cloud_mask)
    clouds = np.zeros((SKY_H, w, 4), dtype=np.uint8)
    for i, box in enumerate(ndimage.find_objects(lab), start=1):
        ch = box[0].stop - box[0].start
        if ch > SKY_H - 2:
            continue
        y = min(max(1, box[0].start // 2), SKY_H - ch - 1)
        part = sky_rgb[box]
        m = lab[box] == i
        tgt = clouds[y : y + ch, box[1]]
        tgt[m, :3] = part[m]
        tgt[m, 3] = 255
    Image.fromarray(clouds, "RGBA").save(OUT / f"{name}-clouds.png")

    back = rgb[hills_top:grass_top]
    rgba(back, not_sky[hills_top:grass_top]).save(OUT / f"{name}-back.png")
    ground = rgb[grass_top : grass_top + GROUND_H]
    rgba(ground, np.ones(ground.shape[:2], bool)).save(OUT / f"{name}-ground.png")

    info = {
        "sky": "#%02x%02x%02x" % tuple(int(c) for c in sky),
        "width": w,
        "back_h": grass_top - hills_top,
        "ground_h": GROUND_H,
        "sky_h": SKY_H,
    }
    print(name, w, "x", h, "hills", hills_top, "grass", grass_top, info)
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
    """Shared palette from all dog pixels in all images. The tongue and the highlight have too
    few pixels for median cut to give them a colour, so each gets its own on top of PALETTE_SIZE."""

    def pixels(mask_of) -> np.ndarray:
        return np.concatenate([s[mask_of(s) & ~bgs[n]] for n, s in sheets.items()])

    fg_pixels = pixels(lambda s: ~tongue_mask(s) & ~white_mask(s))
    sample = fg_pixels[:: max(1, len(fg_pixels) // 200_000)]
    # k-means refinement: without it median cut loses the neutral dark grey and the saddle gets brown blotches
    pal_img = Image.fromarray(sample.reshape(1, -1, 3).astype(np.uint8)).quantize(
        PALETTE_SIZE, method=Image.Quantize.MEDIANCUT, kmeans=20
    )
    palette = np.array(pal_img.getpalette()[: PALETTE_SIZE * 3]).reshape(-1, 3)
    tongue = pixels(tongue_mask).mean(0)
    shades = [np.clip(tongue * k, 0, 255) for k in TONGUE_SHADES]
    return np.vstack(
        [palette, shades[0], tongue, shades[1], pixels(white_mask).mean(0)]
    ).round().astype(int)


def save_palette(palette: np.ndarray) -> None:
    hexes = ["#%02x%02x%02x" % tuple(int(c) for c in p) for p in palette]
    data = {"fur": hexes[:-4], "tongue": hexes[-4:-1], "highlight": hexes[-1]}
    PALETTE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("new palette saved to", PALETTE_FILE.relative_to(ROOT))


def load_palette() -> tuple[np.ndarray, int]:
    """Fur and outline colours, then the tongue shades, then the eye highlight (the order sets the
    indices), and the number of tongue shades."""
    data = json.loads(PALETTE_FILE.read_text(encoding="utf-8"))
    hexes = data["fur"] + data["tongue"] + [data["highlight"]]
    return np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in hexes]), len(data["tongue"])


# Breathing: from the last sleep frame comes a frame with the whole back raised by one pixel.
# Columns measured on sleep-5 (4.10.2026): the back runs from the loin (x 17) to the neck
# (x 35); the head with the ears is to the right of that and stays in place. The ends are
# chosen so the outline never jumps by two pixels: the left end sits inside a flat run (x 16
# and 17 are at the same height), the right end next to a column that is already higher
# (x 36). Raising only part of the back looks like a growing lump.
# Check the columns after a new sleep drawing.
BREATH_FROM = "sleep-5"
BREATH_RAISE = {1: (17, 35)}  # frame: columns (from, to) raised by one pixel
BREATH_DEPTH = 4  # how many rows below the outline move up; the row below is repeated (fur)

# Blinking while she sits and looks at the viewer: derived from that frame, so nothing but the
# eyes moves. Each eye (a dark patch holding a highlight) is filled with the fur around it and
# its bottom row is drawn back in the outline colour, a closed eye.
BLINK_FROM = "sit-4"


def blink(palette: np.ndarray, dark: set, outline: int) -> None:
    a = np.asarray(Image.open(OUT / f"{BLINK_FROM}.png").convert("RGBA")).copy()
    key = a[..., 0].astype(int) << 16 | a[..., 1].astype(int) << 8 | a[..., 2]
    dark_keys = {int(palette[i][0]) << 16 | int(palette[i][1]) << 8 | int(palette[i][2]) for i in dark}
    white = (a[..., :3].astype(int).min(2) > 235) & (a[..., 3] > 0)
    eyes, k = ndimage.label((np.isin(key, list(dark_keys)) | white) & (a[..., 3] > 0))
    for i in range(1, k + 1):
        eye = eyes == i
        if not (eye & white).any():
            continue  # the nose and the outline have no highlight
        around = ndimage.binary_dilation(eye) & ~eye & (a[..., 3] > 0)
        colors, counts = np.unique(key[around], return_counts=True)
        fur = int(colors[counts.argmax()])
        ys, xs = np.where(eye)
        a[eye, :3] = [fur >> 16, fur >> 8 & 255, fur & 255]
        bottom = eye & (np.arange(a.shape[0])[:, None] == ys.max())
        a[bottom, :3] = palette[outline]
    Image.fromarray(a, "RGBA").save(OUT / "sit-blink.png")
    print("blink from", BLINK_FROM)


# The orange ball she chases is drawn here, not by ChatGPT: a pixel circle with Ferro's outline,
# lit from the top left. 9 pixels is about a dog ball next to a Norwich Terrier.
BALL_D = 9
BALL_COLORS = {"light": "#f8b25a", "base": "#ee8a2a", "shade": "#c4601e", "highlight": "#fff3dc"}


def ball(outline_rgb: np.ndarray) -> None:
    r = BALL_D / 2
    yy, xx = np.mgrid[0:BALL_D, 0:BALL_D] + 0.5
    inside = (xx - r) ** 2 + (yy - r) ** 2 <= r * r
    p = np.pad(inside, 1)
    edge = inside & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    # light from the top left: how far each pixel lies along that direction, -1 to 1
    lit = ((r - xx) + (r - yy)) / (r * 1.414)
    rgb = lambda h: [int(h[i : i + 2], 16) for i in (1, 3, 5)]  # noqa: E731
    out = np.zeros((BALL_D, BALL_D, 4), dtype=np.uint8)
    out[inside, 3] = 255
    out[inside & (lit > 0.35)] = rgb(BALL_COLORS["light"]) + [255]
    out[inside & (lit <= 0.35) & (lit > -0.35)] = rgb(BALL_COLORS["base"]) + [255]
    out[inside & (lit <= -0.35)] = rgb(BALL_COLORS["shade"]) + [255]
    out[2, 2] = rgb(BALL_COLORS["highlight"]) + [255]
    out[edge, :3] = outline_rgb
    Image.fromarray(out, "RGBA").save(OUT / "ball.png")
    print("ball", BALL_D, "x", BALL_D)


# The water bowls she drinks from and the drops she splashes beside them: bowl.png (ChatGPT),
# three bowls in a row (red, steel, blue) and five drops below them. The code-drawn bowl was
# rejected (Vatra, 7.10.2026). They are props with colours of their own, so each figure gets its
# own small palette (median cut over its pixels, like the clouds) instead of the dog's, and one
# factor for all: the bowls come out 17x8, low enough that the water lies under her jaw where her
# tongue reaches it in drink-1, and the drops keep their size relative to the bowls. Saved as bowl-<i>.png and water-drop-<i>.png.
PROP_FACTOR = {"bowl": 24.0}
PROP_COLORS = (10, 5)  # colours of a bowl, of a drop
PROP_BIG = 200  # source pixels: a wider figure is a bowl, a narrower one a drop


def props(name: str) -> None:
    rgb = np.asarray(Image.open(SRC / f"{name}.png").convert("RGB"))
    bg = background_mask(rgb)
    bg |= fringe_mask(rgb, bg)
    factor = PROP_FACTOR[name]
    counts = {"bowl": 0, "water-drop": 0}
    for box, own in components(rgb, 400):
        big = box[1].stop - box[1].start >= PROP_BIG
        mine = own & ~bg[box]
        n = PROP_COLORS[0 if big else 1]
        q = Image.fromarray(rgb[box][mine].reshape(1, -1, 3)).quantize(
            n, method=Image.Quantize.MEDIANCUT, kmeans=10
        )
        pal = np.array(q.getpalette()[: n * 3]).reshape(-1, 3)
        idx = np.full(mine.shape, n, dtype=np.int16)
        idx[mine] = np.asarray(q).ravel()
        px = downsample(idx, factor, n)
        if big:  # a drop is all edge: cleaning would turn it into outline
            dark = {i for i, p in enumerate(pal) if p.sum() < 200}
            clean_edges(px, n, dark, set(), int(pal.sum(1).argmin()))
        out = np.zeros((*px.shape, 4), dtype=np.uint8)
        solid = px != n
        out[solid, :3] = pal[px[solid]]
        out[solid, 3] = 255
        kind = "bowl" if big else "water-drop"
        Image.fromarray(out, "RGBA").save(OUT / f"{kind}-{counts[kind]}.png")
        print(kind, counts[kind], "size", px.shape[1], "x", px.shape[0])
        counts[kind] += 1


def breathing(palette: np.ndarray, dark: set, outline: int) -> None:
    src = np.asarray(Image.open(OUT / f"{BREATH_FROM}.png").convert("RGBA"))
    dark_rgb = {tuple(int(c) for c in palette[i]) for i in dark}
    for k, (x0, x1) in BREATH_RAISE.items():
        a = src.copy()
        for x in range(x0, x1 + 1):
            top = int(np.argmax(a[:, x, 3] > 0))
            a[top - 1 : top + BREATH_DEPTH, x] = src[top : top + BREATH_DEPTH + 1, x]
        # where a step is higher than one pixel, fur is left next to the background: close the outline
        solid = a[..., 3] > 0
        p = np.pad(solid, 1)
        exposed = solid & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        for y, x in zip(*np.where(exposed)):
            if tuple(int(c) for c in a[y, x, :3]) not in dark_rgb:
                a[y, x, :3] = palette[outline]
        Image.fromarray(a, "RGBA").save(OUT / f"sleep-breath-{k}.png")
        print("breath", k, "columns", x0, "-", x1)


# Sniffing a spot: the head bobs between the nose on the grass (sniff-5) and one pixel higher.
# sniff-up is derived from sniff-5 by raising every column from SNIFF_HEAD_X to the nose: the
# head and the ears, never the front legs, which end left of it. ChatGPT would redraw the dog.
SNIFF_FROM = "sniff-5"
SNIFF_HEAD_X = 46


def sniff_bob(palette: np.ndarray, dark: set, outline: int) -> None:
    src = np.asarray(Image.open(OUT / f"{SNIFF_FROM}.png").convert("RGBA"))
    a = src.copy()
    a[:-1, SNIFF_HEAD_X:] = src[1:, SNIFF_HEAD_X:]
    a[-1, SNIFF_HEAD_X:] = 0
    # fur left next to the background where the raised head meets the neck: close the outline
    dark_rgb = {tuple(int(c) for c in palette[i]) for i in dark}
    solid = a[..., 3] > 0
    p = np.pad(solid, 1)
    exposed = solid & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    for y, x in zip(*np.where(exposed)):
        if tuple(int(c) for c in a[y, x, :3]) not in dark_rgb:
            a[y, x, :3] = palette[outline]
    Image.fromarray(a, "RGBA").save(OUT / "sniff-up.png")
    print("sniff-up from", SNIFF_FROM, "columns", SNIFF_HEAD_X, "and right")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in BACKGROUNDS:
        (OUT / f"{name}.json").write_text(json.dumps(meadow(name)))
    sheets = {n: np.asarray(Image.open(SRC / f"{n}.png").convert("RGB")) for n in FACTOR}

    bgs = {n: background_mask(s) for n, s in sheets.items()}
    bgs = {n: bg | fringe_mask(sheets[n], bg) for n, bg in bgs.items()}

    if "--new-palette" in sys.argv or not PALETTE_FILE.exists():
        save_palette(new_palette(sheets, bgs))
    palette, tongue_n = load_palette()
    fur_n = len(palette) - tongue_n - 1
    tongue_ids = tuple(range(fur_n, fur_n + tongue_n))
    white_i, transparent = fur_n + tongue_n, fur_n + tongue_n + 1
    dark = {i for i, p in enumerate(palette) if p.sum() < 200}  # outline, nose, eyes
    outline = int(palette[:fur_n].sum(1).argmin())

    for name, rgb in sheets.items():
        bg = bgs[name]
        flat = rgb.reshape(-1, 3).astype(int)
        # nearest fur colour for each source pixel; tongue and highlight only where they are drawn
        best = np.zeros(len(flat), dtype=np.int16)
        best_d = np.full(len(flat), 1 << 30)
        for i, p in enumerate(palette[:fur_n]):
            d = ((flat - p) ** 2).sum(1)
            better = d < best_d
            best[better], best_d[better] = i, d[better]
        idx = best.reshape(bg.shape)
        shade = tongue_shades(rgb, bg, palette[fur_n : fur_n + tongue_n].astype(float))
        idx[shade >= 0] = fur_n + shade[shade >= 0]
        white = white_mask(rgb)
        idx[white] = white_i
        idx[bg] = transparent

        found = components(rgb, 400)
        # the image's ground: the lowest dog (a row of droppings may sit lower)
        ground = max(box[0].stop for box, _ in found if box[1].stop - box[1].start >= 20 * FACTOR[name])
        parts = []
        for box, own in found:
            crop = idx[box].copy()
            crop[~own] = transparent
            is_dog = box[1].stop - box[1].start >= 20 * FACTOR[name]
            factor = FACTOR[name] if is_dog or name not in DROPPINGS else DROPPINGS[name]
            px = downsample(crop, factor, transparent, tongue_ids)
            # the ear used for alignment is measured before cleaning, so frames stay where they were
            ear = ear_right(px, transparent) if px.shape[1] >= 20 else 0
            if name in TOES_X and px.shape[1] >= 20:
                ear = int(np.where((px[-2:] != transparent).any(0))[0].max())  # front toes
            if name in NOSE_X and px.shape[1] >= 20:
                ear = int(np.where((px != transparent).any(0))[0].max())  # nose
            clean_edges(px, transparent, dark, {*tongue_ids, white_i}, outline)
            catchlights(px, white[box] & own, factor, white_i, dark, transparent)
            solid = px != transparent
            out = np.zeros((*px.shape, 4), dtype=np.uint8)
            out[solid, :3] = palette[px[solid]]
            out[solid, 3] = 255
            parts.append((box, px, ear, Image.fromarray(out, "RGBA")))

        dogs = []
        for box, px, ear, img in parts:
            if px.shape[1] < 20:  # the pile, not the dog
                continue
            # alignment: ear at ANCHOR_X, height from the source image's ground
            x = TOES_X.get(name, NOSE_X.get(name, ANCHOR_X)) - ear
            y = CANVAS_H - int(round((ground - box[0].start) / FACTOR[name]))
            canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
            canvas.paste(img, (x, y), img)
            fixed = FIX / f"{name}-{len(dogs)}.png"
            if fixed.exists():
                canvas = Image.open(fixed).convert("RGBA")
                assert canvas.size == (CANVAS_W, CANVAS_H), f"{fixed.name} is {canvas.size}, not {CANVAS_W}x{CANVAS_H}"
            canvas.save(OUT / f"{name}-{len(dogs)}.png")
            dogs.append((box, x))
            print(name, len(dogs) - 1, "size", px.shape[1], "x", px.shape[0], "at", x, y,
                  "(fixed by hand)" if fixed.exists() else "")

        if name in DROPPINGS:
            drops = [img for _, px, _, img in parts if px.shape[1] < 20]
            for i, img in enumerate(drops):
                img.save(OUT / f"{name}-drop-{i}.png")
                print(name, "drop", i, "size", img.width, "x", img.height)
            continue

        # pile: position on the canvas of the dog right of it (the one making it)
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

    breathing(palette, dark, outline)
    ball(palette[outline])
    for name in PROP_FACTOR:
        props(name)
    blink(palette, dark, outline)
    sniff_bob(palette, dark, outline)


if __name__ == "__main__":
    main()
