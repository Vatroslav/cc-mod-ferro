"""Builds the SVG scenes per background from assets/px and writes them to hooks/scene.ts (and to
preview/ for viewing):

- RUN: Ferro runs across the meadow (three layers scroll at different speeds) and now and then
  stops to do something: sit and look at the viewer, sniff a spot, poop while walking or poop in
  one spot. What she leaves on the meadow stays there and scrolls away to the left. A program is
  one run with its stops; the mod plays one of PROGRAMS per turn.
- SLEEP: Ferro lies down and falls asleep, the clouds keep drifting, z's rise above her head.

Every drawing is a PNG (data URI) in an <image> inside <defs>, and the scene places it with
<use>. The Desktop band renders <image> only when the mod draws the Svg as an image (without
isInteractive). Everything is animated with SMIL, which the image mode animates too.
Run (from the repo root, after tools/build.py): python tools/scene.py
"""

import base64
import html
import io
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PX = ROOT / "assets" / "px"

SCALE = 2  # CSS pixels per pixel
VW = 640  # viewBox width; a band narrower than VW*SCALE crops the edges, it does not shrink the pixels
SVG_LIMIT = 131072  # characters the Desktop band accepts in one Svg
RUN_SPEED = 80  # px/s of the ground while she runs
CLOUD_SPEED = 4  # px/s, the clouds drift even while she sleeps
RUN_FRAME_S = 0.13  # any faster and the legs look like they twitch
# ChatGPT laid the frames out without the order of the gallop phases. The real order: stretched
# in the air (4), landing on the front legs (3), hind legs swinging forward (2), gathered (5),
# push-off with the hind legs (0). Frame 1 is a second "stretched" frame, left out.
RUN_ORDER = [4, 3, 2, 5, 0]

# The loop closes when the ground has travelled a whole number of GROUND_TILES meadow widths:
# then the hills (at BACK_RATIO of the speed) have travelled a whole number of widths too (7 per
# 20), and the loop continues without a jump.
# seconds of running before the stop of a scene with one stop (the README previews), the middle of
# GAP_S; a program draws its first gap from GAP_S like every later one
RUN_BEFORE = 9.0
GROUND_TILES = 20
BACK_RATIO = 0.35
FINAL_RUN_MIN_S = 12.0  # at least this much running after the last stop, before the loop starts again
# Running on from a standstill (after sitting): (second, px) the ground has moved since she set off,
# full speed after the last point. Her run frames slide back from where she stood meanwhile, so she
# never moves backwards against the grass (Vatra chose this of four variants, 7.10.2026).
RUN_START = [(0.0, 0.0), (0.25, 6.0), (0.5, 20.0)]

# Programs: what Ferro does on one turn's run and when. The run lasts at most 160 s (from 20 s into
# the turn to 3 min, when she falls asleep), so the stops start within PROGRAM_S and a turn ends
# before the loop starts again. SMIL has no randomness, so the programs are drawn here with a
# fixed seed and the mod picks one per turn. The first stops of a background's programs come in
# exactly the WEIGHTS shares, because most turns see only the first one or two (measured
# 6.10.2026 on 30 days of turns: half of the turns in which Ferro shows end before 79 s); the
# later stops are drawn with the same weights. Never the same stop twice in a row, and she poops
# at most once per run. Not every program has every stop.
PROGRAM_S = 160
PROGRAMS = 10  # per background
# seconds of running between two stops. 12-22 until 7.10.2026, when Vatra wanted less waiting for
# something to happen (the first stop came after 16 s then)
GAP_S = (6.0, 12.0)
SEED = 6
# drinking came in at 0.1 of the first stops, taken from sitting (7.10.2026), so the other shares
# stayed as Vatra set them
WEIGHTS = {"sit": 0.4, "sniff": 0.2, "drink": 0.1, "walkPoop": 0.2, "stillPoop": 0.1}
POOPS = {"walkPoop", "stillPoop"}
SAYS = {"sit": "sits", "sniff": "sniffs", "walkPoop": "poops while walking", "stillPoop": "poops in one spot",
        "drink": "drinks"}

# Props she runs past (Vatra, 7.10.2026): the library is assets/props.json, the drawings come from
# tools/props.py. They stand still on the meadow, so they need no animation of their own: a prop
# is a <use> in a group that moves with the ground (or with the hills, for a far one), and it
# scrolls in from the right as the ground does. Each run has slots where a prop may stand, one
# after every PROP_GAP_S seconds of running (spaced in ground pixels, so none comes while she
# stops); the mod picks what stands in each slot on every turn, by the props' chances in percent
# (what is left to 100 is an empty slot). That is randomness the programs cannot have: an easter
# egg in one turn of a hundred would need a hundred programs.
PROPS_FILE = ROOT / "assets" / "props.json"
PROP_GAP_S = (7.0, 13.0)  # seconds of running between two ground slots
FAR_GAP_S = (20.0, 40.0)  # between two far slots: a far prop crosses the band in about 20 s
PROP_BEHIND = (70, 76)  # the bottom row of a prop behind her, picked per slot; her paws stand on row 79
PROP_FRONT = 81  # the bottom row of a prop in front of her: the band's last row
PROP_FRONT_SHARE = 0.4  # of the slots that may stand in front of her
# the bottom row of a far prop: below the lowest valley of the hills (row 28 of the band), so the
# hills hide it everywhere and only the top shows
FAR_BASE = 34
DOG_W = 76  # her canvas

# Pooping in one spot: (frame, seconds) of poop.png
POOP = [(0, 0.5), (1, 0.35), (2, 0.35), (3, 1.3), (4, 1.6), (5, 0.45)]
WALK_AWAY_PX = 13  # how far she moves away from the pile in the last frame

