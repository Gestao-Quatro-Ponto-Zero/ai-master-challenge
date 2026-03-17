'use client'

import { useState, useMemo } from 'react'
import { Flame, ChevronDown } from 'lucide-react'
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

interface KanbanViewProps {
  deals: Deal[]
  isAdmin: boolean
  selectedAccount: string | null
  dealStatusHistory: Record<string, DealStatusHistoryEntry[]>
  onChangeDealStatus: (dealId: string, nextStage: DealStage) => void
}

const KANBAN_STAGES = ['Prospecting', 'Engaging'] as const
type KanbanStage = (typeof KANBAN_STAGES)[number]

const COLUMN_STYLES: Record<KanbanStage, { bg: string; header: string; headerText: string; dot: string }> = {
  Prospecting: {
    bg: '#f5f6fb',
    header: '#0f1a45',
    headerText: '#ffffff',
    dot: 'rgba(255,255,255,0.5)',
  },
  Engaging: {
    bg: '#fdf8f2',
    header: '#b9915b',
    headerText: '#ffffff',
    dot: 'rgba(255,255,255,0.5)',
  },
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

function KanbanCard({
  deal,
  onSelect,
}: {
  deal: Deal & { dealSmell: number; killerScore: number }
  onSelect: () => void
}) {
  const killer = isKillerDeal(deal)
  const reasons = generateDealReasons(deal)
  const reasonsToShow = killer ? reasons.slice(0, 2) : reasons.slice(0, 1)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
      className="bg-surface rounded-lg p-3 cursor-pointer transition-all duration-200 hover:shadow-md"
      style={{
        border: killer ? '2px solid rgba(185,145,91,0.3)' : '1px solid rgba(0,31,53,0.12)',
        animation: killer ? 'killer-pulse 2s ease-in-out infinite' : undefined,
      }}
      aria-label={`Deal: ${deal.account || 'Sem conta'} - ${deal.product}`}
    >
      {/* Badge row */}
      <div className="flex items-center gap-1.5 flex-wrap mb-2">
        {killer && (
          <Badge variant="primary" className="flex items-center gap-1 !text-[10px] !px-1.5 !py-0.5">
            <Flame size={9} />
            KILLER
          </Badge>
        )}
      </div>

      {/* Account */}
      <p className="text-xs font-bold text-text-main truncate mb-1">
        {deal.account || <span className="text-text-muted italic">Sem conta</span>}
      </p>

      {/* Product */}
      <p className="text-xs text-text-muted mb-2">{deal.product}</p>

      {/* Agent */}
      <p className="text-xs text-text-muted mb-2 truncate">{deal.sales_agent}</p>

      {/* Reasons */}
      {reasonsToShow.length > 0 && (
        <p className="text-xs text-text-muted italic mb-2">
          {reasonsToShow.join(' · ')}
        </p>
      )}

      {/* Scores row */}
      <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold" style={{ color: getScoreColor(deal.dealSmell) }}>
            DS {deal.dealSmell}
          </span>
          <span className="text-xs text-text-muted">·</span>
          <span
            className="text-xs font-semibold px-1.5 py-0.5 rounded"
            style={{ color: getScoreColor(deal.killerScore), background: getScoreBg(deal.killerScore) }}
          >
            KS {deal.killerScore}
          </span>
        </div>
      </div>
    </div>
  )
}

