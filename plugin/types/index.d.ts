// What Ferro does in the band: nothing (the band is not shown), runs or sleeps.
export type FerroPhase = 'run' | 'sleep' | null
// Which run scene a turn shows: pooping while walking, pooping in one spot, sitting, or sniffing.
export type RunVariant = 'run' | 'runStill' | 'runSit' | 'runSniff'

declare module 'claude-code' {
  interface PluginState {
    'cc-mod-ferro': { phase: FerroPhase; scene: number; variant: RunVariant; ball: boolean }
  }
}
