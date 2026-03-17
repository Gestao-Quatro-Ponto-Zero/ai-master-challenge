'use client'

import { X, TrendingUp, Calendar, Building2, Package, User, Lightbulb } from 'lucide-react'
import Badge from './ui/Badge'
import { Deal, DealStage, ACCOUNTS, DEALS } from '../lib/data'
import { DealStatusHistoryEntry } from '../lib/dealStatusHistory'
import {
  computeDealSmell,
  computeKillerScore,
  isKillerDeal,
  getScoreColor,
  getScoreBg,
} from '../lib/scores'
import { generateDealReasons } from '../lib/dealExplanation'

interface DealDetailPanelProps {
  deal: Deal
  allDeals: Deal[]
  onClose: () => void
  statusHistory: DealStatusHistoryEntry[]
  onChangeStatus: (dealId: string, nextStage: DealStage) => void
  onSelectDeal?: (deal: Deal) => void
}

function stageBadgeVariant(stage: string): 'navy' | 'gold' | 'green' | 'gray' {
  switch (stage) {
    case 'Prospecting': return 'navy'
    case 'Engaging': return 'gold'
    case 'Won': return 'green'
    case 'Lost': return 'gray'
    default: return 'gray'
  }
}

function ScoreChip({ label, value }: { label: string; value: number }) {
  return (
    <div
      className="flex flex-col items-center px-4 py-3 rounded-lg"
      style={{ background: getScoreBg(value) }}
    >
      <span className="text-xs text-text-muted mb-1">{label}</span>
      <span className="text-h4 font-bold" style={{ color: getScoreColor(value), lineHeight: 1 }}>
        {value}
      </span>
      <div className="w-full mt-2 h-1 rounded-full bg-[rgba(0,0,0,0.08)] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            background: getScoreColor(value),
          }}
        />
      </div>
    </div>
  )
}

