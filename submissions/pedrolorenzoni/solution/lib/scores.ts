// lib/scores.ts
// Deal Smell and Killer Score calculation logic

import type { Deal, Account } from './data'
import { ACCOUNTS, PRODUCTS } from './data'

const MAX_REVENUE = 11698 // Kan-code (largest account revenue)
const MAX_SALES_PRICE = 26768 // GTK 500

function getAccountData(accountName: string): Account | undefined {
  return ACCOUNTS.find(
    (a) => a.account.toLowerCase() === accountName.toLowerCase()
  )
}

function getProductPrice(productName: string): number {
  const p = PRODUCTS.find(
    (p) => p.product.toLowerCase() === productName.toLowerCase()
  )
  return p?.sales_price ?? 550
}

function daysSinceEngage(engageDateStr: string): number {
  if (!engageDateStr) return 999
  const engageDate = new Date(engageDateStr)
  const now = new Date('2017-02-15') // Reference date relative to data
  const diff = now.getTime() - engageDate.getTime()
  return Math.round(diff / (1000 * 60 * 60 * 24))
}

/**
 * Deal Smell (0–100): How attractive / "smelly" a deal is — higher = better prospect.
 * Formula:
 *  - 30% stage score: Engaging=100, Prospecting=60, Won/Lost=80 (closed deals still relevant for history)
 *  - 25% value score: normalized close_value or product price vs max
 *  - 25% account score: normalized revenue of the account
 *  - 20% recency score: how recently the deal was engaged (more recent = better)
 */
export function computeDealSmell(deal: Deal): number {
  // Stage score
  const stageScores: Record<string, number> = {
    Engaging: 100,
    Prospecting: 60,
    Won: 85,
    Lost: 20,
  }
  const stageScore = stageScores[deal.deal_stage] ?? 50

  // Value score
  const dealValue = deal.close_value > 0 ? deal.close_value : getProductPrice(deal.product)
  const valueScore = Math.min(100, (dealValue / 6000) * 100)

  // Account score
  const account = getAccountData(deal.account)
  const accountRevenue = account?.revenue ?? 0
  const accountScore = Math.min(100, (accountRevenue / MAX_REVENUE) * 100)

  // Recency score (engaged recently = better, up to 180 days)
  const days = daysSinceEngage(deal.engage_date)
  const recencyScore = Math.max(0, 100 - (days / 180) * 100)

  const raw =
    stageScore * 0.30 +
    valueScore * 0.25 +
    accountScore * 0.25 +
    recencyScore * 0.20

  return Math.round(Math.min(100, Math.max(0, raw)))
}

/**
 * Killer Score (0–100): Urgency + size = "kill it now" opportunity.
 * Formula:
 *  - 35% value potential: product sales_price vs max
 *  - 30% account size: employees normalized
 *  - 20% stage urgency: Engaging=100, Prospecting=70
 *  - 15% days engaged (fewer days = fresher = higher score)
 *
 * Threshold >= 80 → "KILLER" badge
 */
export function computeKillerScore(deal: Deal): number {
  // Value potential
  const productPrice = getProductPrice(deal.product)
  const valueScore = Math.min(100, (productPrice / MAX_SALES_PRICE) * 100)

  // Account size
  const account = getAccountData(deal.account)
  const employees = account?.employees ?? 500
  const sizeScore = Math.min(100, (employees / 20000) * 100)

  // Stage urgency
  const urgencyScores: Record<string, number> = {
    Engaging: 100,
    Prospecting: 70,
    Won: 60,
    Lost: 10,
  }
  const urgencyScore = urgencyScores[deal.deal_stage] ?? 50

  // Freshness (deals engaged < 30 days ago score highest)
  const days = daysSinceEngage(deal.engage_date)
  const freshnessScore = Math.max(0, 100 - (days / 120) * 100)

  const raw =
    valueScore * 0.35 +
    sizeScore * 0.30 +
    urgencyScore * 0.20 +
    freshnessScore * 0.15

  return Math.round(Math.min(100, Math.max(0, raw)))
}

export function isKillerDeal(deal: Deal): boolean {
  return computeKillerScore(deal) >= 80
}

/**
 * Compute scores for an account by aggregating its best deal scores
 */
export function computeAccountScores(accountName: string, deals: Deal[]): {
  dealSmell: number
  killerScore: number
  activeDeals: number
} {
  const accountDeals = deals.filter(
    (d) => d.account.toLowerCase() === accountName.toLowerCase()
  )
  if (accountDeals.length === 0) return { dealSmell: 0, killerScore: 0, activeDeals: 0 }

  const activeDeals = accountDeals.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  )

  const maxDealSmell = Math.max(...accountDeals.map(computeDealSmell))
  const maxKillerScore = Math.max(...accountDeals.map(computeKillerScore))

  return {
    dealSmell: maxDealSmell,
    killerScore: maxKillerScore,
    activeDeals: activeDeals.length,
  }
}

export function getScoreColor(score: number): string {
  if (score >= 80) return '#af4332'
  if (score >= 60) return '#b9915b'
  return '#60708a'
}

export function getScoreBg(score: number): string {
  if (score >= 80) return 'rgba(175,67,50,0.12)'
  if (score >= 60) return 'rgba(185,145,91,0.12)'
  return 'rgba(96,112,138,0.10)'
}

// Re-exports from Account Rating and Kill Score modules
export { computeAllAccountRatings, getAccountRating, getRatingClass, getRatingColor } from './accountRating'
export { computeAllKillScores, getKillScoreColor, getKillScoreClass } from './killScore'
