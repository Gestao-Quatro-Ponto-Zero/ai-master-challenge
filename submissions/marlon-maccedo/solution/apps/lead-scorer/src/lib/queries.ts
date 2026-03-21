import { csv, query } from '@/lib/db'
import type { Deal, AgentStats } from '@/types'

// Dataset is historical (2016-2017). Reference date = end of dataset.
const REF_DATE = `DATE '2017-12-31'`

function buildPipelineSQL(whereExtra = ''): string {
  return `
WITH agent_stats AS (
  SELECT
    sales_agent,
    COUNT(*) FILTER (WHERE deal_stage = 'Won')  AS won_count,
    COUNT(*) FILTER (WHERE deal_stage = 'Lost') AS lost_count,
    ROUND(
      COUNT(*) FILTER (WHERE deal_stage = 'Won') * 100.0 /
      NULLIF(COUNT(*) FILTER (WHERE deal_stage IN ('Won', 'Lost')), 0)
    , 1) AS win_rate_pct
  FROM ${csv('sales_pipeline.csv')}
  GROUP BY sales_agent
)
SELECT
  p.opportunity_id,
  p.sales_agent,
  p.product,
  p.account,
  p.deal_stage,
  CAST(p.engage_date AS VARCHAR)              AS engage_date,
  CAST(pr.sales_price AS INTEGER)             AS sales_price,
  pr.series,
  a.sector,
  ROUND(CAST(a.revenue AS DOUBLE), 2)         AS revenue,
  CAST(a.employees AS INTEGER)                AS employees,
  a.office_location,
  t.manager,
  t.regional_office,
  ROUND(COALESCE(ast.win_rate_pct, 62.5), 1)  AS win_rate_pct,
  COALESCE(ast.won_count,  0)                 AS won_count,
  COALESCE(ast.lost_count, 0)                 AS lost_count,
  DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) AS days_in_pipeline,

  -- Score breakdown (for explainability)
  CASE p.deal_stage
    WHEN 'Engaging'    THEN 30
    WHEN 'Prospecting' THEN 15
    ELSE 0
  END AS score_stage,

  CASE
    WHEN pr.sales_price >= 4000 THEN 25
    WHEN pr.sales_price >= 1000 THEN 15
    WHEN pr.sales_price >= 500  THEN 8
    ELSE 3
  END AS score_value,

  CASE
    WHEN CAST(a.revenue AS DOUBLE) > 2741 THEN 20
    WHEN CAST(a.revenue AS DOUBLE) > 1224 THEN 14
    WHEN CAST(a.revenue AS DOUBLE) > 497  THEN 8
    ELSE 4
  END AS score_account,

  CASE
    WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 300 THEN -15
    WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 200 THEN -10
    WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 120 THEN  -5
    ELSE 0
  END AS score_time,

  CASE pr.series
    WHEN 'GTK' THEN 15
    WHEN 'GTX' THEN 8
    ELSE 0
  END AS score_series,

  ROUND(LEAST(10, GREATEST(0,
    (COALESCE(ast.win_rate_pct, 62.5) - 55) / 15.0 * 10
  )), 1) AS score_agent,

  -- Final score (clamped 0-100)
  GREATEST(0, LEAST(100,
    CASE p.deal_stage WHEN 'Engaging' THEN 30 WHEN 'Prospecting' THEN 15 ELSE 0 END
    + CASE WHEN pr.sales_price >= 4000 THEN 25 WHEN pr.sales_price >= 1000 THEN 15 WHEN pr.sales_price >= 500 THEN 8 ELSE 3 END
    + CASE WHEN CAST(a.revenue AS DOUBLE) > 2741 THEN 20 WHEN CAST(a.revenue AS DOUBLE) > 1224 THEN 14 WHEN CAST(a.revenue AS DOUBLE) > 497 THEN 8 ELSE 4 END
    + CASE WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 300 THEN -15 WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 200 THEN -10 WHEN DATE_DIFF('day', CAST(p.engage_date AS DATE), ${REF_DATE}) > 120 THEN -5 ELSE 0 END
    + CASE pr.series WHEN 'GTK' THEN 15 WHEN 'GTX' THEN 8 ELSE 0 END
    + ROUND(LEAST(10, GREATEST(0, (COALESCE(ast.win_rate_pct, 62.5) - 55) / 15.0 * 10)), 1)
  )) AS score

FROM ${csv('sales_pipeline.csv')} p
-- 'GTXPro' in pipeline doesn't match 'GTX Pro' in products — normalize on join
LEFT JOIN ${csv('products.csv')}    pr  ON REPLACE(p.product, 'GTXPro', 'GTX Pro') = pr.product
LEFT JOIN ${csv('accounts.csv')}    a   ON p.account     = a.account
LEFT JOIN ${csv('sales_teams.csv')} t   ON p.sales_agent = t.sales_agent
LEFT JOIN agent_stats               ast ON p.sales_agent = ast.sales_agent
WHERE p.deal_stage IN ('Prospecting', 'Engaging')
${whereExtra}
ORDER BY score DESC, pr.sales_price DESC
`
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface PipelineParams {
  page?: number
  pageSize?: number
  sort?: keyof Deal
  order?: 'asc' | 'desc'
  q?: string
  stage?: string
  region?: string
  agent?: string
}

export interface PipelinePage {
  deals: Deal[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  // for filter dropdowns
  regions: string[]
  agents: string[]
}

// ── Module-level cache ────────────────────────────────────────────────────────

let pipelineCache: Deal[] | null = null

async function getAllDeals(): Promise<Deal[]> {
  if (!pipelineCache) {
    pipelineCache = await query<Deal>(buildPipelineSQL())
  }
  return pipelineCache
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function queryPipeline(params: PipelineParams = {}): Promise<PipelinePage> {
  const {
    page = 1,
    pageSize = 50,
    sort = 'score',
    order = 'desc',
    q = '',
    stage = 'all',
    region = 'all',
    agent = 'all',
  } = params

  const all = await getAllDeals()

  // Filter
  let filtered = all
  if (stage !== 'all') filtered = filtered.filter(d => d.deal_stage === stage)
  if (region !== 'all') filtered = filtered.filter(d => d.regional_office === region)
  if (agent !== 'all') filtered = filtered.filter(d => d.sales_agent === agent)
  if (q) {
    const term = q.toLowerCase()
    filtered = filtered.filter(d =>
      (d.account ?? '').toLowerCase().includes(term) ||
      (d.sales_agent ?? '').toLowerCase().includes(term) ||
      (d.product ?? '').toLowerCase().includes(term) ||
      (d.opportunity_id ?? '').toLowerCase().includes(term)
    )
  }

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    const av = a[sort as keyof Deal] as number | string
    const bv = b[sort as keyof Deal] as number | string
    const cmp = av < bv ? -1 : av > bv ? 1 : 0
    return order === 'desc' ? -cmp : cmp
  })

  // Paginate
  const total = sorted.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, totalPages)
  const offset = (safePage - 1) * pageSize
  const deals = sorted.slice(offset, offset + pageSize)

  // Dropdown options (from full dataset, not filtered)
  const regions = [...new Set(all.map(d => d.regional_office))].sort()
  const agents = [...new Set(all.map(d => d.sales_agent))].sort()

  return { deals, total, page: safePage, pageSize, totalPages, regions, agents }
}