export default function DealDetailPanel({
  deal,
  allDeals,
  onClose,
  statusHistory,
  onChangeStatus,
  onSelectDeal,
}: DealDetailPanelProps) {
  const dealSmell = computeDealSmell(deal)
  const killerScore = computeKillerScore(deal)
  const killer = isKillerDeal(deal)
  const reasonSignals = generateDealReasons(deal)

  const account = ACCOUNTS.find((a) => a.account === deal.account)
  // Somente este bloco de histórico usa base global (todos os vendedores)
  const accountDealsGlobal = deal.account ? DEALS.filter((d) => d.account === deal.account) : []
  const accountWonDeals = accountDealsGlobal.filter((d) => d.deal_stage === 'Won')
  const accountLostDeals = accountDealsGlobal.filter((d) => d.deal_stage === 'Lost')
  const accountClosedDeals = accountDealsGlobal.filter(
    (d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost'
  )
  const accountActiveDeals = accountDealsGlobal.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  )
  const accountWinRate = accountClosedDeals.length > 0
    ? Math.round((accountWonDeals.length / accountClosedDeals.length) * 100)
    : null
  const accountTotalWonRevenue = accountWonDeals.reduce((sum, d) => sum + d.close_value, 0)
  const accountAvgTicketWon = accountWonDeals.length > 0
    ? Math.round(accountTotalWonRevenue / accountWonDeals.length)
    : 0
  const lastPurchaseDate = accountWonDeals
    .filter((d) => d.close_date)
    .sort((a, b) => new Date(b.close_date).getTime() - new Date(a.close_date).getTime())[0]?.close_date

  const productHistoryMap = accountDealsGlobal.reduce((map, currentDeal) => {
      const existing = map.get(currentDeal.product) ?? {
        product: currentDeal.product,
        total: 0,
        won: 0,
        lost: 0,
        revenue: 0,
      }

      existing.total += 1
      if (currentDeal.deal_stage === 'Won') {
        existing.won += 1
        existing.revenue += currentDeal.close_value
      }
      if (currentDeal.deal_stage === 'Lost') {
        existing.lost += 1
      }

      map.set(currentDeal.product, existing)
      return map
    }, new Map<string, { product: string; total: number; won: number; lost: number; revenue: number }>())

  const productHistory = Array.from(productHistoryMap.values())
    .map((item) => ({
      ...item,
      winRate: item.won + item.lost > 0 ? Math.round((item.won / (item.won + item.lost)) * 100) : null,
    }))
    .sort((a, b) => (b.won - a.won) || (b.revenue - a.revenue) || (b.total - a.total))

  const currentProductHistory = productHistory.find((p) => p.product === deal.product)
  const purchasedProducts = productHistory.filter((p) => p.won > 0).map((p) => p.product)

  // Recommendations: top 4 other deals from same agent, sorted by Deal Smell
  const recommendations = allDeals
    .filter((d) =>
      d.opportunity_id !== deal.opportunity_id &&
      d.sales_agent === deal.sales_agent &&
      (d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting')
    )
    .map((d) => ({ deal: d, ds: computeDealSmell(d), ks: computeKillerScore(d) }))
    .sort((a, b) => b.ds - a.ds)
    .slice(0, 4)

  const formatDate = (d: string) => {
    if (!d) return '—'
    const date = new Date(d)
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  const formatDateTime = (d: string) => {
    if (!d) return '—'
    const date = new Date(d)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatCurrency = (v: number) => {
    if (!v) return '—'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(v)
  }

  const handleChangeStatus = (nextStage: DealStage) => {
    if (deal.deal_stage === nextStage) return
    onChangeStatus(deal.opportunity_id, nextStage)
  }

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.35)' }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        className="fixed top-0 right-0 bottom-0 z-50 flex flex-col shadow-xl overflow-y-auto"
        style={{
          width: 'min(420px, 95vw)',
          background: '#ffffff',
          borderLeft: '1px solid var(--color-border)',
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Detalhes do deal"
      >
        {/* Panel header */}
        <div
          className="flex items-start justify-between px-6 py-5 border-b sticky top-0 bg-surface z-10"
          style={{ borderColor: 'var(--color-border)' }}
        >
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              {killer && (
                <Badge variant="primary">KILLER</Badge>
              )}
              <Badge variant={stageBadgeVariant(deal.deal_stage)}>
                {deal.deal_stage}
              </Badge>
            </div>
            <h2 className="text-h5 font-bold text-text-main mt-1">
              {deal.account || 'Conta não identificada'}
            </h2>
            <p className="text-xs text-text-muted mt-0.5">{deal.opportunity_id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors hover:bg-fade ml-2 flex-shrink-0"
            style={{ color: 'var(--color-text-muted)' }}
            aria-label="Fechar painel"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scores */}
        <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <div className="grid grid-cols-2 gap-3">
            <ScoreChip label="Deal Smell" value={dealSmell} />
            <ScoreChip label="Killer Score" value={killerScore} />
          </div>
        </div>

        {/* Deal info */}
        <div className="px-6 py-4 space-y-3 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted">
            Detalhes do Deal
          </h3>

          <InfoRow icon={<Package size={14} />} label="Produto" value={deal.product} />
          <InfoRow icon={<User size={14} />} label="Vendedor" value={deal.sales_agent} />
          <InfoRow icon={<TrendingUp size={14} />} label="Estágio" value={deal.deal_stage} />
          <InfoRow icon={<Calendar size={14} />} label="Início" value={formatDate(deal.engage_date)} />
          {deal.close_date && (
            <InfoRow icon={<Calendar size={14} />} label="Fechamento" value={formatDate(deal.close_date)} />
          )}
          {deal.close_value > 0 && (
            <InfoRow
              icon={<TrendingUp size={14} />}
              label="Valor Fechado"
              value={formatCurrency(deal.close_value)}
              highlight
            />
          )}
        </div>

        {/* Signal basis */}
        <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
            Base da Indicação
          </h3>

          {reasonSignals.length > 0 ? (
            <div className="space-y-1.5">
              {reasonSignals.map((signal) => (
                <p key={signal} className="text-xs text-text-main">
                  • {signal}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted">
              Sem sinal forte de priorização neste momento.
            </p>
          )}

          <p className="text-[11px] text-text-muted mt-2">
            Recência é calculada pelos dias desde o início do deal até o fim da janela histórica do dataset.
          </p>
        </div>

        {/* Account info */}
        {account && (
          <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
              Conta
            </h3>
            <div className="space-y-2">
              <InfoRow icon={<Building2 size={14} />} label="Empresa" value={account.account} />
              <InfoRow icon={<Building2 size={14} />} label="Setor" value={account.sector} />
              <InfoRow icon={<Building2 size={14} />} label="Receita" value={`$${account.revenue}M`} />
              <InfoRow icon={<Building2 size={14} />} label="Funcionários" value={account.employees.toLocaleString()} />
              <InfoRow icon={<Building2 size={14} />} label="Localização" value={account.office_location} />
              {account.subsidiary_of && (
                <InfoRow icon={<Building2 size={14} />} label="Subsidiária de" value={account.subsidiary_of} />
              )}
            </div>
          </div>
        )}

        {/* Purchase history */}
        {account && accountDealsGlobal.length > 0 && (
          <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
              Histórico de Compra
            </h3>
            <p className="text-[11px] text-text-muted mb-3">
              Dados agregados da conta em toda a operação (todos os vendedores).
            </p>

            <div className="space-y-2">
              <InfoRow icon={<TrendingUp size={14} />} label="Deals da conta" value={`${accountDealsGlobal.length}`} />
              <InfoRow icon={<TrendingUp size={14} />} label="Compras (Won)" value={`${accountWonDeals.length}`} />
              <InfoRow icon={<TrendingUp size={14} />} label="Perdas (Lost)" value={`${accountLostDeals.length}`} />
              <InfoRow
                icon={<TrendingUp size={14} />}
                label="Taxa conversão"
                value={accountWinRate !== null ? `${accountWinRate}%` : '—'}
              />
              <InfoRow
                icon={<TrendingUp size={14} />}
                label="Receita (Won)"
                value={accountTotalWonRevenue > 0 ? formatCurrency(accountTotalWonRevenue) : '—'}
              />
              <InfoRow
                icon={<TrendingUp size={14} />}
                label="Ticket médio"
                value={accountAvgTicketWon > 0 ? formatCurrency(accountAvgTicketWon) : '—'}
              />
              <InfoRow
                icon={<Calendar size={14} />}
                label="Última compra"
                value={lastPurchaseDate ? formatDate(lastPurchaseDate) : '—'}
              />
              <InfoRow
                icon={<TrendingUp size={14} />}
                label="Ativos"
                value={`${accountActiveDeals.length}`}
              />
            </div>

            {currentProductHistory && (
              <div
                className="mt-3 rounded-lg px-3 py-2.5"
                style={{ background: 'var(--color-fade)', border: '1px solid var(--color-border)' }}
              >
                <p className="text-[11px] font-bold uppercase tracking-wide text-text-muted mb-1">
                  Produto deste deal
                </p>
                <p className="text-xs text-text-main">
                  {deal.product}: {currentProductHistory.total} oportunidades · {currentProductHistory.won} Won · {currentProductHistory.lost} Lost
                  {currentProductHistory.winRate !== null ? ` · ${currentProductHistory.winRate}% de conversão` : ''}
                </p>
              </div>
            )}

            {purchasedProducts.length > 0 && (
              <p className="text-xs text-text-muted mt-3">
                Produtos já comprados: <strong>{purchasedProducts.join(', ')}</strong>
              </p>
            )}

            {productHistory.length > 0 && (
              <div className="mt-3 space-y-1.5">
                <p className="text-[11px] font-bold uppercase tracking-wide text-text-muted">
                  Mix de produtos (top 4)
                </p>
                {productHistory.slice(0, 4).map((productStat) => (
                  <div
                    key={productStat.product}
                    className="flex items-center justify-between rounded-md px-2.5 py-1.5"
                    style={{ background: 'var(--color-fade)' }}
                  >
                    <span className="text-xs text-text-main font-semibold truncate">
                      {productStat.product}
                    </span>
                    <span className="text-xs text-text-muted ml-3">
                      {productStat.won}W/{productStat.lost}L · {productStat.revenue > 0 ? formatCurrency(productStat.revenue) : '$0'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
            Atualizar Status
          </h3>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleChangeStatus('Prospecting')}
              disabled={deal.deal_stage === 'Prospecting'}
              className="rounded-lg px-3 py-2 text-xs font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: 'rgba(15,26,69,0.3)',
                background: deal.deal_stage === 'Prospecting' ? 'rgba(15,26,69,0.12)' : '#ffffff',
                color: '#0f1a45',
              }}
            >
              Marcar como Prospecting
            </button>
            <button
              type="button"
              onClick={() => handleChangeStatus('Engaging')}
              disabled={deal.deal_stage === 'Engaging'}
              className="rounded-lg px-3 py-2 text-xs font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: 'rgba(185,145,91,0.4)',
                background: deal.deal_stage === 'Engaging' ? 'rgba(185,145,91,0.15)' : '#ffffff',
                color: '#8a6c3f',
              }}
            >
              Marcar como Engaging
            </button>
            <button
              type="button"
              onClick={() => handleChangeStatus('Won')}
              disabled={deal.deal_stage === 'Won'}
              className="rounded-lg px-3 py-2 text-xs font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: 'rgba(22,163,74,0.35)',
                background: deal.deal_stage === 'Won' ? 'rgba(22,163,74,0.12)' : '#ffffff',
                color: '#15803d',
              }}
            >
              Marcar como Won
            </button>
            <button
              type="button"
              onClick={() => handleChangeStatus('Lost')}
              disabled={deal.deal_stage === 'Lost'}
              className="rounded-lg px-3 py-2 text-xs font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: 'rgba(107,114,128,0.4)',
                background: deal.deal_stage === 'Lost' ? 'rgba(107,114,128,0.14)' : '#ffffff',
                color: '#4b5563',
              }}
            >
              Marcar como Lost
            </button>
          </div>

          <p className="text-[11px] text-text-muted mt-2">
            Status atual: <strong>{deal.deal_stage}</strong>
          </p>
        </div>

        <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">
            Histórico de Alterações de Status
          </h3>

          {statusHistory.length === 0 ? (
            <p className="text-xs text-text-muted">
              Nenhuma alteração manual registrada para este deal.
            </p>
          ) : (
            <div className="space-y-2">
              {statusHistory.map((entry, index) => {
                const canRevert = deal.deal_stage !== entry.from
                return (
                  <div
                    key={`${entry.changedAt}-${entry.from}-${entry.to}-${index}`}
                    className="rounded-lg border px-3 py-2"
                    style={{ borderColor: 'var(--color-border)', background: 'var(--color-fade)' }}
                  >
                    <p className="text-xs font-semibold text-text-main">
                      {entry.from} → {entry.to}
                    </p>
                    <p className="text-[11px] text-text-muted mt-0.5">
                      {formatDateTime(entry.changedAt)}
                    </p>
                    <button
                      type="button"
                      onClick={() => handleChangeStatus(entry.from)}
                      disabled={!canRevert}
                      className="mt-2 rounded-md px-2.5 py-1 text-[11px] font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{
                        borderColor: 'rgba(15,26,69,0.2)',
                        background: '#ffffff',
                        color: '#0f1a45',
                      }}
                    >
                      Voltar para {entry.from}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="px-6 py-4">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb size={14} style={{ color: '#b9915b' }} />
              <h3 className="text-xs font-bold uppercase tracking-widest text-text-muted">
                Recomendações
              </h3>
            </div>
            <p className="text-xs text-text-muted mb-3">
              Outros deals de <strong>{deal.sales_agent.split(' ')[0]}</strong>, ordenados por Deal Smell:
            </p>
            <div className="space-y-2">
              {recommendations.map(({ deal: rec, ds, ks }) => (
                <button
                  key={rec.opportunity_id}
                  type="button"
                  onClick={() => onSelectDeal?.(rec)}
                  aria-disabled={!onSelectDeal}
                  className="w-full flex items-center justify-between rounded-lg px-3 py-2.5 border transition-all text-left"
                  style={{
                    borderColor: 'var(--color-border)',
                    background: 'var(--color-fade)',
                    cursor: onSelectDeal ? 'pointer' : 'default',
                  }}
                >
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-text-main truncate">
                      {rec.account || '—'}
                    </p>
                    <p className="text-xs text-text-muted">{rec.product} · {rec.deal_stage}</p>
                    {ds > dealSmell && (
                      <p className="text-xs mt-0.5" style={{ color: '#af4332', fontStyle: 'italic' }}>
                        Foque aqui — DS maior
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-3">
                    <span className="text-xs font-bold" style={{ color: getScoreColor(ds) }}>
                      DS {ds}
                    </span>
                    <span className="text-xs font-semibold" style={{ color: getScoreColor(ks) }}>
                      KS {ks}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>
    </>
  )
}

function InfoRow({
  icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ReactNode
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      <span style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>{icon}</span>
      <span className="text-xs text-text-muted w-24 flex-shrink-0">{label}</span>
      <span
        className="text-xs font-semibold truncate"
        style={{ color: highlight ? '#af4332' : 'var(--color-text)' }}
      >
        {value}
      </span>
    </div>
  )
}
