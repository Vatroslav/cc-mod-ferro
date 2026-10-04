# mod-ferro

<img src="preview/run.svg" width="100%" alt="Ferro, a pixel-art Norwich Terrier, running across a scrolling meadow">

A Claude Code mod for the Code tab of Claude Desktop. When Claude works on a turn for longer than 20 seconds, a band opens above the prompt and Ferro, a Norwich Terrier, runs across a pixel-art meadow:

- the meadow has three layers (clouds, hills with trees, grass) that scroll at different speeds
- roughly every 40 seconds Ferro stops to poop, and the pile scrolls away with the grass
- after 3 minutes Ferro lies down and falls asleep

<img src="preview/sleep.svg" width="100%" alt="Ferro asleep on the meadow">

When the turn ends, the band disappears. Nothing is interactive, so there is nothing to miss when you are not looking.

## How it is built

**Art.** ChatGPT drew the frames (run, poop, sleep, each as a 6-frame strip on a magenta background) and the meadow. `tools/build.py` turns them into real pixel art: it cuts the frames, removes the magenta, snaps them to a true pixel grid, maps every pixel to a frozen 22-colour palette (`assets/palette.json`, plus reserved colours for the tongue and the eye highlight), cleans the outline and aligns all frames on the ear and the ground line. The sleeping breath is derived in code from one frame, so the pose never jumps.

<img src="assets/ref/ferro-ref.png" width="100%" alt="Reference sheet: Ferro standing and running, the palette and all frames">

**Rendering.** The Desktop band can draw an `Svg` element, but it does not render `<image>` with PNG data, so every frame is converted to vector strokes: one `<path>` per colour, one stroke per horizontal run of pixels, defined once in `<defs>` and placed with `<use>`. All animation is SMIL inside the SVG, so the mod draws the scene once and the browser engine animates it. `tools/scene.py` builds both scenes into `plugin/hooks/scene.ts` and `preview/`.

**Constraints that shaped it.**
- The `Svg` element accepts at most 131,072 characters. The running scene is about 110k and the sleeping scene about 84k.
- The loop is seamless: in one loop the ground travels exactly 20 meadow widths and the hills, at 0.35 of the ground speed, exactly 7.
- ChatGPT returned the gallop frames out of phase order, which made Ferro look like she was running backwards. The real order is `[4, 3, 2, 5, 0]`.

**The mod.** `plugin/hooks/register.tsx` starts two timers on `turn.start` (20 s to run, 3 min to sleep), clears them on the main turn's `turn.complete`, keeps the phase in `$.state` and draws the band with a `ui.render` hook on `AbovePrompt`, only on the desktop surface.

## Install

```bash
claude plugin marketplace add <path-to-this-repo>
claude plugin install mod-ferro@mod-ferro --scope user
```

Function hooks of installed plugins may need `"CLAUDE_CODE_ENABLE_FUNCTION_HOOKS": "1"` in the `env` block of `~/.claude/settings.json`. It works only in the Code tab of Claude Desktop, because the terminal has no `Svg` element.

Check and test: `claude plugin validate ./plugin` and `claude plugin test ./plugin`.
