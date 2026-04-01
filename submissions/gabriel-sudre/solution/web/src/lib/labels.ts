export const STAGE_LABELS: Record<string, string> = {
  Won: 'Ganho',
  Lost: 'Perdido',
  Engaging: 'Em Negociação',
  Prospecting: 'Prospecção',
}

export function stageLabel(stage: string): string {
  return STAGE_LABELS[stage] || stage
}

export const METRIC_LABELS: Record<string, string> = {
  win_rate: 'Taxa de Conversão',
  avg_ticket: 'Ticket Médio',
  active_deals: 'Oportunidades Ativas',
  at_risk: 'Em Risco',
  total_potential: 'Potencial Total',
  total_won_value: 'Receita Total',
}
