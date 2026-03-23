// =============================================================================
// ENUMS
// =============================================================================

export type DealStage = 'Prospecting' | 'Engaging' | 'Won' | 'Lost'

export type ActionType =
  | 'PUSH_HARD'
  | 'ACCELERATE'
  | 'MONITOR'
  | 'INVESTIGATE'
  | 'TRANSFER'
  | 'CONSIDER_TRANSFER'
  | 'DISCARD'
  | 'RE_QUALIFY'

export type ViabilityLabel = 'Alta' | 'Média' | 'Baixa'

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface Deal {
  opportunity_id: string
  sales_agent: string
  product: string
  account: string
  deal_stage: DealStage
  close_value: number
  days_in_pipeline: number
  regional_office: string
  score: number
  urgency: number
  probability: number
  value: number
  viability: number
  action: ActionType | null
  /** Texto da ação recomendada (lista GET /deals) */
  message: string
}

export interface DealAction {
  type: ActionType
  message: string
  reason: string
  icon: string
  /** 1 = maior prioridade (varia por ramo da heurística). */
  priority?: number
  details?: Record<string, unknown>
}

export interface DealInfo {
  sales_agent: string
  product: string
  account: string
  close_value: number
  days_in_pipeline: number
  deal_stage: DealStage
  regional_office: string
}

export interface ScoreResult {
  opportunity_id: string
  deal_info: DealInfo
  urgency: number
  probability: number
  value: number
  viability: number
  score: number
  action: DealAction
}

export interface Seller {
  sales_agent: string
  manager: string
  regional_office: string
  win_rate: number
  active_deals: number
  prospecting: number
  avg_ticket: number
  closed_deals: number
  won_deals: number
  viability: number
  viability_label: ViabilityLabel
}

export interface Manager {
  manager: string
  regional_office: string
  n_sellers: number
  avg_win_rate: number
  total_active_deals: number
  total_prospecting: number
  avg_ticket: number
  avg_viability: number
  viability_label: ViabilityLabel
}

export interface Product {
  product: string
  series: string
  sales_price: number
  total_deals: number
  closed_deals: number
  won_deals: number
  win_rate: number
  avg_ticket: number
  avg_cycle_days: number
  active_deals: number
}

export interface Account {
  account: string
  sector: string
  revenue: number
  employees: number
  office_location: string
  subsidiary_of: string | null
  total_deals: number
  won_deals: number
  win_rate: number
  total_won_value: number
  is_top20: boolean
}

export interface Benchmarks {
  global_wr: number
  won_median_days: number
  lost_median_days: number
  engaging_median_days: number
  total_deals: number
  snapshot_date: string
  seller_win_rates: Record<string, number>
  product_win_rates: Record<string, number>
  region_win_rates: Record<string, number>
  top_20_accounts: string[]
}

export interface StageDistribution {
  count: number
  pct: number
}

export interface PipelineSummary {
  total_deals: number
  stages: Record<'Prospecting' | 'Engaging' | 'Won' | 'Lost', StageDistribution>
}

/** Medianas de tempo alinhadas ao filtro Geral / Squad (GET /analysis/pipeline/time-medians) */
export interface PipelineTimeMedians {
  scope: 'geral' | 'squad'
  manager: string | null
  won_median_days: number | null
  lost_median_days: number | null
  engaging_median_days: number | null
  engaging_to_won_ratio: number | null
  cohort_counts: {
    total: number
    won: number
    lost: number
    engaging: number
  }
}

/** GET /analysis/pipeline/win-rate-by-time-bucket */
export interface PipelineWinRateBucketRow {
  bucket: string
  total: number
  won: number
  win_rate: number | null
}

export interface PipelineWinRateByTimeBucket {
  scope: 'geral' | 'squad'
  manager: string | null
  benchmark_global_wr: number | null
  buckets: PipelineWinRateBucketRow[]
  closed_deals_count: number
  scoped_closed_win_rate: number | null
}

export interface ActionDistribution {
  count: number
  pct: number
}

export interface ActionAnalysis {
  total_deals: number
  distribution: Record<ActionType, ActionDistribution>
  by_seller: Record<string, Record<string, number>>
  by_product: Record<string, Record<string, number>>
  by_region: Record<string, Record<string, number>>
}

export interface TransferDeal {
  opportunity_id: string
  sales_agent: string
  product: string
  account: string
  score: number
  viability: number
  action: ActionType
  message: string
  details: Record<string, unknown>
}

export interface TransferAnalysis {
  total_transfers: number
  deals: TransferDeal[]
}

// =============================================================================
// REGIONAL ANALYSIS
// =============================================================================

export interface RegionSummary {
  region: string
  deals_engaging: number
  sellers_count: number
  avg_score: number
  avg_viability: number
  win_rate: number
  total_load: number
  avg_load_per_seller: number
  total_prospecting: number
  avg_prospecting_per_seller: number
  discard_pct: number
  transfer_pct: number
  actions: Record<string, number>
}

