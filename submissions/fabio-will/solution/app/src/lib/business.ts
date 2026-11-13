/** Business case math, shared by the interactive panel (client) and the static answers (server). */

export interface Shares {
  auto: number
  assist: number
  autoPrecision: number
}

export interface Inputs {
  volume: number
  triageMin: number
  assistSavedMin: number
  reworkMin: number
  auditShare: number
  auditMin: number
  hourCost: number
}

/** Declared premises. Volume comes from the brief (~30k tickets a year); the rest is stated on the page. */
export const DEFAULT_INPUTS: Inputs = { volume: 2500, triageMin: 3, assistSavedMin: 2, reworkMin: 15, auditShare: 0.02, auditMin: 1, hourCost: 45 }

export const FULL_TIME_HOURS = 160

/** Minutes saved per month. Shares and error rate come from the model; everything else is a declared premise. */
export function savedMinutes(i: Inputs, s: Shares): number {
  const auto = i.volume * s.auto
  const gross = auto * i.triageMin + i.volume * s.assist * i.assistSavedMin
  const rework = auto * (1 - s.autoPrecision) * i.reworkMin
  const audit = auto * i.auditShare * i.auditMin
  return gross - rework - audit
}
