import { apiFetch, API_BASE } from './client'
import type {
  ActionAnalysis,
  TransferAnalysis,
  Benchmarks,
  PipelineSummary,
  PipelineTimeMedians,
  PipelineWinRateByTimeBucket,
  RegionalAnalysis,
  RegionalDetail,
  ProductsAnalysis,
  ProductDetail,
  WonValueOverTime,
  GlobalAlertsBundleResponse,
  SellerAlertsResponse,
} from '@/types'

export const fetchActionAnalysis = (): Promise<ActionAnalysis> =>
  apiFetch<ActionAnalysis>('/analysis/actions')

export const fetchTransferAnalysis = (): Promise<TransferAnalysis> =>
  apiFetch<TransferAnalysis>('/analysis/transfers')

export const fetchBenchmarks = (): Promise<Benchmarks> =>
  apiFetch<Benchmarks>('/benchmarks')

export type PipelineSummaryScope = 'geral' | 'squad'

export const fetchPipelineSummary = (params?: {
  scope?: PipelineSummaryScope
  manager?: string
}): Promise<PipelineSummary> => {
  const scope = params?.scope ?? 'geral'
  return apiFetch<PipelineSummary>('/analysis/pipeline', {
    scope,
    ...(scope === 'squad' && params?.manager ? { manager: params.manager } : {}),
  })
}

/** Medianas de dias (Won/Lost/Engaging) no mesmo recorte que o resumo de estágios */
export const fetchPipelineTimeMedians = (params?: {
  scope?: PipelineSummaryScope
  manager?: string
}): Promise<PipelineTimeMedians> => {
  const scope = params?.scope ?? 'geral'
  return apiFetch<PipelineTimeMedians>('/analysis/pipeline/time-medians', {
    scope,
    ...(scope === 'squad' && params?.manager ? { manager: params.manager } : {}),
  })
}

/** Win rate por faixa de dias + contagens Won/Lost (mesmo recorte Geral/Squad) */
export const fetchPipelineWinRateByTimeBucket = (params?: {
  scope?: PipelineSummaryScope
  manager?: string
}): Promise<PipelineWinRateByTimeBucket> => {
  const scope = params?.scope ?? 'geral'
  return apiFetch<PipelineWinRateByTimeBucket>('/analysis/pipeline/win-rate-by-time-bucket', {
    scope,
    ...(scope === 'squad' && params?.manager ? { manager: params.manager } : {}),
  })
}

// =============================================================================
// REGIONAL ANALYSIS
// =============================================================================

export type RegionalProductsScope = 'geral' | 'squad'

/** Overview completo de todas as regiões com insights e transferências inter-regionais */
export const fetchRegionalAnalysis = (params?: {
  scope?: RegionalProductsScope
  manager?: string
}): Promise<RegionalAnalysis> => {
  const scope = params?.scope ?? 'geral'
  return apiFetch<RegionalAnalysis>('/analysis/regional', {
    scope,
    ...(scope === 'squad' && params?.manager ? { manager: params.manager } : {}),
  })
}

/** Drill-down de uma região específica com tabela de vendedores */
export const fetchRegionalDetail = (region: string): Promise<RegionalDetail> =>
  apiFetch<RegionalDetail>(`/analysis/regional/${encodeURIComponent(region)}`)

// =============================================================================
// PRODUCTS ANALYSIS
// =============================================================================

/** Overview completo de todos os produtos com insights, ciclo de tempo e especialistas */
export const fetchProductsAnalysis = (params?: {
  scope?: RegionalProductsScope
  manager?: string
}): Promise<ProductsAnalysis> => {
  const scope = params?.scope ?? 'geral'
  return apiFetch<ProductsAnalysis>('/analysis/products', {
    scope,
    ...(scope === 'squad' && params?.manager ? { manager: params.manager } : {}),
  })
}

/** Drill-down de um produto específico com lista de deals em Engaging */
export const fetchProductDetail = (product: string): Promise<ProductDetail> =>
  apiFetch<ProductDetail>(`/analysis/products/${encodeURIComponent(product)}`)

// =============================================================================
// WON VALUE OVER TIME
// =============================================================================

export const fetchWonValueOverTime = (salesAgent: string): Promise<WonValueOverTime> =>
  apiFetch<WonValueOverTime>('/analysis/sellers/won-value-over-time', { sales_agent: salesAgent })

// =============================================================================
// ALERTS
// =============================================================================

/** Inclui `squad` quando `manager` é informado (mesmo critério de escopo do pipeline). */
export const fetchGlobalAlerts = (params?: { manager?: string }): Promise<GlobalAlertsBundleResponse> =>
  apiFetch<GlobalAlertsBundleResponse>('/analysis/alerts', params?.manager ? { manager: params.manager } : undefined)

/** Alertas do vendedor (prospecção, carga, DISCARD). `null` se 404 (sem deals Engaging). */
export async function fetchSellerAlerts(salesAgent: string): Promise<SellerAlertsResponse | null> {
  const res = await fetch(`${API_BASE}/analysis/alerts/seller/${encodeURIComponent(salesAgent)}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json() as Promise<SellerAlertsResponse>
}