export async function getDeal(id: string): Promise<Deal | null> {
  const all = await getAllDeals()
  return all.find(d => d.opportunity_id === id) ?? null
}

export async function getTeamStats(): Promise<AgentStats[]> {
  const deals = await getAllDeals()

  const byAgent = new Map<string, Deal[]>()
  for (const d of deals) {
    ;(byAgent.get(d.sales_agent) ?? (byAgent.set(d.sales_agent, []), byAgent.get(d.sales_agent)!)).push(d)
  }

  return Array.from(byAgent.entries()).map(([agent, agentDeals]) => {
    const first = agentDeals[0]
    return {
      sales_agent: agent,
      manager: first.manager,
      regional_office: first.regional_office,
      open_deals: agentDeals.length,
      pipeline_value: agentDeals.reduce((s, d) => s + (d.sales_price ?? 0), 0),
      avg_score: Math.round(agentDeals.reduce((s, d) => s + d.score, 0) / agentDeals.length),
      hot_deals: agentDeals.filter(d => d.score >= 70).length,
      warm_deals: agentDeals.filter(d => d.score >= 40 && d.score < 70).length,
      cold_deals: agentDeals.filter(d => d.score < 40).length,
      win_rate_pct: first.win_rate_pct,
    }
  }).sort((a, b) => b.avg_score - a.avg_score)
}

