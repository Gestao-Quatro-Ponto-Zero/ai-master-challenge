import type { Deal, Account } from './data'
import { ACCOUNTS, PRODUCTS, DEALS } from './data'

const RECENCY_REFERENCE_DATE = DEALS.reduce((maxDate, currentDeal) => {
  const candidateDates = [currentDeal.engage_date, currentDeal.close_date].filter(Boolean)
  for (const dateStr of candidateDates) {
    const parsedDate = new Date(dateStr)
    if (!Number.isNaN(parsedDate.getTime()) && parsedDate > maxDate) {
      maxDate = parsedDate
    }
  }
  return maxDate
}, new Date('2017-01-01'))

function getAccountData(accountName: string): Account | undefined {
  if (!accountName) return undefined
  const normalized = accountName.trim().toLowerCase()
  return ACCOUNTS.find((account) => account.account.toLowerCase() === normalized)
}

function getProductPrice(productName: string): number {
  const normalized = productName.trim().toLowerCase()
  const product = PRODUCTS.find((p) => p.product.toLowerCase() === normalized)
  return product?.sales_price ?? 0
}

function daysSinceEngage(engageDateStr: string): number | null {
  if (!engageDateStr) return null
  const engageDate = new Date(engageDateStr)
  if (Number.isNaN(engageDate.getTime())) return null

  const diff = RECENCY_REFERENCE_DATE.getTime() - engageDate.getTime()
  const days = Math.round(diff / (1000 * 60 * 60 * 24))
  return Math.max(0, days)
}

function formatK(value: number): string {
  const inThousands = value / 1000
  const rounded = Math.round(inThousands * 10) / 10
  return Number.isInteger(rounded) ? `${rounded.toFixed(0)}K` : `${rounded.toFixed(1)}K`
}

export function generateDealReasons(deal: Deal): string[] {
  const reasons: string[] = []
  const productPrice = getProductPrice(deal.product)
  const account = getAccountData(deal.account)
  const employees = account?.employees ?? 0
  const accountRevenue = account?.revenue ?? 0
  const days = daysSinceEngage(deal.engage_date)

  if (productPrice >= 5000) {
    reasons.push(`Produto premium ($${formatK(productPrice)})`)
  }

  if (deal.product === 'GTK 500') {
    reasons.push('Produto GTK 500 — maior ticket')
  }

  if (employees >= 5000) {
    reasons.push(`Empresa grande (${formatK(employees)} func.)`)
  }

  if (accountRevenue >= 5000) {
    reasons.push('Conta de alto revenue')
  }

  if (deal.close_value >= 3000) {
    reasons.push(`Valor de fechamento: $${formatK(deal.close_value)}`)
  }

  if (deal.deal_stage === 'Engaging') {
    reasons.push('Em negociação ativa')
  }

  if (days !== null && days <= 30) {
    reasons.push(`Engajamento recente (${days}d)`)
  }

  if (deal.deal_stage === 'Prospecting' && days !== null && days <= 45) {
    reasons.push('Prospect fresco — ainda quente')
  }

  return reasons.slice(0, 2)
}
