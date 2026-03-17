'use client'

import { useState, useMemo } from 'react'
import { Flame, ChevronDown, ChevronRight, Sparkles, AlertTriangle, Target, Undo2, Search } from 'lucide-react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import DealDetailPanel from '../DealDetailPanel'
import { Deal, DealStage } from '../../lib/data'
import { DealStatusHistoryEntry } from '../../lib/dealStatusHistory'
import {
  computeDealSmell,
  computeKillerScore,
  isKillerDeal,
  getScoreColor,
  getScoreBg,
} from '../../lib/scores'
import { generateDealReasons } from '../../lib/dealExplanation'

interface ListViewProps {
  deals: Deal[]
  isAdmin: boolean
  selectedAccount: string | null
  dealStatusHistory: Record<string, DealStatusHistoryEntry[]>
  onChangeDealStatus: (dealId: string, nextStage: DealStage) => void
}

type DealWithScores = Deal & { dealSmell: number; killerScore: number }
type SellerFocusMode = 'software' | 'dealSmell' | 'killScore'
type SellerFocusOption = {
  label: string
  summary: string
  heading: string
  badge: string
  accent: string
  softBg: string
  activeBg: string
}

const SELLER_FOCUS_OPTIONS: Record<
  SellerFocusMode,
  SellerFocusOption
> = {
  software: {
    label: 'Visão indicada pelo software',
    summary: 'Priorização automática equilibrando Deal Smell e Kill Score.',
    heading: 'visão indicada pelo software',
    badge: 'Recomendado',
    accent: '#0f1a45',
    softBg: 'rgba(15,26,69,0.08)',
    activeBg: 'linear-gradient(135deg, rgba(15,26,69,0.14) 0%, rgba(15,26,69,0.03) 100%)',
  },
  dealSmell: {
    label: 'Filtrar por mais Deal Smell',
    summary: 'Aqui você encontra os deals com mais urgência de acompanhamento comercial.',
    heading: 'ordenados por Deal Smell',
    badge: 'Urgência',
    accent: '#af4332',
    softBg: 'rgba(175,67,50,0.10)',
    activeBg: 'linear-gradient(135deg, rgba(175,67,50,0.16) 0%, rgba(175,67,50,0.03) 100%)',
  },
  killScore: {
    label: 'Filtrar por mais Kill Score',
    summary: 'Aqui você encontra os deals com maior potencial estratégico de fechamento.',
    heading: 'ordenados por Kill Score',
    badge: 'Potencial',
    accent: '#1f7a4a',
    softBg: 'rgba(31,122,74,0.10)',
    activeBg: 'linear-gradient(135deg, rgba(31,122,74,0.16) 0%, rgba(31,122,74,0.03) 100%)',
  },
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

function formatCurrency(v: number) {
  if (!v) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v)
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
}

function applyCloseDateForStageChange(deal: Deal, nextStage: DealStage): Deal {
  const isClosedStage = nextStage === 'Won' || nextStage === 'Lost'
  const today = new Date().toISOString().slice(0, 10)

  return {
    ...deal,
    deal_stage: nextStage,
    close_date: isClosedStage ? (deal.close_date || today) : '',
  }
}

function DealCard({
  deal,
  onSelect,
}: {
  deal: DealWithScores
  onSelect: () => void
}) {
  const killer = isKillerDeal(deal)
  const reasons = generateDealReasons(deal)

  return (
    <Card
      hoverable
      killerPulse={killer}
      onClick={onSelect}
      className="p-4"
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left content */}
        <div className="min-w-0 flex-1">
          {/* Header row */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {killer && (
              <Badge variant="primary" className="flex items-center gap-1">
                <Flame size={10} />
                KILLER
              </Badge>
            )}
            <Badge variant={stageBadgeVariant(deal.deal_stage)}>
              {deal.deal_stage}
            </Badge>
          </div>

          {/* Account */}
          <h3 className="text-sm font-bold text-text-main truncate">
            {deal.account || <span className="text-text-muted italic">Conta não informada</span>}
          </h3>

          {/* Meta row */}
          <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
            <span className="text-xs text-text-muted">{deal.product}</span>
            <span className="text-xs text-text-muted">·</span>
            <span className="text-xs text-text-muted">{deal.sales_agent}</span>
            <span className="text-xs text-text-muted">·</span>
            <span className="text-xs text-text-muted">Desde {formatDate(deal.engage_date)}</span>
            {deal.close_value > 0 && (
              <>
                <span className="text-xs text-text-muted">·</span>
                <span className="text-xs font-semibold" style={{ color: '#af4332' }}>
                  {formatCurrency(deal.close_value)}
                </span>
              </>
            )}
          </div>

          {reasons.length > 0 && (
            <p className="text-xs mt-1.5 italic" style={{ color: 'var(--color-text-muted)' }}>
              {reasons.join(' · ')}
            </p>
          )}
        </div>

        {/* Scores */}
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-text-muted">Deal Smell</div>
              <div className="text-sm font-bold" style={{ color: getScoreColor(deal.dealSmell) }}>
                {deal.dealSmell}
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-text-muted">KS</div>
              <div
                className="text-sm font-bold px-2 py-0.5 rounded-md"
                style={{
                  color: getScoreColor(deal.killerScore),
                  background: getScoreBg(deal.killerScore),
                }}
              >
                {deal.killerScore}
              </div>
            </div>
          </div>
          <ChevronRight size={14} style={{ color: 'var(--color-text-muted)' }} />
        </div>
      </div>
    </Card>
  )
}