/** Used by /team/[agent] page */
export async function getAgentDeals(agentName: string): Promise<Deal[]> {
  const all = await getAllDeals()
  return all.filter(d => d.sales_agent === agentName)
}

// ── Dashboard stats ───────────────────────────────────────────────────────────

function groupBy<T>(arr: T[], key: (item: T) => string): Map<string, T[]> {
  const map = new Map<string, T[]>()
  for (const item of arr) {
    const k = key(item)
    const existing = map.get(k)
    if (existing) existing.push(item)
    else map.set(k, [item])
  }
  return map
}

export interface DashboardStats {
  total: number
  pipelineValue: number
  hot: number
  warm: number
  cold: number
  avgScore: number
  engaging: number
  prospecting: number
  byRegion: { region: string; deals: number; value: number }[]
  byProduct: { product: string; deals: number; value: number }[]
  byAging: { label: string; deals: number }[]
  topAgents: { agent: string; avgScore: number; hot: number; deals: number }[]
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const all = await getAllDeals()

  const hot  = all.filter(d => d.score >= 70).length
  const warm = all.filter(d => d.score >= 40 && d.score < 70).length
  const cold = all.filter(d => d.score < 40).length
  const pipelineValue = all.reduce((s, d) => s + (d.sales_price ?? 0), 0)
  const avgScore = Math.round(all.reduce((s, d) => s + d.score, 0) / all.length)
  const engaging    = all.filter(d => d.deal_stage === 'Engaging').length
  const prospecting = all.filter(d => d.deal_stage === 'Prospecting').length

  const regionMap = groupBy(all, d => d.regional_office ?? 'N/A')
  const byRegion = Array.from(regionMap.entries())
    .map(([region, deals]) => ({
      region,
      deals: deals.length,
      value: deals.reduce((s, d) => s + (d.sales_price ?? 0), 0),
    }))
    .sort((a, b) => b.value - a.value)

  const productMap = groupBy(all, d => d.product ?? 'N/A')
  const byProduct = Array.from(productMap.entries())
    .map(([product, deals]) => ({
      product,
      deals: deals.length,
      value: deals.reduce((s, d) => s + (d.sales_price ?? 0), 0),
    }))
    .sort((a, b) => b.value - a.value)

  const agingBuckets = [
    { label: '0–60 dias',  test: (d: Deal) => d.days_in_pipeline <= 60 },
    { label: '61–120 dias', test: (d: Deal) => d.days_in_pipeline > 60  && d.days_in_pipeline <= 120 },
    { label: '121–200 dias', test: (d: Deal) => d.days_in_pipeline > 120 && d.days_in_pipeline <= 200 },
    { label: '200+ dias',  test: (d: Deal) => d.days_in_pipeline > 200 },
  ]
  const byAging = agingBuckets.map(b => ({
    label: b.label,
    deals: all.filter(b.test).length,
  }))

  const agentMap = groupBy(all, d => d.sales_agent)
  const topAgents = Array.from(agentMap.entries())
    .map(([agent, deals]) => ({
      agent,
      avgScore: Math.round(deals.reduce((s, d) => s + d.score, 0) / deals.length),
      hot: deals.filter(d => d.score >= 70).length,
      deals: deals.length,
    }))
    .sort((a, b) => b.avgScore - a.avgScore)
    .slice(0, 10)

  return {
    total: all.length, pipelineValue, hot, warm, cold, avgScore,
    engaging, prospecting, byRegion, byProduct, byAging, topAgents,
  }
}
