---
verified:
  - by: claude/opus-5.5
    at: 2026-10-06T11:15:00+02:00
    how: >-
      Claude Code 2.1.288 (the build Desktop ran): plugin API types written by the plugin-authoring
      skill and the binary; ~/.claude.json; claude plugin validate and test of ./plugin; the .in_use
      marker of this session's process; a probe mod in the Desktop band, read by Vatra
  - by: claude/opus-5.5
    at: 2026-10-06T21:30:00+02:00
    how: >-
      Claude Code 2.1.288 in Desktop: a second probe mod (hot reload) drew Ferro's summer sitting
      scene from PNG frames without isInteractive above the same scene in vector strokes with it;
      Vatra compared the two in the band
  - by: human:vatra
    at: 2026-10-07T16:10:00+02:00
    how: >-
      In Desktop: Ferro, already asleep in a conversation, lay down again from the standing frame
      every time he opened that conversation
  - by: human:vatra
    at: 2026-10-15T09:45:00+02:00
    how: >-
      In Desktop (Claude Code 2.1.295), a new session with the installed 0.15.0: the band's
      dismiss Button showed and closing it worked
  - by: human:vatra
    at: 2026-10-16T11:24:00+02:00
    how: >-
      Screenshot of the Desktop band (Claude Code 2.1.299) with the installed 0.15.0 and
      cc-mod-running-task 0.1.1: the scene, the running-task row below it in the same band, and a
      plain "Close" button cut off at the band's right edge
stale_after: 2026-12-06T00:00:00+01:00
---

# The Desktop band: what this mod relies on

Facts about Claude Code and the Code tab of Claude Desktop that the mod and the README depend on.
Checked on Claude Code 2.1.288, the build Desktop ran on 6.10.2026. Claude Code ships new builds
every few days, so check again when the mod misbehaves after an update.

## The `Svg` element

- Every remote surface draws it: Desktop, the mobile app and VS Code. The terminal has no `Svg`.
- `source` is the whole SVG document, at most 131,072 characters.
- Without `isInteractive` the surface draws it as an image; with it, in a script-less sandboxed
  frame (hover, tooltips). Since 0.7.3 the mod draws it as an image; until 0.7.2 it set
  `isInteractive`.
- **`<image>` with a PNG data URI renders only without `isInteractive`** (probe, 6.10.2026). In the
  sandboxed frame it draws nothing, which is why Ferro's frames were vector strokes until 0.7.2.
  Drawn as an image, the PNG shows.
- **SMIL animates in both modes** (`animateTransform` in the same probe). The types name SMIL as a
  reason for `isInteractive`, but the image mode animated it too.
- **Ferro's own scene from PNG frames, drawn as an image, looks the same as the vector one**
  (second probe, 6.10.2026, read by Vatra): the summer sitting scene with the ball, every layer
  and frame an `<image>` with a PNG data URI in `<defs>`, placed with `<use>`, and
  `image-rendering="pixelated"` on the root `<svg>`. Shown above the same scene in vector strokes
  with `isInteractive`, it was as sharp and as wide. That scene is 30,674 characters as PNG and
  120,006 as vector strokes.
- In the first probe (a small test drawing), the image-mode `Svg` came out wider than the `width`
  it was given. With Ferro's scene and the same `width` and `height` as the mod passes, it did not.
- Scrolling the band restarted the animation in both modes (second probe): the image mode is no
  worse than the sandboxed frame here. Opening a conversation again restarts it too (Vatra,
  7.10.2026), so the mod swaps in a sleeping scene without lying down once she has lain down.

## The band above the prompt

- `ui.render` on `AbovePrompt` is raised on the terminal and desktop surfaces only. With no `Svg`
  in the terminal, the mod works only in the Code tab of Desktop.
- A `Button` with `role="dismiss"` beside the `Svg` (0.15.0) gives the band a close control in
  Desktop; Vatra used it on 15.10.2026 (2.1.295). On 16.10.2026 (2.1.299), with cc-mod-running-task
  wrapping her tree in its own `Box`, Desktop drew it inline as a plain "Close" button beside the
  scene instead, cut off at the band's right edge. Not separated: the wrapping or the new build.
  The types say only that a desktop draws its close control "at the site's trailing edge".
- `bodyColumns` is the band's width less the engine's five columns at the right end, which hold
  its `[-]` (types, 2.1.299).
- The order of installed plugins in the `ui.render` chain is not defined by the types. On
  16.10.2026 cc-mod-running-task was above Ferro (its rows below her scene in one band). The `claude` 2.1.281 on the PATH drops `role`
  in `claude plugin test`.
- The engine draws nothing of its own in the band. When `next(e)` resolves to
  `{ type: 'engine', ref }`, no plugin beneath drew anything, and Ferro may draw.

## Function hooks of installed plugins

- They sit behind the rollout switch `tengu_plugin_hooks_modules`. In 2.1.288 its default is on,
  and on 6.10.2026 Vatra's account had it on (`~/.claude.json`); on 4.10.2026 it was off.
- `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS` is a setting the 2.1.288 binary knows. On 4.10.2026, with the
  switch off, setting it to `"1"` in the `env` block of `~/.claude/settings.json` made the installed
  mod run. With the switch on it was not tested whether the setting is still needed.

## Installing

- `claude plugin install` copies the plugin into
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Each process that runs a version
  leaves a file named by its PID in that version's `.in_use/`: on 6.10.2026 a new Desktop session
  ran the installed 0.7.2 that way, without hot reload.
- `claude plugin marketplace add <source>` takes a URL, a path or a GitHub repo, and
  `claude plugin install --scope` takes `user`, `project` or `local`. The terminal `claude` on
  Vatra's PATH was 2.1.281, older than Desktop's own 2.1.288.
