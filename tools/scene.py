"""Builds two SVG scenes per background from assets/px and writes them to hooks/scene.ts
(and to preview/ for viewing):

- RUN: Ferro runs across the meadow (three layers scroll at different speeds), stops now and
  then to poop, and the pile stays on the meadow and scrolls away to the left.
- SLEEP: Ferro lies down and falls asleep, the clouds keep drifting, z's rise above her head.

The Desktop band does not render <image> with a PNG (data URI), but it does render <use>. So
every drawing is converted to vector strokes (one <path> per colour) inside <defs>, and the
scene places it with <use>. Everything is animated with SMIL.
Run (from the repo root, after tools/build.py): python tools/scene.py
"""

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PX = ROOT / "assets" / "px"

SCALE = 2  # CSS pixels per pixel
VW = 640  # viewBox width; a band narrower than VW*SCALE crops the edges, it does not shrink the pixels
RUN_SPEED = 80  # px/s of the ground while she runs
CLOUD_SPEED = 4  # px/s, the clouds drift even while she sleeps
RUN_FRAME_S = 0.13  # any faster and the legs look like they twitch
# ChatGPT laid the frames out without the order of the gallop phases. The real order: stretched
# in the air (4), landing on the front legs (3), hind legs swinging forward (2), gathered (5),
# push-off with the hind legs (0). Frame 1 is a second "stretched" frame, left out.
RUN_ORDER = [4, 3, 2, 5, 0]

# Schedule of one RUN loop: run, poop, run. The second run lasts exactly long enough for the
# ground to travel 20 meadow widths in one loop and the hills (at 0.35 of the speed) exactly 7,
# so the loop continues without a jump.
RUN_BEFORE = 16.0
POOP = [(0, 0.5), (1, 0.35), (2, 0.35), (3, 1.3), (4, 1.6), (5, 0.45)]  # (frame, seconds)
WALK_AWAY_PX = 13  # how far she moves away from the pile in the last frame
GROUND_TILES = 20
BACK_RATIO = 0.35

# Sleep: intro (frame, seconds), then breathing on the last frame. build.py derives the
# breathing frame from sleep-5 (back raised by one pixel, head in place); ChatGPT would redraw
# every frame from scratch, so Ferro would tremble instead of breathe.
SLEEP_INTRO = [(0, 0.6), (1, 0.6), (2, 1.6), (3, 1.0), (4, 1.0)]
BREATH = [("sleep-5", 1.8), ("sleep-breath-1", 1.2)]

# Backgrounds from build.py (name: where Ferro is, for the alt text). The mod picks one at
# random on every turn. The first one is previewed in preview/run.svg and sleep.svg, the
# others in preview/<name>-run.svg and <name>-sleep.svg.
BACKGROUNDS = {"meadow": "the meadow", "autumn": "the autumn meadow"}

Z_GLYPH = ["####", "..#.", ".#..", "####"]


def fmt(t: float) -> str:
    return f"{t:.4f}".rstrip("0").rstrip(".")


def size(name: str) -> tuple[int, int]:
    with Image.open(PX / name) as im:
        return im.size


def sprite_def(id_: str, name: str) -> str:
    """PNG as a <g> with one path per colour: every horizontal run of pixels is a stroke of width 1."""
    a = np.asarray(Image.open(PX / name).convert("RGBA"))
    by_color: dict[str, list[str]] = {}
    for y in range(a.shape[0]):
        row = a[y]
        x = 0
        last_end: dict[str, int] = {}
        while x < a.shape[1]:
            if row[x, 3] < 128:
                x += 1
                continue
            color = "#%02x%02x%02x" % tuple(int(c) for c in row[x, :3])
            end = x + 1
            while end < a.shape[1] and row[end, 3] >= 128 and (row[end, :3] == row[x, :3]).all():
                end += 1
            parts = by_color.setdefault(color, [])
            if color in last_end:
                parts.append(f"m{x - last_end[color]} 0h{end - x}")
            else:
                parts.append(f"M{x} {y}.5h{end - x}")
            last_end[color] = end
            x = end
    paths = "".join(f'<path stroke="{c}" d="{"".join(p)}"/>' for c, p in by_color.items())
    return f'<g id="{id_}" fill="none" stroke-width="1">{paths}</g>'


def linear(points: list[tuple[float, float]], period: float, y: int = 0, repeat: bool = True) -> str:
    """Movement along x through key points (second, x), linear between them."""
    vals = ";".join(f"{fmt(x)} {y}" for _, x in points)
    keys = ";".join(fmt(t / period) for t, _ in points)
    rep = 'repeatCount="indefinite"' if repeat else 'fill="freeze"'
    return (
        f'<animateTransform attributeName="transform" type="translate" values="{vals}" '
        f'keyTimes="{keys}" dur="{fmt(period)}s" {rep}/>'
    )


