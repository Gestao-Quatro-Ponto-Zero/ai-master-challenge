export interface Deal {
  opportunity_id: string
  sales_agent: string
  product: string
  account: string
  deal_stage: 'Engaging' | 'Prospecting'
  engage_date: string
  sales_price: number
  series: string
  sector: string
  revenue: number
  employees: number
  office_location: string
  manager: string
  regional_office: string
  win_rate_pct: number
  won_count: number
  lost_count: number
  days_in_pipeline: number
  // Score breakdown
  score_stage: number
  score_value: number
  score_account: number
  score_time: number
  score_series: number
  score_agent: number
  score: number
}

export interface AgentStats {
  sales_agent: string
  manager: string
  regional_office: string
  open_deals: number
  pipeline_value: number
  avg_score: number
  hot_deals: number
  warm_deals: number
  cold_deals: number
  win_rate_pct: number
}

export type ScoreLabel = 'hot' | 'warm' | 'cold'

export function scoreLabel(score: number): ScoreLabel {
  if (score >= 70) return 'hot'
  if (score >= 40) return 'warm'
  return 'cold'
}
