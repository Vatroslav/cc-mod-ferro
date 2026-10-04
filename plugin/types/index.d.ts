// What Ferro does in the band: nothing (the band is not shown), runs or sleeps.
export type FerroPhase = 'run' | 'sleep' | null

declare module 'claude-code' {
  interface PluginState {
    'mod-ferro': { phase: FerroPhase; scene: number }
  }
}
