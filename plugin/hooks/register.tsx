import { atom, read, update } from 'claude-code'
import type { Register, Timer } from 'claude-code'

import type { FerroPhase } from '../types'
import { SCENE_MAX_WIDTH, SCENES } from './scene'

// Ferro comes out only when a turn lasts longer than this, so short answers do not flash the band.
const RUN_AFTER_MS = 20_000
// When Claude works for too long, Ferro lies down and falls asleep.
const SLEEP_AFTER_MS = 180_000
const PX_PER_COLUMN = 8

const phase = atom({ plugin: 'mod-ferro', key: 'phase' } as const, null as FerroPhase)
// This turn's background, an index into SCENES: picked at random on every turn.
const scene = atom({ plugin: 'mod-ferro', key: 'scene' } as const, 0)

export const register: Register = on => {
  let timers: Timer[] = []
  const cancelTimers = () => {
    timers.forEach(t => t.cancel())
    timers = []
  }

  on('turn.start', async ($, e, next) => {
    cancelTimers()
    await update($, phase, () => null)
    await update($, scene, () => Math.floor(Math.random() * SCENES.length))
    timers = [
      $.clock.after(RUN_AFTER_MS, () => void update($, phase, () => 'run')),
      $.clock.after(SLEEP_AFTER_MS, () => void update($, phase, () => 'sleep')),
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

    const { Box, Svg } = $.ui.resolve(e)
    const s = SCENES[await read($, scene)] ?? SCENES[0]

    // Without an explicit width the frame stays at 300 px. Desktop counts the band in columns
    // of ~8 CSS pixels (measured 4.10.2026: 94 columns, ~753 px). On a narrower band the scene
    // is cropped at the sides and the pixels keep their size.
    const width = Math.min(SCENE_MAX_WIDTH, Math.max(300, e.props.bodyColumns * PX_PER_COLUMN - 8))

    return (
      <Box>
        <Svg
          source={now === 'sleep' ? s.sleep : s.run}
          alt={now === 'sleep' ? `Ferro asleep on ${s.place}` : `Ferro running across ${s.place}`}
          width={width}
          height={s.height}
          isInteractive
        />
      </Box>
    )
  })
}
