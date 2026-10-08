"""Cuts the props she runs past (assets/src/props-*.png, ChatGPT) into real pixels: one pixel per
ChatGPT pixel, on its own grid, with a palette of its own per figure (median cut over its pixels,
like the bowls). Scaling a drawing down to a set height lost most of its detail and broke its
outline into stray dots (Vatra, 7.10.2026), so a prop is as big as ChatGPT drew it.

A sheet is cut only if ChatGPT drew it to the measures it was asked for (Vatra, 8.10.2026: if it is
not good, reject the file and ask for a new one). Guessing the grid of a sheet drawn off it cut
across its pixels: Orthanc's four horns were thinner than one of its blocks and broke. So the
message asks for a grid over the whole image (`grid` of the sheet in the registry: pixels across and
down) and a size for each object (`size` of the prop), and a sheet whose pixels are off that grid, or
with a figure off its size or too tall for its place, is rejected whole: its props stay out of the
mod and ChatGPT draws it again. Nothing is rescaled or repaired to make it fit. Sheets cut before
the rule carry `approved_by_eye` (Vatra saw them in the band) and are not checked.
`python tools/props.py --template <sheet>` draws the grid and the box of each object as an image to
attach to the message (assets/ref/template-<sheet>.png).

ChatGPT never held the grid (four tries for Orthanc, 8.10.2026), so a prop can also come from PixelLab
(tools/pixellab.py), which draws in real pixels at the size asked: a `native` sheet is one prop's own
image (assets/src/prop-<name>.png), nothing to cut. It passes the same gate (`native_check`): only
fully opaque or fully clear pixels, its size, its place.

The registry is assets/props.json, one entry per prop: its sheet, where it stands ("ground": on the
meadow, behind or in front of her; "far": behind the hills; "edge": at the far edge of the meadow, in
front of the forest) and its chance in percent per slot (see
scene.py). The entries of a sheet name its figures in the order they stand in it: rows top to
bottom, each left to right. Saves assets/px/prop-<name>.png, and preview/props.html to compare each
with its drawing.

Run (from the repo root): python tools/props.py
"""

import json
import sys
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
# The tallest a prop may be: one on the grass behind her stands on row 70 at the highest, a far one
# behind the hills with its top 2 rows below the top of the band and its bottom above row 55, one at
# the edge of the meadow in front of the forest on row 56 (scene.py). A taller drawing is not shrunk, because that
# loses its detail (Vatra, 7.10.2026): ChatGPT draws it again, smaller.
MAX_H = {"ground": 70, "far": 53, "edge": 56}
# How far a sheet may be off what was asked before it is rejected: its pixel size off the grid's
# (image width / pixels across), and a figure off its size, by a share or at least SIZE_SLACK pixels.
GRID_TOLERANCE = 0.05
SIZE_TOLERANCE = 0.10
SIZE_SLACK = 2
TEMPLATE_W = 1536  # the width of a template image; its pixels are TEMPLATE_W / pixels across


def registry() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["props"]


