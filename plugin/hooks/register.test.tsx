import { expect, mock, test } from 'claude-code/testing'

// Tests without a real session: the clock is fake and the test moves it. Under the mod sits the
// test's "Claude Code", which answers the band as the real engine does when no plugin draws it:
// { type: 'engine', ref: 0 }. With `beneath` set it stands for another mod beneath Ferro that has
// something to show (the files of a delete prompt) and draws it as <Text>.

const PLUGIN = 'cc-mod-ferro'

function props(bodyColumns = 94, isWorking = true) {
  return { hasSurvey: false, isWorking, maxRows: 10, bodyColumns, scroll: { offset: 0, bodyRows: 10 }, view: {} }
}

function setup(on: any) {
  const clock = mock.clock(on)
  const below = { text: null as string | null }
  on('turn.start', async ($: any, e: any) => ({ turnId: e.turnId }))
  on('turn.complete', async () => ({ text: '' }))
  on('ui.render', { component: 'AbovePrompt' }, async ($: any, e: any) => {
    if (below.text === null) {
      return { type: 'engine', ref: 0 }
    }
    const { Text } = $.ui.resolve(e)
    return <Text>{below.text}</Text>
  })
  return { clock, below }
}

async function band($: any, surface: 'desktop' | 'terminal' = 'desktop', p = props()) {
  const ui = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: p })
  const svg = await ui.find({ type: 'Svg' })
  const drawn = await ui.drawn()
  await ui.unmount()
  return { svg, drawn, isEngine: drawn.type === 'engine' }
}

const complete = (turnId: string, agentId?: string) => ({
  answer: '', durationMs: 0, isAborted: false, turnId, reason: 'answer', ...(agentId ? { agentId } : {}),
})

test("short turn: for the first 20 s the band is Claude Code's", async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(19_000)
  const { svg, isEngine } = await band($)
  expect(svg).toBeUndefined()
  expect(isEngine).toBe(true)
})

test('after 20 s Ferro runs, after 3 min she sleeps, on the same background', async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(20_000)
  const run = (await band($)).svg?.props.alt
  const place = run.match(/^Ferro (?:running|chasing an orange ball) across (the (?:autumn |winter )?meadow)$/)
  expect(place).not.toBeNull()
  await clock.advance(160_000)
  expect((await band($)).svg?.props.alt).toBe(`Ferro asleep on ${place[1]}`)
})

test('a band drawn beneath Ferro goes first, and she runs again when it is gone', async ($: any, on) => {
  const { clock, below } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  below.text = 'rm: 2 files'
  const held = await band($)
  expect(held.svg).toBeUndefined()
  expect(held.drawn).toMatchObject({ type: 'Text', children: ['rm: 2 files'] })
  below.text = null
  expect((await band($)).svg).toBeDefined()
})

test('the end of the main turn closes the band, the end of a subagent does not', async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  await $.turn.complete(complete('t2', 'agent-1'))
  expect((await band($)).svg).toBeDefined()
  await $.turn.complete(complete('t1'))
  expect((await band($)).svg).toBeUndefined()
  // timers of a finished turn no longer open the band
  await clock.advance(200_000)
  expect((await band($)).svg).toBeUndefined()
})

test("when Claude is not working or in the terminal, the band is not Ferro's", async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  expect((await band($, 'desktop', props(94, false))).svg).toBeUndefined()
  expect((await band($, 'terminal')).svg).toBeUndefined()
})

test('the width follows the band, at most 1280 px', async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  expect((await band($, 'desktop', props(94))).svg?.props.width).toBe(744)
  expect((await band($, 'desktop', props(400))).svg?.props.width).toBe(1280)
  expect((await band($, 'desktop', props(10))).svg?.props.width).toBe(300)
})

test('the scene is drawn as an image: the sandboxed frame does not render the PNG frames', async ($: any, on) => {
  const { clock } = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  const { svg } = await band($)
  expect(svg?.props.source).toContain('<image')
  expect(svg?.props.isInteractive).toBeUndefined()
})

test('the scenes of every background fit the Svg element limit', async () => {
  const { SCENES } = await import('./scene')
  expect(SCENES.length).toBeGreaterThan(0)
  for (const s of SCENES) {
    expect(s.programs.length).toBeGreaterThan(0)
    for (const p of s.programs) {
      expect(s.head.length + p.body.length + p.ball.length).toBeLessThanOrEqual(131072)
      // the ball goes in whole, inside the scene
      const withBall = s.head + p.body.slice(0, p.ballAt) + p.ball + p.body.slice(p.ballAt)
      expect(withBall.startsWith('<svg') && withBall.endsWith('</svg>')).toBe(true)
      expect(withBall).toContain('<use href="#ball"')
    }
    expect(s.sleep.length).toBeLessThanOrEqual(131072)
  }
})

test('every turn picks a program of its background', async ($: any, on) => {
  const { SCENES } = await import('./scene')
  const { clock } = setup(on)
  const seen = new Set<string>()
  for (let i = 0; i < 40; i++) {
    await $.turn.start({ text: 'x', turnId: `t${i}` })
    await clock.advance(20_000)
    const source: string = (await band($)).svg?.props.source
    const k = SCENES.findIndex(s => source.startsWith(s.head))
    expect(k).toBeGreaterThanOrEqual(0)
    const body = source.slice(SCENES[k].head.length)
    const j = SCENES[k].programs.findIndex(
      p => body === p.body || body === p.body.slice(0, p.ballAt) + p.ball + p.body.slice(p.ballAt),
    )
    expect(j).toBeGreaterThanOrEqual(0)
    seen.add(`${k}-${j}`)
    await $.turn.complete(complete(`t${i}`))
  }
  // 40 turns over 2 backgrounds x 10 programs (with or without the ball) do not all play the same run
  expect(seen.size).toBeGreaterThan(1)
})