def discrete(attr: str, values: list[str], times: list[float], period: float) -> str:
    """Discrete animation over the whole loop; times are the start of each value in seconds."""
    keys = ";".join(fmt(t / period) for t in times)
    return (
        f'<animate attributeName="{attr}" values="{";".join(values)}" keyTimes="{keys}" '
        f'dur="{fmt(period)}s" calcMode="discrete" repeatCount="indefinite"/>'
    )


def tiles(tile: str, y: int, width: int, travel: float) -> str:
    """Enough copies of a layer to cover the viewBox and the whole distance it travels in a loop."""
    copies = math.ceil((VW + travel) / width) + 1
    return "".join(f'<use href="#{tile}" x="{k * width}" y="{y}"/>' for k in range(copies))


def meadow_defs(meadow: dict) -> list[str]:
    name = meadow["name"]
    return [
        sprite_def("clouds", f"{name}-clouds.png"),
        sprite_def("back", f"{name}-back.png"),
        sprite_def("ground", f"{name}-ground.png"),
    ]


def clouds_layer(meadow: dict) -> str:
    mw = meadow["width"]
    period = mw / CLOUD_SPEED
    return f"<g>{linear([(0, 0), (period, -mw)], period)}{tiles('clouds', 0, mw, mw)}</g>"


def svg(body: str, defs: list[str], meadow: dict, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW * SCALE}" height="{height * SCALE}" '
        f'viewBox="0 0 {VW} {height}" preserveAspectRatio="xMidYMid slice" '
        f'shape-rendering="crispEdges">'
        f'<rect width="{VW}" height="{height}" fill="{meadow["sky"]}"/>'
        f'<defs>{"".join(defs)}</defs>{body}</svg>'
    )


def run_scene(meadow: dict, dog_x: int, dog_y: int) -> str:
    mw = meadow["width"]
    poop_start = RUN_BEFORE
    poop_len = sum(s for _, s in POOP)
    walk_from = poop_start + poop_len - POOP[-1][1]
    poop_end = poop_start + poop_len
    pile_at = poop_start + sum(s for _, s in POOP[:4])
    ground_total = GROUND_TILES * mw
    run_after = (ground_total - WALK_AWAY_PX) / RUN_SPEED - RUN_BEFORE
    period = poop_end + run_after
    d1 = RUN_BEFORE * RUN_SPEED

    # path of the ground through the loop: runs, stands, steps away, runs to the end
    ground_pts = [(0, 0), (poop_start, -d1), (walk_from, -d1), (poop_end, -d1 - WALK_AWAY_PX),
                  (period, -ground_total)]
    back_pts = [(t, x * BACK_RATIO) for t, x in ground_pts]
    y_back = meadow["sky_h"]
    y_ground = meadow["sky_h"] + meadow["back_h"]

    defs = meadow_defs(meadow) + [sprite_def("pile", "poop-pile.png")]
    for i in sorted(set(RUN_ORDER)):
        defs.append(sprite_def(f"r{i}", f"run-{i}.png"))
    for i, _ in enumerate(POOP):
        defs.append(sprite_def(f"p{i}", f"poop-{i}.png"))

    layers = (
        clouds_layer(meadow)
        + f"<g>{linear(back_pts, period)}{tiles('back', y_back, mw, ground_total * BACK_RATIO)}</g>"
        + f"<g>{linear(ground_pts, period)}{tiles('ground', y_ground, mw, ground_total)}</g>"
    )

    # running: its own fast cycle, the whole group hidden while she poops
    cycle = RUN_FRAME_S * len(RUN_ORDER)
    run_imgs = ""
    for slot, frame in enumerate(RUN_ORDER):
        vals = ";".join("visible" if j == slot else "hidden" for j in range(len(RUN_ORDER)))
        run_imgs += (
            f'<use href="#r{frame}" visibility="hidden"><animate attributeName="visibility" '
            f'values="{vals}" dur="{fmt(cycle)}s" calcMode="discrete" repeatCount="indefinite"/></use>'
        )
    run_group = (
        "<g>"
        + discrete("display", ["inline", "none", "inline"], [0, poop_start, poop_end], period)
        + run_imgs
        + "</g>"
    )

    poop_imgs = ""
    t = poop_start
    for i, (_, s) in enumerate(POOP):
        poop_imgs += (
            f'<use href="#p{i}" display="none">'
            + discrete("display", ["none", "inline", "none"], [0, t, t + s], period)
            + "</use>"
        )
        t += s

    # the pile stays in place on the meadow, so it scrolls with the ground
    pile = json.loads((PX / "poop-pile.json").read_text())
    pile_pts = [(0, 0), (walk_from, 0), (poop_end, -WALK_AWAY_PX),
                (period, -WALK_AWAY_PX - run_after * RUN_SPEED)]
    pile_el = (
        f"<g>{linear(pile_pts, period)}"
        f'<use href="#pile" x="{dog_x + pile["x"]}" y="{dog_y + pile["y"]}" display="none">'
        + discrete("display", ["none", "inline"], [0, pile_at], period)
        + "</use></g>"
    )

    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    body = (
        layers
        + pile_el
        + f'<g transform="translate({dog_x} {dog_y})">{run_group}{poop_imgs}</g>'
    )
    return svg(body, defs, meadow, height)


