"""A reference page of every drawing in assets/px: preview/sprites.html, one section per animation,
enlarged with sharp pixels, each with its file name, size and whether the mod uses it.

"In the mod" means the drawing's data URI is in plugin/hooks/scene.ts, so run tools/scene.py
first. The page links the PNGs by relative path, so it shows the files as they are on disk.
Run (from the repo root, after tools/build.py and tools/scene.py): python tools/sprites.py
"""

import html
import re
from pathlib import Path

from scene import PX, ROOT, sprite_def

OUT = ROOT / "preview" / "sprites.html"
SCENE_TS = ROOT / "plugin" / "hooks" / "scene.ts"

# (section, file name pattern, zoom); a file goes to the first section it matches
SECTIONS = [
    ("Running", r"run-\d+", 4),
    ("Sitting and looking at you", r"sit-.+", 4),
    ("Sniffing a spot", r"sniff-.+", 4),
    ("Pooping in one spot", r"poop-\d+", 4),
    ("Pooping while walking", r"poop-walk-\d+", 4),
    ("Sleeping", r"sleep-.+", 4),
    ("Props", r"ball|poop-pile|poop-walk-drop-\d+", 8),
    ("Summer meadow", r"meadow-.+", 4),
    ("Autumn meadow", r"autumn-.+", 4),
    ("Winter meadow", r"winter-.+", 4),
]


def order(name: str) -> tuple:
    """Natural order: sit-2 before sit-10, the derived frames (sit-blink) after the numbered ones."""
    return tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"-", name))


def main() -> None:
    ts = SCENE_TS.read_text(encoding="utf-8")
    files = sorted((f for f in PX.glob("*.png")), key=lambda f: order(f.stem))
    sections: dict[str, list[tuple[Path, int]]] = {title: [] for title, _, _ in SECTIONS}
    other: list[tuple[Path, int]] = []
    for f in files:
        for title, pattern, zoom in SECTIONS:
            if re.fullmatch(pattern, f.stem):
                sections[title].append((f, zoom))
                break
        else:
            other.append((f, 4))
    if other:
        sections["Other"] = other

    used = unused = 0
    parts = []
    for title, items in sections.items():
        if not items:
            continue
        cards = []
        for f, zoom in items:
            image = sprite_def("x", f.name)
            in_mod = re.search(r'href="([^"]+)"', image).group(1) in ts
            used += in_mod
            unused += not in_mod
            w, h = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', image).groups())
            cards.append(
                f'<figure class="{"" if in_mod else "unused"}">'
                f'<img src="../assets/px/{html.escape(f.name)}" width="{w * zoom}" height="{h * zoom}" '
                f'alt="{html.escape(f.stem)}">'
                f"<figcaption><b>{html.escape(f.stem)}</b> {w}x{h}"
                f'{"" if in_mod else " <span>not in the mod</span>"}</figcaption></figure>'
            )
        parts.append(f"<h2>{html.escape(title)}</h2>\n<div class=\"row\">{''.join(cards)}</div>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ferro - every drawing</title>
<style>
  body {{ font: 14px system-ui, sans-serif; background: #2a2a2a; color: #ddd; margin: 16px; }}
  h2 {{ font-size: 14px; font-weight: 600; margin: 22px 0 8px; }}
  p {{ margin: 0 0 12px; color: #aaa; }}
  .row {{ display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }}
  figure {{ margin: 0; }}
  img {{ display: block; image-rendering: pixelated; background:
    repeating-conic-gradient(#6aa86a 0 25%, #5f9c5f 0 50%) 0 0 / 16px 16px; }}
  figcaption {{ margin-top: 4px; font-size: 12px; color: #aaa; }}
  figcaption b {{ color: #eee; font-weight: 600; }}
  figcaption span {{ color: #e9a04a; }}
  .unused img {{ opacity: .55; }}
</style>
</head>
<body>
<p>Every drawing in <code>assets/px</code>, enlarged (dog frames and backgrounds 4x, props 8x), on a
checkerboard so the transparent pixels show. {used} are in the mod, {unused} are built but not in it
(dimmed). Regenerate with <code>python tools/sprites.py</code> after <code>tools/build.py</code> and
<code>tools/scene.py</code>.</p>
{chr(10).join(parts)}
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(OUT.relative_to(ROOT), f"{used} in the mod, {unused} not")


if __name__ == "__main__":
    main()
