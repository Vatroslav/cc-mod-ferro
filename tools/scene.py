"""Builds two SVG scenes per background from assets/px and writes them to hooks/scene.ts
(and to preview/ for viewing):

- RUN: Ferro runs across the meadow (three layers scroll at different speeds), stops now and
  then to poop, and the pile stays on the meadow and scrolls away to the left.
- SLEEP: Ferro lies down and falls asleep, the clouds keep drifting, z's rise above her head.

Every drawing is a PNG (data URI) in an <image> inside <defs>, and the scene places it with
<use>. The Desktop band renders <image> only when the mod draws the Svg as an image (without
isInteractive). Everything is animated with SMIL, which the image mode animates too.
Run (from the repo root, after tools/build.py): python tools/scene.py
"""

import base64
import io
import json
import math
from pathlib import Path

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
BACKGROUNDS = {"meadow": "the meadow", "autumn": "the autumn meadow", "winter": "the winter meadow"}
# The backgrounds the mod picks from; the others are built and previewed, but not in scene.ts.
# Winter is switched off for now (Vatra, 4.10.2026).
IN_MOD = ["meadow", "autumn"]

Z_GLYPH = ["####", "..#.", ".#..", "####"]


def fmt(t: float) -> str:
    return f"{t:.4f}".rstrip("0").rstrip(".")


def size(name: str) -> tuple[int, int]:
    with Image.open(PX / name) as im:
        return im.size


def sprite_def(id_: str, name: str) -> str:
    """PNG as an <image> with an indexed-colour PNG in a data URI: about a sixth of the size of
    vector strokes (one path per colour), which the scenes used until 6.10.2026."""
    im = Image.open(PX / name).convert("RGBA")
    colors = sorted(set(im.getdata()))
    index = {c: i for i, c in enumerate(colors)}
    indexed = Image.new("P", im.size)
    indexed.putdata([index[c] for c in im.getdata()])
    indexed.putpalette([v for c in colors for v in c[:3]])
    buf = io.BytesIO()
    indexed.save(buf, "PNG", optimize=True, transparency=bytes(c[3] for c in colors))
    data = base64.b64encode(buf.getvalue()).decode()
    return f'<image id="{id_}" width="{im.width}" height="{im.height}" href="data:image/png;base64,{data}"/>'


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
        f'shape-rendering="crispEdges" image-rendering="pixelated" style="image-rendering:pixelated">'
        f'<rect width="{VW}" height="{height}" fill="{meadow["sky"]}"/>'
        f'<defs>{"".join(defs)}</defs>{body}</svg>'
    )


def run_scene(meadow: dict, dog_x: int, dog_y: int, ball: bool = False) -> str:
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
    ball_el = ""
    if ball:
        ball_el = ball_layer(ground_pts, poop_start, poop_end, period, dog_x, dog_y)
    body = (
        layers
        + pile_el
        + ball_el
        + f'<g transform="translate({dog_x} {dog_y})">{run_group}{poop_imgs}</g>'
    )
    return svg(body, defs, meadow, height)


# The orange ball she chases: it bounces ahead of her while she runs, rolls on and comes to
# rest on the grass when she stops to poop, and pops up again when she reaches it.
BALL_BOUNCE_S = 0.55  # one bounce, roughly
BALL_BOUNCE_H = 14  # px
BALL_GAP = (8, 52)  # px between her nose and the ball while she chases it, nearest and farthest
BALL_GAP_S = 3.7  # seconds of one swing from near to far and back
BALL_ROLL_MIN = 40  # px the ball rolls on at least when she stops
BALL_ROLL_S = 1.2
NOSE_X = 58  # x of her nose on the run canvas


