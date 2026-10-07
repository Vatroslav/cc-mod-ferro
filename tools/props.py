"""Cuts the props she runs past (assets/src/props-*.png, ChatGPT) into real pixels: one pixel per
ChatGPT pixel, on its own grid, with a palette of its own per figure (median cut over its pixels,
like the bowls). Scaling a drawing down to a set height lost most of its detail and broke its
outline into stray dots (Vatra, 7.10.2026), so a prop is as big as ChatGPT drew it, and one that is
too big for its place is drawn again, smaller (MAX_H).

The registry is assets/props.json, one entry per prop: its sheet, where it stands ("ground": on the
meadow, behind or in front of her; "far": behind the hills) and its chance in percent per slot (see
scene.py). The entries of a sheet name its figures in the order they stand in it: rows top to
bottom, each left to right. Saves assets/px/prop-<name>.png, and preview/props.html to compare each
with its drawing.

Run (from the repo root): python tools/props.py
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from build import OUT, ROOT, SRC, background_mask, clean_edges, fringe_mask

REGISTRY = ROOT / "assets" / "props.json"
MERGE_PX = 8  # source pixels: parts of one figure closer than this belong together
MIN_AREA = 4000  # source pixels: smaller specks (the flying cars around the future city) are left out
COLORS = 20
GRID_PX = (3.0, 16.0)  # the sizes of a ChatGPT pixel looked for, in source pixels
SUBGRID = 0.7  # see pixel_size
# The tallest a prop may be: one on the grass behind her stands on row 70 at the highest, and a far
# one stands behind the hills on row 34 (scene.py). A taller drawing is not shrunk, because that
# loses its detail (Vatra, 7.10.2026): ChatGPT draws it again, smaller.
MAX_H = {"ground": 70, "far": 34}


def registry() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["props"]


def figures(rgb: np.ndarray, bg: np.ndarray) -> list[tuple[tuple[slice, slice], np.ndarray]]:
    """(box, mask) of each figure, rows top to bottom, each left to right."""
    fg = ~bg
    lab, _ = ndimage.label(ndimage.binary_dilation(ndimage.binary_opening(fg, iterations=1), iterations=MERGE_PX))
    found = []
    for i, box in enumerate(ndimage.find_objects(lab), start=1):
        own = fg[box] & (lab[box] == i)
        if own.sum() < MIN_AREA:
            continue
        ys, xs = np.where(own)
        y0, x0 = box[0].start + ys.min(), box[1].start + xs.min()
        tight = (slice(y0, box[0].start + ys.max() + 1), slice(x0, box[1].start + xs.max() + 1))
        found.append((tight, own[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]))
    found.sort(key=lambda f: f[0][0].start)
    rows: list[list] = []
    for f in found:
        if rows and f[0][0].start < max(g[0][0].stop for g in rows[-1]):
            rows[-1].append(f)
        else:
            rows.append([f])
    return [f for row in rows for f in sorted(row, key=lambda f: f[0][1].start)]


def energies(rgb: np.ndarray, own: np.ndarray) -> list[np.ndarray]:
    """How much the colour changes across each boundary, for rows (0) and columns (1):
    e[b] is the change between pixel b and b + 1, where a grid line at b + 1 would be."""
    a = rgb.astype(int)
    return [(np.abs(np.diff(a, axis=0)).sum(2) * (own[1:] & own[:-1])).sum(1),
            (np.abs(np.diff(a, axis=1)).sum(2) * (own[:, 1:] & own[:, :-1])).sum(0)]


def on_grid(energy: np.ndarray, p: float, ph: float) -> float:
    n = len(energy)
    pos = np.round(np.arange(ph, n, p)).astype(int) - 1
    pos = pos[(pos >= 0) & (pos < n)]
    return float(energy[pos].mean()) if len(pos) else 0.0


def best_phase(energy: np.ndarray, p: float, step: float = 0.5) -> tuple[float, float]:
    return max((on_grid(energy, p, ph), ph) for ph in np.arange(0, p, step))


def pixel_size(figs: list[list[np.ndarray]]) -> float:
    """ChatGPT's pixel size in source pixels, for a whole sheet: it draws a sheet on one grid of
    flat square blocks, so the colour changes of every figure, along both axes, line up on a grid
    of one size. The size with the strongest changes on its lines wins. A multiple of the size
    scores about as high (every second line of the grid is a line of the double), and on one figure
    alone it sometimes won (7.10.2026: the tower came out at twice the size of the town beside it),
    so a half or a third of the winner takes over when it scores at least SUBGRID of it."""

    def score(p: float, step: float = 0.5) -> float:
        return sum(best_phase(es[0], p, step)[0] + best_phase(es[1], p, step)[0] for es in figs)

    _, p = max((score(q), q) for q in np.arange(*GRID_PX, 0.05))
    for k in (3, 2):
        if p / k >= GRID_PX[0] and score(p / k) >= SUBGRID * score(p):
            p /= k
            break
    return max((score(q, 0.1), q) for q in np.arange(p - 0.1, p + 0.1, 0.01))[1]


def grid_lines(energy: np.ndarray, p: float) -> list[int]:
    """Where ChatGPT's pixels start along one axis, from 0 to the end: on the grid of size p, each
    line snapped to the strongest change near it, because the grid of a generated image drifts a
    little."""
    n = len(energy)
    ph = best_phase(energy, p, 0.1)[1]
    lines, r = [0], max(1, int(p / 3))
    for line in np.arange(ph, n + 1, p):
        b = int(round(line)) - 1
        lo, hi = max(b - r, 0), min(b + r + 1, n)
        if lo < hi:
            b = lo + int(np.argmax(energy[lo:hi]))
        if b + 1 - lines[-1] >= p / 2:
            lines.append(b + 1)
    if n + 1 - lines[-1] < p / 2:
        lines.pop()
    return lines + [n + 1]


def cut(rgb: np.ndarray, own: np.ndarray, p: float, outline: bool) -> np.ndarray:
    """One figure as RGBA real pixels, one per ChatGPT pixel (p source pixels): each takes the most
    common colour of the middle of its block, so the blocks' blurred edges do not vote. With
    `outline`, the edge is cleaned as Ferro's is (stray pixels removed, the dark outline closed)."""
    q = Image.fromarray(rgb[own].reshape(1, -1, 3)).quantize(COLORS, method=Image.Quantize.MEDIANCUT, kmeans=10)
    pal = np.array(q.getpalette()[: COLORS * 3]).reshape(-1, 3)
    idx = np.full(own.shape, COLORS, dtype=np.int16)
    idx[own] = np.asarray(q).ravel()
    es = energies(rgb, own)
    rows, cols = grid_lines(es[0], p), grid_lines(es[1], p)
    px = np.full((len(rows) - 1, len(cols) - 1), COLORS, dtype=np.int16)
    for y, (y0, y1) in enumerate(zip(rows, rows[1:])):
        my = (y1 - y0) // 4
        for x, (x0, x1) in enumerate(zip(cols, cols[1:])):
            mx = (x1 - x0) // 4
            counts = np.bincount(idx[y0 + my : y1 - my, x0 + mx : x1 - mx].ravel(), minlength=COLORS + 1)
            if counts[COLORS] * 2 < counts.sum():
                counts[COLORS] = 0
                px[y, x] = counts.argmax()
    if outline:
        dark = {i for i, c in enumerate(pal) if c.sum() < 200}
        clean_edges(px, COLORS, dark, set(), int(pal.sum(1).argmin()))
    # rows and columns left empty at the edges
    solid = px != COLORS
    ys, xs = np.where(solid)
    px, solid = px[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1], solid[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    out = np.zeros((*px.shape, 4), dtype=np.uint8)
    out[solid, :3] = pal[px[solid]]
    out[solid, 3] = 255
    return out


def main() -> None:
    PREVIEW_SRC.mkdir(parents=True, exist_ok=True)
    props = registry()
    too_big = []
    names = [p["name"] for p in props]
    assert len(set(names)) == len(names), "two props with the same name"
    for where in ("ground", "far"):
        total = sum(p["chance"] for p in props if p["where"] == where)
        assert total <= 100, f"the chances of the {where} props add up to {total}, over 100"
    for sheet in dict.fromkeys(p["sheet"] for p in props):
        mine = [p for p in props if p["sheet"] == sheet]
        rgb = np.asarray(Image.open(SRC / f"{sheet}.png").convert("RGB"))
        bg = background_mask(rgb)
        bg |= fringe_mask(rgb, bg)
        found = figures(rgb, bg)
        assert len(found) == len(mine), f"{sheet}: {len(found)} figures, the registry names {len(mine)}"
        size = pixel_size([energies(rgb[box], own) for box, own in found])
        print(f"{sheet}: a ChatGPT pixel is {size:.2f} source pixels")
        for p, (box, own) in zip(mine, found):
            out = cut(rgb[box], own, size, p["where"] == "ground")
            Image.fromarray(out, "RGBA").save(OUT / f"prop-{p['name']}.png")
            src = np.dstack([rgb[box], np.where(own, 255, 0).astype(np.uint8)])
            Image.fromarray(src, "RGBA").save(PREVIEW_SRC / f"{p['name']}.png")
            big = out.shape[0] > MAX_H[p["where"]]
            if big:
                too_big.append(p["name"])
            print(f"{p['name']}: {out.shape[1]} x {out.shape[0]} ({p['where']}, {p['chance']}%)"
                  + (f" TOO TALL, at most {MAX_H[p['where']]}: draw it again, smaller" if big else ""))
    page(props)
    if too_big:
        print("too tall:", ", ".join(too_big))


PREVIEW = ROOT / "preview"
PREVIEW_SRC = PREVIEW / "props-src"
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ferro - props</title>
<style>
  body {{ font: 14px system-ui, sans-serif; background: #2a2a2a; color: #ddd; margin: 16px; }}
  .prop {{ display: flex; gap: 24px; align-items: flex-end; margin: 0 0 28px; flex-wrap: wrap; }}
  .prop div {{ display: flex; flex-direction: column; gap: 4px; }}
  img {{ background: #6aa95a; image-rendering: pixelated; }}
  img.src {{ image-rendering: auto; }}
  small {{ color: #999; }}
</style>
</head>
<body>
  <p>The props of assets/props.json (written by tools/props.py, not committed). Left: the figure as
  ChatGPT drew it, at its own size. Middle: the real pixels the mod uses, enlarged to about the same
  size. Right: at the size the band shows it (2 CSS pixels per pixel), next to Ferro.</p>
{rows}
</body>
</html>
"""


def page(props: list[dict]) -> None:
    rows = []
    for p in props:
        w, h = Image.open(OUT / f"prop-{p['name']}.png").size
        sw, sh = Image.open(PREVIEW_SRC / f"{p['name']}.png").size
        zoom = max(1, round(sh / h))
        rows.append(
            f'  <h3>{p["name"]} <small>{p["where"]}, {p["chance"]}% per slot, {w} x {h} pixels</small></h3>\n'
            f'  <div class="prop">\n'
            f'    <div><img class="src" src="props-src/{p["name"]}.png" width="{sw}" height="{sh}">'
            f'<small>ChatGPT, its own size</small></div>\n'
            f'    <div><img src="../assets/px/prop-{p["name"]}.png" width="{w * zoom}" height="{h * zoom}">'
            f'<small>pixels, enlarged {zoom}x</small></div>\n'
            f'    <div><img src="../assets/px/prop-{p["name"]}.png" width="{w * 2}" height="{h * 2}">'
            f'<small>in the band</small></div>\n'
            f'    <div><img src="../assets/px/run-0.png" width="152" height="88"><small>Ferro in the band</small></div>\n'
            f'  </div>'
        )
    (PREVIEW / "props.html").write_text(PAGE.format(rows="\n".join(rows)), encoding="utf-8")


if __name__ == "__main__":
    main()
