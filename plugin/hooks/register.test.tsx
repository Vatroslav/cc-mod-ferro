import { expect, mock, test } from 'claude-code/testing'

// Testovi bez prave sesije: sat je lažan i pomiče ga test, a ispod moda stoji "Claude Code"
// testa koji traku crta kao <Text>engine</Text>, pa se vidi kad mod traku ne preuzme.

const PLUGIN = 'mod-ferro'

function props(bodyColumns = 94, isWorking = true) {
  return { hasSurvey: false, isWorking, maxRows: 10, bodyColumns, scroll: { offset: 0, bodyRows: 10 }, view: {} }
}

function setup(on: any) {
  const clock = mock.clock(on)
  on('turn.start', async ($: any, e: any) => ({ turnId: e.turnId }))
  on('turn.complete', async () => ({ text: '' }))
  on('ui.render', { component: 'AbovePrompt' }, async ($: any, e: any) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine</Text>
  })
  return clock
}

async function band($: any, surface: 'desktop' | 'terminal' = 'desktop', p = props()) {
  const ui = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: p })
  const svg = await ui.find({ type: 'Svg' })
  const engine = await ui.find({ type: 'Text', text: 'engine' })
  await ui.unmount()
  return { svg, engine }
}

const complete = (turnId: string, agentId?: string) => ({
  answer: '', durationMs: 0, isAborted: false, turnId, reason: 'answer', ...(agentId ? { agentId } : {}),
})

test('kratki turn: prvih 20 s traka je Claude Codeova', async ($: any, on) => {
  const clock = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(19_000)
  const { svg, engine } = await band($)
  expect(svg).toBeUndefined()
  expect(engine).toBeDefined()
})

test('nakon 20 s Ferro trči, nakon 3 min spava', async ($: any, on) => {
  const clock = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(20_000)
  expect((await band($)).svg?.props.alt).toBe('Ferro trči po livadi')
  await clock.advance(160_000)
  expect((await band($)).svg?.props.alt).toBe('Ferro spava na livadi')
})

test('kraj glavnog turna gasi traku, kraj subagenta ne', async ($: any, on) => {
  const clock = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  await $.turn.complete(complete('t2', 'agent-1'))
  expect((await band($)).svg).toBeDefined()
  await $.turn.complete(complete('t1'))
  expect((await band($)).svg).toBeUndefined()
  // timeri ugašenog turna više ne pale traku
  await clock.advance(200_000)
  expect((await band($)).svg).toBeUndefined()
})

test('kad Claude ne radi ili je u terminalu, traka nije Ferrina', async ($: any, on) => {
  const clock = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  expect((await band($, 'desktop', props(94, false))).svg).toBeUndefined()
  expect((await band($, 'terminal')).svg).toBeUndefined()
})

test('širina prati traku, najviše 1280 px', async ($: any, on) => {
  const clock = setup(on)
  await $.turn.start({ text: 'x', turnId: 't1' })
  await clock.advance(25_000)
  expect((await band($, 'desktop', props(94))).svg?.props.width).toBe(744)
  expect((await band($, 'desktop', props(400))).svg?.props.width).toBe(1280)
  expect((await band($, 'desktop', props(10))).svg?.props.width).toBe(300)
})

test('scene svih pozadina stanu u limit Svg elementa', async () => {
  const { SCENES } = await import('./scene')
  expect(SCENES.length).toBeGreaterThan(0)
  for (const s of SCENES) {
    expect(s.run.length).toBeLessThanOrEqual(131072)
    expect(s.sleep.length).toBeLessThanOrEqual(131072)
    expect(s.run).not.toContain('<image')
  }
})
