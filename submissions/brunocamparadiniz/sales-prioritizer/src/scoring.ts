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
  type WinRateMap,
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
  /** True when the account has at least one historical Won deal (+15 pts Account Loyalty). */
  accountLoyaltyApplied: boolean
  /** Win rate (0–1) for the product's series based on closed-deal history. Null = insufficient data. */
  productSeriesWinRate: number | null
  /** True when the deal's sector win rate is above the cross-sector average. */
  isHotSector: boolean
  /** True when the product series win rate is above the cross-series average. */
  isHighConversionProduct: boolean
  /** Win rate (0–1) for the deal's regional office. Null = < 5 closed deals in that region. */
  regionalWinRate: number | null
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

  // ── Reference date: use the most recent engage_date in the dataset ─────────
  // Avoids scores drifting over time if the dataset isn't live-updated.
  const maxEngageTs = allPipeline.reduce((max, r) => {
    if (!r.engage_date) return max
    const t = new Date(r.engage_date).getTime()
    return t > max ? t : max
  }, 0)
  const today = maxEngageTs > 0 ? new Date(maxEngageTs) : new Date()

  // ── Manager win-rate bonus ──────────────────────────────────────────────────
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

  const validMgrEntries = Object.values(byManager).filter((m) => m.total >= 5)
  const avgManagerRate =
    validMgrEntries.length > 0
      ? validMgrEntries.reduce((s, m) => s + m.won / m.total, 0) / validMgrEntries.length
      : 0.5

  // ── Regional win-rate map ──────────────────────────────────────────────────
  // Joins pipeline with sales_teams to get regional_office; requires ≥ 5 closed deals per region.
  const byRegional: WinRateMap = {}
  for (const row of allPipeline) {
    if (row.deal_stage !== 'Won' && row.deal_stage !== 'Lost') continue
    const team = teamMap.get(row.sales_agent)
    if (!team?.regional_office) continue
    const office = team.regional_office
    if (!byRegional[office]) byRegional[office] = { won: 0, total: 0 }
    byRegional[office].total++
    if (row.deal_stage === 'Won') byRegional[office].won++
  }

  // ── Product series win-rate map ─────────────────────────────────────────────
  // Joins pipeline with products to get series; requires ≥ 3 closed deals per series.
  const byProductSeries: WinRateMap = {}
  for (const row of allPipeline) {
    if (row.deal_stage !== 'Won' && row.deal_stage !== 'Lost') continue
    const prod = productMap.get(row.product)
    if (!prod?.series) continue
    const s = prod.series
    if (!byProductSeries[s]) byProductSeries[s] = { won: 0, total: 0 }
    byProductSeries[s].total++
    if (row.deal_stage === 'Won') byProductSeries[s].won++
  }

  const validSeriesEntries = Object.values(byProductSeries).filter((s) => s.total >= 3)
  const avgSeriesWinRate =
    validSeriesEntries.length > 0
      ? validSeriesEntries.reduce((sum, s) => sum + s.won / s.total, 0) / validSeriesEntries.length
      : 0.5

  // ── Sector win-rate map ────────────────────────────────────────────────────
  // Joins pipeline with accounts to get sector; requires ≥ 3 closed deals per sector.
  const bySector: WinRateMap = {}
  for (const row of allPipeline) {
    if (row.deal_stage !== 'Won' && row.deal_stage !== 'Lost') continue
    const acct = accountMap.get(row.account)
    if (!acct?.sector) continue
    const sec = acct.sector
    if (!bySector[sec]) bySector[sec] = { won: 0, total: 0 }
    bySector[sec].total++
    if (row.deal_stage === 'Won') bySector[sec].won++
  }

  const validSectorEntries = Object.values(bySector).filter((s) => s.total >= 3)
  const avgSectorWinRate =
    validSectorEntries.length > 0
      ? validSectorEntries.reduce((sum, s) => sum + s.won / s.total, 0) / validSectorEntries.length
      : 0.5

  return allPipeline
    .filter((r) => r.deal_stage === 'Engaging' || r.deal_stage === 'Prospecting')
    .map((row) => {
      const acct = accountMap.get(row.account)
      const prod = productMap.get(row.product)
      const team = teamMap.get(row.sales_agent)
      const listPrice = prod?.sales_price ?? row.close_value ?? 0
      const series = prod?.series ?? '—'

      // Manager bonus: +10 when manager outperforms cross-manager average
      const mgrData = team ? byManager[team.manager] : null
      const managerBonus =
        mgrData && mgrData.total >= 5 && mgrData.won / mgrData.total > avgManagerRate ? 10 : 0

      // Account Loyalty: +15 when account has at least one Won deal in history
      const acctHistory = byAccount[row.account]
      const accountLoyaltyBonus = acctHistory?.won > 0 ? 15 : 0

      // Product series win rate (null if series has < 3 closed deals)
      const seriesData = byProductSeries[series]
      const seriesWinRate = seriesData && seriesData.total >= 3 ? seriesData.won / seriesData.total : null

      // Regional win rate (null if < 5 closed deals in the region)
      const regionalData = team ? byRegional[team.regional_office] : null
      const regionalWinRate = regionalData && regionalData.total >= 5 ? regionalData.won / regionalData.total : null

      // Sector & series badges
      const sectorData = acct ? bySector[acct.sector] : null
      const isHotSector =
        sectorData && sectorData.total >= 3 ? sectorData.won / sectorData.total > avgSectorWinRate : false
      const isHighConversionProduct =
        seriesWinRate !== null ? seriesWinRate > avgSeriesWinRate : false

      const { score, scoreBreakdown, stagnation, justification } = computeDealScore({
        row,
        listPrice,
        byAccount,
        byAgent,
        p75ThresholdDays,
        today,
        managerBonus,
        series,
        seriesWinRate,
        accountLoyaltyBonus,
        regionalWinRate,
        regionalOffice: team?.regional_office ?? '—',
      })

      return {
        opportunity_id: row.opportunity_id,
        sales_agent: row.sales_agent,
        manager: team?.manager ?? '—',
        regional_office: team?.regional_office ?? '—',
        account: row.account,
        sector: acct?.sector ?? '—',
        product: row.product,
        series,
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
        accountLoyaltyApplied: accountLoyaltyBonus > 0,
        productSeriesWinRate: seriesWinRate,
        isHotSector,
        isHighConversionProduct,
        regionalWinRate,
      } satisfies ScoredDeal
    })
    .sort((a, b) => b.score - a.score)
}
