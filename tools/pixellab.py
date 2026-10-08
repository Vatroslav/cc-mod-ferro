"""Draws a prop in real pixels with PixelLab (pixellab.ai, API v2), at the size assets/props.json
asks for, because ChatGPT never held a pixel grid (four tries for Orthanc, 8.10.2026): its pixels
came out 5.6 to 10.1 source pixels for the 13.9 asked, so the sheet had to be cut on a guessed grid,
which broke the drawing. PixelLab draws the pixels themselves, so nothing is cut or scaled.

One call of "Generate image (Pro)" (generate-image-v2) gives up to 64 candidates for a prop of at
most 42 pixels a side. Each one goes through the gate of tools/props.py (`native_check`: only fully
clear or fully opaque pixels, the size asked, its place); the ones that pass are shown on
preview/pixellab.html, enlarged and at the size the band shows them, and Vatra picks one.

A prop's entry in props.json gives the text (`prompt`) and may give a drawing to follow
(`reference`: an image in assets/ref/ and which figure of it, left to right, as props.py finds
them). The style image is the tower already in the mod (assets/px/prop-tower.png): the pixel size,
outline and shading of the far buildings, not its colours.

The token is secrets/pixellab-token.txt (from pixellab.ai/account, gitignored); this script reads
it itself and never prints it.

Run (from the repo root):
  python tools/pixellab.py balance          what is left on the account
  python tools/pixellab.py draw <prop>      candidates in preview/pixellab/<prop>/, the page
  python tools/pixellab.py pick <prop> <n>  candidate n becomes assets/src/<sheet>.png; then
                                            python tools/props.py and python tools/scene.py
"""

import base64
import io
import shutil
import sys
import time

import numpy as np
import requests
from PIL import Image

from build import OUT, ROOT, SRC, background_mask, fringe_mask
from props import figures, native_check, registry

API = "https://api.pixellab.ai/v2"
TOKEN = ROOT / "secrets" / "pixellab-token.txt"
STYLE = OUT / "prop-tower.png"
PREVIEW = ROOT / "preview"
POLL_S = 6
TIMEOUT_S = 600
ZOOM = 6


def headers() -> dict:
    return {"Authorization": f"Bearer {TOKEN.read_text(encoding='utf-8').strip()}"}


def b64(img: Image.Image) -> dict:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return {"type": "base64", "base64": base64.b64encode(buf.getvalue()).decode(), "format": "png"}


def reference(spec: dict) -> Image.Image:
    """One figure of a ChatGPT sheet, on a clear background, as the drawing to follow."""
    rgb = np.asarray(Image.open(ROOT / "assets" / "ref" / spec["image"]).convert("RGB"))
    bg = background_mask(rgb)
    bg |= fringe_mask(rgb, bg)
    box, own = figures(rgb, bg)[spec["figure"]]
    return Image.fromarray(np.dstack([rgb[box], np.where(own, 255, 0).astype(np.uint8)]), "RGBA")


def images_in(x) -> list[Image.Image]:
    """Every base64 image anywhere in a job's response."""
    if isinstance(x, dict):
        if "base64" in x:
            return [Image.open(io.BytesIO(base64.b64decode(x["base64"]))).convert("RGBA")]
        return [im for v in x.values() for im in images_in(v)]
    if isinstance(x, list):
        return [im for v in x for im in images_in(v)]
    return []


def balance() -> None:
    r = requests.get(f"{API}/balance", headers=headers(), timeout=30)
    r.raise_for_status()
    print(r.json())


