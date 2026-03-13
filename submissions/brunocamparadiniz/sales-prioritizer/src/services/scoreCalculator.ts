/**
 * @module scoreCalculator
 *
 * Pure scoring functions for deal prioritization.
 * No database access, no React — fully unit-testable.
 *
 * Composite score formula (weights sum to 100%):
 *   score = winRate×0.40 + recency×0.25 + valueEfficiency×0.20 + stageWeight×0.15
 *
 * Stagnation penalty: −20% applied after composition when an Engaging deal
 * has been open longer than the P75 days-to-close of historical Won deals.
 */

import type { PipelineRow } from '../db'

// ─── Shared types ────────────────────────────────────────────────────────────

/** Accumulated won/total counts per key (account or agent). */
export interface WinRateMap {
  [key: string]: { won: number; total: number }
}

/** The four scored components that make up the composite score. */
export interface ScoreBreakdown {
  /** Win rate contribution (weight 40%). */
  winRate: number
  /** Recency contribution (weight 25%). */
  recency: number
  /** Value-efficiency contribution (weight 20%). */
  valueEfficiency: number
  /** Pipeline-stage contribution (weight 15%). */
  stageWeight: number
}

/** Whether a deal has stalled past the P75 healthy-close threshold. */
export interface StagnationInfo {
  isStagnant: boolean
  /** Days since engage_date (calendar days to today). */
  daysEngaging: number
  /** P75 days-to-close derived from historical Won deals. */
  p75ThresholdDays: number
}

/** All inputs needed to score a single pipeline row (no DB calls). */
export interface DealScoreInput {
  row: Pick<PipelineRow, 'opportunity_id' | 'deal_stage' | 'engage_date' | 'account' | 'sales_agent'>
  listPrice: number
  byAccount: WinRateMap
  byAgent: WinRateMap
  p75ThresholdDays: number
  today: Date
  /**
   * Optional flat bonus from manager performance analysis.
   * Added by the orchestrator (scoring.ts) when the deal's manager has a
   * historical win rate above the cross-manager average. Value: 10 points.
   */
  managerBonus?: number
  /**
   * Product series name — used to look up the series win rate multiplier.
   */
  series: string
  /**
   * Historical win rate for the deal's product series (0–1).
   * Null when the series has < 3 closed deals (avoids small-sample bias).
   * Applied as a multiplier to baseScore: multiplier = 0.85 + seriesWinRate × 0.30
   * mapping 0% → ×0.85 (penalty), 50% → ×1.00 (neutral), 100% → ×1.15 (bonus).
   */
  seriesWinRate: number | null
  /**
   * +15 flat bonus when the account has at least one historical Won deal (Account Loyalty).
   * Signals the prospect has already committed to a purchase before.
   */
  accountLoyaltyBonus: number
  /**
   * Historical win rate (0–1) for the deal's regional office.
   * Null when the region has < 5 closed deals. Mentioned in justification to give authority.
   */
  regionalWinRate: number | null
  /** Regional office name — used to label the regional win rate in justification. */
  regionalOffice: string
}

/** Output of computeDealScore — fully self-contained scoring result. */
export interface DealScoreResult {
  score: number
  scoreBreakdown: ScoreBreakdown
  stagnation: StagnationInfo
  justification: string
}

// ─── Building blocks ─────────────────────────────────────────────────────────

/**
 * Builds win-rate lookup maps from the full pipeline history.
 *
 * Only considers Won and Lost rows (closed deals). Open deals are excluded
 * because their outcome is unknown and would bias the rate.
 *
 * Minimum sample thresholds are enforced downstream in `scoreWinRate` to
 * avoid over-fitting on tiny samples:
 *   - Account rate: requires ≥ 2 closed deals
 *   - Agent rate:   requires ≥ 5 closed deals
 *
 * @param pipeline - Full pipeline array (all stages).
 * @returns Two maps: one keyed by account name, one by sales agent name.
 */
export function buildWinRates(pipeline: PipelineRow[]): { byAccount: WinRateMap; byAgent: WinRateMap } {
  const byAccount: WinRateMap = {}
  const byAgent: WinRateMap = {}

  for (const row of pipeline) {
    if (row.deal_stage !== 'Won' && row.deal_stage !== 'Lost') continue

    if (!byAccount[row.account]) byAccount[row.account] = { won: 0, total: 0 }
    byAccount[row.account].total++
    if (row.deal_stage === 'Won') byAccount[row.account].won++

    if (!byAgent[row.sales_agent]) byAgent[row.sales_agent] = { won: 0, total: 0 }
    byAgent[row.sales_agent].total++
    if (row.deal_stage === 'Won') byAgent[row.sales_agent].won++
  }

  return { byAccount, byAgent }
}