# Sleep: intro (frame, seconds), then breathing on the last frame. build.py derives the
# breathing frame from sleep-5 (back raised by one pixel, head in place); ChatGPT would redraw
# every frame from scratch, so Ferro would tremble instead of breathe.
SLEEP_INTRO = [(0, 0.6), (1, 0.6), (2, 1.6), (3, 1.0), (4, 1.0)]
BREATH = [("sleep-5", 1.8), ("sleep-breath-1", 1.2)]
# how long she lies down before she breathes; the mod swaps in the scene without it then
SLEEP_INTRO_S = sum(s for _, s in SLEEP_INTRO)

# Backgrounds from build.py (name: where Ferro is, for the alt text). The mod picks one at
# random on every turn. The first one is previewed in preview/run.svg and sleep.svg, the
# others in preview/<name>-run.svg and <name>-sleep.svg.
BACKGROUNDS = {"meadow": "the meadow", "autumn": "the autumn meadow", "winter": "the winter meadow"}
# The backgrounds the mod picks from; the others are built and previewed, but not in scene.ts.
# Winter is switched off for now (Vatra, 4.10.2026).
IN_MOD = ["meadow", "autumn"]

Z_GLYPH = ["####", "..#.", ".#..", "####"]


def fmt(t: float, digits: int = 4) -> str:
    return f"{t:.{digits}f}".rstrip("0").rstrip(".")


def key(t: float, period: float) -> str:
    """A keyTime: five decimals, so a frame change in a three-minute loop lands within 2 ms."""
    return fmt(t / period, 5)


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


def linear(points: list[tuple[float, float]], period: float, y: int = 0, repeat: bool = True,
           begin: float = 0) -> str:
    """Movement along x through key points (second, x), linear between them. A negative `begin`
    starts the movement that many seconds in."""
    vals = ";".join(f"{fmt(x)} {y}" for _, x in points)
    keys = ";".join(key(t, period) for t, _ in points)
    rep = 'repeatCount="indefinite"' if repeat else 'fill="freeze"'
    start = f' begin="{fmt(begin)}s"' if begin else ""
    return (
        f'<animateTransform attributeName="transform" type="translate" values="{vals}" '
        f'keyTimes="{keys}" dur="{fmt(period)}s"{start} {rep}/>'
    )


def discrete(attr: str, values: list[str], times: list[float], period: float) -> str:
    """Discrete animation over the whole loop; times are the start of each value in seconds."""
    keys = ";".join(key(t, period) for t in times)
    return (
        f'<animate attributeName="{attr}" values="{";".join(values)}" keyTimes="{keys}" '
        f'dur="{fmt(period)}s" calcMode="discrete" repeatCount="indefinite"/>'
    )


def windows(times: list[tuple[float, float]], period: float) -> str:
    """display="inline" only within the given (start, end) windows of the loop; a window may
    start at 0 or end at the end of the loop, and windows that touch are joined."""
    merged: list[tuple[float, float]] = []
    for a, b in sorted(times):
        if merged and a <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    vals, keys = ["none"], [0.0]
    for a, b in merged:
        if a == 0:
            vals[-1] = "inline"
        else:
            vals.append("inline")
            keys.append(a)
        if b < period:
            vals.append("none")
            keys.append(b)
    return discrete("display", vals, keys, period)


def tiles(tile: str, y: int, width: int, travel: float) -> str:
    """Enough copies of a layer to cover the viewBox and the whole distance it travels in a loop."""
    copies = math.ceil((VW + travel) / width) + 1
    return "".join(f'<use href="#{tile}" x="{k * width}" y="{y}"/>' for k in range(copies))


def at(points: list[tuple[float, float]], t: float) -> float:
    """x of a piecewise linear path at second t."""
    for (t0, x0), (t1, x1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            return x1 if t1 == t0 else x0 + (x1 - x0) * (t - t0) / (t1 - t0)
    return points[-1][1]


def cycle(prefix: str, frames: list, frame_s: float) -> str:
    """Frames shown one after another in their own fast loop; None is a slot with nothing."""
    out = ""
    for slot, frame in enumerate(frames):
        if frame is None:
            continue
        vals = ";".join("visible" if j == slot else "hidden" for j in range(len(frames)))
        out += (
            f'<use href="#{prefix}{frame}" visibility="hidden"><animate attributeName="visibility" '
            f'values="{vals}" dur="{fmt(frame_s * len(frames))}s" calcMode="discrete" '
            f'repeatCount="indefinite"/></use>'
        )
    return out


def meadow_defs(meadow: dict) -> list[str]:
    name = meadow["name"]
    return [
        sprite_def("clouds", f"{name}-clouds.png"),
        sprite_def("back", f"{name}-back.png"),
        sprite_def("ground", f"{name}-ground.png"),
    ]


def clouds_layer(meadow: dict, begin: float = 0) -> str:
    mw = meadow["width"]
    period = mw / CLOUD_SPEED
    return f"<g>{linear([(0, 0), (period, -mw)], period, begin=begin)}{tiles('clouds', 0, mw, mw)}</g>"


def svg_head(defs: list[str], meadow: dict) -> str:
    """The scene up to and including </defs>; the body and </svg> follow."""
    height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW * SCALE}" height="{height * SCALE}" '
        f'viewBox="0 0 {VW} {height}" preserveAspectRatio="xMidYMid slice" '
        f'shape-rendering="crispEdges" image-rendering="pixelated" style="image-rendering:pixelated">'
        f'<rect width="{VW}" height="{height}" fill="{meadow["sky"]}"/>'
        f'<defs>{"".join(defs)}</defs>'
    )