def sheets() -> dict[str, dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["sheets"]


def check(spec: dict, shape: tuple[int, ...], size: float, mine: list[dict], found: list) -> list[str]:
    """What is off the measures the sheet was asked for: nothing for a sheet drawn to them."""
    across, down = spec["grid"]
    block = shape[1] / across
    problems = []
    if abs(size / block - 1) > GRID_TOLERANCE:
        problems.append(f"its pixels are {size:.1f} source pixels, the grid asked has {block:.1f} "
                        f"({shape[1] / size:.0f} across instead of {across})")
    if abs(shape[0] / block - down) > GRID_TOLERANCE * down:
        problems.append(f"the image is {shape[0] / block:.0f} grid pixels down instead of {down}")
    for p, (box, _) in zip(mine, found):
        w, h = (box[1].stop - box[1].start) / block, (box[0].stop - box[0].start) / block
        aw, ah = p["size"]
        if any(abs(got - want) > max(SIZE_SLACK, SIZE_TOLERANCE * want) for got, want in ((w, aw), (h, ah))):
            problems.append(f"{p['name']} is {w:.0f} x {h:.0f} grid pixels, asked {aw} x {ah}")
    return problems


def native_check(img: np.ndarray, p: dict) -> tuple[list[str], np.ndarray | None]:
    """A prop drawn in real pixels (RGBA): what is off its measures, and the prop trimmed to its
    pixels. Nothing is changed: a half-clear pixel is a problem, not something to round."""
    a = img[..., 3]
    if not a.any():
        return ["empty"], None
    problems = []
    half = int(((a > 0) & (a < 255)).sum())
    if half:
        problems.append(f"{half} half-clear pixels")
    ys, xs = np.where(a > 0)
    out = img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    h, w = out.shape[:2]
    aw, ah = p["size"]
    if any(abs(got - want) > max(SIZE_SLACK, SIZE_TOLERANCE * want) for got, want in ((w, aw), (h, ah))):
        problems.append(f"{w} x {h} pixels, asked {aw} x {ah}")
    if h > MAX_H[p["where"]]:
        problems.append(f"{h} pixels tall, at most {MAX_H[p['where']]}")
    return problems, out


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
    specs = sheets()
    too_big, rejected = [], {}
    names = [p["name"] for p in props]
    assert len(set(names)) == len(names), "two props with the same name"
    # a ground slot takes a ground prop, a far slot a far one or one at the edge
    for pool in (("ground",), ("far", "edge")):
        total = sum(p["chance"] for p in props if p["where"] in pool)
        assert total <= 100, f"the chances of the {' and '.join(pool)} props add up to {total}, over 100"
    for sheet in dict.fromkeys(p["sheet"] for p in props):
        mine = [p for p in props if p["sheet"] == sheet]
        spec = specs.get(sheet, {})
        assert {"grid", "native", "approved_by_eye"} & spec.keys(), f"{sheet}: give it its measures in the sheets of props.json"
        assert "approved_by_eye" in spec or all("size" in p for p in mine), f"{sheet}: give each prop the size asked"
        assert not spec.get("native") or len(mine) == 1, f"{sheet}: a native sheet is one prop"
        if not (SRC / f"{sheet}.png").exists():
            # a sheet not drawn yet: its props stay out of the mod
            for p in mine:
                (OUT / f"prop-{p['name']}.png").unlink(missing_ok=True)
            print(f"{sheet}: not drawn yet, so {', '.join(p['name'] for p in mine)} wait")
            continue
        if spec.get("native"):
            p = mine[0]
            problems, out = native_check(np.asarray(Image.open(SRC / f"{sheet}.png").convert("RGBA")), p)
            if problems:
                rejected[sheet] = problems
                (OUT / f"prop-{p['name']}.png").unlink(missing_ok=True)
                print(f"{sheet}: REJECTED, so {p['name']} stays out of the mod:\n  " + "\n  ".join(problems))
                continue
            Image.fromarray(out, "RGBA").save(OUT / f"prop-{p['name']}.png")
            Image.fromarray(out, "RGBA").save(PREVIEW_SRC / f"{p['name']}.png")
            print(f"{p['name']}: {out.shape[1]} x {out.shape[0]} ({p['where']}, {p['chance']}%, real pixels)")
            continue
        rgb = np.asarray(Image.open(SRC / f"{sheet}.png").convert("RGB"))
        bg = background_mask(rgb)
        bg |= fringe_mask(rgb, bg)
        found = figures(rgb, bg)
        if len(found) != len(mine):
            problems = [f"{len(found)} figures, the registry names {len(mine)}"]
        else:
            size = pixel_size([energies(rgb[box], own) for box, own in found])
            print(f"{sheet}: a ChatGPT pixel is {size:.2f} source pixels")
            problems = check(spec, rgb.shape, size, mine, found) if "grid" in spec else []
        cuts = []
        if not problems:
            for p, (box, own) in zip(mine, found):
                out = cut(rgb[box], own, size, p["where"] != "far")
                cuts.append(out)
                if out.shape[0] > MAX_H[p["where"]]:
                    if "grid" in spec:
                        problems.append(f"{p['name']} is {out.shape[0]} pixels tall, at most {MAX_H[p['where']]}")
                    else:
                        too_big.append(p["name"])
        if problems:
            # rejected whole: none of its props goes into the mod until ChatGPT draws it again
            rejected[sheet] = problems
            for p in mine:
                (OUT / f"prop-{p['name']}.png").unlink(missing_ok=True)
            print(f"{sheet}: REJECTED, so {', '.join(p['name'] for p in mine)} stay out of the mod "
                  "until ChatGPT draws it again:")
            for x in problems:
                print("  " + x)
            continue
        for p, (box, own), out in zip(mine, found, cuts):
            Image.fromarray(out, "RGBA").save(OUT / f"prop-{p['name']}.png")
            src = np.dstack([rgb[box], np.where(own, 255, 0).astype(np.uint8)])
            Image.fromarray(src, "RGBA").save(PREVIEW_SRC / f"{p['name']}.png")
            big = p["name"] in too_big
            print(f"{p['name']}: {out.shape[1]} x {out.shape[0]} ({p['where']}, {p['chance']}%)"
                  + (f" TOO TALL, at most {MAX_H[p['where']]}: draw it again, smaller" if big else ""))
    page(props, rejected)
    if too_big:
        print("too tall:", ", ".join(too_big))


def template(sheet: str) -> None:
    """The measures of a sheet as an image to attach to its ChatGPT message: on magenta, a box for
    each object, left to right as the message lists them, at its size on the sheet's grid, its
    bottom on the same line 4 pixels above the bottom. Each box is a checkerboard of the grid's
    pixels, so it shows both how big the object is and how big one pixel is."""
    mine = [p for p in registry() if p["sheet"] == sheet]
    across, down = sheets()[sheet]["grid"]
    gap = (across - sum(p["size"][0] for p in mine)) / (len(mine) + 1)
    assert gap >= 4, f"{sheet}: the objects do not fit {across} pixels across with room between them"
    cells = np.zeros((down, across), dtype=np.uint8)  # 0 magenta, 1 and 2 the checkerboard
    x, bottom = gap, down - 4
    for p in mine:
        w, h = p["size"]
        x0, y0 = round(x), bottom - h
        yy, xx = np.mgrid[y0:bottom, x0 : x0 + w]
        cells[y0:bottom, x0 : x0 + w] = 1 + (yy + xx) % 2
        x += w + gap
    colours = np.array([[255, 0, 255], [235, 235, 235], [190, 190, 190]], dtype=np.uint8)
    img = Image.fromarray(colours[cells]).resize((TEMPLATE_W, TEMPLATE_W * down // across), Image.NEAREST)
    path = ROOT / "assets" / "ref" / f"template-{sheet}.png"
    img.save(path)
    print(f"{path.relative_to(ROOT)}: {across} x {down} grid pixels, "
          + ", ".join(f"{p['name']} {p['size'][0]} x {p['size'][1]}" for p in mine))


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


def page(props: list[dict], rejected: dict[str, list[str]]) -> None:
    rows = []
    for sheet, problems in rejected.items():
        rows.append(
            f'  <h3>{sheet} <small>REJECTED: its props stay out of the mod until ChatGPT draws it again</small></h3>\n'
            f'  <ul>{"".join(f"<li>{x}</li>" for x in problems)}</ul>\n'
            f'  <img class="src" src="../assets/src/{sheet}.png" width="600">'
        )
    for p in props:
        if not (OUT / f"prop-{p['name']}.png").exists():
            continue
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
    if sys.argv[1:2] == ["--template"]:
        template(sys.argv[2])
    else:
        main()
