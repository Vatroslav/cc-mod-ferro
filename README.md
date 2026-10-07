# cc-mod-ferro

<img src="preview/ball-sit.svg" width="100%" alt="Ferro, a pixel-art Norwich Terrier, chasing an orange ball across a scrolling meadow, then sitting down to look at you">

A Claude Code mod for the Code tab of Claude Desktop. When Claude works on a turn for longer than 20 seconds, a band opens above the prompt and Ferro, a Norwich Terrier, runs across a pixel-art meadow. When the turn ends, the band disappears. Nothing is interactive, so there is nothing to miss when you are not looking.

## What Ferro does

Every turn picks a meadow, a program for the run and whether she chases a ball, all at random. A program is a run with a stop every 12 to 22 seconds, the first one 16 seconds in: she sits, sniffs or poops, never the same thing twice in a row and poops at most once. The scenes below have one stop each, 16 seconds in.

**Sits down and looks at you** (the first stop in half of the programs; a short turn sees only that one). She brakes, sits, turns her head to you, blinks, tilts her head, turns back and runs on.

<img src="preview/sit.svg" width="100%" alt="Ferro sits down on the meadow and looks at you">

**Sniffs a spot** (the first stop in a fifth). She slows down with her head lowering, pushes her nose into the grass a few times, lifts her head and runs on.

<img src="preview/sniff.svg" width="100%" alt="Ferro stops and sniffs a spot on the meadow">

**Poops while walking** (the first stop in a fifth), the way the real Ferro does: hunched, walking slowly forward, leaving a row of droppings that scrolls away with the grass.

<img src="preview/run.svg" width="100%" alt="Ferro poops while walking across the meadow">

**Poops in one spot** (the first stop in a tenth), the rare way.

<img src="preview/autumn-run-still.svg" width="100%" alt="Ferro stops and poops in one spot on the autumn meadow">

**Chases an orange ball** (a third of the turns, on top of the above). The ball bounces ahead of her; at every stop it rolls on and waits on the grass until she reaches it, then pops up again.

<img src="preview/autumn-ball-run.svg" width="100%" alt="Ferro chases an orange ball across the autumn meadow">

**Falls asleep** after 3 minutes. She lies down and breathes, and z's rise above her head.

<img src="preview/autumn-sleep.svg" width="100%" alt="Ferro asleep on the autumn meadow">

**The meadow** is summer or autumn, in three layers (clouds, hills with trees, grass) that scroll at different speeds. A winter meadow is built but switched off for now.

<img src="preview/winter-sit.svg" width="100%" alt="Ferro sits down on the winter meadow">

## How it is built

**Art.** ChatGPT drew the frames (run, poop, sleep and sit as 6-frame strips, the hunched walk as a 4-frame strip with three droppings, all on a magenta background) and the three meadows. `tools/build.py` turns them into real pixel art: it cuts the frames, removes the magenta, snaps them to a true pixel grid, maps every pixel to a frozen 22-colour palette (`assets/palette.json`, plus three reserved shades for the tongue and one colour for the eye highlight), cleans the outline, keeps one highlight in each eye and aligns the frames on the ground line and on the ear, or on the front paws where the head turns. ChatGPT drew some strips at a different scale than asked, so each strip has its own factor that gives Ferro the same head size everywhere. The sleeping breath and the blink while she sits are derived in code from one frame, so the pose never jumps. The orange ball is drawn in code. Each meadow is split into its three layers, and the clouds get their own small palette so their light-blue shading survives. Colours the meadow palette misses by far get extra slots, which keeps the brown trunks of the winter trees brown.

<img src="assets/ref/ferro-ref.png" width="100%" alt="Reference sheet for ChatGPT: Ferro standing, running and facing the viewer, the palette and every frame of every animation">

The reference sheet above goes into every ChatGPT request for new frames, so new drawings keep the same Ferro. The instructions and the prompts that produced each strip are in `assets/ref/chatgpt-project.md`.

**Rendering.** The Desktop band can draw an `Svg` element. Every frame and background layer is a small indexed-colour PNG in an `<image>` (data URI), defined once in `<defs>` and placed with `<use>`; `image-rendering="pixelated"` keeps the pixels sharp at 2x. The band renders `<image>` only when the `Svg` is drawn as an image, not in the sandboxed frame (`isInteractive`), so the mod draws it as an image. Until version 0.7.2 every frame was converted to vector strokes (one `<path>` per colour, one stroke per horizontal run of pixels), about six times the size. All animation is SMIL inside the SVG, so the mod draws the scene once and the browser engine animates it. `tools/scene.py` puts a run together from its stops (each kind of stop is one function that says which frames show when and how far the ground moves), draws ten programs per meadow with a fixed seed, since SMIL has no randomness, and writes them with the sleeping scene into `plugin/hooks/scene.ts` and `preview/`.

**Constraints that shaped it.** The facts about Claude Code and the Desktop band behind them, with the build and the date they were last checked, are in [`docs/desktop-band.md`](docs/desktop-band.md).
- The `Svg` element accepts at most 131,072 characters. A run is a head every program of a meadow shares (the meadow and every frame of every stop, about 35k) and the program's own timeline; the largest program with the ball is about 71.6k (winter), and the sleeping scene about 18k. As vector strokes a scene with a single stop was 85k to 118k, and winter with the ball came within 117 characters of the limit, so until the PNG frames each kind of stop was a scene of its own and a turn had one kind.
- The ball is a separate piece of SVG the mod inserts into the plain program, so no program is stored twice.
- The loop is seamless: in one loop the ground travels a whole multiple of 20 meadow widths and the hills, at 0.35 of the ground speed, a whole multiple of 7. The run lasts at most 160 seconds before she falls asleep, so a program's stops fill those 160 seconds and a turn never sees the loop start again.
- ChatGPT returned the gallop frames out of phase order, which made Ferro look like she was running backwards. The real order is `[4, 3, 2, 5, 0]`.

**The mod.** `plugin/hooks/register.tsx` starts two timers on `turn.start` (20 s to run, 3 min to sleep) and picks the turn's meadow, program (one of ten) and ball (one in three), keeping all of it in `$.state`. The timers are cleared on the main turn's `turn.complete`. The band is drawn with a `ui.render` hook on `AbovePrompt`, only on the desktop surface. Ferro is only a pastime, so she gives the band up to any other mod that has something to show there (the files a delete prompt is about, for one): the hook asks the plugins beneath first and draws only when the band would otherwise be empty.

## Install

```bash
claude plugin marketplace add <path-to-this-repo>
claude plugin install cc-mod-ferro@cc-mod-ferro --scope user
```

Function hooks of installed plugins may need `"CLAUDE_CODE_ENABLE_FUNCTION_HOOKS": "1"` in the `env` block of `~/.claude/settings.json`. It works only in the Code tab of Claude Desktop: the band above the prompt exists only there and in the terminal, and the terminal has no `Svg` element.

Check and test: `claude plugin validate ./plugin` and `claude plugin test ./plugin`.