# What Ferro does at a stop. Each kind is a function that returns a Stop; a new kind is one more
# function here and one more entry in WEIGHTS and SAYS.
@dataclass
class Stop:
    """What Ferro does between two runs. Times are seconds from the moment she stops running.
    `ground`: (second, px) how far the ground has moved by then, from (0, 0) to the end of the stop.
    `stills`: the windows in which each drawing shows on her canvas.
    `sprites`: the file of every sprite id the stop uses.
    `cycles`: frames looping within a window, (prefix, frames, seconds per frame, start, end).
    `props`: what she leaves on the meadow, (sprite id, second it appears, x, y on her canvas).
    `front`: what lies on the meadow in front of her and scrolls with the ground, (sprite id, x, y
    on her canvas at second `at`, at, windows in which it shows); a window may start before the
    stop, while she still runs.
    `run_from`: px right of the run frames where she stands at the end of the stop. If set, she
    runs on from a standstill: the run starts there and slides back to its place while the ground
    speeds up (RUN_START)."""
    dur: float
    ground: list[tuple[float, float]]
    stills: dict[str, list[tuple[float, float]]]
    sprites: dict[str, str]
    cycles: list[tuple[str, list, float, float, float]] = field(default_factory=list)
    props: list[tuple[str, float, int, int]] = field(default_factory=list)
    front: list[tuple[str, int, int, float, list[tuple[float, float]]]] = field(default_factory=list)
    run_from: int = 0


def sequence(frames: list[tuple[str, float]]) -> tuple[dict[str, list[tuple[float, float]]], float]:
    """Drawings shown one after another: their windows and the total length."""
    stills: dict[str, list[tuple[float, float]]] = {}
    t = 0.0
    for id_, s in frames:
        stills.setdefault(id_, []).append((t, t + s))
        t += s
    return stills, t


def still_poop() -> Stop:
    """Pooping in one spot, the rare way: she stops, squats, the pile drops, she steps away."""
    stills, t = sequence([(f"p{i}", s) for i, s in POOP])
    pile = json.loads((PX / "poop-pile.json").read_text())
    return Stop(
        dur=t,
        ground=[(0, 0), (t - POOP[-1][1], 0), (t, WALK_AWAY_PX)],
        stills=stills,
        sprites={f"p{i}": f"poop-{i}.png" for i, _ in POOP} | {"pile": "poop-pile.png"},
        props=[("pile", sum(s for _, s in POOP[:4]), pile["x"], pile["y"])],
    )


# Pooping while walking, the way the real Ferro does it: crouch with frames 1-2 of poop.png, walk
# hunched while the ground moves slowly and a dropping falls behind her now and then, stand up
# with frame 5 of poop.png.
CROUCH = [(1, 0.3), (2, 0.3)]  # (poop frame, seconds)
HUNCH_WALK_S = 7.0
HUNCH_WALK_SPEED = 22  # px/s of the ground while she walks hunched
HUNCH_FRAME_S = 0.2
DROPS = [(0.8, 0), (2.5, 1), (4.2, 1), (5.9, 2)]  # (seconds into the walk, dropping sprite)
REAR_X = 12  # x of her rear on the poop-walk canvas, where the droppings fall


