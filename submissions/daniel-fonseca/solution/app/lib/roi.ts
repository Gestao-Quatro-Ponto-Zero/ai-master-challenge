/**
 * Modelo de economia do Painel › ROI (PRD §4.2 e §9). Funções puras, sem dependências, testadas em
 * lib/roi.test.mjs (`node --test lib/roi.test.mjs`).
 *
 * Economia nos casos com autonomia da IA =
 *   volume anual × % elegível (DS1) × % com autonomia (DS2) × minutos por ticket ÷ 60 × custo/hora
 *
 * A economia oficial considera só os casos com autonomia: a revisão humana entra sem ganho (PRD §4.2, C13).
 */

/** Horas de trabalho de um atendente em tempo integral por ano: 38 h/semana × 52 semanas (CAGED, CBO 4223-20). */
export const HOURS_PER_FTE_YEAR = 38 * 52

export interface RoiInputs {
  /** tickets por ano */
  annualVolume: number
  /** minutos de manuseio por ticket */
  handleMinutes: number
  /** custo por hora de atendente, em R$ */
  hourlyCost: number
  /** fração dos tickets elegíveis (DS1) em que a IA teria autonomia (DS2), 0–1 */
  autonomyShare: number
  /** fração dos tickets do DS1 elegíveis para automação, 0–1 */
  eligibleShare: number
}

export interface RoiResult {
  /** fração do volume total resolvida com autonomia da IA (elegível × autonomia) */
  automatedShare: number
  automatedTickets: number
  hoursSaved: number
  savingsBrl: number
  /** atendentes em tempo integral liberados (horas ÷ 1.976) */
  ftesFreed: number
  totalCostBefore: number
  totalCostAfter: number
  costPerTicketBefore: number
  costPerTicketAfter: number
}

/** Limites dos controles da tela (também usados para sanear valores digitados). */
export const ROI_BOUNDS = {
  annualVolume: { min: 1_000, max: 500_000, step: 1_000 },
  handleMinutes: { min: 1, max: 60, step: 0.1 },
  hourlyCost: { min: 5, max: 200, step: 0.1 },
  autonomyShare: { min: 0, max: 1, step: 0.001 },
} as const

const clamp = (n: number, min: number, max: number) => (Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : min)

export function sanitizeInputs(i: RoiInputs): RoiInputs {
  return {
    annualVolume: clamp(i.annualVolume, ROI_BOUNDS.annualVolume.min, ROI_BOUNDS.annualVolume.max),
    handleMinutes: clamp(i.handleMinutes, ROI_BOUNDS.handleMinutes.min, ROI_BOUNDS.handleMinutes.max),
    hourlyCost: clamp(i.hourlyCost, ROI_BOUNDS.hourlyCost.min, ROI_BOUNDS.hourlyCost.max),
    autonomyShare: clamp(i.autonomyShare, 0, 1),
    eligibleShare: clamp(i.eligibleShare, 0, 1),
  }
}

export function computeRoi(raw: RoiInputs): RoiResult {
  const i = sanitizeInputs(raw)
  const automatedShare = i.eligibleShare * i.autonomyShare
  const automatedTickets = i.annualVolume * automatedShare
  const hoursSaved = (automatedTickets * i.handleMinutes) / 60
  const savingsBrl = hoursSaved * i.hourlyCost
  const costPerTicketBefore = (i.handleMinutes / 60) * i.hourlyCost
  const totalCostBefore = costPerTicketBefore * i.annualVolume
  const totalCostAfter = totalCostBefore - savingsBrl
  return {
    automatedShare,
    automatedTickets,
    hoursSaved,
    savingsBrl,
    ftesFreed: hoursSaved / HOURS_PER_FTE_YEAR,
    totalCostBefore,
    totalCostAfter,
    costPerTicketBefore,
    costPerTicketAfter: totalCostAfter / i.annualVolume,
  }
}

/** Formato mínimo das premissas lidas de analysis_metrics (cost_premises e app_summary.roi_inputs). */
export interface PremiseSource {
  annual_ticket_volume: { value: number }
  handle_time_minutes: { value: number }
  agent_hourly_cost_brl: { value: number }
}
export interface RoiInputsSource {
  ds1_eligible_share: number
  ds2_autonomy_share_non_sensitive: number
}

/** Valores padrão da tela a partir dos dados publicados no Supabase. */
export function defaultInputs(premises: PremiseSource, roi: RoiInputsSource): RoiInputs {
  return {
    annualVolume: premises.annual_ticket_volume.value,
    handleMinutes: premises.handle_time_minutes.value,
    hourlyCost: premises.agent_hourly_cost_brl.value,
    autonomyShare: roi.ds2_autonomy_share_non_sensitive,
    eligibleShare: roi.ds1_eligible_share,
  }
}
