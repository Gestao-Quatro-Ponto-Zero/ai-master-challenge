// lib/killScore.ts
// Kill Score system — identifies deals that should be abandoned
// Scale: 0-100. Higher = should abandon.
// Vermelho (80-100), Laranja (60-79), Amarelo (40-59), Verde (0-39)

import { DEALS, PRODUCTS } from './data'
import type { Deal } from './data'
import { computeAllAccountRatings } from './accountRating'

export interface KillScore {
  opportunity_id: string
  account: string
  sales_agent: string
  product: string
  deal_stage: string
  kill_score: number
  kill_classificacao: 'Vermelho' | 'Laranja' | 'Amarelo' | 'Verde'
  dias_no_pipeline: number
  media_won_dias: number
  recomendacao: string
}

const REFERENCE_DATE = new Date('2018-01-01')

function clip(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24))
}

export function getKillScoreClass(score: number): 'Vermelho' | 'Laranja' | 'Amarelo' | 'Verde' {
  if (score >= 80) return 'Vermelho'
  if (score >= 60) return 'Laranja'
  if (score >= 40) return 'Amarelo'
  return 'Verde'
}

export function getKillScoreColor(cls: string): string {
  switch (cls) {
    case 'Vermelho': return '#af4332'
    case 'Laranja': return '#d97706'
    case 'Amarelo': return '#eab308'
    case 'Verde': return '#16a34a'
    default: return '#60708a'
  }
}

function getRecomendacao(cls: 'Vermelho' | 'Laranja' | 'Amarelo' | 'Verde'): string {
  switch (cls) {
    case 'Vermelho': return 'Abandonar. Pivotar para deal mais saudavel do mesmo agente.'
    case 'Laranja': return 'Ultima tentativa em 7 dias. Focar no sinal mais critico.'
    case 'Amarelo': return 'Reduzir frequencia. Follow-up espacado.'
    case 'Verde': return 'Continuar. Deal saudavel.'
  }
}

function getProductPrice(productName: string): number {
  const p = PRODUCTS.find(
    pr => pr.product.toLowerCase() === productName.toLowerCase()
  )
  return p?.sales_price ?? 550
}

let cachedScores: KillScore[] | null = null

export function computeAllKillScores(): KillScore[] {
  if (cachedScores) return cachedScores

  const wonDeals = DEALS.filter(d => d.deal_stage === 'Won')
  const lostDeals = DEALS.filter(d => d.deal_stage === 'Lost')
  const activeDeals = DEALS.filter(
    d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  )

  // Average Won cycle time in days
  const wonCycleTimes = wonDeals
    .filter(d => d.engage_date && d.close_date)
    .map(d => daysBetween(new Date(d.engage_date), new Date(d.close_date)))
  const mediaWon = wonCycleTimes.length > 0
    ? wonCycleTimes.reduce((a, b) => a + b, 0) / wonCycleTimes.length
    : 90

  // Account ratings map
  const accountRatings = computeAllAccountRatings()
  const ratingMap = new Map(accountRatings.map(r => [r.account, r.rating_final]))

  // Product conversion rates: Won / (Won + Lost)
  const productWonCount = new Map<string, number>()
  const productLostCount = new Map<string, number>()
  for (const d of wonDeals) {
    productWonCount.set(d.product, (productWonCount.get(d.product) || 0) + 1)
  }
  for (const d of lostDeals) {
    productLostCount.set(d.product, (productLostCount.get(d.product) || 0) + 1)
  }

  // Compute ROI per day for all active deals (needed for percentile ranking)
  const roiPerDay: { idx: number; roi: number }[] = []
  for (let i = 0; i < activeDeals.length; i++) {
    const deal = activeDeals[i]
    const engageDate = deal.engage_date ? new Date(deal.engage_date) : null
    const diasNoPipeline = engageDate
      ? Math.max(1, daysBetween(engageDate, REFERENCE_DATE))
      : 1
    const dealValue = deal.close_value > 0 ? deal.close_value : getProductPrice(deal.product)
    const roi = dealValue / diasNoPipeline
    roiPerDay.push({ idx: i, roi })
  }

  // Sort by ROI ascending for percentile ranking
  const roiSorted = [...roiPerDay].sort((a, b) => a.roi - b.roi)
  // Assign percentile ranks: lowest ROI gets rank close to 0 (inverted = score 100)
  const roiPercentileMap = new Map<number, number>()
  for (let rank = 0; rank < roiSorted.length; rank++) {
    // Percentile: rank / (n-1), inverted: lowest ROI = highest score
    const percentile = roiSorted.length > 1
      ? rank / (roiSorted.length - 1)
      : 0.5
    // Inverted: low ROI (low rank position in ascending sort) = high score
    // rank 0 (lowest ROI) -> percentile 0 -> inverted score 100
    // rank n-1 (highest ROI) -> percentile 1 -> inverted score 0
    const invertedScore = (1 - percentile) * 100
    roiPercentileMap.set(roiSorted[rank].idx, invertedScore)
  }

  const scores: KillScore[] = activeDeals.map((deal, idx) => {
    const engageDate = deal.engage_date ? new Date(deal.engage_date) : null
    const diasNoPipeline = engageDate
      ? Math.max(0, daysBetween(engageDate, REFERENCE_DATE))
      : 0

    // 1. Tempo Excedente (30%)
    let tempoScore = 0
    if (diasNoPipeline > mediaWon) {
      tempoScore = clip(
        ((diasNoPipeline - mediaWon) / (2 * mediaWon)) * 100,
        0, 100
      )
    }

    // 2. Estagnacao (25%)
    const stageMultiplier = deal.deal_stage === 'Prospecting' ? 1.0 : 0.6
    const estagnacaoScore = clip(
      (diasNoPipeline / mediaWon) * stageMultiplier * 50,
      0, 100
    )

    // 3. Rating Invertido (20%)
    let ratingInvScore = 75 // pessimistic default
    if (deal.account) {
      const accountRating = ratingMap.get(deal.account)
      if (accountRating !== undefined) {
        ratingInvScore = 100 - accountRating
      }
    }

    // 4. ROI do Esforco (15%)
    const roiScore = roiPercentileMap.get(idx) ?? 50

    // 5. Conversao do Produto (10%)
    const won = productWonCount.get(deal.product) || 0
    const lost = productLostCount.get(deal.product) || 0
    let convProdutoScore = 50 // default for products with no history
    if (won + lost > 0) {
      const taxa = (won / (won + lost)) * 100
      convProdutoScore = 100 - taxa
    }

    const killScore = Math.round(
      tempoScore * 0.30 +
      estagnacaoScore * 0.25 +
      ratingInvScore * 0.20 +
      roiScore * 0.15 +
      convProdutoScore * 0.10
    )

    const classificacao = getKillScoreClass(killScore)

    return {
      opportunity_id: deal.opportunity_id,
      account: deal.account,
      sales_agent: deal.sales_agent,
      product: deal.product,
      deal_stage: deal.deal_stage,
      kill_score: killScore,
      kill_classificacao: classificacao,
      dias_no_pipeline: diasNoPipeline,
      media_won_dias: Math.round(mediaWon),
      recomendacao: getRecomendacao(classificacao),
    }
  })

  // Sort by kill_score descending (worst deals first)
  scores.sort((a, b) => b.kill_score - a.kill_score)

  cachedScores = scores
  return scores
}