def walk_poop() -> Stop:
    last = len(POOP) - 1
    stills, walk_start = sequence([(f"p{i}", s) for i, s in CROUCH])
    walk_end = walk_start + HUNCH_WALK_S
    end = walk_end + POOP[last][1]
    stills[f"p{last}"] = [(walk_end, end)]
    walked = HUNCH_WALK_S * HUNCH_WALK_SPEED
    walk_frames = sorted(PX.glob("poop-walk-[0-9].png"))
    sprites = {f"p{i}": f"poop-{i}.png" for i in [i for i, _ in CROUCH] + [last]}
    sprites |= {f"w{i}": f.name for i, f in enumerate(walk_frames)}
    # the droppings fall behind her rear, on the ground line of her canvas
    canvas_h = size("poop-walk-0.png")[1]
    props = []
    for s, k in DROPS:
        w, h = size(f"poop-walk-drop-{k}.png")
        sprites[f"d{k}"] = f"poop-walk-drop-{k}.png"
        props.append((f"d{k}", walk_start + s, REAR_X - w // 2, canvas_h - h))
    return Stop(
        dur=end,
        ground=[(0, 0), (walk_start, 0), (walk_end, walked), (end, walked + WALK_AWAY_PX)],
        stills=stills,
        sprites=sprites,
        cycles=[("w", list(range(len(walk_frames))), HUNCH_FRAME_S, walk_start, walk_end)],
        props=props,
    )


# Sitting and looking at the viewer: brake, sit, turn the head to the viewer, blink and tilt the
# head, turn back, get up, stand on all fours and run on from there (Vatra, 7.10.2026: she went
# from half sitting straight into a full gallop). The frames are sit.png (0 brake, 1 sitting down,
# 2 sitting in profile, 3 head three-quarters, 4 facing the viewer, 5 head tilt), sit-blink.png,
# derived from 4, and sit-up.png, standing, derived from poop-0.
SIT = [(0, 0.3), (1, 0.3), (2, 0.5), (3, 0.3), (4, 1.6), ("blink", 0.15), (4, 1.2), (5, 1.4),
       (4, 1.0), ("blink", 0.15), (4, 0.6), (3, 0.3), (2, 0.4), (1, 0.3), ("up", 0.35)]  # (frame, seconds)
BRAKE_PX = 10  # how far the ground still moves while she brakes


def sit() -> Stop:
    stills, t = sequence([(f"s{f}", s) for f, s in SIT])
    # sit-up is poop-0 moved right to where she sat; the run starts there
    stand_x = Image.open(PX / "sit-up.png").getbbox()[0] - Image.open(PX / "poop-0.png").getbbox()[0]
    return Stop(
        dur=t,
        ground=[(0, 0), (SIT[0][1], BRAKE_PX), (t, BRAKE_PX)],
        stills=stills,
        sprites={f"s{f}": f"sit-{f}.png" for f, _ in SIT},
        run_from=stand_x,
    )


# Sniffing one spot: slow down with the head lowering (sniff-0), sniff with the head bobbing
# between the nose on the grass (sniff-5) and one pixel higher (sniff-up), lift the head (sniff-0
# again). The walk with the nose down (sniff-1 to 4) is not used: no drawing of it looked right,
# and neither did 1 to 5 spots with a dash between them (Vatra, 6.10.2026: "not like Ferro"; one
# sniff and that's it).
SNIFF_TURN = (0.35, 12)  # (seconds, px of ground) of sniff-0, when she slows down and when she lifts her head
SNIFF_BOBS = 3
SNIFF_DOWN_S, SNIFF_UP_S, SNIFF_LAST_S = 0.32, 0.14, 0.4  # nose on the grass, head up, last sniff


def sniff() -> Stop:
    turn_s, turn_px = SNIFF_TURN
    stills: dict[str, list[tuple[float, float]]] = {"n0": [(0, turn_s)], "n5": [], "nu": []}
    t = turn_s
    for _ in range(SNIFF_BOBS):
        stills["n5"].append((t, t + SNIFF_DOWN_S))
        stills["nu"].append((t + SNIFF_DOWN_S, t + SNIFF_DOWN_S + SNIFF_UP_S))
        t += SNIFF_DOWN_S + SNIFF_UP_S
    stills["n5"].append((t, t + SNIFF_LAST_S))
    t += SNIFF_LAST_S
    stills["n0"].append((t, t + turn_s))  # lifts the head and moves off
    return Stop(
        dur=t + turn_s,
        ground=[(0, 0), (turn_s, turn_px), (t, turn_px), (t + turn_s, 2 * turn_px)],
        stills=stills,
        sprites={"n0": "sniff-0.png", "n5": "sniff-5.png", "nu": "sniff-up.png"},
    )


# Drinking from the red bowl, approached like sniffing (Vatra, 7.10.2026): the bowl comes in with
# the grass, she slows down and lowers her head (sniff-0) and stops at it, laps, lifts her head
# (sniff-0 again) and runs on, and the bowl scrolls away. Lapping loops the frames of drink-lap.png
# as 1, 2, 3, 4 and 3 again without its drops (Vatra). The lapping frames have the bowl drawn in;
# the bowl on its own lies in front of her while she runs to it and away from it, and hides while
# she laps, where it would cover her tongue in the water.
LAP_ORDER = [0, 1, 2, 3, 2]
LAP_DROPS = [None, 1, 2, 3, None]
LAP_FRAME_S = 0.15
LAPS = 5
BOWL_LEAD_S = 6.0  # seconds before she stops that the bowl starts coming in, off the right edge
BOWL_AFTER_S = 6.0  # seconds after she runs on that it is still there, until it is off the left edge


def drink() -> Stop:
    turn_s, turn_px = SNIFF_TURN
    lap_end = turn_s + LAPS * len(LAP_ORDER) * LAP_FRAME_S
    end = lap_end + turn_s
    bowl = json.loads((PX / "drink-lap.json").read_text())["bowl"]
    sprites = {"n0": "sniff-0.png", "bowl": "drink-lap-bowl.png"}
    sprites |= {f"l{i}": f"drink-lap-{i}.png" for i in set(LAP_ORDER)}
    sprites |= {f"ld{i}": f"drink-lap-drops-{i}.png" for i in LAP_DROPS if i is not None}
    return Stop(
        dur=end,
        ground=[(0, 0), (turn_s, turn_px), (lap_end, turn_px), (end, 2 * turn_px)],
        stills={"n0": [(0, turn_s), (lap_end, end)]},
        sprites=sprites,
        cycles=[("l", LAP_ORDER, LAP_FRAME_S, turn_s, lap_end), ("ld", LAP_DROPS, LAP_FRAME_S, turn_s, lap_end)],
        front=[("bowl", bowl["x"], bowl["y"], turn_s, [(-BOWL_LEAD_S, turn_s), (lap_end, end + BOWL_AFTER_S)])],
    )


STOPS = {"sit": sit, "sniff": sniff, "walkPoop": walk_poop, "stillPoop": still_poop, "drink": drink}


def run_head(meadow: dict, stops: dict[str, Stop]) -> str:
    """The head of every run scene of a background: the meadow and every drawing any stop uses,
    so all programs of a background share it."""
    sprites = {f"r{i}": f"run-{i}.png" for i in sorted(set(RUN_ORDER))}
    for stop in stops.values():
        sprites |= stop.sprites
    return svg_head(meadow_defs(meadow) + [sprite_def(id_, f) for id_, f in sprites.items()], meadow)


def run_body(meadow: dict, dog_x: int, dog_y: int, program: list[tuple[float, Stop]],
             ball: bool = False, info: dict | None = None) -> str:
    """Everything after </defs> of one run, up to and including </svg>: running, a stop after
    each (seconds of running, stop) of the program, then running on until the loop closes.
    It marks where the props go (PROP_MARKS, see take_marks). `info` gets the ground's path and
    the stops, for prop_slots."""
    mw = meadow["width"]
    t = d = 0.0  # second of the loop, px the ground has moved
    ground_pts = [(0.0, 0.0)]
    shift_pts = [(0.0, 0.0)]  # px her run frames lie right of their place, after a stop with run_from
    start_s = start_px = 0.0  # the run after the last stop sets off from a standstill over this
    stops: list[tuple[float, float]] = []
    stills: dict[str, list[tuple[float, float]]] = {}
    cycles: dict[tuple, list[tuple[float, float]]] = {}
    props: list[tuple[str, float, int, int]] = []
    fronts: list[tuple[str, int, int, float, list[tuple[float, float]]]] = []
    for run_s, stop in program:
        t += run_s
        d += start_px + (run_s - start_s) * RUN_SPEED
        ground_pts += [(t + s, -(d + x)) for s, x in stop.ground]
        for id_, ws in stop.stills.items():
            stills.setdefault(id_, []).extend((t + a, t + b) for a, b in ws)
        for prefix, frames, frame_s, a, b in stop.cycles:
            cycles.setdefault((prefix, tuple(frames), frame_s), []).append((t + a, t + b))
        props += [(id_, t + s, x, y) for id_, s, x, y in stop.props]
        fronts += [(id_, x, y, t + s, [(t + a, t + b) for a, b in ws]) for id_, x, y, s, ws in stop.front]
        stops.append((t, t + stop.dur))
        t += stop.dur
        d += stop.ground[-1][1]
        start_s, start_px = RUN_START[-1] if stop.run_from else (0.0, 0.0)
        if stop.run_from:
            ground_pts += [(t + s, -(d + x)) for s, x in RUN_START[1:]]
            shift_pts += [(t - stop.dur, 0), (t, stop.run_from), (t + start_s, 0)]
    tiles_n = GROUND_TILES
    while tiles_n * mw - d < FINAL_RUN_MIN_S * RUN_SPEED:
        tiles_n += GROUND_TILES
    ground_total = tiles_n * mw
    period = t + start_s + (ground_total - d - start_px) / RUN_SPEED
    ground_pts.append((period, -ground_total))
    shift_pts.append((period, 0))

    back_pts = [(s, x * BACK_RATIO) for s, x in ground_pts]
    y_back = meadow["sky_h"]
    y_ground = meadow["sky_h"] + meadow["back_h"]
    if info is not None:
        info.update(ground_pts=ground_pts, stops=stops)
    # far props behind the hills, ground props behind her on the grass
    layers = (
        clouds_layer(meadow)
        + f"<g>{linear(back_pts, period)}{PROP_MARKS[0]}{tiles('back', y_back, mw, ground_total * BACK_RATIO)}</g>"
        + f"<g>{linear(ground_pts, period)}{tiles('ground', y_ground, mw, ground_total)}{PROP_MARKS[1]}</g>"
    )

    # what she leaves on the meadow: placed where the ground is when it appears, then it scrolls
    # with the ground
    left = "".join(
        f'<use href="#{id_}" x="{round(dog_x + x - at(ground_pts, s))}" y="{dog_y + y}" display="none">'
        + discrete("display", ["none", "inline"], [0, s], period)
        + "</use>"
        for id_, s, x, y in props
    )
    left_el = f"<g>{linear(ground_pts, period)}{left}</g>" if left else ""

    # running: its own fast cycle, the whole group hidden at every stop (and moved only while it is
    # hidden or setting off from a standstill)
    runs = list(zip([0.0] + [b for _, b in stops], [a for a, _ in stops] + [period]))
    shift = linear(shift_pts, period) if len(shift_pts) > 2 else ""
    dog = f'<g>{windows(runs, period)}{shift}{cycle("r", RUN_ORDER, RUN_FRAME_S)}</g>'
    for id_, ws in stills.items():
        dog += f'<g display="none">{windows(ws, period)}<use href="#{id_}"/></g>'
    for (prefix, frames, frame_s), ws in cycles.items():
        dog += f'<g display="none">{windows(ws, period)}{cycle(prefix, list(frames), frame_s)}</g>'

    # in front of her: placed where the ground is at second `at`, shown only in its windows
    front = "".join(
        f'<use href="#{id_}" x="{round(dog_x + x - at(ground_pts, s))}" y="{dog_y + y}" display="none">'
        + windows(ws, period)
        + "</use>"
        for id_, x, y, s, ws in fronts
    )
    # the props in front of her go in the same group
    front_el = f"<g>{linear(ground_pts, period)}{front}{PROP_MARKS[2]}</g>"

    ball_el = ball_layer(ground_pts, shift_pts, stops, period, dog_x, dog_y) if ball else ""
    return (layers + left_el + ball_el + f'<g transform="translate({dog_x} {dog_y})">{dog}</g>'
            + front_el + "</svg>")


# Where run_body leaves room for the props: far, behind her, in front of her. take_marks removes
# them and returns where they were, and the mod inserts the props there.
PROP_MARKS = ("<!--far-->", "<!--behind-->", "<!--front-->")


def take_marks(body: str) -> tuple[str, list[int]]:
    """The body without the prop marks, and the index of each mark in it."""
    at_ = []
    for mark in PROP_MARKS:
        i = body.index(mark)
        body = body[:i] + body[i + len(mark):]
        at_.append(i)
    return body, at_


def load_props() -> list[dict]:
    """The registry with each drawing's size, without the props too tall for their place (they
    wait for a smaller drawing, see tools/props.py)."""
    props = []
    for p in json.loads(PROPS_FILE.read_text(encoding="utf-8"))["props"]:
        p["w"], p["h"] = size(f"prop-{p['name']}.png")
        tallest = PROP_BEHIND[0] if p["where"] == "ground" else FAR_BASE
        if p["h"] > tallest:
            print(f"prop {p['name']} left out: {p['h']} pixels tall, at most {tallest}")
            continue
        props.append(p)
    return props


def prop_slots(ground_pts: list, stops: list[tuple[float, float]], dog_x: int, rng: random.Random,
               widest: int) -> tuple[list[list[int]], list[int]]:
    """Where the props of one run may stand, in the coordinates of the layer they move with, from
    the start of the run to when she falls asleep (PROGRAM_S): ground slots [x, bottom row, 1 if in
    front of her] and far slots [x]. A slot is placed so the prop comes in at the right edge of
    the viewBox after its gap of running. Nothing stands in front of her where she stops: there the
    prop would stand still over her for the whole stop."""
    run_end = -at(ground_pts, PROGRAM_S)  # px the ground has moved when she falls asleep
    still = [(-at(ground_pts, a), -at(ground_pts, b)) for a, b in stops]
    ground, x = [], VW
    while True:
        x += round(rng.uniform(*PROP_GAP_S) * RUN_SPEED)
        if x - VW >= run_end:
            break
        covers = any(x - d1 < dog_x + DOG_W + 8 and x - d0 + widest > dog_x - 8 for d0, d1 in still)
        front = not covers and rng.random() < PROP_FRONT_SHARE
        ground.append([x, PROP_FRONT if front else rng.randint(*PROP_BEHIND), int(front)])
    far, x = [], VW
    while True:
        x += round(rng.uniform(*FAR_GAP_S) * RUN_SPEED * BACK_RATIO)
        if x - VW >= run_end * BACK_RATIO:
            break
        far.append(x)
    return ground, far


def pick_prop(props: list[dict], where: str, roll: float) -> int:
    """The prop a slot gets for a roll in [0, 1), by the chances; -1 for none. The mod does the
    same in run.ts."""
    r = roll * 100
    for i, p in enumerate(props):
        if p["where"] == where:
            r -= p["chance"]
            if r < 0:
                return i
    return -1


def with_props(body: str, marks: list[int], slots: list, far: list, props: list[dict],
               picks: dict, ball: tuple[str, int] | None = None) -> str:
    """The body with the picked props (and the ball) put in, as the mod does in run.ts."""
    used = sorted({i for i in picks["ground"] + picks["far"] if i >= 0})
    far_s = "".join(f'<use href="#prop-{props[i]["name"]}" x="{x}" y="{FAR_BASE - props[i]["h"] + 1}"/>'
                    for x, i in zip(far, picks["far"]) if i >= 0)
    behind, front = "", ""
    for (x, row, in_front), i in zip(slots, picks["ground"]):
        if i >= 0:
            use = f'<use href="#prop-{props[i]["name"]}" x="{x}" y="{row - props[i]["h"] + 1}"/>'
            if in_front:
                front += use
            else:
                behind += use
    pieces = [(marks[0], far_s), (marks[1], behind), (marks[2], front)] + ([ball[::-1]] if ball else [])
    for at_, piece in sorted(pieces, key=lambda t: -t[0]):
        body = body[:at_] + piece + body[at_:]
    defs = "".join(props[i]["def"] for i in used)
    return (f"<defs>{defs}</defs>" if defs else "") + body


# The orange ball she chases: it bounces ahead of her while she runs, rolls on and comes to
# rest on the grass at every stop, and pops up again when she reaches it.
BALL_BOUNCE_S = 0.55  # one bounce, roughly
BALL_BOUNCE_H = 14  # px
BALL_GAP = (8, 52)  # px between her nose and the ball while she chases it, nearest and farthest
BALL_GAP_S = 3.7  # seconds of one swing from near to far and back
BALL_ROLL_MIN = 40  # px the ball rolls on at least when she stops
BALL_ROLL_S = 1.2
NOSE_X = 58  # x of her nose on the run canvas


def ball_layer(ground_pts: list, shift_pts: list, stops: list[tuple[float, float]], period: float,
               dog_x: int, dog_y: int) -> str:
    """The ball through the whole loop. At each (stop, go) it rolls on far enough that she
    reaches it just as she runs again (or BALL_ROLL_MIN, if she would reach it sooner), and lies
    on the meadow until she reaches it. `shift_pts`: how far right of their place her run frames
    are, when she sets off from a standstill."""
    d = size("ball.png")[0]
    top = dog_y + size("run-0.png")[1] - d  # the ball's top when it lies on the grass

    def nose(t: float) -> float:
        return dog_x + NOSE_X + at(shift_pts, t)

    mid, amp = (BALL_GAP[0] + BALL_GAP[1]) / 2, (BALL_GAP[1] - BALL_GAP[0]) / 2
    reaches: list[float] = []

    def swing(t: float) -> float:
        return mid + amp * math.sin(2 * math.pi * t / BALL_GAP_S)

    def gap(t: float) -> float:
        """Her nose to the ball while she chases it: the swing, growing out of her nose for a
        second after she reaches it, and back to where the loop starts in the last second."""
        reached = [r for r in reaches if r <= t]
        g = swing(t) if not reached else 2 + (swing(t) - 2) * min(1.0, (t - reached[-1]) / 1.0)
        if t > period - 1:
            g += (swing(0) - g) * (t - (period - 1))
        return g

    rests = []
    for i, (stop, go) in enumerate(stops):
        x_stop = nose(stop) + gap(stop)
        moved = at(ground_pts, go) - at(ground_pts, stop)  # negative: the ground moves left
        roll = max(BALL_ROLL_MIN, nose(go) + 2 - x_stop - moved)
        reach = go
        while reach < period and x_stop + roll + at(ground_pts, reach) - at(ground_pts, stop) > nose(reach) + 2:
            reach += 0.01
        assert reach < (stops[i + 1][0] if i + 1 < len(stops) else period), "she reaches the ball too late"
        reaches.append(reach)
        rests.append((stop, reach, x_stop, roll))
    chase = list(zip([0.0] + reaches, [a for a, _ in stops] + [period]))

    xs = []
    for a, b in chase:
        t = a
        while t < b:
            xs.append((t, nose(t) + gap(t)))
            t += 0.5
        xs.append((b, nose(b) + gap(b)))

    # bounces: a whole number in each window, so the ball is on the grass when it stops and
    # when it pops up again
    keys = [(0.0, 0)]
    for a, b in chase:
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
        f'keyTimes="{";".join(key(t, period) for t, _ in keys)}" calcMode="spline" '
        f'keySplines="{";".join(splines)}" dur="{fmt(period)}s" repeatCount="indefinite"/>'
    )
    chased = (
        f"<g>{windows(chase, period)}<g>{linear(xs, period)}<g>{bounce}"
        f'<use href="#ball" x="0" y="{top}"/></g></g></g>'
    )

    # lying on the meadow: placed where the ground is when she stops, rolls on, then scrolls with
    # the ground until she reaches it
    resting = ""
    for stop, reach, x_stop, roll in rests:
        roll_pts = [(0, 0), (stop, 0), (stop + BALL_ROLL_S / 2, roll * 0.75), (stop + BALL_ROLL_S, roll),
                    (period, roll)]
        resting += (
            f'<g display="none">{windows([(stop, reach)], period)}<g>{linear(roll_pts, period)}'
            f'<use href="#ball" x="{round(x_stop - at(ground_pts, stop))}" y="{top}"/></g></g>'
        )
    resting = f"<g>{linear(ground_pts, period)}{resting}</g>"
    # its own <defs>, so the scene with the ball is the plain scene with this one piece inserted
    return f'<defs>{sprite_def("ball", "ball.png")}</defs>' + chased + resting


def draw_programs(rng: random.Random, stops: dict[str, Stop]) -> list[list[tuple[float, str]]]:
    """PROGRAMS runs, each a list of (seconds of running before the stop, kind of stop)."""
    firsts = [kind for kind, w in WEIGHTS.items() for _ in range(round(w * PROGRAMS))]
    assert len(firsts) == PROGRAMS, "the WEIGHTS shares must come out whole in PROGRAMS"
    programs = []
    for kind in firsts:
        # the first stop comes after a gap like every later one (Vatra, 7.10.2026)
        first_s = round(rng.uniform(*GAP_S), 1)
        program, t, pooped = [(first_s, kind)], first_s + stops[kind].dur, kind in POOPS
        while True:
            run_s = round(rng.uniform(*GAP_S), 1)
            if t + run_s >= PROGRAM_S:
                break
            kinds = [k for k in WEIGHTS if k != kind and not (pooped and k in POOPS)]
            kind = rng.choices(kinds, [WEIGHTS[k] for k in kinds])[0]
            pooped = pooped or kind in POOPS
            program.append((run_s, kind))
            t += run_s + stops[kind].dur
        programs.append(program)
    return programs


def describe(program: list[tuple[float, str]], stops: dict[str, Stop]) -> str:
    """'sits at 16 s, sniffs at 41 s, ...': the second of the run each stop starts."""
    out, t = [], 0.0
    for run_s, kind in program:
        t += run_s
        out.append(f"{SAYS[kind]} at {round(t)} s")
        t += stops[kind].dur
    return ", ".join(out)


def sleep_scene(meadow: dict, dog_x: int, dog_y: int, lie_down: bool = True) -> str:
    """She lies down and falls asleep. Without `lie_down` she is already asleep: the scene starts
    where the other one is when the intro ends (the clouds too), so the mod can swap them then. A
    scene starts from its first frame whenever the band draws it anew (reopening the
    conversation), and she should not lie down again every time."""
    mw = meadow["width"]
    breath_frames = list(dict.fromkeys(name for name, _ in BREATH))
    intro_frames = SLEEP_INTRO if lie_down else []
    defs = meadow_defs(meadow) + [sprite_def(f"s{i}", f"sleep-{i}.png") for i, _ in intro_frames]
    defs += [sprite_def(f"b{k}", f"{name}.png") for k, name in enumerate(breath_frames)]

    dog = ""
    t = 0.0
    for i, s in intro_frames:
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

    layers = (
        clouds_layer(meadow, begin=0 if lie_down else -SLEEP_INTRO_S)
        + f"<g>{tiles('back', meadow['sky_h'], mw, 0)}</g>"
        + f"<g>{tiles('ground', meadow['sky_h'] + meadow['back_h'], mw, 0)}</g>"
    )
    body = layers + f'<g transform="translate({dog_x} {dog_y})">{dog}{zs}</g>'
    return svg_head(defs, meadow) + body + "</svg>"


def with_ball_piece(plain: str, with_ball: str) -> tuple[str, int]:
    """The ball as a piece of the plain scene: (piece, index where it goes)."""
    at_ = next(i for i, (a, b) in enumerate(zip(plain, with_ball)) if a != b)
    piece = with_ball[at_ : at_ + len(with_ball) - len(plain)]
    assert plain[:at_] + piece + plain[at_:] == with_ball
    return piece, at_


PROGRAMS_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ferro - programs</title>
<style>
  body {{ font: 14px system-ui, sans-serif; background: #2a2a2a; color: #ddd; margin: 16px; }}
  h2 {{ font-size: 14px; font-weight: 600; margin: 18px 0 6px; }}
  p {{ margin: 0 0 12px; color: #aaa; }}
  .band {{ width: 720px; height: 164px; overflow: hidden; border: 1px solid #555; }}
  .band img {{ height: 164px; width: 100%; display: block; }}
</style>
</head>
<body>
  <p>The {n} programs of the summer meadow (generated by tools/scene.py, not committed). The mod
  plays one per turn, on any meadow; every other one here chases the ball. The band shows the
  run from its start, 20 s into a turn, and a turn sleeps after 160 s of it. Reload the page to
  watch from the start again.</p>
{bands}
</body>
</html>
"""


def main() -> None:
    dog_w, dog_h = size("run-0.png")
    preview = ROOT / "preview"
    preview.mkdir(exist_ok=True)
    stops = {kind: make() for kind, make in STOPS.items()}
    rng = random.Random(SEED)
    # the slots get a generator of their own, so the programs stay as they were drawn
    slot_rng = random.Random(SEED + 1)
    props = load_props()
    for p in props:
        p["def"] = sprite_def(f"prop-{p['name']}", f"prop-{p['name']}.png")
    widest = max(p["w"] for p in props if p["where"] == "ground")
    props_defs = sum(len(p["def"]) for p in props)
    scenes = []
    for k, (name, place) in enumerate(BACKGROUNDS.items()):
        meadow = json.loads((PX / f"{name}.json").read_text()) | {"name": name}
        height = meadow["sky_h"] + meadow["back_h"] + meadow["ground_h"]
        dog_x = VW // 2 - dog_w // 2 - 20
        dog_y = height - dog_h - 2
        # the mod's head has the drawings of the stops in WEIGHTS only: a stop not yet in the
        # programs (drinking, until its share is set) shows in its preview alone
        head = run_head(meadow, {kind: stops[kind] for kind in WEIGHTS})
        prefix = "" if k == 0 else f"{name}-"
        for kind in (kind for kind in stops if kind not in WEIGHTS):
            program = [(RUN_BEFORE, stops[kind])]
            own_head = run_head(meadow, {kind: stops[kind]})
            (preview / f"{prefix}{kind}.svg").write_text(
                own_head + take_marks(run_body(meadow, dog_x, dog_y, program))[0], encoding="utf-8")

        # one stop per scene, for the README and for looking at one kind of stop
        for kind, file in (("walkPoop", "run"), ("stillPoop", "run-still"), ("sit", "sit"), ("sniff", "sniff"),
                           ("drink", "drink")):
            program = [(RUN_BEFORE, stops[kind])]
            (preview / f"{prefix}{file}.svg").write_text(
                head + take_marks(run_body(meadow, dog_x, dog_y, program))[0], encoding="utf-8")
            (preview / f"{prefix}ball-{file}.svg").write_text(
                head + take_marks(run_body(meadow, dog_x, dog_y, program, ball=True))[0], encoding="utf-8")

        # the programs: the mod plays one per turn; the ball is a piece it inserts at `ballAt`, the
        # props it picks go in at `marks`
        programs, bands, largest, fullest = [], [], 0, 0
        preview_rng = random.Random(SEED + 2)
        for i, drawn in enumerate(draw_programs(rng, stops)):
            program = [(run_s, stops[kind]) for run_s, kind in drawn]
            info: dict = {}
            plain, marks = take_marks(run_body(meadow, dog_x, dog_y, program, info=info))
            with_ball = take_marks(run_body(meadow, dog_x, dog_y, program, ball=True))[0]
            piece, ball_at = with_ball_piece(plain, with_ball)
            slots, far = prop_slots(info["ground_pts"], info["stops"], dog_x, slot_rng, widest)
            programs.append({"body": plain, "ball": piece, "ballAt": ball_at, "marks": marks, "slots": slots,
                             "far": far})
            largest = max(largest, len(head) + len(with_ball))
            # every slot taken and every drawing in: more than any turn gets, the mod drops props then
            fullest = max(fullest, len(head) + len(with_ball) + props_defs + 60 * (len(slots) + len(far)))
            if k == 0:
                file, says = f"program-{i}.svg", describe(drawn, stops)
                print(f"  program {i}: {says}; {len(slots)} ground slots, {len(far)} far")
                if i % 2:
                    file, says = f"ball-{file}", f"with the ball: {says}"
                picks = {"ground": [pick_prop(props, "ground", preview_rng.random()) for _ in slots],
                         "far": [pick_prop(props, "far", preview_rng.random()) for _ in far]}
                shown = with_props(plain, marks, slots, far, props, picks, (piece, ball_at) if i % 2 else None)
                (preview / file).write_text(head + shown, encoding="utf-8")
                names = [props[j]["name"] for j in picks["far"] + picks["ground"] if j >= 0]
                bands.append(f'  <h2>Program {i}: {html.escape(says)}</h2>\n'
                             f'  <p>Props this time: {html.escape(", ".join(names) or "none")}</p>\n'
                             f'  <div class="band"><img src="{file}" alt="Ferro, program {i}"></div>')
                if i == 0:
                    # every prop once, in turn: ground props in the slots, far ones in the far slots
                    ground_i = [j for j, p in enumerate(props) if p["where"] == "ground"]
                    far_i = [j for j, p in enumerate(props) if p["where"] == "far"]
                    every = {"ground": [ground_i[n % len(ground_i)] if ground_i else -1 for n in range(len(slots))],
                             "far": [far_i[n % len(far_i)] if far_i else -1 for n in range(len(far))]}
                    (preview / "props-every.svg").write_text(
                        head + with_props(plain, marks, slots, far, props, every), encoding="utf-8")
                    bands.insert(0, '  <h2>Every prop in turn (program 0, each slot filled; a real turn '
                                    'picks by the chances)</h2>\n'
                                    '  <div class="band"><img src="props-every.svg" alt="Ferro, every prop"></div>')
        assert largest <= SVG_LIMIT, f"{name}: a program with the ball is {largest} chars"
        print(f"{name}: head {len(head)} chars, {len(programs)} programs, largest with the ball "
              f"{largest} of {SVG_LIMIT}; with every slot taken and every prop drawing {fullest}")
        if k == 0:
            (preview / "programs.html").write_text(PROGRAMS_PAGE.format(n=len(programs), bands="\n".join(bands)),
                                                   encoding="utf-8")

        sleep = sleep_scene(meadow, dog_x, dog_y)
        (preview / f"{prefix}sleep.svg").write_text(sleep, encoding="utf-8")
        print(name, "sleep", len(sleep), "chars", "" if name in IN_MOD else "(preview only, not in the mod)")
        asleep = sleep_scene(meadow, dog_x, dog_y, lie_down=False)
        (preview / f"{prefix}asleep.svg").write_text(asleep, encoding="utf-8")
        assert len(asleep) <= SVG_LIMIT, f"{name}: asleep is {len(asleep)} chars"
        if name in IN_MOD:
            scenes.append({"place": place, "height": height * SCALE, "head": head, "programs": programs,
                           "sleep": sleep, "asleep": asleep})

    ts = (
        "// Generated by tools/scene.py - do not edit by hand.\n"
        f"export const SCENE_MAX_WIDTH = {VW * SCALE}\n"
        f"export const SLEEP_INTRO_MS = {round(SLEEP_INTRO_S * 1000)}\n"
        f"export const SVG_LIMIT = {SVG_LIMIT}\n"
        f"export const FAR_BASE = {FAR_BASE}\n"
        f"export const PROPS = {json.dumps([{k: p[k] for k in ('name', 'where', 'chance', 'h', 'def')} for p in props])}\n"
        f"export const SCENES = {json.dumps(scenes)}\n"
    )
    (ROOT / "plugin" / "hooks" / "scene.ts").write_text(ts, encoding="utf-8")
    print("scene.ts", len(ts), "chars")


if __name__ == "__main__":
    main()
