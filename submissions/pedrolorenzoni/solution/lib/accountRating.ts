// lib/accountRating.ts
// Account Rating system — evaluates account health based on deal history
// Scale: 0-100. Classification: A (80-100), B (60-79), C (40-59), D (0-39)

import { DEALS } from './data'
import type { Deal } from './data'

export interface AccountRating {
  account: string
  rating_final: number
  classificacao: 'A' | 'B' | 'C' | 'D'
  recencia_score: number
  taxa_conversao_score: number
  expansao_score: number
  recorrencia_score: number
  ticket_medio_score: number
  ltv_score: number
  recomendacao: string
}

// Reference date: dataset ends 2017-12, so "today" = 2018-01-01
const REFERENCE_DATE = new Date('2018-01-01')

function daysBetween(a: Date, b: Date): number {
  return Math.abs(Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24)))
}

function minMaxNormalize(value: number, min: number, max: number): number {
  if (max === min) return 50
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
}

// Inverted min-max: smaller value = higher score
function minMaxNormalizeInverted(value: number, min: number, max: number): number {
  if (max === min) return 50
  return Math.max(0, Math.min(100, ((max - value) / (max - min)) * 100))
}

export function getRatingClass(score: number): 'A' | 'B' | 'C' | 'D' {
  if (score >= 80) return 'A'
  if (score >= 60) return 'B'
  if (score >= 40) return 'C'
  return 'D'
}

export function getRatingColor(cls: string): string {
  switch (cls) {
    case 'A': return '#16a34a'
    case 'B': return '#b9915b'
    case 'C': return '#d97706'
    case 'D': return '#af4332'
    default: return '#60708a'
  }
}

function getRecomendacao(cls: 'A' | 'B' | 'C' | 'D'): string {
  switch (cls) {
    case 'A': return 'Conta premium. Priorizar cross-sell e upsell de produtos de maior valor.'
    case 'B': return 'Conta saudavel. Manter relacionamento e buscar expansao de portfolio.'
    case 'C': return 'Conta em risco. Investigar barreiras de conversao e reativar engajamento.'
    case 'D': return 'Conta critica. Avaliar viabilidade de continuidade ou mudanca de estrategia.'
  }
}

let cachedRatings: AccountRating[] | null = null

