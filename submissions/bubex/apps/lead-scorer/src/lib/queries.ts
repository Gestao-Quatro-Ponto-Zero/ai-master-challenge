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

// Module-level cache
let pipelineCache: Deal[] | null = null

export async function getPipeline(): Promise<Deal[]> {
  if (!pipelineCache) {
    pipelineCache = await query<Deal>(buildPipelineSQL())
  }
  return pipelineCache
}

export async function getDeal(id: string): Promise<Deal | null> {
  const all = await getPipeline()
  return all.find(d => d.opportunity_id === id) ?? null
}

export async function getTeamStats(): Promise<AgentStats[]> {
  const deals = await getPipeline()

  const byAgent = new Map<string, Deal[]>()
  for (const d of deals) {
    const list = byAgent.get(d.sales_agent) ?? []
    list.push(d)
    byAgent.set(d.sales_agent, list)
  }

  return Array.from(byAgent.entries()).map(([agent, agentDeals]) => {
    const first = agentDeals[0]
    return {
      sales_agent: agent,
      manager: first.manager,
      regional_office: first.regional_office,
      open_deals: agentDeals.length,
      pipeline_value: agentDeals.reduce((s, d) => s + d.sales_price, 0),
      avg_score: Math.round(agentDeals.reduce((s, d) => s + d.score, 0) / agentDeals.length),
      hot_deals: agentDeals.filter(d => d.score >= 70).length,
      warm_deals: agentDeals.filter(d => d.score >= 40 && d.score < 70).length,
      cold_deals: agentDeals.filter(d => d.score < 40).length,
      win_rate_pct: first.win_rate_pct,
    }
  }).sort((a, b) => b.avg_score - a.avg_score)
}
