import { FAR_BASE, PROPS, SCENES, SVG_LIMIT } from './scene'

type Scene = (typeof SCENES)[number]
type Program = Scene['programs'][number]

// What stands in each slot of a run this turn: an index into PROPS, -1 for an empty slot.
export type PropPicks = { ground: number[]; far: number[] }

// The prop a slot gets for a roll in [0, 1), by the chances in percent; -1 for none (what is left
// to 100). tools/scene.py does the same for its previews (pick_prop).
export function pickProp(where: 'ground' | 'far', roll: number): number {
  let r = roll * 100
  for (let i = 0; i < PROPS.length; i++) {
    if (PROPS[i].where !== where) continue
    r -= PROPS[i].chance
    if (r < 0) return i
  }
  return -1
}

export function pickProps(p: Program, random: () => number = Math.random): PropPicks {
  return { ground: p.slots.map(() => pickProp('ground', random())), far: p.far.map(() => pickProp('far', random())) }
}

const use = (i: number, x: number, bottom: number) =>
  `<use href="#prop-${PROPS[i].name}" x="${x}" y="${bottom - PROPS[i].h + 1}"/>`

function compose(s: Scene, p: Program, withBall: boolean, picks: PropPicks): string {
  let far = ''
  let behind = ''
  let front = ''
  p.far.forEach((x, k) => {
    const i = picks.far[k] ?? -1
    if (i >= 0) far += use(i, x, FAR_BASE)
  })
  p.slots.forEach(([x, bottom, inFront], k) => {
    const i = picks.ground[k] ?? -1
    if (i < 0) return
    if (inFront) front += use(i, x, bottom)
    else behind += use(i, x, bottom)
  })
  const pieces: [number, string][] = [
    [p.marks[0], far],
    [p.marks[1], behind],
    [p.marks[2], front],
  ]
  if (withBall) pieces.push([p.ballAt, p.ball])
  // from the last index to the first, so each index still points into the program's body
  let body = p.body
  for (const [at, piece] of pieces.sort((a, b) => b[0] - a[0])) {
    body = body.slice(0, at) + piece + body.slice(at)
  }
  const used = [...new Set([...picks.ground, ...picks.far].filter(i => i >= 0))].sort((a, b) => a - b)
  const defs = used.map(i => PROPS[i].def).join('')
  return s.head + (defs ? `<defs>${defs}</defs>` : '') + body
}

// The run of a turn: the background's head, the program's body, the ball and the props picked for
// it. Should the props ever take a run over the Svg limit, the last ones are left out until it fits.
export function runScene(s: Scene, p: Program, withBall: boolean, picks: PropPicks): string {
  let ground = picks.ground.slice()
  let far = picks.far.slice()
  let run = compose(s, p, withBall, { ground, far })
  while (run.length > SVG_LIMIT) {
    const g = ground.findLastIndex(i => i >= 0)
    const f = far.findLastIndex(i => i >= 0)
    if (g < 0 && f < 0) break
    if (g >= 0) ground = ground.map((i, k) => (k === g ? -1 : i))
    else far = far.map((i, k) => (k === f ? -1 : i))
    run = compose(s, p, withBall, { ground, far })
  }
  return run
}
