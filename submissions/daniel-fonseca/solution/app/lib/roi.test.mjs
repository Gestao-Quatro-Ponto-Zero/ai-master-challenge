// Testes das fórmulas do ROI (PRD §7). Rodar: node --test lib/roi.test.mjs (Node ≥ 23 lê o .ts direto).
import assert from "node:assert/strict"
import { test } from "node:test"

import { computeRoi, defaultInputs, HOURS_PER_FTE_YEAR, sanitizeInputs } from "./roi.ts"

// Valores publicados em analysis_metrics (cost_premises.json e app_summary.json → roi_inputs)
const premises = {
  annual_ticket_volume: { value: 30000 },
  handle_time_minutes: { value: 8.6 },
  agent_hourly_cost_brl: { value: 21.3 },
}
const roiInputs = { ds1_eligible_share: 0.444, ds2_autonomy_share_non_sensitive: 0.4221 }
const near = (actual, expected, tol, msg) => assert.ok(Math.abs(actual - expected) <= tol, `${msg}: ${actual} ≠ ${expected} ± ${tol}`)

test("padrões: ≈ 18,7% de automação, ~810 h e ~R$ 17 mil por ano", () => {
  const r = computeRoi(defaultInputs(premises, roiInputs))
  near(r.automatedShare, 0.1874, 0.0005, "automação total")
  near(r.automatedTickets, 5622, 2, "tickets com autonomia")
  near(r.hoursSaved, 806, 10, "horas por ano")
  near(r.savingsBrl, 17_165, 50, "economia anual")
  assert.ok(r.savingsBrl > 16_500 && r.savingsBrl < 17_500, "economia na faixa de R$ 17 mil")
})

test("atendentes liberados = horas ÷ 1.976", () => {
  assert.equal(HOURS_PER_FTE_YEAR, 1976)
  const r = computeRoi(defaultInputs(premises, roiInputs))
  near(r.ftesFreed, r.hoursSaved / 1976, 1e-9, "FTE")
  near(r.ftesFreed, 0.41, 0.01, "FTE padrão")
})

test("custo por ticket: R$ 3,05 antes e cai na proporção da automação", () => {
  const r = computeRoi(defaultInputs(premises, roiInputs))
  near(r.costPerTicketBefore, 3.05, 0.005, "antes")
  near(r.costPerTicketAfter, 3.053 * (1 - 0.18741), 0.005, "depois")
  near(r.totalCostBefore - r.totalCostAfter, r.savingsBrl, 1e-6, "diferença = economia")
})

test("economia escala linearmente com cada premissa", () => {
  const base = defaultInputs(premises, roiInputs)
  const r1 = computeRoi(base)
  near(computeRoi({ ...base, annualVolume: 60000 }).savingsBrl, 2 * r1.savingsBrl, 1e-6, "volume ×2")
  near(computeRoi({ ...base, handleMinutes: 17.2 }).savingsBrl, 2 * r1.savingsBrl, 1e-6, "minutos ×2")
  near(computeRoi({ ...base, hourlyCost: 42.6 }).savingsBrl, 2 * r1.savingsBrl, 1e-6, "custo/hora ×2")
  assert.equal(computeRoi({ ...base, autonomyShare: 0 }).savingsBrl, 0)
})

test("entradas fora da faixa são saneadas", () => {
  const s = sanitizeInputs({ annualVolume: -5, handleMinutes: Number.NaN, hourlyCost: 1e9, autonomyShare: 1.5, eligibleShare: -1 })
  assert.equal(s.annualVolume, 1000)
  assert.equal(s.handleMinutes, 1)
  assert.equal(s.hourlyCost, 200)
  assert.equal(s.autonomyShare, 1)
  assert.equal(s.eligibleShare, 0)
})
