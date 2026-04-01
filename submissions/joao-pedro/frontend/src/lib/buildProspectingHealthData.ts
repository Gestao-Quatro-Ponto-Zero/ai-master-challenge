import type { ProspectingHealthDatum } from '@/components/charts/ProspectingHealthHorizontalChart'
import type { PipelineSummaryScope } from '@/api/analysis'
import type { Seller } from '@/types'

function pctOfTeam(count: number, total: number) {
  if (total <= 0) return 0
  return Math.round((count / total) * 1000) / 10
}

/**
 * Séries do gráfico "Saúde do Pipeline: Prospecting" (Pipeline Analysis / Macro Analysis).
 * Recorte alinhado ao toggle Geral vs Squad do manager.
 */
export function buildProspectingHealthData(
  sellers: Seller[],
  scope: PipelineSummaryScope,
  managerName?: string,
): ProspectingHealthDatum[] {
  const team =
    scope === 'squad' && managerName ? sellers.filter((s) => s.manager === managerName) : sellers
  const total = team.length
  if (total === 0) return []

  const noProsp = team.filter((s) => s.prospecting === 0).length
  const overloaded = team.filter((s) => s.active_deals > 100).length
  const both = team.filter((s) => s.prospecting === 0 && s.active_deals > 100).length

  return [
    {
      id: 'no_prospecting',
      label: 'Sem prospecting',
      tooltipTitle: 'Vendedores sem prospecting',
      pct: pctOfTeam(noProsp, total),
      count: noProsp,
      total,
    },
    {
      id: 'overloaded',
      label: 'Sobrecarga >100',
      tooltipTitle:
        'Vendedores sobrecarregados: mais de 100 deals ativos (Prospecção + Engajamento)',
      pct: pctOfTeam(overloaded, total),
      count: overloaded,
      total,
    },
    {
      id: 'both',
      label: 'Sobrecarga + sem prosp.',
      tooltipTitle: 'Sobrecarga + sem prospecting — ciclo travado',
      pct: pctOfTeam(both, total),
      count: both,
      total,
    },
  ]
}
