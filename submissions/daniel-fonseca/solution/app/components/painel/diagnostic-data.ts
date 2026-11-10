import "server-only"

import { DIMENSIONS, type DimensionData, type GroupStat, type Interval, type MetricKey, type Overall } from "@/components/painel/diagnostic-types"
import { getDiagnosticCuts, getMetric } from "@/lib/queries/analysis"

/** Payloads de analysis_metrics usados no Diagnóstico (app_summary.json e diagnostic_ci.json). */
export interface AppSummary {
  overview: {
    n: number
    pct_open: number
    pct_pending: number
    pct_closed: number
    n_closed: number
    pct_coherent_closed: number
    hours_median_coherent: number
    csat_mean: number
    csat_ci_low: number
    csat_ci_high: number
  }
  tests: { dimension: string; metric: string; p_value: number; significant: boolean; test: string }[]
  ranking_trap: {
    n_combinations: number
    p_value: number
    worst: { canal: string; prioridade: string; tipo: string; csat: number; n: number }
    best: { canal: string; prioridade: string; tipo: string; csat: number; n: number }
  }
  csat_model: { k: number; r2: number; r2_adj: number }
  roi_inputs: {
    ds1_eligible_share: number
    ds1_eligible_rule: string
    ds2_autonomy_share_all: number
    ds2_autonomy_share_non_sensitive: number
    ds2_autonomy_precision: number
    autonomy_rule: string
    total_autonomy_share: number
  }
}

interface DiagnosticCi {
  rows: { dimension: string; value: string; pct_open_ci: Interval; pct_pending_ci: Interval; hours_ci: Interval; n_coherent: number }[]
  produto_top10: string[]
  produto_outros: {
    groups: number
    n: number
    n_closed: number
    n_coherent: number
    pct_open: number
    pct_open_ci: Interval
    pct_pending: number
    pct_pending_ci: Interval
    csat_mean: number
    csat_ci: Interval
    hours_median_coherent: number
    hours_ci: Interval
  }
}

const TEST_METRIC: Record<string, MetricKey> = {
  pct_open: "pct_open",
  pct_pending: "pct_pending",
  hours_median_coherent: "hours",
  csat_mean: "csat",
}

export async function getDiagnosticData(): Promise<{ summary: AppSummary; dimensions: DimensionData[]; overall: Overall }> {
  const [cuts, summary, ci] = await Promise.all([getDiagnosticCuts(), getMetric<AppSummary>("app_summary"), getMetric<DiagnosticCi>("diagnostic_ci")])
  const ciKey = new Map(ci.rows.map((r) => [`${r.dimension}|${r.value}`, r]))

  const dimensions = DIMENSIONS.map((d): DimensionData => {
    const rows = cuts.filter((c) => c.dimension === d.key)
    let groups: GroupStat[] = rows.map((c) => {
      const x = ciKey.get(`${c.dimension}|${c.value}`)
      return {
        value: c.value,
        n: c.n,
        nClosed: c.n_closed,
        nCoherent: x?.n_coherent ?? 0,
        pct_open: c.pct_open,
        pct_open_ci: x?.pct_open_ci ?? [c.pct_open, c.pct_open],
        pct_pending: c.pct_pending,
        pct_pending_ci: x?.pct_pending_ci ?? [c.pct_pending, c.pct_pending],
        hours: c.hours_median_coherent,
        hours_ci: x?.hours_ci ?? [c.hours_median_coherent, c.hours_median_coherent],
        csat: c.csat_mean,
        csat_ci: [c.csat_ci_low, c.csat_ci_high],
      }
    })
    if (d.key === "produto") {
      const top = new Set(ci.produto_top10)
      const o = ci.produto_outros
      groups = groups.filter((g) => top.has(g.value))
      groups.push({
        value: "Outros",
        isOther: true,
        otherCount: o.groups,
        n: o.n,
        nClosed: o.n_closed,
        nCoherent: o.n_coherent,
        pct_open: o.pct_open,
        pct_open_ci: o.pct_open_ci,
        pct_pending: o.pct_pending,
        pct_pending_ci: o.pct_pending_ci,
        hours: o.hours_median_coherent,
        hours_ci: o.hours_ci,
        csat: o.csat_mean,
        csat_ci: o.csat_ci,
      })
    }
    const tests = { pct_open: null, pct_pending: null, hours: null, csat: null } as DimensionData["tests"]
    for (const t of summary.tests.filter((t) => t.dimension === d.key)) {
      const m = TEST_METRIC[t.metric]
      if (m) tests[m] = { p: t.p_value, significant: t.significant, test: t.test }
    }
    return { ...d, groups, tests, totalGroups: rows.length }
  })

  const o = summary.overview
  return { summary, dimensions, overall: { pct_open: o.pct_open, pct_pending: o.pct_pending, hours: o.hours_median_coherent, csat: o.csat_mean } }
}
