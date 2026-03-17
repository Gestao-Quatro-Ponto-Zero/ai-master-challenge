'use client'

import { useState, useMemo } from 'react'
import { X, TrendingUp, Star } from 'lucide-react'
import DashboardNavbar from '@/components/DashboardNavbar'
import { DEALS, SALES_AGENTS } from '@/lib/data'
import { computeAllAccountRatings } from '@/lib/accountRating'
import { useAuth } from '@/context/AuthContext'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatRevenue(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

function pct(num: number, den: number): string {
  if (den === 0) return '0%'
  return `${Math.round((num / den) * 100)}%`
}

// ─── Compute agent stats ──────────────────────────────────────────────────────

function useAgentStats() {
  return useMemo(() => {
    const ratingMap = new Map(computeAllAccountRatings().map(r => [r.account, r.classificacao]))

    return SALES_AGENTS.map(agent => {
      const name = agent.sales_agent
      const agentDeals = DEALS.filter(d => d.sales_agent === name)
      const won = agentDeals.filter(d => d.deal_stage === 'Won')
      const lost = agentDeals.filter(d => d.deal_stage === 'Lost')
      const active = agentDeals.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting')

      const revenue = won.reduce((s, d) => s + d.close_value, 0)
      const avgTicket = won.length > 0 ? Math.round(revenue / won.length) : 0
      const winRate = won.length + lost.length > 0
        ? Math.round((won.length / (won.length + lost.length)) * 100)
        : 0

      const ratingDCount = active.filter(d => d.account && ratingMap.get(d.account) === 'D').length
      const ratingDPct = active.length > 0 ? Math.round((ratingDCount / active.length) * 100) : 0

      return {
        ...agent,
        totalDeals: agentDeals.length,
        wonDeals: won.length,
        lostDeals: lost.length,
        activeDeals: active.length,
        revenue,
        avgTicket,
        winRate,
        ratingDPct,
        allDeals: agentDeals,
      }
    })
  }, [])
}

// ─── Agent Drawer ─────────────────────────────────────────────────────────────

function AgentDrawer({ agentName, onClose, allStats }: {
  agentName: string
  onClose: () => void
  allStats: ReturnType<typeof useAgentStats>
}) {
  const stats = allStats.find(s => s.sales_agent === agentName)
  if (!stats) return null

  const stageColors: Record<string, string> = {
    Won: '#16a34a', Lost: '#af4332', Engaging: '#b9915b', Prospecting: '#60708a',
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}
      onClick={onClose}
    >
      <div
        style={{ background: '#ffffff', width: '480px', maxWidth: '100vw', height: '100vh', overflowY: 'auto', padding: '32px 28px', boxShadow: '-12px 0 50px rgba(0,0,0,0.2)', position: 'relative' }}
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'rgba(0,31,53,0.06)', border: 'none', borderRadius: '8px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#60708a' }}
          aria-label="Fechar"
        >
          <X size={16} />
        </button>

        {/* Agent header */}
        <div style={{ marginBottom: '24px' }}>
          <div
            style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#0f1a45', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px', fontWeight: 800, fontFamily: 'Manrope, sans-serif', marginBottom: '12px' }}
          >
            {stats.sales_agent.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#001f35', fontFamily: 'Manrope, sans-serif', marginBottom: '2px' }}>
            {stats.sales_agent}
          </h2>
          <p style={{ fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            {stats.regional_office} · {stats.manager}
          </p>
        </div>

        {/* Stats grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {[
            { label: 'Receita Won', value: formatRevenue(stats.revenue), color: '#16a34a' },
            { label: 'Win Rate', value: `${stats.winRate}%`, color: '#b9915b' },
            { label: 'Ticket Médio', value: formatRevenue(stats.avgTicket), color: '#0f1a45' },
            { label: 'Deals Ativos', value: stats.activeDeals.toString(), color: '#af4332' },
            { label: 'Deals Won', value: stats.wonDeals.toString(), color: '#16a34a' },
            { label: 'Rating D%', value: `${stats.ratingDPct}%`, color: stats.ratingDPct > 30 ? '#af4332' : '#60708a' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: '#f8f9fa', borderRadius: '10px', padding: '12px 14px' }}>
              <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>{label}</p>
              <p style={{ fontSize: '18px', fontWeight: 800, color, fontFamily: 'Manrope, sans-serif' }}>{value}</p>
            </div>
          ))}
        </div>

        {/* Recent deals */}
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', marginBottom: '12px' }}>
          Deals Recentes ({stats.allDeals.length})
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '350px', overflowY: 'auto' }}>
          {stats.allDeals.slice(0, 40).map(deal => (
            <div
              key={deal.opportunity_id}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#f8f9fa', borderRadius: '8px', fontSize: '12px' }}
            >
              <div>
                <span style={{ fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{deal.product}</span>
                {deal.account && <span style={{ color: '#60708a', marginLeft: '6px', fontFamily: 'Inter, sans-serif' }}>{deal.account}</span>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {deal.close_value > 0 && (
                  <span style={{ fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>${deal.close_value.toLocaleString()}</span>
                )}
                <span
                  style={{
                    background: `${stageColors[deal.deal_stage]}18`,
                    color: stageColors[deal.deal_stage],
                    borderRadius: '9999px',
                    padding: '2px 8px',
                    fontWeight: 600,
                    fontFamily: 'Inter, sans-serif',
                    fontSize: '11px',
                  }}
                >
                  {deal.deal_stage}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Agent Row ────────────────────────────────────────────────────────────────

function AgentRow({ stats, rank, onSelect, isMe }: {
  stats: ReturnType<typeof useAgentStats>[0]
  rank: number
  onSelect: () => void
  isMe?: boolean
}) {
  return (
    <tr
      onClick={onSelect}
      style={{ cursor: 'pointer', borderBottom: '1px solid rgba(0,31,53,0.06)', transition: 'background 0.15s' }}
      onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = '#f8f9fa'}
      onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
    >
      <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 700, color: rank <= 3 ? '#b9915b' : '#60708a', fontFamily: 'Manrope, sans-serif' }}>
        {rank <= 3 ? <Star size={14} style={{ display: 'inline', marginRight: '4px' }} /> : null}#{rank}
      </td>
      <td style={{ padding: '12px 16px' }}>
        <p className={isMe ? 'agent-blink' : ''} style={{ fontSize: '14px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{stats.sales_agent}</p>
        <p style={{ fontSize: '11px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>{stats.manager}</p>
      </td>
      <td style={{ padding: '12px 16px', fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>{stats.regional_office}</td>
      <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 700, color: '#16a34a', fontFamily: 'Manrope, sans-serif' }}>{formatRevenue(stats.revenue)}</td>
      <td style={{ padding: '12px 16px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
        <span style={{ fontWeight: 600 }}>{stats.wonDeals}</span>
        <span style={{ color: '#60708a', marginLeft: '4px' }}>/ {stats.wonDeals + stats.lostDeals}</span>
      </td>
      <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 700, color: '#b9915b', fontFamily: 'Manrope, sans-serif' }}>{stats.winRate}%</td>
      <td style={{ padding: '12px 16px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{formatRevenue(stats.avgTicket)}</td>
      <td style={{ padding: '12px 16px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{stats.activeDeals}</td>
      <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 600, color: stats.ratingDPct > 30 ? '#af4332' : '#001f35', fontFamily: 'Manrope, sans-serif' }}>
        {stats.ratingDPct}%
      </td>
    </tr>
  )
}

// ─── Org Chart ────────────────────────────────────────────────────────────────

function OrgChart({ agentStats, visibleAgents, currentAgent }: { agentStats: ReturnType<typeof useAgentStats>; visibleAgents: typeof SALES_AGENTS; currentAgent: string | null }) {
  const regionOrder = ['Central', 'East', 'West']
  const regions = regionOrder.filter(region => visibleAgents.some(a => a.regional_office === region))
  const visibleAgentNames = new Set(visibleAgents.map(a => a.sales_agent))

  if (regions.length === 0) return null

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${Math.max(regions.length, 1)}, minmax(0, 1fr))`,
        gap: '20px',
        marginBottom: '40px',
      }}
    >
      {regions.map(region => {
        const regionAgents = visibleAgents.filter(a => a.regional_office === region)
        const managers = Array.from(new Set(regionAgents.map(a => a.manager)))

        const regionRevenue = agentStats
          .filter(s => s.regional_office === region && visibleAgentNames.has(s.sales_agent))
          .reduce((sum, s) => sum + s.revenue, 0)

        return (
          <div
            key={region}
            style={{
              background: '#ffffff',
              border: '1px solid rgba(0,31,53,0.1)',
              borderRadius: '16px',
              padding: '20px',
              boxShadow: '0 0 22px rgba(0,0,0,0.07)',
            }}
          >
            {/* Region header */}
            <div
              style={{
                background: '#0f1a45',
                borderRadius: '10px',
                padding: '12px 16px',
                marginBottom: '16px',
                textAlign: 'center',
              }}
            >
              <p style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff', fontFamily: 'Manrope, sans-serif', letterSpacing: '0.04em' }}>
                {region}
              </p>
              <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', fontFamily: 'Inter, sans-serif', marginTop: '2px' }}>
                {formatRevenue(regionRevenue)}
              </p>
            </div>

            {/* Managers + agents */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {managers.map(manager => {
                const managerAgents = regionAgents.filter(a => a.manager === manager)
                const managerAgentsByRevenue = managerAgents
                  .map(a => ({ agent: a, stats: agentStats.find(s => s.sales_agent === a.sales_agent) }))
                  .sort((a, b) => (b.stats?.revenue ?? 0) - (a.stats?.revenue ?? 0))

                return (
                  <div key={manager}>
                    {/* Manager box */}
                    <div
                      style={{
                        background: 'rgba(185,145,91,0.1)',
                        border: '1px solid rgba(185,145,91,0.3)',
                        borderRadius: '8px',
                        padding: '8px 12px',
                        marginBottom: '6px',
                      }}
                    >
                      <p style={{ fontSize: '12px', fontWeight: 700, color: '#0f1a45', fontFamily: 'Manrope, sans-serif' }}>{manager}</p>
                      <p style={{ fontSize: '10px', color: '#b9915b', fontFamily: 'Inter, sans-serif' }}>Manager</p>
                    </div>

                    {/* Agents */}
                    <div style={{ paddingLeft: '12px', borderLeft: '2px solid rgba(0,31,53,0.1)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'minmax(0, 1fr) 120px 170px',
                          alignItems: 'center',
                          columnGap: '18px',
                          padding: '2px 10px',
                          fontSize: '10px',
                          fontWeight: 700,
                          color: '#60708a',
                          fontFamily: 'Inter, sans-serif',
                          letterSpacing: '0.03em',
                          textTransform: 'uppercase',
                        }}
                      >
                        <span>Nome</span>
                        <span style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Receita</span>
                        <span style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Taxa de Conversão</span>
                      </div>
                      {managerAgentsByRevenue.map(({ agent: a, stats }) => {
                        const isMe = currentAgent === a.sales_agent
                        return (
                          <div
                            key={a.sales_agent}
                            style={{
                              background: '#f8f9fa',
                              borderRadius: '6px',
                              padding: '6px 10px',
                              display: 'grid',
                              gridTemplateColumns: 'minmax(0, 1fr) 120px 170px',
                              alignItems: 'center',
                              columnGap: '18px',
                            }}
                          >
                            <p className={isMe ? 'agent-blink' : ''} style={{ fontSize: '11px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                              {a.sales_agent.split(' ')[0]}
                            </p>
                            <span style={{ fontSize: '10px', color: '#0f1a45', fontWeight: 700, fontFamily: 'Inter, sans-serif', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                              {formatRevenue(stats?.revenue ?? 0)}
                            </span>
                            {stats && (
                              <span style={{ fontSize: '10px', color: '#16a34a', fontWeight: 700, fontFamily: 'Inter, sans-serif', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                                {stats.winRate}%
                              </span>
                            )}
                            {!stats && (
                              <span style={{ fontSize: '10px', color: '#60708a', fontWeight: 700, fontFamily: 'Inter, sans-serif', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                                0%
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TeamPage() {
  const { role, agent } = useAuth()
  const agentStats = useAgentStats()
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)

  const sellerManager = useMemo(() => {
    if (role !== 'seller' || !agent) return null
    return SALES_AGENTS.find(a => a.sales_agent === agent)?.manager ?? null
  }, [role, agent])

  const visibleAgents = useMemo(() => {
    if (!sellerManager) return SALES_AGENTS
    return SALES_AGENTS.filter(a => a.manager === sellerManager)
  }, [sellerManager])
  const visibleManagersCount = useMemo(() => new Set(visibleAgents.map(a => a.manager)).size, [visibleAgents])
  const visibleRegionsCount = useMemo(() => new Set(visibleAgents.map(a => a.regional_office)).size, [visibleAgents])

  const sortedAgents = useMemo(
    () => [...agentStats]
      .filter(s => visibleAgents.some(v => v.sales_agent === s.sales_agent))
      .sort((a, b) => b.revenue - a.revenue),
    [agentStats, visibleAgents]
  )

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <style>{`
        @keyframes blink-name {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.2; }
        }
        .agent-blink { animation: blink-name 1.2s ease-in-out infinite; }
      `}</style>
      <DashboardNavbar />

      <main
        style={{
          paddingTop: '94px',
          paddingLeft: '24px',
          paddingRight: '24px',
          paddingBottom: '48px',
          maxWidth: '1400px',
          margin: '0 auto',
        }}
      >
        {/* Page header */}
        <div style={{ marginBottom: '28px' }}>
          <h1
            style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#001f35',
              fontFamily: 'Manrope, sans-serif',
              marginBottom: '4px',
            }}
          >
            Equipe
          </h1>
          <p style={{ fontSize: '14px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            {visibleAgents.length} agentes · {visibleManagersCount} {visibleManagersCount === 1 ? 'manager' : 'managers'} · {visibleRegionsCount} {visibleRegionsCount === 1 ? 'região' : 'regiões'}
          </p>
        </div>

        {/* Org chart */}
        <div style={{ marginBottom: '16px' }}>
          <h2
            style={{
              fontSize: '16px',
              fontWeight: 700,
              color: '#001f35',
              fontFamily: 'Manrope, sans-serif',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <TrendingUp size={16} style={{ color: '#b9915b' }} />
            Organograma
          </h2>
          <OrgChart agentStats={agentStats} visibleAgents={visibleAgents} currentAgent={agent} />
        </div>

        {/* Leaderboard table */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid rgba(0,31,53,0.1)',
            borderRadius: '16px',
            boxShadow: '0 0 22px rgba(0,0,0,0.07)',
            overflow: 'hidden',
          }}
        >
          <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(0,31,53,0.08)' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
              Leaderboard de Agentes
            </h2>
            <p style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', marginTop: '2px' }}>
              Clique em um agente para ver detalhes
            </p>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(0,31,53,0.08)' }}>
                  {['#', 'Agente', 'Região', 'Receita', 'Won / Total', 'Win Rate', 'Ticket Médio', 'Ativos', 'Rating D%'].map(col => (
                    <th
                      key={col}
                      style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '11px',
                        fontWeight: 700,
                        color: '#60708a',
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                        fontFamily: 'Inter, sans-serif',
                        background: '#fafbfc',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedAgents.map((stats, i) => (
                  <AgentRow
                    key={stats.sales_agent}
                    stats={stats}
                    rank={i + 1}
                    onSelect={() => setSelectedAgent(stats.sales_agent)}
                    isMe={stats.sales_agent === agent}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {selectedAgent && (
        <AgentDrawer
          agentName={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          allStats={agentStats}
        />
      )}
    </div>
  )
}
