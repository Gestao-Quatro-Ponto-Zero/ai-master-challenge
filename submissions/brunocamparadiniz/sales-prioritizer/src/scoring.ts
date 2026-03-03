/**
 * @module scoring
 *
 * Database orchestration layer for deal scoring.
 * Loads all required tables from IndexedDB, builds lookup structures,
 * then delegates computation to the pure functions in services/scoreCalculator.
 *
 * This is the only module in the scoring pipeline that performs async I/O.
 */

import { db, type Account, type Product, type SalesTeam } from './db'
import {
  buildWinRates,
  computeP75DaysToClose,
  computeDealScore,
  type ScoreBreakdown,
  type StagnationInfo,
} from './services/scoreCalculator'

export type { ScoreBreakdown, StagnationInfo }

/** A scored, enriched deal ready for display — joins pipeline + accounts + products + teams. */
export interface ScoredDeal {
  opportunity_id: string
  sales_agent: string
  manager: string
  regional_office: string
  account: string
  sector: string
  product: string
  series: string
  list_price: number
  deal_stage: string
  engage_date: string
  close_date: string
  close_value: number
  score: number
  scoreBreakdown: ScoreBreakdown
  stagnation: StagnationInfo
  justification: string
  /** True when the deal's manager has a win rate above the cross-manager average. */
  managerBonusApplied: boolean
}

/**
 * Loads all pipeline tables from IndexedDB, computes scores for every active deal
 * (Prospecting + Engaging), and returns them sorted by score descending.
 *
 * Steps:
 *   1. Fetch all four tables in parallel.
 *   2. Build win-rate maps and the P75 stagnation threshold from historical data.
 *   3. For each active deal, resolve product/account/team lookups and call `computeDealScore`.
 *   4. Sort results by score descending so the highest-priority deals appear first.
 *
 * @returns Sorted array of ScoredDeal objects.
 */
export async function computeScoredDeals(): Promise<ScoredDeal[]> {
  const [allPipeline, accounts, products, teams] = await Promise.all([
    db.pipeline.toArray(),
    db.accounts.toArray(),
    db.products.toArray(),
    db.sales_teams.toArray(),
  ])

  const accountMap = new Map<string, Account>(accounts.map((a) => [a.account, a]))
  const productMap = new Map<string, Product>(products.map((p) => [p.product, p]))
  const teamMap = new Map<string, SalesTeam>(teams.map((t) => [t.sales_agent, t]))

  const { byAccount, byAgent } = buildWinRates(allPipeline)
  const p75ThresholdDays = computeP75DaysToClose(allPipeline)
  const today = new Date()

  // ── Manager win-rate bonus ──────────────────────────────────────────────────
  // Aggregate Won/Lost counts per manager by joining pipeline rows with teams.
  const byManager: { [manager: string]: { won: number; total: number } } = {}
  for (const row of allPipeline) {
    if (row.deal_stage !== 'Won' && row.deal_stage !== 'Lost') continue
    const team = teamMap.get(row.sales_agent)
    if (!team) continue
    const mgr = team.manager
    if (!byManager[mgr]) byManager[mgr] = { won: 0, total: 0 }
    byManager[mgr].total++
    if (row.deal_stage === 'Won') byManager[mgr].won++
  }

  // Average win rate across managers with at least 5 closed deals (avoids small-sample bias)
  const validMgrEntries = Object.values(byManager).filter((m) => m.total >= 5)
  const avgManagerRate =
    validMgrEntries.length > 0
      ? validMgrEntries.reduce((s, m) => s + m.won / m.total, 0) / validMgrEntries.length
      : 0.5

  return allPipeline
    .filter((r) => r.deal_stage === 'Engaging' || r.deal_stage === 'Prospecting')
    .map((row) => {
      const acct = accountMap.get(row.account)
      const prod = productMap.get(row.product)
      const team = teamMap.get(row.sales_agent)
      const listPrice = prod?.sales_price ?? row.close_value ?? 0

      // +10 bonus when the deal's manager outperforms the cross-manager average
      const mgrData = team ? byManager[team.manager] : null
      const managerBonus =
        mgrData && mgrData.total >= 5 && mgrData.won / mgrData.total > avgManagerRate ? 10 : 0

      const { score, scoreBreakdown, stagnation, justification } = computeDealScore({
        row,
        listPrice,
        byAccount,
        byAgent,
        p75ThresholdDays,
        today,
        managerBonus,
      })

      return {
        opportunity_id: row.opportunity_id,
        sales_agent: row.sales_agent,
        manager: team?.manager ?? '—',
        regional_office: team?.regional_office ?? '—',
        account: row.account,
        sector: acct?.sector ?? '—',
        product: row.product,
        series: prod?.series ?? '—',
        list_price: listPrice,
        deal_stage: row.deal_stage,
        engage_date: row.engage_date,
        close_date: row.close_date,
        close_value: row.close_value,
        score,
        scoreBreakdown,
        stagnation,
        justification,
        managerBonusApplied: managerBonus > 0,
      } satisfies ScoredDeal
    })
    .sort((a, b) => b.score - a.score)
}
