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
  python tools/pixellab.py page <prop>      the page again from the saved candidates (no call)
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
    (out / "job.txt").write_text(job["background_job_id"], encoding="utf-8")
    for i, im in enumerate(found):
        im.save(out / f"{i}.png")
    page(name)


def pick(name: str, i: str) -> None:
    p = next(q for q in registry() if q["name"] == name)
    shutil.copy(PREVIEW / "pixellab" / name / f"{i}.png", SRC / f"{p['sheet']}.png")
    print(f"{name}: candidate {i} is {(SRC / (p['sheet'] + '.png')).relative_to(ROOT)}")


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Ferro - NAME from PixelLab</title>
<style>
  body { font: 14px system-ui, sans-serif; background: #2a2a2a; color: #ddd; margin: 16px; }
  .bar { position: sticky; top: 0; background: #2a2a2a; padding: 8px 0 12px; z-index: 1; }
  .bar button { font: inherit; padding: 4px 12px; margin-right: 6px; }
  #status { margin-top: 8px; }
  .grid { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; }
  .card { display: flex; flex-direction: column; gap: 6px; padding: 8px; border: 3px solid #444; border-radius: 6px; }
  .card.keep { border-color: #3c3; }
  .card.drop { display: none; }
  .pics { display: flex; gap: 8px; align-items: flex-end; }
  .card button { font: inherit; flex: 1; }
  .row { display: flex; gap: 6px; align-items: center; }
  img { background: #9cc7e8; image-rendering: pixelated; }
</style></head><body>
<div class="bar">
  <b>NAME</b>: PASSED of TOTAL PixelLab candidates pass the measures. Keep or drop each one; "Next round"
  makes the kept ones the new set (when none is kept, it drops only the dropped ones). The choices stay
  after a reload. Ferro in the band for scale: <img src="../assets/px/run-0.png" width="152" height="88"><br>
  <button id="next">Next round</button><button id="back">Previous round</button><button id="reset">Start over</button>
  <div id="status"></div>
</div>
<div class="grid">
CELLS
</div>
<script>
const KEY = "pixellab-NAME-JOB";
const ALL = [IDS];
let s = JSON.parse(localStorage.getItem(KEY) || "null") || { rounds: [ALL], marks: {} };
const save = () => localStorage.setItem(KEY, JSON.stringify(s));
const pool = () => s.rounds[s.rounds.length - 1];
function show() {
  const p = pool();
  for (const card of document.querySelectorAll(".card")) {
    const id = +card.dataset.id, m = s.marks[id];
    card.style.display = p.includes(id) ? "" : "none";
    card.className = "card" + (m ? " " + m : "");
  }
  const kept = p.filter(id => s.marks[id] === "keep"), dropped = p.filter(id => s.marks[id] === "drop");
  document.getElementById("status").textContent =
    `Round ${s.rounds.length}: ${p.length} in the set, ${kept.length} kept, ${dropped.length} dropped, ` +
    `${p.length - kept.length - dropped.length} left to decide. Kept: ${kept.join(", ") || "none"}. ` +
    `In the set: ${p.filter(id => s.marks[id] !== "drop").join(", ")}.`;
  save();
}
document.querySelectorAll(".card button").forEach(b => b.onclick = () => {
  const id = +b.closest(".card").dataset.id;
  s.marks[id] = s.marks[id] === b.dataset.mark ? undefined : b.dataset.mark;
  show();
});
document.getElementById("next").onclick = () => {
  const p = pool(), kept = p.filter(id => s.marks[id] === "keep");
  const next = kept.length ? kept : p.filter(id => s.marks[id] !== "drop");
  s.rounds.push(next); s.marks = {}; show();
};
document.getElementById("back").onclick = () => { if (s.rounds.length > 1) { s.rounds.pop(); s.marks = {}; show(); } };
document.getElementById("reset").onclick = () => { s = { rounds: [ALL], marks: {} }; show(); };
show();
</script>
</body></html>
"""


def page(name: str) -> None:
    """Gates the saved candidates of a prop and writes preview/pixellab.html, where Vatra keeps or
    drops them round by round until one is left."""
    p = next(q for q in registry() if q["name"] == name)
    out = PREVIEW / "pixellab" / name
    ids = sorted(int(f.stem) for f in out.glob("*.png"))
    passed = []
    for i in ids:
        problems, _ = native_check(np.asarray(Image.open(out / f"{i}.png").convert("RGBA")), p)
        if problems:
            print(f"  {i}: rejected: {'; '.join(problems)}")
        else:
            passed.append(i)
    print(f"{name}: {len(ids)} candidates, {len(passed)} pass: {passed}")
    cells = []
    for i in passed:
        w, h = Image.open(out / f"{i}.png").size
        cells.append(f'<div class="card" data-id="{i}"><div class="pics">'
                     f'<img src="pixellab/{name}/{i}.png" width="{w * ZOOM}" height="{h * ZOOM}">'
                     f'<img src="pixellab/{name}/{i}.png" width="{w * 2}" height="{h * 2}"></div>'
                     f'<div class="row"><b>{i}</b><button data-mark="keep">Keep</button>'
                     f'<button data-mark="drop">Drop</button></div></div>')
    job = (out / "job.txt").read_text(encoding="utf-8").strip() if (out / "job.txt").exists() else "0"
    html = (PAGE.replace("NAME", name).replace("PASSED", str(len(passed))).replace("TOTAL", str(len(ids)))
            .replace("CELLS", "\n".join(cells)).replace("JOB", job).replace("IDS", ", ".join(map(str, passed))))
    (PREVIEW / "pixellab.html").write_text(html, encoding="utf-8")
    print(f"preview/pixellab.html: {len(passed)} candidates")


if __name__ == "__main__":
    cmd = sys.argv[1:]
    if cmd == ["balance"]:
        balance()
    elif cmd[:1] == ["draw"] and len(cmd) == 2:
        draw(cmd[1])
    elif cmd[:1] == ["page"] and len(cmd) == 2:
        page(cmd[1])
    elif cmd[:1] == ["pick"] and len(cmd) == 3:
        pick(cmd[1], cmd[2])
    else:
        sys.exit(__doc__)
