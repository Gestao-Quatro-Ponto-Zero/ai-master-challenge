'use client'

import { useState, useMemo, useEffect, useCallback, useReducer } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import DashboardNavbar from '../../components/DashboardNavbar'
import AccountsSidebar from '../../components/AccountsSidebar'
import ListView from '../../components/views/ListView'
import KanbanView from '../../components/views/KanbanView'
import { DEALS, Deal, DealStage } from '../../lib/data'
import { DealStatusHistoryEntry } from '../../lib/dealStatusHistory'
import { computeDealSmell, computeKillerScore } from '../../lib/scores'
import DailyBriefingModal from '../../components/DailyBriefingModal'

type ViewMode = 'list' | 'kanban'
type KpiCard = {
  label: string
  value: string
  sub: string
  color: string
}

type DealsState = {
  dealsInScope: Deal[]
  dealStatusHistory: Record<string, DealStatusHistoryEntry[]>
}

type DealsAction =
  | { type: 'reset_scope'; deals: Deal[] }
  | { type: 'change_status'; dealId: string; nextStage: DealStage; changedAt: string }

function dealsStateReducer(state: DealsState, action: DealsAction): DealsState {
  switch (action.type) {
    case 'reset_scope':
      return {
        dealsInScope: action.deals,
        dealStatusHistory: {},
      }
    case 'change_status': {
      const currentDeal = state.dealsInScope.find((deal) => deal.opportunity_id === action.dealId)
      if (!currentDeal || currentDeal.deal_stage === action.nextStage) return state

      const today = action.changedAt.slice(0, 10)
      const isClosedStage = action.nextStage === 'Won' || action.nextStage === 'Lost'

      return {
        dealsInScope: state.dealsInScope.map((deal) => {
          if (deal.opportunity_id !== action.dealId) return deal
          return {
            ...deal,
            deal_stage: action.nextStage,
            close_date: isClosedStage ? (deal.close_date || today) : '',
          }
        }),
        dealStatusHistory: {
          ...state.dealStatusHistory,
          [action.dealId]: [
            {
              from: currentDeal.deal_stage,
              to: action.nextStage,
              changedAt: action.changedAt,
            },
            ...(state.dealStatusHistory[action.dealId] ?? []),
          ],
        },
      }
    }
    default:
      return state
  }
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`
  return `$${value.toFixed(0)}`
}

function buildKpiCards(dealsInScope: Deal[]): KpiCard[] {
  const wonDeals = dealsInScope.filter((d) => d.deal_stage === 'Won')
  const lostDeals = dealsInScope.filter((d) => d.deal_stage === 'Lost')
  const activeDeals = dealsInScope.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  )

  const totalRevenue = wonDeals.reduce((sum, deal) => sum + deal.close_value, 0)
  const wonAndLostTotal = wonDeals.length + lostDeals.length
  const winRate = wonAndLostTotal > 0
    ? Math.round((wonDeals.length / wonAndLostTotal) * 1000) / 10
    : 0
  const avgTicket = wonDeals.length > 0 ? Math.round(totalRevenue / wonDeals.length) : 0

  return [
    {
      label: 'Receita Total (Won)',
      value: formatCurrency(totalRevenue),
      sub: `${wonDeals.length} deals fechados`,
      color: '#16a34a',
    },
    {
      label: 'Win Rate',
      value: `${winRate}%`,
      sub: `${lostDeals.length} deals perdidos`,
      color: '#b9915b',
    },
    {
      label: 'Ticket Médio (Won)',
      value: formatCurrency(avgTicket),
      sub: 'por deal fechado',
      color: '#0f1a45',
    },
    {
      label: 'Pipeline Ativo',
      value: `${activeDeals.length.toLocaleString()} deals`,
      sub: 'Engaging + Prospecting',
      color: '#af4332',
    },
  ]
}

export default function DashboardPage() {
  const { isAuthenticated, role, agent } = useAuth()
  const router = useRouter()
  const [view, setView] = useState<ViewMode>('list')
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [showDealsWithoutAccount, setShowDealsWithoutAccount] = useState(false)
  const [dealsState, dispatchDealsState] = useReducer(dealsStateReducer, {
    dealsInScope: [],
    dealStatusHistory: {},
  })
  const [showBriefing, setShowBriefing] = useState(false)

  const dealsInScope = dealsState.dealsInScope
  const dealStatusHistory = dealsState.dealStatusHistory

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login')
    }
  }, [isAuthenticated, router])

  // Auto-open daily briefing once per session for sellers
  useEffect(() => {
    if (role === 'seller' && isAuthenticated) {
      const key = `g4crm_briefing_${agent}`
      if (!sessionStorage.getItem(key)) {
        setShowBriefing(true)
        sessionStorage.setItem(key, '1')
      }
    }
  }, [role, isAuthenticated, agent])

  const scopedDeals = useMemo(() => {
    if (role === 'seller' && agent) {
      return DEALS.filter((d) => d.sales_agent === agent)
    }
    return DEALS
  }, [role, agent])

  useEffect(() => {
    dispatchDealsState({ type: 'reset_scope', deals: scopedDeals })
  }, [scopedDeals])

  const handleDealStatusChange = useCallback((dealId: string, nextStage: DealStage) => {
    dispatchDealsState({
      type: 'change_status',
      dealId,
      nextStage,
      changedAt: new Date().toISOString(),
    })
  }, [])

  const kpiCards = useMemo(() => buildKpiCards(dealsInScope), [dealsInScope])

  const top3Deals = useMemo(() => {
    if (role !== 'seller') return []
    const active = dealsInScope.filter(
      (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
    )
    return active
      .map((d) => ({ deal: d, score: computeDealSmell(d) * 0.55 + computeKillerScore(d) * 0.45 }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
      .map((x) => x.deal)
  }, [role, dealsInScope])

  const dealsWithoutAccountCount = useMemo(() => {
    if (role !== 'seller' || !agent) return 0
    return dealsInScope.filter((d) => !d.account?.trim()).length
  }, [role, agent, dealsInScope])

  const filteredDeals = useMemo(() => {
    if (role === 'seller' && agent) {
      let sellerDeals = dealsInScope

      if (!showDealsWithoutAccount) {
        sellerDeals = sellerDeals.filter((d) => Boolean(d.account?.trim()))
      }

      if (selectedAccount) {
        return sellerDeals.filter((d) => d.account === selectedAccount)
      }
      return sellerDeals
    }
    return dealsInScope
  }, [role, agent, selectedAccount, dealsInScope, showDealsWithoutAccount])

  if (!isAuthenticated) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: '#0f1a45' }}
      >
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      <DashboardNavbar view={view} onViewChange={setView} />

      {showBriefing && top3Deals.length > 0 && (
        <DailyBriefingModal
          deals={top3Deals}
          agentName={agent ?? ''}
          onClose={() => setShowBriefing(false)}
        />
      )}

      <div className="dashboard-body">
        {/* Sidebar */}
        <AccountsSidebar
          selectedAccount={selectedAccount}
          onSelectAccount={setSelectedAccount}
        />

        {/* Main content */}
        <main className="dashboard-main" role="main">
          {/* KPI Row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '16px',
              marginBottom: '24px',
              padding: '0 4px',
            }}
          >
            {kpiCards.map((kpi) => (
              <div
                key={kpi.label}
                style={{
                  background: '#ffffff',
                  border: '1px solid rgba(0,31,53,0.1)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  borderLeft: `4px solid ${kpi.color}`,
                }}
              >
                <p
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: '#60708a',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    marginBottom: '6px',
                    fontFamily: 'Inter, sans-serif',
                  }}
                >
                  {kpi.label}
                </p>
                <p
                  style={{
                    fontSize: '22px',
                    fontWeight: 800,
                    color: kpi.color,
                    fontFamily: 'Manrope, sans-serif',
                    lineHeight: 1.1,
                    marginBottom: '4px',
                  }}
                >
                  {kpi.value}
                </p>
                <p
                  style={{
                    fontSize: '12px',
                    color: '#60708a',
                    fontFamily: 'Inter, sans-serif',
                  }}
                >
                  {kpi.sub}
                </p>
              </div>
            ))}
          </div>

          {view === 'list' ? (
            <ListView
              deals={filteredDeals}
              isAdmin={role === 'admin'}
              selectedAccount={selectedAccount}
              dealStatusHistory={dealStatusHistory}
              onChangeDealStatus={handleDealStatusChange}
              showDealsWithoutAccount={showDealsWithoutAccount}
              onToggleShowDealsWithoutAccount={() =>
                setShowDealsWithoutAccount((current) => !current)
              }
              dealsWithoutAccountCount={dealsWithoutAccountCount}
            />
          ) : (
            <KanbanView
              deals={filteredDeals}
              isAdmin={role === 'admin'}
              selectedAccount={selectedAccount}
              dealStatusHistory={dealStatusHistory}
              onChangeDealStatus={handleDealStatusChange}
            />
          )}
        </main>
      </div>
    </div>
  )
}