export function computeAllAccountRatings(): AccountRating[] {
  if (cachedRatings) return cachedRatings

  const wonDeals = DEALS.filter(d => d.deal_stage === 'Won')
  const lostDeals = DEALS.filter(d => d.deal_stage === 'Lost')

  // Group Won deals by account
  const wonByAccount = new Map<string, Deal[]>()
  for (const d of wonDeals) {
    if (!d.account) continue
    const existing = wonByAccount.get(d.account) || []
    existing.push(d)
    wonByAccount.set(d.account, existing)
  }

  // Group Lost deals by account
  const lostByAccount = new Map<string, Deal[]>()
  for (const d of lostDeals) {
    if (!d.account) continue
    const existing = lostByAccount.get(d.account) || []
    existing.push(d)
    lostByAccount.set(d.account, existing)
  }

  // Collect raw values for min-max normalization
  const allLastWonDates: number[] = []
  const allAvgIntervals: number[] = []
  const allTicketMedios: number[] = []
  const allLTVs: number[] = []

  // Pre-compute per-account raw values
  type RawValues = {
    account: string
    lastWonTimestamp: number
    taxaConversao: number
    distinctProducts: number
    avgInterval: number | null // null if only 1 Won deal
    ticketMedio: number
    ltv: number
  }

  const rawData: RawValues[] = []

  for (const [account, deals] of Array.from(wonByAccount.entries())) {
    const closeDates = deals
      .map(d => new Date(d.close_date))
      .sort((a, b) => a.getTime() - b.getTime())

    const lastWonTimestamp = closeDates[closeDates.length - 1].getTime()
    allLastWonDates.push(lastWonTimestamp)

    // Taxa de conversao
    const wonCount = deals.length
    const lostCount = (lostByAccount.get(account) || []).length
    const taxaConversao = (wonCount / (wonCount + lostCount)) * 100

    // Distinct products bought
    const distinctProducts = new Set(deals.map(d => d.product)).size

    // Recorrencia: average interval between Won close_dates
    let avgInterval: number | null = null
    if (closeDates.length > 1) {
      let totalInterval = 0
      for (let i = 1; i < closeDates.length; i++) {
        totalInterval += daysBetween(closeDates[i - 1], closeDates[i])
      }
      avgInterval = totalInterval / (closeDates.length - 1)
      allAvgIntervals.push(avgInterval)
    }

    // Ticket medio
    const totalValue = deals.reduce((sum, d) => sum + d.close_value, 0)
    const ticketMedio = totalValue / deals.length
    allTicketMedios.push(ticketMedio)

    // LTV
    allLTVs.push(totalValue)

    rawData.push({
      account,
      lastWonTimestamp,
      taxaConversao,
      distinctProducts,
      avgInterval,
      ticketMedio,
      ltv: totalValue,
    })
  }

  // Compute min/max for normalization
  const minDate = Math.min(...allLastWonDates)
  const maxDate = Math.max(...allLastWonDates)
  const minInterval = allAvgIntervals.length > 0 ? Math.min(...allAvgIntervals) : 0
  const maxInterval = allAvgIntervals.length > 0 ? Math.max(...allAvgIntervals) : 1
  const minTicket = Math.min(...allTicketMedios)
  const maxTicket = Math.max(...allTicketMedios)
  const minLTV = Math.min(...allLTVs)
  const maxLTV = Math.max(...allLTVs)

  const TOTAL_PRODUCTS = 7 // 7 distinct products (GTXPro and GTX Pro are same)

  const ratings: AccountRating[] = rawData.map(raw => {
    // 1. Recencia (25%) — more recent last Won = higher score
    const recencia_score = minMaxNormalize(raw.lastWonTimestamp, minDate, maxDate)

    // 2. Taxa de conversao (20%) — already 0-100
    const taxa_conversao_score = raw.taxaConversao

    // 3. Potencial de expansao (20%) — fewer products bought = more opportunity
    const expansao_score = (1 - raw.distinctProducts / TOTAL_PRODUCTS) * 100

    // 4. Recorrencia (15%) — smaller interval = higher score (inverted)
    // Accounts with only 1 Won deal get 0
    let recorrencia_score = 0
    if (raw.avgInterval !== null) {
      recorrencia_score = minMaxNormalizeInverted(raw.avgInterval, minInterval, maxInterval)
    }

    // 5. Ticket medio (10%)
    const ticket_medio_score = minMaxNormalize(raw.ticketMedio, minTicket, maxTicket)

    // 6. LTV realizado (10%)
    const ltv_score = minMaxNormalize(raw.ltv, minLTV, maxLTV)

    const rating_final = Math.round(
      recencia_score * 0.25 +
      taxa_conversao_score * 0.20 +
      expansao_score * 0.20 +
      recorrencia_score * 0.15 +
      ticket_medio_score * 0.10 +
      ltv_score * 0.10
    )

    const classificacao = getRatingClass(rating_final)

    return {
      account: raw.account,
      rating_final,
      classificacao,
      recencia_score: Math.round(recencia_score * 100) / 100,
      taxa_conversao_score: Math.round(taxa_conversao_score * 100) / 100,
      expansao_score: Math.round(expansao_score * 100) / 100,
      recorrencia_score: Math.round(recorrencia_score * 100) / 100,
      ticket_medio_score: Math.round(ticket_medio_score * 100) / 100,
      ltv_score: Math.round(ltv_score * 100) / 100,
      recomendacao: getRecomendacao(classificacao),
    }
  })

  // Sort by rating descending
  ratings.sort((a, b) => b.rating_final - a.rating_final)

  cachedRatings = ratings
  return ratings
}

export function getAccountRating(accountName: string): AccountRating | null {
  const ratings = computeAllAccountRatings()
  return ratings.find(r => r.account === accountName) || null
}
