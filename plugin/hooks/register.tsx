import { atom, read, update } from 'claude-code'
import type { Register, Timer } from 'claude-code'

import type { FerroPhase } from '../types'
import { SCENE_MAX_WIDTH, SCENES, SLEEP_INTRO_MS } from './scene'

// Ferro comes out only when a turn lasts longer than this, so short answers do not flash the band.
const RUN_AFTER_MS = 20_000
// When Claude works for too long, Ferro lies down and falls asleep.
const SLEEP_AFTER_MS = 180_000
const PX_PER_COLUMN = 8
// In about a third of the turns she chases an orange ball.
const BALL_SHARE = 1 / 3

const phase = atom({ plugin: 'cc-mod-ferro', key: 'phase' } as const, null as FerroPhase)
// This turn's background, an index into SCENES: picked at random on every turn.
const scene = atom({ plugin: 'cc-mod-ferro', key: 'scene' } as const, 0)
// This turn's run, an index into the background's programs, also picked per turn. A program is a
// run with its stops (sitting, sniffing, drinking, pooping), drawn in tools/scene.py: SMIL has no randomness.
const program = atom({ plugin: 'cc-mod-ferro', key: 'program' } as const, 0)
// Whether she chases the ball this turn, also picked per turn.
const ball = atom({ plugin: 'cc-mod-ferro', key: 'ball' } as const, false)

export const register: Register = on => {
  let timers: Timer[] = []
  const cancelTimers = () => {
    timers.forEach(t => t.cancel())
    timers = []
  }

  on('turn.start', async ($, e, next) => {
    cancelTimers()
    await update($, phase, () => null)
    const background = Math.floor(Math.random() * SCENES.length)
    await update($, scene, () => background)
    await update($, program, () => Math.floor(Math.random() * SCENES[background].programs.length))
    await update($, ball, () => Math.random() < BALL_SHARE)
    timers = [
      $.clock.after(RUN_AFTER_MS, () => void update($, phase, () => 'run')),
      $.clock.after(SLEEP_AFTER_MS, () => void update($, phase, () => 'sleep')),
      // The band starts a scene from its first frame whenever it draws it anew (reopening the
      // conversation), so once she has lain down she sleeps on in the scene without lying down.
      // It starts where the other one is when she has lain down, so the swap does not show.
      $.clock.after(SLEEP_AFTER_MS + SLEEP_INTRO_MS, () => void update($, phase, () => 'asleep')),
    ]
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    // Subagent turns do not close the band, only the end of the main turn does.
    if (e.agentId === undefined) {
      cancelTimers()
      await update($, phase, () => null)
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // The terminal has no Svg element.
    if (e.surface === 'terminal' || e.props.hasSurvey || !e.props.isWorking) {
      return next(e)
    }
    const now = await read($, phase)
    if (now === null) {
      return next(e)
    }
    // Ferro is only a pastime, so any band drawn beneath her (the files a delete prompt is about,
    // background tasks) goes first and she waits. `{ type: 'engine' }` is the engine's own band,
    // which is empty: nobody beneath has anything to show.
    const beneath = await next(e)
    if (beneath.type !== 'engine') {
      return beneath
    }

    const { Box, Svg } = $.ui.resolve(e)
    const s = SCENES[await read($, scene)] ?? SCENES[0]
    const p = s.programs[await read($, program)] ?? s.programs[0]
    const withBall = await read($, ball)
    // every program of a background shares the head (the meadow and all drawings); the ball is a
    // piece of SVG inserted into the program's body
    const run = s.head + (withBall ? p.body.slice(0, p.ballAt) + p.ball + p.body.slice(p.ballAt) : p.body)
    const runAlt = withBall ? `Ferro chasing an orange ball across ${s.place}` : `Ferro running across ${s.place}`

    // Without an explicit width the frame stays at 300 px. Desktop counts the band in columns
    // of ~8 CSS pixels (measured 4.10.2026: 94 columns, ~753 px). On a narrower band the scene
    // is cropped at the sides and the pixels keep their size.
    const width = Math.min(SCENE_MAX_WIDTH, Math.max(300, e.props.bodyColumns * PX_PER_COLUMN - 8))

    // Drawn as an image (no isInteractive): only then does the band render the PNG frames, and
    // SMIL animates there too.
    return (
      <Box>
        <Svg
          source={now === 'sleep' ? s.sleep : now === 'asleep' ? s.asleep : run}
          alt={now === 'run' ? runAlt : `Ferro asleep on ${s.place}`}
          width={width}
          height={s.height}
        />
      </Box>
    )
  })
}