/**
 * Computes the 75th-percentile days-to-close from historical Won deals.
 *
 * The P75 value is used as the stagnation threshold: an Engaging deal open
 * longer than this is considered stagnant (top 25% slowest healthy deals).
 *
 * Duration is measured from engage_date → close_date. Rows with missing or
 * negative durations are filtered out to prevent data quality issues from
 * skewing the threshold.
 *
 * Falls back to 180 days if no valid Won records exist.
 *
 * @param pipeline - Full pipeline array (all stages).
 * @returns P75 duration in whole days.
 */
export function computeP75DaysToClose(pipeline: PipelineRow[]): number {
  const durations = pipeline
    .filter((r) => r.deal_stage === 'Won' && r.engage_date && r.close_date)
    .map((r) => (new Date(r.close_date).getTime() - new Date(r.engage_date).getTime()) / 86_400_000)
    .filter((d) => d > 0)
    .sort((a, b) => a - b)

  if (durations.length === 0) return 180

  return Math.round(durations[Math.floor(durations.length * 0.75)])
}

/**
 * Scores how recently a deal entered the engagement phase.
 *
 * Rationale: deals engaged recently are still "warm" — the prospect is
 * actively in conversation. Deals that have not been touched in months
 * are likely forgotten or deprioritised by the prospect.
 *
 * Formula: score = max(0, 100 − (daysAgo / 180) × 100)
 *   - Engaged today     → 100
 *   - Engaged 90d ago   →  50
 *   - Engaged 180d+ ago →   0 (flat floor)
 *
 * **Weight in composite score: 25%**
 *
 * @param engageDateStr - ISO date string from engage_date column.
 * @returns Integer 0–100.
 */
export function scoreRecency(engageDateStr: string, today: Date): number {
  const daysAgo = Math.max(
    0,
    (today.getTime() - new Date(engageDateStr).getTime()) / 86_400_000
  )
  return Math.max(0, Math.round(100 - (daysAgo / 180) * 100))
}

/**
 * Scores the probability of closing based on historical win rates.
 *
 * Blends account-level and agent-level historical rates because both
 * signals carry independent predictive value:
 *   - The account's rate reflects how receptive that company is overall.
 *   - The agent's rate reflects their closing skill in general.
 *
 * Blend when both signals are available: account×0.60 + agent×0.40
 * (account-level signal is weighted higher because it is more specific
 * to the actual buying decision-maker).
 *
 * Minimum sample guards (prevents overfitting on small histories):
 *   - Account rate: requires ≥ 2 closed deals for the account
 *   - Agent rate:   requires ≥ 5 closed deals for the agent
 *   - Falls back to a neutral 0.50 (50 score) when both are unavailable
 *
 * **Weight in composite score: 40%**
 *
 * @param accountKey - Account name (primary key in accounts table).
 * @param agentKey   - Sales agent name (primary key in sales_teams table).
 * @param byAccount  - Win-rate map built by `buildWinRates`.
 * @param byAgent    - Win-rate map built by `buildWinRates`.
 * @returns { score: 0–100, label: human-readable explanation }.
 */
export function scoreWinRate(
  accountKey: string,
  agentKey: string,
  byAccount: WinRateMap,
  byAgent: WinRateMap
): { score: number; label: string } {
  const acct = byAccount[accountKey]
  const agent = byAgent[agentKey]

  const acctRate = acct && acct.total >= 2 ? acct.won / acct.total : null
  const agentRate = agent && agent.total >= 5 ? agent.won / agent.total : null

  let rate = 0.5
  let label = 'sem histórico suficiente'

  if (acctRate !== null && agentRate !== null) {
    rate = acctRate * 0.6 + agentRate * 0.4
    label = `conta fecha ${Math.round(acctRate * 100)}% das vezes; ${agentKey.split(' ')[0]} tem ${Math.round(agentRate * 100)}% de win rate`
  } else if (acctRate !== null) {
    rate = acctRate
    label = `conta fecha ${Math.round(acctRate * 100)}% das vezes historicamente`
  } else if (agentRate !== null) {
    rate = agentRate
    label = `vendedor tem ${Math.round(agentRate * 100)}% de win rate histórico`
  }

  return { score: Math.round(rate * 100), label }
}

