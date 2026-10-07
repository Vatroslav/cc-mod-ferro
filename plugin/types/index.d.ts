// What Ferro does in the band: nothing (the band is not shown), runs, lies down and falls asleep
// ('sleep'), or is already asleep ('asleep', the sleeping scene without lying down).
export type FerroPhase = 'run' | 'sleep' | 'asleep' | null

declare module 'claude-code' {
  interface PluginState {
    // program: which run this turn plays, an index into the background's programs
    'cc-mod-ferro': { phase: FerroPhase; scene: number; program: number; ball: boolean }
  }
}