def draw(name: str) -> None:
    p = next(q for q in registry() if q["name"] == name)
    w, h = p["size"]
    body = {
        "description": p["prompt"],
        "image_size": {"width": w, "height": h},
        "no_background": True,
        "style_image": {"image": b64(Image.open(STYLE)), "size": dict(zip(("width", "height"), Image.open(STYLE).size)),
                        "usage_description": "pixel size, outline and shading of a building far in the distance"},
        "style_options": {"color_palette": False, "outline": True, "detail": True, "shading": True},
    }
    if "reference" in p:
        ref = reference(p["reference"])
        body["reference_images"] = [{"image": b64(ref), "size": {"width": ref.width, "height": ref.height},
                                     "usage_description": "the building to draw: follow its shape"}]
    r = requests.post(f"{API}/generate-image-v2", headers=headers(), json=body, timeout=60)
    if r.status_code >= 400:
        sys.exit(f"{r.status_code}: {r.text[:500]}")
    job = r.json()
    print(f"job {job['background_job_id']}, usage {job.get('usage')}")
    start = time.time()
    while True:
        time.sleep(POLL_S)
        s = requests.get(f"{API}/background-jobs/{job['background_job_id']}", headers=headers(), timeout=30)
        s.raise_for_status()
        s = s.json()
        if s["status"] == "completed":
            break
        if s["status"] == "failed" or time.time() - start > TIMEOUT_S:
            sys.exit(f"job {s['status']}: {str(s.get('last_response'))[:500]}")
    print(f"done in {time.time() - start:.0f} s, usage {s.get('usage')}")
    found = images_in(s.get("last_response"))
    # 64 candidates may come as one image of 8 x 8 tiles
    if len(found) == 1 and found[0].size != (w, h) and found[0].width % w == 0 and found[0].height % h == 0:
        grid = found[0]
        found = [grid.crop((x, y, x + w, y + h)) for y in range(0, grid.height, h) for x in range(0, grid.width, w)]
    out = PREVIEW / "pixellab" / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    passed = []
    for i, im in enumerate(found):
        im.save(out / f"{i}.png")
        problems, _ = native_check(np.asarray(im), p)
        if problems:
            print(f"  {i}: {im.width} x {im.height}, rejected: {'; '.join(problems)}")
        else:
            passed.append(i)
    print(f"{name}: {len(found)} candidates, {len(passed)} pass: {passed}")
    page(name, passed, len(found))


def pick(name: str, i: str) -> None:
    p = next(q for q in registry() if q["name"] == name)
    shutil.copy(PREVIEW / "pixellab" / name / f"{i}.png", SRC / f"{p['sheet']}.png")
    print(f"{name}: candidate {i} is {(SRC / (p['sheet'] + '.png')).relative_to(ROOT)}")


def page(name: str, passed: list[int], total: int) -> None:
    cells = []
    for i in passed:
        w, h = Image.open(PREVIEW / "pixellab" / name / f"{i}.png").size
        cells.append(f'<div><img src="pixellab/{name}/{i}.png" width="{w * ZOOM}" height="{h * ZOOM}">'
                     f'<img src="pixellab/{name}/{i}.png" width="{w * 2}" height="{h * 2}"><b>{i}</b></div>')
    (PREVIEW / "pixellab.html").write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Ferro - {name} from PixelLab</title>
<style>
  body {{ font: 14px system-ui, sans-serif; background: #2a2a2a; color: #ddd; margin: 16px; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-end; }}
  .grid div {{ display: flex; gap: 8px; align-items: flex-end; }}
  img {{ background: #9cc7e8; image-rendering: pixelated; }}
</style></head><body>
<p>{name}: {len(passed)} of {total} PixelLab candidates pass the measures (written by tools/pixellab.py,
not committed). Each: enlarged {ZOOM}x, then at the size the band shows it, then its number.
Ferro in the band for scale: <img src="../assets/px/run-0.png" width="152" height="88"></p>
<div class="grid">
{chr(10).join(cells)}
</div></body></html>
""", encoding="utf-8")
    print(f"preview/pixellab.html: {len(passed)} candidates")


if __name__ == "__main__":
    cmd = sys.argv[1:]
    if cmd == ["balance"]:
        balance()
    elif cmd[:1] == ["draw"] and len(cmd) == 2:
        draw(cmd[1])
    elif cmd[:1] == ["pick"] and len(cmd) == 3:
        pick(cmd[1], cmd[2])
    else:
        sys.exit(__doc__)
