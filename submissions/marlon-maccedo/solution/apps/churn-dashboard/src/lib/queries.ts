import { csv, query } from '@/lib/db'
import type { ChurnOverview, SegmentBreakdown, ChurnByMonth } from '@/types'

const ACCOUNTS      = csv('ravenstack_accounts.csv')
const SUBSCRIPTIONS = csv('ravenstack_subscriptions.csv')
const CHURN_EVENTS  = csv('ravenstack_churn_events.csv')

// ── Cache ─────────────────────────────────────────────────────────────────────

let overviewCache:  ChurnOverview | null = null
let industryCache:  SegmentBreakdown[] | null = null
let channelCache:   SegmentBreakdown[] | null = null
let planCache:      SegmentBreakdown[] | null = null
let timelineCache:  ChurnByMonth[] | null = null

// ── Shared CTE ────────────────────────────────────────────────────────────────

const WITH_ACCT_MRR = `
  WITH sub_agg AS (
    SELECT account_id, SUM(mrr_amount) AS mrr
    FROM ${SUBSCRIPTIONS}
    GROUP BY account_id
  ),
  acct AS (
    SELECT
      a.account_id,
      a.industry,
      a.referral_source,
      a.plan_tier,
      a.churn_flag,
      COALESCE(s.mrr, 0) AS mrr
    FROM ${ACCOUNTS} a
    LEFT JOIN sub_agg s ON a.account_id = s.account_id
  )
`

// ── Queries ───────────────────────────────────────────────────────────────────

export async function getOverview(): Promise<ChurnOverview> {
  if (overviewCache) return overviewCache

  const rows = await query<Record<string, number>>(`
    ${WITH_ACCT_MRR}
    SELECT
      COUNT(*)                                                       AS total_accounts,
      SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END)            AS churned_accounts,
      SUM(mrr)                                                       AS mrr_total,
      SUM(CASE WHEN churn_flag = TRUE  THEN mrr ELSE 0 END)         AS mrr_churned,
      SUM(CASE WHEN churn_flag = FALSE THEN mrr ELSE 0 END)         AS mrr_retained,
      AVG(CASE WHEN churn_flag = TRUE  THEN mrr END)                AS avg_mrr_churned,
      AVG(CASE WHEN churn_flag = FALSE THEN mrr END)                AS avg_mrr_retained
    FROM acct
  `)

  const r = rows[0]
  const total   = Number(r.total_accounts)
  const churned = Number(r.churned_accounts)

  overviewCache = {
    totalAccounts:   total,
    churnedAccounts: churned,
    churnRate:       total > 0 ? Math.round((churned / total) * 1000) / 10 : 0,
    mrrTotal:        Math.round(Number(r.mrr_total)),
    mrrChurned:      Math.round(Number(r.mrr_churned)),
    mrrRetained:     Math.round(Number(r.mrr_retained)),
    arrTotal:        0, // not in live query — use Python JSON for arr
    avgMrrChurned:   Math.round(Number(r.avg_mrr_churned)),
    avgMrrRetained:  Math.round(Number(r.avg_mrr_retained)),
  }
  return overviewCache
}

export async function getChurnByIndustry(): Promise<SegmentBreakdown[]> {
  if (industryCache) return industryCache

  industryCache = await query<SegmentBreakdown>(`
    ${WITH_ACCT_MRR}
    SELECT
      industry                                                                 AS segment,
      COUNT(*)                                                                 AS total,
      SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END)                      AS churned,
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS "churnRate",
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN mrr ELSE 0 END), 0)          AS "mrrLost"
    FROM acct
    GROUP BY industry
    ORDER BY "churnRate" DESC
  `)
  return industryCache
}

export async function getChurnByChannel(): Promise<SegmentBreakdown[]> {
  if (channelCache) return channelCache

  channelCache = await query<SegmentBreakdown>(`
    ${WITH_ACCT_MRR}
    SELECT
      referral_source                                                          AS segment,
      COUNT(*)                                                                 AS total,
      SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END)                      AS churned,
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS "churnRate",
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN mrr ELSE 0 END), 0)          AS "mrrLost"
    FROM acct
    GROUP BY referral_source
    ORDER BY "churnRate" DESC
  `)
  return channelCache
}

export async function getChurnByPlan(): Promise<SegmentBreakdown[]> {
  if (planCache) return planCache

  planCache = await query<SegmentBreakdown>(`
    ${WITH_ACCT_MRR}
    SELECT
      plan_tier                                                                AS segment,
      COUNT(*)                                                                 AS total,
      SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END)                      AS churned,
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS "churnRate",
      ROUND(SUM(CASE WHEN churn_flag = TRUE THEN mrr ELSE 0 END), 0)          AS "mrrLost"
    FROM acct
    GROUP BY plan_tier
    ORDER BY "churnRate" DESC
  `)
  return planCache
}

export async function getChurnTimeline(): Promise<ChurnByMonth[]> {
  if (timelineCache) return timelineCache

  timelineCache = await query<ChurnByMonth>(`
    SELECT
      LEFT(CAST(churn_date AS VARCHAR), 7)   AS month,
      COUNT(*)                               AS count,
      ROUND(SUM(refund_amount_usd), 0)       AS "mrrLost"
    FROM ${CHURN_EVENTS}
    WHERE is_reactivation = FALSE
    GROUP BY month
    ORDER BY month ASC
  `)
  return timelineCache
}
