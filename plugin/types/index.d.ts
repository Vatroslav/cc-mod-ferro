// Što Ferro radi u traci: ništa (traka se ne prikazuje), trči ili spava.
export type FerroPhase = 'run' | 'sleep' | null

declare module 'claude-code' {
  interface PluginState {
    'mod-ferro': { phase: FerroPhase }
  }
}