def sleep_scene(meadow: dict, dog_x: int, dog_y: int) -> str:
    mw = meadow["width"]
    breath_frames = list(dict.fromkeys(name for name, _ in BREATH))
    defs = meadow_defs(meadow) + [sprite_def(f"s{i}", f"sleep-{i}.png") for i, _ in SLEEP_INTRO]
    defs += [sprite_def(f"b{k}", f"{name}.png") for k, name in enumerate(breath_frames)]

    dog = ""
    t = 0.0
    for i, s in SLEEP_INTRO:
        dog += (
            f'<use href="#s{i}" visibility="hidden"><set attributeName="visibility" to="visible" '
            f'begin="{fmt(t)}s" dur="{fmt(s)}s"/></use>'
        )
        t += s
    intro = t
    # breathing: a loop of the frames in BREATH, the same frame may come more than once
    period = sum(s for _, s in BREATH)
    starts = [sum(s for _, s in BREATH[:j]) for j in range(len(BREATH))]
    keys = ";".join(fmt(st / period) for st in starts)
    for k, name in enumerate(breath_frames):
        vals = ";".join("visible" if n == name else "hidden" for n, _ in BREATH)
        dog += (
            f'<use href="#b{k}" visibility="hidden"><animate attributeName="visibility" '
            f'values="{vals}" keyTimes="{keys}" dur="{fmt(period)}s" begin="{fmt(intro)}s" '
            f'calcMode="discrete" repeatCount="indefinite"/></use>'
        )

    # z's: appear above the head, rise and fade, one after another
    zpath = "".join(
        f"M{x} {y}h1v1h-1z"
        for y, row in enumerate(Z_GLYPH)
        for x, c in enumerate(row)
        if c == "#"
    )
    zs = ""
    rise = 14
    zdur = 3.0
    for k in range(3):
        xs = [f"{60 + j * 6 // rise} {12 - j}" for j in range(rise + 1)]
        zs += (
            f'<g opacity="0"><path fill="#2b3a55" d="{zpath}"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{";".join(xs)}" dur="{fmt(zdur)}s" begin="{fmt(intro + k)}s" '
            f'calcMode="discrete" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.6;1" '
            f'dur="{fmt(zdur)}s" begin="{fmt(intro + k)}s" repeatCount="indefinite"/></g>'
        )

    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    layers = (
        clouds_layer(meadow)
        + f"<g>{tiles('back', meadow['sky_h'], mw, 0)}</g>"
        + f"<g>{tiles('ground', meadow['sky_h'] + meadow['back_h'], mw, 0)}</g>"
    )
    body = layers + f'<g transform="translate({dog_x} {dog_y})">{dog}{zs}</g>'
    return svg(body, defs, meadow, height)


def main() -> None:
    dog_w, dog_h = size("run-0.png")
    preview = ROOT / "preview"
    preview.mkdir(exist_ok=True)
    scenes = []
    for k, (name, place) in enumerate(BACKGROUNDS.items()):
        meadow = json.loads((PX / f"{name}.json").read_text()) | {"name": name}
        height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
        dog_x = VW // 2 - dog_w // 2 - 20
        dog_y = height - dog_h - 2
        run = run_scene(meadow, dog_x, dog_y)
        sleep = sleep_scene(meadow, dog_x, dog_y)
        scenes.append({"place": place, "height": height * SCALE, "run": run, "sleep": sleep})
        prefix = "" if k == 0 else f"{name}-"
        (preview / f"{prefix}run.svg").write_text(run, encoding="utf-8")
        (preview / f"{prefix}sleep.svg").write_text(sleep, encoding="utf-8")
        print(name, "RUN", len(run), "chars; SLEEP", len(sleep), "chars; limit 131072")

    ts = (
        "// Generated by tools/scene.py - do not edit by hand.\n"
        f"export const SCENE_MAX_WIDTH = {VW * SCALE}\n"
        f"export const SCENES = {json.dumps(scenes)}\n"
    )
    (ROOT / "plugin" / "hooks" / "scene.ts").write_text(ts, encoding="utf-8")


if __name__ == "__main__":
    main()