def ball_layer(ground_pts: list, stop: float, go: float, period: float, dog_x: int, dog_y: int) -> str:
    """The ball from second 0 to `stop` (when she stops to poop) and again from the moment she
    reaches it after `go` (when she runs again) to the end of the loop."""
    d = size("ball.png")[0]
    top = dog_y + size("run-0.png")[1] - d  # the ball's top when it lies on the grass
    nose = dog_x + NOSE_X
    mid, amp = (BALL_GAP[0] + BALL_GAP[1]) / 2, (BALL_GAP[1] - BALL_GAP[0]) / 2

    def swing(t: float) -> float:
        return mid + amp * math.sin(2 * math.pi * t / BALL_GAP_S)

    # while she poops, the ball lies on the meadow: it rolls on far enough that she reaches it
    # just as she runs again (or BALL_ROLL_MIN, if she would reach it sooner)
    x_stop = nose + swing(stop)
    moved = at(ground_pts, go) - at(ground_pts, stop)  # negative: the ground moves left
    roll = max(BALL_ROLL_MIN, nose + 2 - x_stop - moved)
    reach = go
    while reach < period and x_stop + roll + at(ground_pts, reach) - at(ground_pts, stop) > nose + 2:
        reach += 0.01

    def gap(t: float) -> float:
        if t <= stop:
            return swing(t)
        g = 2 + (swing(t) - 2) * min(1.0, (t - reach) / 1.0)  # from her nose, out to the swing
        if t > period - 1:  # back to where the loop starts
            g += (swing(0) - g) * (t - (period - 1))
        return g

    xs = [(t, nose + gap(t)) for t in [i * 0.5 for i in range(int(stop / 0.5) + 1)] + [stop]]
    t = reach
    while t < period:
        xs.append((t, nose + gap(t)))
        t += 0.5
    xs.append((period, nose + swing(0)))

    # bounces: a whole number in each window, so the ball is on the grass when it stops and
    # when it pops up again
    keys = [(0.0, 0)]
    for a, b in ((0.0, stop), (reach, period)):
        if keys[-1][0] < a:
            keys.append((a, 0))
        n = max(1, round((b - a) / BALL_BOUNCE_S))
        for i in range(n):
            t0 = a + (b - a) * i / n
            keys += [(t0 + (b - a) / n / 2, -BALL_BOUNCE_H), (t0 + (b - a) / n, 0)]
    up, down, flat = "0 0 .58 1", ".42 0 1 1", "0 0 1 1"
    splines = [up if y1 < y0 else down if y1 > y0 else flat for (_, y0), (_, y1) in zip(keys, keys[1:])]
    bounce = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(f"0 {y}" for _, y in keys)}" '
        f'keyTimes="{";".join(fmt(t / period) for t, _ in keys)}" calcMode="spline" '
        f'keySplines="{";".join(splines)}" dur="{fmt(period)}s" repeatCount="indefinite"/>'
    )
    chased = (
        "<g>" + discrete("display", ["inline", "none", "inline"], [0, stop, reach], period)
        + f"<g>{linear(xs, period)}<g>{bounce}"
        + f'<use href="#ball" x="0" y="{top}"/></g></g></g>'
    )

    # lying on the meadow: placed where the ground is when she stops, rolls on, then scrolls with
    # the ground until she reaches it
    roll_pts = [(0, 0), (stop, 0), (stop + BALL_ROLL_S / 2, roll * 0.75), (stop + BALL_ROLL_S, roll),
                (period, roll)]
    resting = (
        "<g>" + discrete("display", ["none", "inline", "none"], [0, stop, reach], period)
        + f"<g>{linear(ground_pts, period)}<g>{linear(roll_pts, period)}"
        + f'<use href="#ball" x="{round(x_stop - at(ground_pts, stop))}" y="{top}"/></g></g></g>'
    )
    # its own <defs>, so the scene with the ball is the plain scene with this one piece inserted
    return f'<defs>{sprite_def("ball", "ball.png")}</defs>' + chased + resting