/**
 * Scores the revenue efficiency of a deal relative to time already invested.
 *
 * Rationale: a high-value deal that was just engaged is more efficient than
 * a low-value deal that has been sitting open for months. This component
 * rewards deals that justify their pipeline age.
 *
 * Formula: valuePerDay = listPrice / max(1, daysInPipeline)
 *          score = min(100, round((valuePerDay / $100) × 100))
 *   - $100+/day → 100  (e.g. $5 482 deal open 50 days)
 *   - $10/day   →  10
 *   - <$1/day   →   0
 *
 * The $100/day ceiling was calibrated against the product catalogue:
 * GTK 500 ($26 768) closed within 267 days ≈ $100/day.
 *
 * **Weight in composite score: 20%**
 *
 * @param listPrice     - Product list price from products.csv (sales_price).
 * @param engageDateStr - ISO date string from engage_date column.
 * @returns { score: 0–100, label: human-readable value tier }.
 */
export function scoreValueEfficiency(listPrice: number, engageDateStr: string, today: Date): { score: number; label: string } {
  const daysInPipeline = Math.max(
    1,
    (today.getTime() - new Date(engageDateStr).getTime()) / 86_400_000
  )
  const valuePerDay = listPrice / daysInPipeline
  const score = Math.min(100, Math.round((valuePerDay / 100) * 100))

  const label =
    listPrice >= 4000
      ? `deal de alto valor ($${listPrice.toLocaleString()})`
      : listPrice >= 1000
        ? `deal de valor médio ($${listPrice.toLocaleString()})`
        : `deal de baixo valor ($${listPrice.toLocaleString()})`

  return { score, label }
}

/**
 * Returns a fixed weight for the deal's current pipeline stage.
 *
 * Stage captures how far into the sales process a deal is. Engaging deals
 * are in active negotiation — much closer to a buying decision than
 * Prospecting deals which are just entering the pipeline.
 *
 * Scores by stage:
 *   - Engaging    → 100 (active negotiation, highest signal of imminent close)
 *   - Prospecting →  50 (pipeline entry, early-stage intent)
 *   - Won / Lost  →   0 (not active — excluded from active scoring anyway)
 *
 * **Weight in composite score: 15%**
 *
 * @param stage - deal_stage value from sales_pipeline.csv.
 * @returns 0, 50, or 100.
 */
export function getStageWeight(stage: string): number {
  if (stage === 'Engaging') return 100
  if (stage === 'Prospecting') return 50
  return 0
}

/**
 * Builds a human-readable priority justification string for a deal card.
 *
 * Assembles contextual sentence fragments from each scoring component and
 * stagnation status, then prefixes with an urgency emoji based on final score:
 *   - score ≥ 80 → 🔥 Alta prioridade
 *   - score ≥ 55 → ⚡ Prioridade média
 *   - score  < 55 → ❄️ Baixa prioridade
 *
 * @param recencyScore - Output of `scoreRecency`.
 * @param winRateLabel - Label string from `scoreWinRate`.
 * @param valueLabel   - Label string from `scoreValueEfficiency`.
 * @param stage        - Raw deal_stage string.
 * @param totalScore   - Final post-penalty composite score.
 * @param stagnation   - Stagnation info from `computeDealScore`.
 * @returns Localised justification string (pt-BR).
 */
