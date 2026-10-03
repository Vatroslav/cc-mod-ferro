import { atom, read, update } from 'claude-code'
import type { Register, Timer } from 'claude-code'

import type { FerroPhase } from '../types'
import { RUN_SVG, SCENE_HEIGHT, SCENE_MAX_WIDTH, SLEEP_SVG } from './scene'

// Ferro izađe tek kad turn traje dulje od ovoga, da kratki odgovori ne trepću trakom.
const RUN_AFTER_MS = 20_000
// Kad Claude radi predugo, Ferro legne i zaspi.
const SLEEP_AFTER_MS = 180_000
const PX_PER_COLUMN = 8

const phase = atom({ plugin: 'mod-ferro', key: 'phase' } as const, null as FerroPhase)

export const register: Register = on => {
  let timers: Timer[] = []
  const cancelTimers = () => {
    timers.forEach(t => t.cancel())
    timers = []
  }

  on('turn.start', async ($, e, next) => {
    cancelTimers()
    await update($, phase, () => null)
    timers = [
      $.clock.after(RUN_AFTER_MS, () => void update($, phase, () => 'run')),
      $.clock.after(SLEEP_AFTER_MS, () => void update($, phase, () => 'sleep')),
    ]
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    // Turnovi subagenata ne gase traku, samo kraj glavnog turna.
    if (e.agentId === undefined) {
      cancelTimers()
      await update($, phase, () => null)
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // Terminal nema Svg element.
    if (e.surface === 'terminal' || e.props.hasSurvey || !e.props.isWorking) {
      return next(e)
    }
    const now = await read($, phase)
    if (now === null) {
      return next(e)
    }

    const { Box, Svg } = $.ui.resolve(e)

    // Bez zadane širine okvir ostaje na 300 px. Desktop broji traku u stupcima od ~8 CSS
    // piksela (izmjereno 4.10.2026.: 94 stupca, ~753 px). Scena se na užoj traci reže sa
    // strane, a pikseli ostaju iste veličine.
    const width = Math.min(SCENE_MAX_WIDTH, Math.max(300, e.props.bodyColumns * PX_PER_COLUMN - 8))

    return (
      <Box>
        <Svg
          source={now === 'sleep' ? SLEEP_SVG : RUN_SVG}
          alt={now === 'sleep' ? 'Ferro spava na livadi' : 'Ferro trči po livadi'}
          width={width}
          height={SCENE_HEIGHT}
          isInteractive
        />
      </Box>
    )
  })
}