/** Admin grouped view */
function AdminGroupedView({
  dealsWithScores,
  allDeals,
  selectedAccount,
  opportunityCodeSearch,
  onOpportunityCodeSearchChange,
  dealStatusHistory,
  onChangeDealStatus,
}: {
  dealsWithScores: DealWithScores[]
  allDeals: Deal[]
  selectedAccount: string | null
  opportunityCodeSearch: string
  onOpportunityCodeSearchChange: (value: string) => void
  dealStatusHistory: Record<string, DealStatusHistoryEntry[]>
  onChangeDealStatus: (dealId: string, nextStage: DealStage) => void
}) {
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [collapsedAgents, setCollapsedAgents] = useState<Set<string>>(new Set())

  const grouped = useMemo(() => {
    let filtered = selectedAccount
      ? dealsWithScores.filter((d) => d.account === selectedAccount)
      : dealsWithScores

    const normalizedOpportunityCodeSearch = opportunityCodeSearch.trim().toLowerCase()
    if (normalizedOpportunityCodeSearch) {
      filtered = filtered.filter((d) =>
        d.opportunity_id.toLowerCase().includes(normalizedOpportunityCodeSearch)
      )
    }

    const map = new Map<string, DealWithScores[]>()
    for (const d of filtered) {
      const existing = map.get(d.sales_agent) ?? []
      map.set(d.sales_agent, [...existing, d])
    }
    // Sort deals within each group by dealSmell desc
    map.forEach((arr, key) => {
      map.set(key, arr.sort((a, b) => b.dealSmell - a.dealSmell).slice(0, 5))
    })
    // Sort agents by their top deal's dealSmell
    return Array.from(map.entries()).sort((entryA, entryB) => {
      const a = entryA[1]
      const b = entryB[1]
      const maxA = Math.max(...a.map((d: DealWithScores) => d.dealSmell))
      const maxB = Math.max(...b.map((d: DealWithScores) => d.dealSmell))
      return maxB - maxA
    })
  }, [dealsWithScores, selectedAccount, opportunityCodeSearch])

  const toggleAgent = (agent: string) => {
    setCollapsedAgents((prev) => {
      const next = new Set(prev)
      next.has(agent) ? next.delete(agent) : next.add(agent)
      return next
    })
  }

  const handleSelectedDealStatusChange = (dealId: string, nextStage: DealStage) => {
    onChangeDealStatus(dealId, nextStage)
    setSelectedDeal((current) => {
      if (!current || current.opportunity_id !== dealId || current.deal_stage === nextStage) return current
      return applyCloseDateForStageChange(current, nextStage)
    })
  }

  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <label
          htmlFor="admin-opportunity-search"
          className="text-xs font-semibold text-text-muted uppercase tracking-wide"
        >
          Buscar por código da oportunidade
        </label>
        <div className="relative max-w-md">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'var(--color-text-muted)' }}
          />
          <input
            id="admin-opportunity-search"
            type="search"
            value={opportunityCodeSearch}
            onChange={(e) => onOpportunityCodeSearchChange(e.target.value)}
            placeholder="Ex.: HAXMC4IX"
            className="w-full rounded-xl border bg-surface py-2.5 pl-9 pr-16 text-sm text-text-main outline-none transition-colors"
            style={{ borderColor: 'var(--color-border)' }}
          />
          {opportunityCodeSearch && (
            <button
              type="button"
              onClick={() => onOpportunityCodeSearchChange('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-semibold text-primary hover:underline"
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      {grouped.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-text-muted">
          <p className="text-sm">Nenhum deal encontrado</p>
          {opportunityCodeSearch.trim() && (
            <p className="text-xs mt-1">
              para o código {opportunityCodeSearch.trim().toUpperCase()}
            </p>
          )}
        </div>
      ) : (
        grouped.map(([agent, deals]) => (
          <section key={agent}>
            <button
              className="flex items-center gap-2 mb-3 w-full text-left"
              onClick={() => toggleAgent(agent)}
            >
              <span className="text-sm font-bold text-text-main">{agent}</span>
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(175,67,50,0.1)', color: '#af4332' }}
              >
                {deals.length}
              </span>
              <ChevronDown
                size={14}
                className="ml-auto transition-transform duration-200"
                style={{
                  color: 'var(--color-text-muted)',
                  transform: collapsedAgents.has(agent) ? 'rotate(-90deg)' : 'rotate(0)',
                }}
              />
            </button>
            {!collapsedAgents.has(agent) && (
              <div className="space-y-3">
                {deals.map((d) => (
                  <DealCard key={d.opportunity_id} deal={d} onSelect={() => setSelectedDeal(d)} />
                ))}
              </div>
            )}
          </section>
        ))
      )}

      {selectedDeal && (
        <DealDetailPanel
          deal={selectedDeal}
          allDeals={allDeals}
          onClose={() => setSelectedDeal(null)}
          statusHistory={dealStatusHistory[selectedDeal.opportunity_id] ?? []}
          onChangeStatus={handleSelectedDealStatusChange}
          onSelectDeal={(nextDeal) => setSelectedDeal(nextDeal)}
        />
      )}
    </div>
  )
}

export default function ListView({
  deals,
  isAdmin,
  selectedAccount,
  dealStatusHistory,
  onChangeDealStatus,
}: ListViewProps) {
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [focusMode, setFocusMode] = useState<SellerFocusMode>('software')
  const [opportunityCodeSearch, setOpportunityCodeSearch] = useState('')
  const activeFocusOption = SELLER_FOCUS_OPTIONS[focusMode]

  const dealsWithScores = useMemo<DealWithScores[]>(() => {
    return deals.map((d) => ({
      ...d,
      dealSmell: computeDealSmell(d),
      killerScore: computeKillerScore(d),
    }))
  }, [deals])

  if (isAdmin) {
    return (
      <AdminGroupedView
        dealsWithScores={dealsWithScores}
        allDeals={deals}
        selectedAccount={selectedAccount}
        opportunityCodeSearch={opportunityCodeSearch}
        onOpportunityCodeSearchChange={setOpportunityCodeSearch}
        dealStatusHistory={dealStatusHistory}
        onChangeDealStatus={onChangeDealStatus}
      />
    )
  }

  const handleSelectedDealStatusChange = (dealId: string, nextStage: DealStage) => {
    onChangeDealStatus(dealId, nextStage)
    setSelectedDeal((current) => {
      if (!current || current.opportunity_id !== dealId || current.deal_stage === nextStage) return current
      return applyCloseDateForStageChange(current, nextStage)
    })
  }

  // Seller view
  const filtered = useMemo(() => {
    let list = dealsWithScores
    if (selectedAccount) {
      list = list.filter((d) => d.account === selectedAccount)
    }

    const normalizedOpportunityCodeSearch = opportunityCodeSearch.trim().toLowerCase()

    if (!selectedAccount && !normalizedOpportunityCodeSearch) {
      list = list.filter(
        (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
      )
    }

    if (normalizedOpportunityCodeSearch) {
      list = list.filter((d) =>
        d.opportunity_id.toLowerCase().includes(normalizedOpportunityCodeSearch)
      )
    }

    const sorted = [...list]

    if (focusMode === 'dealSmell') {
      return sorted.sort((a, b) => (b.dealSmell - a.dealSmell) || (b.killerScore - a.killerScore))
    }

    if (focusMode === 'killScore') {
      return sorted.sort((a, b) => (b.killerScore - a.killerScore) || (b.dealSmell - a.dealSmell))
    }

    return sorted.sort((a, b) => {
      const aPriority = a.dealSmell * 0.55 + a.killerScore * 0.45
      const bPriority = b.dealSmell * 0.55 + b.killerScore * 0.45
      return (bPriority - aPriority) || (b.dealSmell - a.dealSmell)
    })
  }, [dealsWithScores, selectedAccount, focusMode, opportunityCodeSearch])

  return (
    <div className="p-6 space-y-3">
      <div className="mb-4 space-y-3">
        <div className="grid gap-2 md:grid-cols-3">
          {(Object.keys(SELLER_FOCUS_OPTIONS) as SellerFocusMode[]).map((mode) => {
            const option = SELLER_FOCUS_OPTIONS[mode]
            const isActive = focusMode === mode

            return (
              <button
                key={mode}
                type="button"
                onClick={() => setFocusMode(mode)}
                aria-pressed={isActive}
                className="rounded-2xl border p-3 text-left transition-all duration-200"
                style={{
                  borderColor: isActive ? option.accent : 'rgba(15,26,69,0.14)',
                  background: isActive ? option.activeBg : '#ffffff',
                  boxShadow: isActive ? `0 10px 26px -20px ${option.accent}` : 'none',
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex items-center gap-2">
                    <span
                      className="h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ background: option.softBg, color: option.accent }}
                    >
                      {mode === 'software' && <Sparkles size={14} />}
                      {mode === 'dealSmell' && <AlertTriangle size={14} />}
                      {mode === 'killScore' && <Target size={14} />}
                    </span>
                    <p className="text-xs font-semibold text-text-main leading-tight">{option.label}</p>
                  </div>
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full font-semibold tracking-wide uppercase"
                    style={{ color: option.accent, background: option.softBg }}
                  >
                    {option.badge}
                  </span>
                </div>
                <p className="text-xs mt-2 text-text-muted leading-relaxed">{option.summary}</p>
                {isActive && (
                  <div
                    className="mt-2 h-0.5 rounded-full"
                    style={{ background: `linear-gradient(90deg, ${option.accent} 0%, transparent 100%)` }}
                  />
                )}
              </button>
            )
          })}
        </div>

        <div
          className="rounded-xl border px-3 py-2"
          style={{
            borderColor: activeFocusOption.softBg,
            background: `linear-gradient(135deg, ${activeFocusOption.softBg} 0%, rgba(255,255,255,0.92) 100%)`,
          }}
        >
          <p className="text-xs leading-relaxed">
            <span className="font-semibold" style={{ color: activeFocusOption.accent }}>
              {activeFocusOption.badge}:
            </span>{' '}
            <span className="text-text-main">{activeFocusOption.summary}</span>
          </p>
        </div>

        {focusMode !== 'software' && (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setFocusMode('software')}
              className="text-xs px-3 py-1.5 rounded-full border font-semibold transition-colors inline-flex items-center gap-1.5"
              style={{
                borderColor: 'rgba(15,26,69,0.18)',
                color: '#0f1a45',
                background: '#ffffff',
              }}
            >
              <Undo2 size={13} />
              Voltar para visão indicada pelo software
            </button>
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="seller-opportunity-search"
            className="text-xs font-semibold text-text-muted uppercase tracking-wide"
          >
            Buscar por código da oportunidade
          </label>
          <div className="relative max-w-md">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--color-text-muted)' }}
            />
            <input
              id="seller-opportunity-search"
              type="search"
              value={opportunityCodeSearch}
              onChange={(e) => setOpportunityCodeSearch(e.target.value)}
              placeholder="Ex.: HAXMC4IX"
              className="w-full rounded-xl border bg-surface py-2.5 pl-9 pr-16 text-sm text-text-main outline-none transition-colors"
              style={{ borderColor: 'var(--color-border)' }}
            />
            {opportunityCodeSearch && (
              <button
                type="button"
                onClick={() => setOpportunityCodeSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-semibold text-primary hover:underline"
              >
                Limpar
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-text-main">
            Deals{' '}
            <span className="text-text-muted font-normal">
              — {SELLER_FOCUS_OPTIONS[focusMode].heading}
            </span>
          </h2>
          <span
            className="text-xs px-2 py-1 rounded-full"
            style={{ background: 'rgba(175,67,50,0.1)', color: '#af4332' }}
          >
            {filtered.length} deals
          </span>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-text-muted">
          <p className="text-sm">Nenhum deal encontrado</p>
          {opportunityCodeSearch.trim() && (
            <p className="text-xs mt-1">
              para o código {opportunityCodeSearch.trim().toUpperCase()}
            </p>
          )}
          {selectedAccount && (
            <p className="text-xs mt-1">para a conta {selectedAccount}</p>
          )}
        </div>
      ) : (
        filtered.map((d) => (
          <DealCard key={d.opportunity_id} deal={d} onSelect={() => setSelectedDeal(d)} />
        ))
      )}

      {selectedDeal && (
        <DealDetailPanel
          deal={selectedDeal}
          allDeals={deals}
          onClose={() => setSelectedDeal(null)}
          statusHistory={dealStatusHistory[selectedDeal.opportunity_id] ?? []}
          onChangeStatus={handleSelectedDealStatusChange}
          onSelectDeal={(nextDeal) => setSelectedDeal(nextDeal)}
        />
      )}
    </div>
  )
}