export function buildJustification(
  recencyScore: number,
  winRateLabel: string,
  valueLabel: string,
  stage: string,
  totalScore: number,
  stagnation: StagnationInfo,
  managerBonusApplied?: boolean,
  accountLoyaltyApplied?: boolean,
  seriesWinRate?: number | null,
  regionalWinRate?: number | null,
  regionalOffice?: string,
): string {
  const parts: string[] = []

  if (recencyScore >= 70) parts.push('engajamento recente')
  else if (recencyScore <= 30) parts.push('deal esfriando — sem contato recente')

  parts.push(winRateLabel)
  parts.push(valueLabel)

  if (stage === 'Engaging') parts.push('em negociação ativa')
  else if (stage === 'Prospecting') parts.push('ainda em prospecção')

  if (stagnation.isStagnant) {
    parts.push(
      `estagnado há ${stagnation.daysEngaging}d (P75 dos deals fechados = ${stagnation.p75ThresholdDays}d) — penalidade de 20% aplicada`
    )
  }

  if (accountLoyaltyApplied) {
    parts.push('conta com histórico de compra anterior (+15 pts lealdade)')
  }

  if (managerBonusApplied) {
    parts.push('manager da região com win rate acima da média (+10 pts)')
  }

  if (seriesWinRate !== null && seriesWinRate !== undefined) {
    const pct = Math.round(seriesWinRate * 100)
    if (seriesWinRate >= 0.55) {
      parts.push(`série do produto com alta conversão histórica (${pct}% win rate)`)
    } else if (seriesWinRate <= 0.35) {
      parts.push(`série do produto com baixa conversão (${pct}% win rate) — multiplicador aplicado`)
    }
  }

  if (regionalWinRate !== null && regionalWinRate !== undefined && regionalOffice) {
    parts.push(`regional ${regionalOffice} fecha ${Math.round(regionalWinRate * 100)}% dos deals historicamente`)
  }

  const prefix =
    totalScore >= 80 ? '🔥 Alta prioridade: '
    : totalScore >= 55 ? '⚡ Prioridade média: '
    : '❄️ Baixa prioridade: '

  return prefix + parts.join('; ')
}

// ─── Main entry point ─────────────────────────────────────────────────────────

/**
 * Computes the full priority score for a single active deal.
 *
 * Composite formula (all weights sum to 100%):
 * ```
 *   baseScore = winRate×0.40 + recency×0.25 + valueEfficiency×0.20 + stageWeight×0.15
 * ```
 * Stagnation penalty: if the deal is Engaging and `daysEngaging > p75ThresholdDays`,
 * the score is penalised by 20%: `score = round(baseScore × 0.80)`.
 *
 * This function is pure — it receives all required data as arguments and
 * produces a deterministic result with no side effects.
 *
 * @param input - Pre-fetched deal data and precomputed lookup maps.
 * @returns Composite score, per-component breakdown, stagnation status, and justification.
 */
export function computeDealScore(input: DealScoreInput): DealScoreResult {
  const {
    row, listPrice, byAccount, byAgent, p75ThresholdDays, today,
    managerBonus = 0, series: _series, seriesWinRate, accountLoyaltyBonus = 0,
    regionalWinRate, regionalOffice = '—',
  } = input

  const recency = scoreRecency(row.engage_date, today)
  const { score: winRate, label: winRateLabel } = scoreWinRate(row.account, row.sales_agent, byAccount, byAgent)
  const { score: valueEfficiency, label: valueLabel } = scoreValueEfficiency(listPrice, row.engage_date, today)
  const stageWeightScore = getStageWeight(row.deal_stage)

  const baseScore = Math.round(
    winRate * 0.40 +
    recency * 0.25 +
    valueEfficiency * 0.20 +
    stageWeightScore * 0.15
  )

  // Product series win-rate multiplier: maps 0%→×0.85, 50%→×1.00, 100%→×1.15
  const seriesMultiplier = seriesWinRate !== null && seriesWinRate !== undefined
    ? 0.85 + seriesWinRate * 0.30
    : 1.0
  const adjustedBase = Math.round(baseScore * seriesMultiplier)

  const daysEngaging = Math.round((today.getTime() - new Date(row.engage_date).getTime()) / 86_400_000)
  const isStagnant = row.deal_stage === 'Engaging' && daysEngaging > p75ThresholdDays
  const stagnation: StagnationInfo = { isStagnant, daysEngaging, p75ThresholdDays }

  // Order: series adjustment → stagnation penalty → flat bonuses → clamp 1–99
  const penalised = isStagnant ? Math.round(adjustedBase * 0.8) : adjustedBase
  const withBonuses = penalised + managerBonus + accountLoyaltyBonus
  // Clamp to 1–99 so no deal shows 0 (ignored) or 100 (falsely perfect) from edge cases
  const score = Math.max(1, Math.min(99, withBonuses))

  return {
    score,
    scoreBreakdown: { winRate, recency, valueEfficiency, stageWeight: stageWeightScore },
    stagnation,
    justification: buildJustification(
      recency, winRateLabel, valueLabel, row.deal_stage, score, stagnation,
      managerBonus > 0, accountLoyaltyBonus > 0, seriesWinRate, regionalWinRate, regionalOffice,
    ),
  }
}
