// What Ferro does in the band: nothing (the band is not shown), runs or sleeps.
export type FerroPhase = 'run' | 'sleep' | null

declare module 'claude-code' {
  interface PluginState {
    // program: which run this turn plays, an index into the background's programs
    'cc-mod-ferro': { phase: FerroPhase; scene: number; program: number; ball: boolean }
  }
}