export interface LoadImbalance {
  detected: boolean
  ratio?: number
  most_loaded?: { region: string; avg_load_per_seller: number }
  least_loaded?: { region: string; avg_load_per_seller: number }
}

export interface RegionalAnalysis {
  global_wr: number
  regions: RegionSummary[]
  insights: {
    best_region: {
      region: string
      win_rate: number
      avg_score: number
      avg_viability: number
      sellers_count: number
    }
    worst_region: {
      region: string
      win_rate: number
      avg_score: number
      avg_viability: number
      sellers_count: number
    }
    load_imbalance: LoadImbalance
  }
  inter_regional_transfers: {
    total_transfers: number
    inter_regional_count: number
    inter_regional_pct: number
  }
}

export interface RegionalSellerRow {
  sales_agent: string
  deals_engaging: number
  avg_score: number
  avg_viability: number
  total_load: number
  prospecting: number
  win_rate: number
}

export interface RegionalDetail {
  region: string
  deals_engaging: number
  sellers_count: number
  avg_score: number
  avg_viability: number
  sellers: RegionalSellerRow[]
}

// =============================================================================
// PRODUCTS ANALYSIS
// =============================================================================

export interface ProductSummary {
  product: string
  deals_engaging: number
  avg_score: number
  win_rate: number
  avg_ticket: number
  avg_days_engaging: number
  avg_cycle_days_won: number
  cycle_ratio: number | null
  discard_pct: number
  transfer_pct: number
  actions: Record<string, number>
}

export interface ProductSpecialist {
  product: string
  sales_agent: string
  combo_wr: number
  seller_avg_wr: number
  delta: number
}

export interface ProductsAnalysis {
  global_wr: number
  products: ProductSummary[]
  insights: {
    best_product: {
      product: string
      win_rate: number
      avg_ticket: number
      deals_engaging: number
    }
    worst_product: {
      product: string
      win_rate: number
      avg_ticket: number
      deals_engaging: number
    }
    most_stuck: {
      product: string
      avg_days_engaging: number
      avg_cycle_days_won: number
      ratio: number
    } | null
    high_discard_warning: {
      product: string
      discard_pct: number
    } | null
  }
  specialists: ProductSpecialist[]
}

export interface ProductDealRow {
  opportunity_id: string
  label: string
  score: number
  sales_agent: string
  days_in_pipeline: number
  close_value: number
  action: ActionType
}

export interface ProductDetail {
  product: string
  deals_engaging: number
  avg_score: number
  win_rate: number
  delta_vs_global: number
  avg_ticket: number
  deals: ProductDealRow[]
}

// =============================================================================
// FILTER TYPES
// =============================================================================

export interface DealFilters {
  sales_agent?: string
  product?: string
  account?: string
  action?: ActionType
  min_score?: number
  min_days?: number
  all_stages?: boolean
}

export interface SellerFilters {
  region?: string
  viability?: ViabilityLabel
  sort_by?: 'viability' | 'win_rate' | 'active_deals' | 'prospecting'
}

export interface ManagerFilters {
  region?: string
  viability?: ViabilityLabel
  sort_by?: 'avg_viability' | 'avg_win_rate' | 'total_active_deals' | 'total_prospecting'
}

export interface ProductFilters {
  series?: string
  sort_by?: 'win_rate' | 'active_deals' | 'avg_ticket' | 'avg_cycle_days'
}

export interface AccountFilters {
  sector?: string
  office_location?: string
  top20_only?: boolean
  min_deals?: number
  sort_by?: 'total_deals' | 'win_rate' | 'total_won_value' | 'revenue'
}

// =============================================================================
// GLOBAL ALERTS
// =============================================================================

export type AlertSeverity = 'error' | 'warning' | 'info' | 'success'

export interface GlobalAlert {
  key: string
  severity: AlertSeverity
  triggered: boolean
  title: string
  message: string
  data: Record<string, unknown>
}

/** Um recorte de alertas (empresa inteira ou squad de um manager). */
export interface GlobalAlertsScopePayload {
  scope?: 'geral' | 'squad'
  total_alerts: number
  triggered_count: number
  alerts: GlobalAlert[]
}

/** @deprecated Use GlobalAlertsScopePayload */
export type GlobalAlertsResponse = GlobalAlertsScopePayload

export interface GlobalAlertsBundleResponse {
  geral: GlobalAlertsScopePayload
  squad: (GlobalAlertsScopePayload & { manager: string }) | null
}

/** GET /analysis/alerts/seller/{sales_agent} — alertas por vendedor (Engaging). */
export interface SellerAlertsResponse {
  sales_agent: string
  total_alerts: number
  triggered_count: number
  alerts: GlobalAlert[]
}

// =============================================================================
// WON VALUE OVER TIME
// =============================================================================

export interface WonValuePoint {
  date: string
  value: number
  count: number
}

export interface WonValueOverTime {
  sales_agent: string
  date_range: { min: string; max: string } | null
  points: WonValuePoint[]
}