# Pooping while walking, the way the real Ferro does it (run_scene, pooping in one spot, is the
# rare variant): run, crouch with frames 1-2 of poop.png, walk hunched while the ground moves
# slowly and a dropping falls behind her now and then, stand up with frame 5 of poop.png, run.
CROUCH = [(1, 0.3), (2, 0.3)]  # (poop frame, seconds)
HUNCH_WALK_S = 7.0
HUNCH_WALK_SPEED = 22  # px/s of the ground while she walks hunched
HUNCH_FRAME_S = 0.2
DROPS = [(0.8, 0), (2.5, 1), (4.2, 1), (5.9, 2)]  # (seconds into the walk, dropping sprite)
REAR_X = 12  # x of her rear on the poop-walk canvas, where the droppings fall


def at(points: list[tuple[float, float]], t: float) -> float:
    """x of a piecewise linear path at second t."""
    for (t0, x0), (t1, x1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            return x1 if t1 == t0 else x0 + (x1 - x0) * (t - t0) / (t1 - t0)
    return points[-1][1]


def cycle(prefix: str, frames: list, frame_s: float) -> str:
    """Frames shown one after another in their own fast loop."""
    out = ""
    for slot, frame in enumerate(frames):
        vals = ";".join("visible" if j == slot else "hidden" for j in range(len(frames)))
        out += (
            f'<use href="#{prefix}{frame}" visibility="hidden"><animate attributeName="visibility" '
            f'values="{vals}" dur="{fmt(frame_s * len(frames))}s" calcMode="discrete" '
            f'repeatCount="indefinite"/></use>'
        )
    return out


def shown(inner: str, start: float, end: float, period: float) -> str:
    """Shown only from second `start` to `end` of the loop."""
    return (
        "<g>" + discrete("display", ["none", "inline", "none"], [0, start, end], period)
        + inner + "</g>"
    )


def run_walk_scene(meadow: dict, dog_x: int, dog_y: int, run_before: float = RUN_BEFORE,
                   ball: bool = False) -> str:
    mw = meadow["width"]
    crouch_start = run_before
    walk_start = crouch_start + sum(s for _, s in CROUCH)
    walk_end = walk_start + HUNCH_WALK_S
    poop_end = walk_end + POOP[-1][1]
    ground_total = GROUND_TILES * mw
    d1 = run_before * RUN_SPEED
    d2 = d1 + HUNCH_WALK_S * HUNCH_WALK_SPEED
    d3 = d2 + WALK_AWAY_PX
    period = poop_end + (ground_total - d3) / RUN_SPEED

    # path of the ground: runs, stops while she crouches, walks slowly, steps away, runs
    ground_pts = [(0, 0), (crouch_start, -d1), (walk_start, -d1), (walk_end, -d2),
                  (poop_end, -d3), (period, -ground_total)]
    back_pts = [(t, x * BACK_RATIO) for t, x in ground_pts]
    y_back = meadow["sky_h"]
    y_ground = meadow["sky_h"] + meadow["back_h"]

    walk_frames = sorted(PX.glob("poop-walk-[0-9].png"))
    drop_sprites = sorted({k for _, k in DROPS})
    defs = meadow_defs(meadow)
    defs += [sprite_def(f"r{i}", f"run-{i}.png") for i in sorted(set(RUN_ORDER))]
    defs += [sprite_def(f"p{i}", f"poop-{i}.png") for i in [i for i, _ in CROUCH] + [len(POOP) - 1]]
    defs += [sprite_def(f"w{i}", f.name) for i, f in enumerate(walk_frames)]
    defs += [sprite_def(f"d{k}", f"poop-walk-drop-{k}.png") for k in drop_sprites]

    layers = (
        clouds_layer(meadow)
        + f"<g>{linear(back_pts, period)}{tiles('back', y_back, mw, ground_total * BACK_RATIO)}</g>"
        + f"<g>{linear(ground_pts, period)}{tiles('ground', y_ground, mw, ground_total)}</g>"
    )

    run_group = (
        "<g>"
        + discrete("display", ["inline", "none", "inline"], [0, crouch_start, poop_end], period)
        + cycle("r", RUN_ORDER, RUN_FRAME_S)
        + "</g>"
    )
    dog = run_group
    t = crouch_start
    for i, s in CROUCH:
        dog += shown(f'<use href="#p{i}"/>', t, t + s, period)
        t += s
    dog += shown(cycle("w", list(range(len(walk_frames))), HUNCH_FRAME_S), walk_start, walk_end, period)
    dog += shown(f'<use href="#p{len(POOP) - 1}"/>', walk_end, poop_end, period)

    # droppings lie on the meadow: each is placed where the ground is when it falls, then
    # scrolls with the ground
    canvas_h = size("poop-walk-0.png")[1]
    drops = ""
    for s, k in DROPS:
        t_drop = walk_start + s
        w, h = size(f"poop-walk-drop-{k}.png")
        x = round(dog_x + REAR_X - w // 2 - at(ground_pts, t_drop))
        drops += (
            f'<use href="#d{k}" x="{x}" y="{dog_y + canvas_h - h}" display="none">'
            + discrete("display", ["none", "inline"], [0, t_drop], period)
            + "</use>"
        )
    drops_el = f"<g>{linear(ground_pts, period)}{drops}</g>"

    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    ball_el = ""
    if ball:
        ball_el = ball_layer(ground_pts, crouch_start, poop_end, period, dog_x, dog_y)
    body = layers + drops_el + ball_el + f'<g transform="translate({dog_x} {dog_y})">{dog}</g>'
    return svg(body, defs, meadow, height)


# Sitting and looking at the viewer, a turn of its own instead of pooping: run, brake, sit, turn
# the head to the viewer, blink and tilt the head, turn back, stand up, run. The frames are
# sit.png (0 brake, 1 sitting down, 2 sitting in profile, 3 head three-quarters, 4 facing the
# viewer, 5 head tilt) and sit-blink.png, derived from 4.
SIT = [(0, 0.3), (1, 0.3), (2, 0.5), (3, 0.3), (4, 1.6), ("blink", 0.15), (4, 1.2), (5, 1.4),
       (4, 1.0), ("blink", 0.15), (4, 0.6), (3, 0.3), (2, 0.4), (1, 0.3)]  # (frame, seconds)
BRAKE_PX = 10  # how far the ground still moves while she brakes


def run_sit_scene(meadow: dict, dog_x: int, dog_y: int, ball: bool = False,
                  run_before: float = RUN_BEFORE) -> str:
    mw = meadow["width"]
    sit_start = run_before
    brake_end = sit_start + SIT[0][1]
    sit_end = sit_start + sum(s for _, s in SIT)
    ground_total = GROUND_TILES * mw
    d1 = run_before * RUN_SPEED
    d2 = d1 + BRAKE_PX
    period = sit_end + (ground_total - d2) / RUN_SPEED

    # path of the ground: runs, slows down while she brakes, stands while she sits, runs
    ground_pts = [(0, 0), (sit_start, -d1), (brake_end, -d2), (sit_end, -d2), (period, -ground_total)]
    back_pts = [(t, x * BACK_RATIO) for t, x in ground_pts]
    y_back = meadow["sky_h"]
    y_ground = meadow["sky_h"] + meadow["back_h"]

    defs = meadow_defs(meadow)
    defs += [sprite_def(f"r{i}", f"run-{i}.png") for i in sorted(set(RUN_ORDER))]
    defs += [sprite_def(f"s{f}", f"sit-{f}.png") for f in dict.fromkeys(f for f, _ in SIT)]

    layers = (
        clouds_layer(meadow)
        + f"<g>{linear(back_pts, period)}{tiles('back', y_back, mw, ground_total * BACK_RATIO)}</g>"
        + f"<g>{linear(ground_pts, period)}{tiles('ground', y_ground, mw, ground_total)}</g>"
    )
    dog = (
        "<g>"
        + discrete("display", ["inline", "none", "inline"], [0, sit_start, sit_end], period)
        + cycle("r", RUN_ORDER, RUN_FRAME_S)
        + "</g>"
    )
    t = sit_start
    for f, s in SIT:
        dog += shown(f'<use href="#s{f}"/>', t, t + s, period)
        t += s

    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    ball_el = ball_layer(ground_pts, sit_start, sit_end, period, dog_x, dog_y) if ball else ""
    body = layers + ball_el + f'<g transform="translate({dog_x} {dog_y})">{dog}</g>'
    return svg(body, defs, meadow, height)


# Sniffing, a turn of its own: run, slow down with the head lowering (sniff-0), then a few times
# in a row: walk with the nose to the grass (sniff-1 to 4) and stop to sniff one spot, the head
# bobbing between the nose on the grass (sniff-5) and one pixel higher (sniff-up); lift the head
# (sniff-0 again) and run. How many stops (1 to SNIFF_MAX_STOPS) the mod picks per turn, so each
# count is a scene of its own. Each stop has its own walk and number of bobs, so they differ.
SNIFF_MAX_STOPS = 5
SNIFF_TURN = (0.35, 12)  # (seconds, px of ground) of sniff-0, when she slows down and when she lifts her head
SNIFF_WALK_SPEED = 20  # px/s of the ground while she walks with her nose down
SNIFF_FRAME_S = 0.22
SNIFF_WALKS = [1.8, 1.2, 2.2, 1.0, 1.5]  # seconds of walking before each stop
SNIFF_BOBS = [3, 2, 4, 2, 3]  # head bobs at each stop
SNIFF_DOWN_S, SNIFF_UP_S, SNIFF_LAST_S = 0.32, 0.14, 0.4  # nose on the grass, head up, last sniff


def windows(times: list[tuple[float, float]], period: float) -> str:
    """display="inline" only within the given (start, end) windows of the loop."""
    vals, keys = ["none"], [0.0]
    for a, b in times:
        vals += ["inline", "none"]
        keys += [a, b]
    return discrete("display", vals, keys, period)


def run_sniff_scene(meadow: dict, dog_x: int, dog_y: int, stops: int, ball: bool = False,
                    run_before: float = RUN_BEFORE) -> str:
    mw = meadow["width"]
    turn_s, turn_px = SNIFF_TURN
    ground_total = GROUND_TILES * mw

    # the timeline: (what, start, end) and the path of the ground through it
    t, d = run_before, run_before * RUN_SPEED
    ground_pts = [(0, 0), (t, -d)]
    turns, walks, downs, ups = [(t, t + turn_s)], [], [], []
    t, d = t + turn_s, d + turn_px
    ground_pts.append((t, -d))
    for k in range(stops):
        walks.append((t, t + SNIFF_WALKS[k]))
        t, d = t + SNIFF_WALKS[k], d + SNIFF_WALKS[k] * SNIFF_WALK_SPEED
        ground_pts.append((t, -d))
        for _ in range(SNIFF_BOBS[k]):
            downs.append((t, t + SNIFF_DOWN_S))
            ups.append((t + SNIFF_DOWN_S, t + SNIFF_DOWN_S + SNIFF_UP_S))
            t += SNIFF_DOWN_S + SNIFF_UP_S
        downs.append((t, t + SNIFF_LAST_S))
        t += SNIFF_LAST_S
        ground_pts.append((t, -d))
    turns.append((t, t + turn_s))
    t, d = t + turn_s, d + turn_px
    ground_pts.append((t, -d))
    sniff_start, sniff_end = run_before, t
    period = sniff_end + (ground_total - d) / RUN_SPEED
    ground_pts.append((period, -ground_total))
    back_pts = [(t, x * BACK_RATIO) for t, x in ground_pts]
    y_back = meadow["sky_h"]
    y_ground = meadow["sky_h"] + meadow["back_h"]

    defs = meadow_defs(meadow)
    defs += [sprite_def(f"r{i}", f"run-{i}.png") for i in sorted(set(RUN_ORDER))]
    defs += [sprite_def(f"n{i}", f"sniff-{i}.png") for i in range(6)]
    defs += [sprite_def("nu", "sniff-up.png")]

    layers = (
        clouds_layer(meadow)
        + f"<g>{linear(back_pts, period)}{tiles('back', y_back, mw, ground_total * BACK_RATIO)}</g>"
        + f"<g>{linear(ground_pts, period)}{tiles('ground', y_ground, mw, ground_total)}</g>"
    )
    dog = (
        "<g>"
        + discrete("display", ["inline", "none", "inline"], [0, sniff_start, sniff_end], period)
        + cycle("r", RUN_ORDER, RUN_FRAME_S)
        + "</g>"
    )
    dog += f'<g display="none">{windows(turns, period)}<use href="#n0"/></g>'
    dog += f'<g display="none">{windows(walks, period)}{cycle("n", [1, 2, 3, 4], SNIFF_FRAME_S)}</g>'
    dog += f'<g display="none">{windows(downs, period)}<use href="#n5"/></g>'
    dog += f'<g display="none">{windows(ups, period)}<use href="#nu"/></g>'

    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    ball_el = ball_layer(ground_pts, sniff_start, sniff_end, period, dog_x, dog_y) if ball else ""
    body = layers + ball_el + f'<g transform="translate({dog_x} {dog_y})">{dog}</g>'
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
        # running: she sits and looks at the viewer, poops while walking, or (rarely) poops in one
        # spot; each comes plain and with the ball, which the mod inserts at `ballAt` when it wants it
        prefix = "" if k == 0 else f"{name}-"
        runs = {}
        for key, make, file in (("run", run_walk_scene, "run"), ("runStill", run_scene, "run-still"),
                                ("runSit", run_sit_scene, "sit")):
            plain, with_ball = make(meadow, dog_x, dog_y), make(meadow, dog_x, dog_y, ball=True)
            at = next(i for i, (a, b) in enumerate(zip(plain, with_ball)) if a != b)
            piece = with_ball[at : at + len(with_ball) - len(plain)]
            assert plain[:at] + piece + plain[at:] == with_ball
            runs[key] = {"svg": plain, "ball": piece, "ballAt": at}
            (preview / f"{prefix}{file}.svg").write_text(plain, encoding="utf-8")
            (preview / f"{prefix}ball-{file}.svg").write_text(with_ball, encoding="utf-8")
            print(name, key, len(plain), "with the ball", len(with_ball), "chars; limit 131072")
        # sniffing (not in the mod yet): every count of stops is measured; the preview has each
        # count on the summer meadow, the ball with three stops, and three stops on the others
        for n in range(1, SNIFF_MAX_STOPS + 1):
            plain = run_sniff_scene(meadow, dog_x, dog_y, n)
            with_ball = run_sniff_scene(meadow, dog_x, dog_y, n, ball=True)
            if k == 0 or n == 3:
                (preview / f"{prefix}sniff-{n}.svg").write_text(plain, encoding="utf-8")
            if k == 0 and n == 3:
                (preview / f"{prefix}ball-sniff-{n}.svg").write_text(with_ball, encoding="utf-8")
            print(name, f"sniff {n} stops", len(plain), "with the ball", len(with_ball), "chars")
        sleep = sleep_scene(meadow, dog_x, dog_y)
        (preview / f"{prefix}sleep.svg").write_text(sleep, encoding="utf-8")
        print(name, "sleep", len(sleep), "chars", "" if name in IN_MOD else "(preview only, not in the mod)")
        if name in IN_MOD:
            scenes.append({"place": place, "height": height * SCALE, **runs, "sleep": sleep})

    ts = (
        "// Generated by tools/scene.py - do not edit by hand.\n"
        f"export const SCENE_MAX_WIDTH = {VW * SCALE}\n"
        f"export const SCENES = {json.dumps(scenes)}\n"
    )
    (ROOT / "plugin" / "hooks" / "scene.ts").write_text(ts, encoding="utf-8")


if __name__ == "__main__":
    main()