export default function KanbanView({
  deals,
  isAdmin,
  selectedAccount,
  dealStatusHistory,
  onChangeDealStatus,
}: KanbanViewProps) {
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [agentFilter, setAgentFilter] = useState<string>('')

  const agents = useMemo(
    () => Array.from(new Set(deals.map((d) => d.sales_agent))).sort(),
    [deals]
  )

  const dealsWithScores = useMemo(
    () =>
      deals.map((d) => ({
        ...d,
        dealSmell: computeDealSmell(d),
        killerScore: computeKillerScore(d),
      })),
    [deals]
  )

  const filtered = useMemo(() => {
    let list = dealsWithScores
    if (selectedAccount) list = list.filter((d) => d.account === selectedAccount)
    if (agentFilter) list = list.filter((d) => d.sales_agent === agentFilter)
    return list
  }, [dealsWithScores, selectedAccount, agentFilter])

  const byStage = useMemo(() => {
    const map: Record<KanbanStage, typeof filtered> = {
      Prospecting: [],
      Engaging: [],
    }
    for (const d of filtered) {
      if (d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging') {
        map[d.deal_stage].push(d)
      }
    }
    // Sort each column by dealSmell desc
    for (const stage of KANBAN_STAGES) {
      map[stage] = map[stage].sort((a, b) => b.dealSmell - a.dealSmell)
    }
    return map
  }, [filtered])

  const handleSelectedDealStatusChange = (dealId: string, nextStage: DealStage) => {
    onChangeDealStatus(dealId, nextStage)
    setSelectedDeal((current) => {
      if (!current || current.opportunity_id !== dealId || current.deal_stage === nextStage) return current
      return applyCloseDateForStageChange(current, nextStage)
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      {isAdmin && (
        <div
          className="px-6 py-3 border-b flex items-center gap-3 flex-wrap"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        >
          <span className="text-xs font-semibold text-text-muted">Filtrar por vendedor:</span>
          <div className="relative">
            <select
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              className="text-xs rounded-md bg-fade border py-1.5 pl-3 pr-8 outline-none appearance-none"
              style={{
                borderColor: 'var(--color-border)',
                color: 'var(--color-text)',
                fontFamily: 'var(--font-sans)',
                minWidth: '180px',
              }}
            >
              <option value="">Todos os vendedores</option>
              {agents.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
            <ChevronDown
              size={12}
              className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--color-text-muted)' }}
            />
          </div>
          {agentFilter && (
            <button
              onClick={() => setAgentFilter('')}
              className="text-xs text-primary font-semibold hover:underline"
            >
              Limpar
            </button>
          )}
        </div>
      )}

      {/* Board */}
      <div className="flex-1 overflow-auto p-6">
        <div className="kanban-board">
          {KANBAN_STAGES.map((stage) => {
            const style = COLUMN_STYLES[stage]
            const stageDeals = byStage[stage]
            const totalValue = stageDeals.reduce((sum, d) => sum + (d.close_value ?? 0), 0)
            const headerContent = (
              <>
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: style.dot }}
                  />
                  <span className="text-xs font-bold" style={{ color: style.headerText }}>
                    {stage}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded-full"
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      color: style.headerText,
                    }}
                  >
                    {stageDeals.length}
                  </span>
                </div>
              </>
            )

            return (
              <div
                key={stage}
                className="flex flex-col rounded-xl overflow-hidden"
                style={{
                  background: style.bg,
                  border: '1px solid rgba(0,0,0,0.06)',
                }}
              >
                {/* Column header */}
                <div
                  className="px-4 py-3 flex items-center justify-between"
                  style={{ background: style.header }}
                >
                  {headerContent}
                </div>

                {/* Total value (if any) */}
                {totalValue > 0 && (
                  <div
                    className="px-4 py-2 text-xs font-semibold"
                    style={{ background: 'rgba(0,0,0,0.03)', color: style.header, borderBottom: '1px solid rgba(0,0,0,0.06)' }}
                  >
                    Total: ${totalValue.toLocaleString()}
                  </div>
                )}

                {/* Cards */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2" style={{ maxHeight: 'calc(100vh - 280px)' }}>
                  {stageDeals.length === 0 ? (
                    <div className="text-center py-8 text-xs text-text-muted">
                      Sem deals nesta coluna
                    </div>
                  ) : (
                    stageDeals.map((d) => (
                      <KanbanCard
                        key={d.opportunity_id}
                        deal={d}
                        onSelect={() => setSelectedDeal(d)}
                      />
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

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
