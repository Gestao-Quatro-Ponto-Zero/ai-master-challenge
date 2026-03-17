'use client'

import { useState, useMemo, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { useRouter } from 'next/navigation'
import DashboardNavbar from '@/components/DashboardNavbar'
import { DEALS, SALES_AGENTS } from '@/lib/data'
import { useAuth } from '@/context/AuthContext'
import { computeAllAccountRatings } from '@/lib/accountRating'
import { computeAllKillScores } from '@/lib/killScore'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatRevenue(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

type TabId = 'agents' | 'managers' | 'regions'

// ─── Compute Stats ────────────────────────────────────────────────────────────

function useStats() {
  return useMemo(() => {
    const ratingMap = new Map(computeAllAccountRatings().map(r => [r.account, r.classificacao]))
    const killMap = new Map(computeAllKillScores().map(k => [k.opportunity_id, k]))

    const agentStats = SALES_AGENTS.map(agent => {
      const name = agent.sales_agent
      const agentDeals = DEALS.filter(d => d.sales_agent === name)
      const won = agentDeals.filter(d => d.deal_stage === 'Won')
      const lost = agentDeals.filter(d => d.deal_stage === 'Lost')
      const active = agentDeals.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting')

      const revenue = won.reduce((s, d) => s + d.close_value, 0)
      const avgTicket = won.length > 0 ? Math.round(revenue / won.length) : 0
      const winRate = won.length + lost.length > 0 ? Math.round((won.length / (won.length + lost.length)) * 100) : 0

      const ratingDCount = active.filter(d => d.account && ratingMap.get(d.account) === 'D').length
      const ratingDPct = active.length > 0 ? Math.round((ratingDCount / active.length) * 100) : 0

      const killRedCount = active.filter(d => killMap.get(d.opportunity_id)?.kill_classificacao === 'Vermelho').length
      const killRedPct = active.length > 0 ? Math.round((killRedCount / active.length) * 100) : 0

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
        killRedPct,
      }
    })

    // Manager stats
    const managerNames = Array.from(new Set(SALES_AGENTS.map(a => a.manager)))
    const managerStats = managerNames.map(manager => {
      const team = agentStats.filter(a => a.manager === manager)
      return {
        manager,
        region: team[0]?.regional_office ?? '',
        agentCount: team.length,
        totalDeals: team.reduce((s, a) => s + a.totalDeals, 0),
        wonDeals: team.reduce((s, a) => s + a.wonDeals, 0),
        revenue: team.reduce((s, a) => s + a.revenue, 0),
        avgWinRate: team.length > 0 ? Math.round(team.reduce((s, a) => s + a.winRate, 0) / team.length) : 0,
        avgTicket: (() => {
          const totalWon = team.reduce((s, a) => s + a.wonDeals, 0)
          const totalRev = team.reduce((s, a) => s + a.revenue, 0)
          return totalWon > 0 ? Math.round(totalRev / totalWon) : 0
        })(),
        activeDeals: team.reduce((s, a) => s + a.activeDeals, 0),
        avgRatingDPct: team.length > 0 ? Math.round(team.reduce((s, a) => s + a.ratingDPct, 0) / team.length) : 0,
        avgKillRedPct: team.length > 0 ? Math.round(team.reduce((s, a) => s + a.killRedPct, 0) / team.length) : 0,
      }
    })

    // Region stats
    const regionNames = ['Central', 'East', 'West']
    const regionStats = regionNames.map(region => {
      const team = agentStats.filter(a => a.regional_office === region)
      const revenue = team.reduce((s, a) => s + a.revenue, 0)
      const wonDeals = team.reduce((s, a) => s + a.wonDeals, 0)
      const lostDeals = team.reduce((s, a) => s + a.lostDeals, 0)
      const activeDeals = team.reduce((s, a) => s + a.activeDeals, 0)
      const winRate = wonDeals + lostDeals > 0 ? Math.round((wonDeals / (wonDeals + lostDeals)) * 100) : 0

      return { region, revenue, wonDeals, lostDeals, activeDeals, winRate, agentCount: team.length }
    })

    // Global KPIs
    const wonAll = DEALS.filter(d => d.deal_stage === 'Won')
    const lostAll = DEALS.filter(d => d.deal_stage === 'Lost')
    const activeAll = DEALS.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting')
    const totalRevenue = wonAll.reduce((s, d) => s + d.close_value, 0)
    const globalWinRate = Math.round((wonAll.length / (wonAll.length + lostAll.length)) * 100)
    const globalAvgTicket = wonAll.length > 0 ? Math.round(totalRevenue / wonAll.length) : 0

    return { agentStats, managerStats, regionStats, totalRevenue, globalWinRate, globalAvgTicket, wonAll, activeAll }
  }, [])
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid rgba(0,31,53,0.1)',
        borderRadius: '12px',
        padding: '18px 20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        borderLeft: `4px solid ${color}`,
      }}
    >
      <p style={{ fontSize: '11px', fontWeight: 600, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', marginBottom: '6px' }}>
        {label}
      </p>
      <p style={{ fontSize: '24px', fontWeight: 800, color, fontFamily: 'Manrope, sans-serif', lineHeight: 1, marginBottom: '4px' }}>
        {value}
      </p>
      <p style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>{sub}</p>
    </div>
  )
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function BarTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { region: string; revenue: number; winRate: number } }> }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#0f1a45', color: '#fff', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', fontFamily: 'Manrope, sans-serif' }}>
      <p style={{ fontWeight: 700 }}>{d.region}</p>
      <p style={{ color: '#b9915b' }}>{formatRevenue(d.revenue)}</p>
      <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Win rate: {d.winRate}%</p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PerformancePage() {
  const { role, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated && role === 'seller') {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, role, router])

  const [tab, setTab] = useState<TabId>('agents')
  const stats = useStats()

  const sortedAgents = useMemo(() => [...stats.agentStats].sort((a, b) => b.revenue - a.revenue), [stats])
  const sortedManagers = useMemo(() => [...stats.managerStats].sort((a, b) => b.revenue - a.revenue), [stats])

  const REGION_COLORS: Record<string, string> = {
    Central: '#0f1a45',
    East: '#b9915b',
    West: '#af4332',
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
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
          <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#001f35', fontFamily: 'Manrope, sans-serif', marginBottom: '4px' }}>
            Performance
          </h1>
          <p style={{ fontSize: '14px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            Visão geral de performance de vendas
          </p>
        </div>

        {/* KPI row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '16px',
            marginBottom: '32px',
          }}
        >
          <KpiCard label="Receita Total" value={formatRevenue(stats.totalRevenue)} sub={`${stats.wonAll.length} deals ganhos`} color="#16a34a" />
          <KpiCard label="Win Rate" value={`${stats.globalWinRate}%`} sub="Won / (Won + Lost)" color="#b9915b" />
          <KpiCard label="Ticket Médio" value={formatRevenue(stats.globalAvgTicket)} sub="por deal Won" color="#0f1a45" />
          <KpiCard label="Pipeline Ativo" value={stats.activeAll.length.toLocaleString()} sub="Engaging + Prospecting" color="#af4332" />
          <KpiCard label="Total Deals" value={DEALS.length.toLocaleString()} sub="todos os estágios" color="#60708a" />
        </div>

        {/* Tab switcher */}
        <div
          style={{
            display: 'flex',
            gap: '0',
            marginBottom: '24px',
            background: '#ffffff',
            border: '1px solid rgba(0,31,53,0.1)',
            borderRadius: '12px',
            padding: '4px',
            width: 'fit-content',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
        >
          {([
            { id: 'agents' as TabId, label: 'Agentes' },
            { id: 'managers' as TabId, label: 'Managers' },
            { id: 'regions' as TabId, label: 'Regiões' },
          ] as const).map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              style={{
                padding: '8px 20px',
                border: 'none',
                borderRadius: '9px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: 'Manrope, sans-serif',
                background: tab === id ? '#0f1a45' : 'transparent',
                color: tab === id ? '#ffffff' : '#60708a',
                transition: 'all 0.2s ease',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Agentes tab */}
        {tab === 'agents' && (
          <div
            style={{
              background: '#ffffff',
              border: '1px solid rgba(0,31,53,0.1)',
              borderRadius: '16px',
              boxShadow: '0 0 22px rgba(0,0,0,0.07)',
              overflow: 'hidden',
            }}
          >
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(0,31,53,0.08)', background: '#fafbfc' }}>
                    {['#', 'Agente', 'Região', 'Manager', 'Receita', 'Win Rate', 'Ticket Médio', 'Ativos', 'Rating D%', 'Kill Red%'].map(col => (
                      <th key={col} style={{ padding: '12px 14px', textAlign: 'left', fontSize: '11px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedAgents.map((a, i) => (
                    <tr
                      key={a.sales_agent}
                      style={{ borderBottom: '1px solid rgba(0,31,53,0.06)', transition: 'background 0.15s' }}
                      onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = '#f8f9fa'}
                      onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
                    >
                      <td style={{ padding: '11px 14px', fontSize: '13px', fontWeight: 700, color: i < 3 ? '#b9915b' : '#60708a', fontFamily: 'Manrope, sans-serif' }}>
                        #{i + 1}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {a.sales_agent}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
                        <span
                          style={{
                            background: `${REGION_COLORS[a.regional_office]}12`,
                            color: REGION_COLORS[a.regional_office],
                            borderRadius: '9999px',
                            padding: '2px 8px',
                            fontWeight: 600,
                            fontSize: '11px',
                          }}
                        >
                          {a.regional_office}
                        </span>
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}>
                        {a.manager}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '14px', fontWeight: 700, color: '#16a34a', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {formatRevenue(a.revenue)}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', fontWeight: 700, color: '#b9915b', fontFamily: 'Manrope, sans-serif' }}>
                        {a.winRate}%
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {formatRevenue(a.avgTicket)}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                        {a.activeDeals}
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', fontWeight: 600, color: a.ratingDPct > 30 ? '#af4332' : '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                        {a.ratingDPct}%
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '13px', fontWeight: 600, color: a.killRedPct > 30 ? '#af4332' : '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                        {a.killRedPct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Managers tab */}
        {tab === 'managers' && (
          <div
            style={{
              background: '#ffffff',
              border: '1px solid rgba(0,31,53,0.1)',
              borderRadius: '16px',
              boxShadow: '0 0 22px rgba(0,0,0,0.07)',
              overflow: 'hidden',
            }}
          >
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(0,31,53,0.08)', background: '#fafbfc' }}>
                    {['#', 'Manager', 'Região', 'Time', 'Receita', 'Win Rate', 'Ticket Médio', 'Ativos', 'Avg Rating D%', 'Avg Kill Red%'].map(col => (
                      <th key={col} style={{ padding: '12px 14px', textAlign: 'left', fontSize: '11px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedManagers.map((m, i) => (
                    <tr
                      key={m.manager}
                      style={{ borderBottom: '1px solid rgba(0,31,53,0.06)', transition: 'background 0.15s' }}
                      onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = '#f8f9fa'}
                      onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
                    >
                      <td style={{ padding: '13px 14px', fontSize: '13px', fontWeight: 700, color: i < 3 ? '#b9915b' : '#60708a', fontFamily: 'Manrope, sans-serif' }}>#{i + 1}</td>
                      <td style={{ padding: '13px 14px', fontSize: '14px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>{m.manager}</td>
                      <td style={{ padding: '13px 14px' }}>
                        <span style={{ background: `${REGION_COLORS[m.region]}12`, color: REGION_COLORS[m.region], borderRadius: '9999px', padding: '2px 8px', fontWeight: 600, fontSize: '11px', fontFamily: 'Inter, sans-serif' }}>{m.region}</span>
                      </td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>{m.agentCount} agentes</td>
                      <td style={{ padding: '13px 14px', fontSize: '14px', fontWeight: 700, color: '#16a34a', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>{formatRevenue(m.revenue)}</td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', fontWeight: 700, color: '#b9915b', fontFamily: 'Manrope, sans-serif' }}>{m.avgWinRate}%</td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>{formatRevenue(m.avgTicket)}</td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{m.activeDeals}</td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', fontWeight: 600, color: m.avgRatingDPct > 30 ? '#af4332' : '#001f35', fontFamily: 'Manrope, sans-serif' }}>{m.avgRatingDPct}%</td>
                      <td style={{ padding: '13px 14px', fontSize: '13px', fontWeight: 600, color: m.avgKillRedPct > 30 ? '#af4332' : '#001f35', fontFamily: 'Manrope, sans-serif' }}>{m.avgKillRedPct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Regions tab */}
        {tab === 'regions' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* Region cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {stats.regionStats.map(r => (
                <div
                  key={r.region}
                  style={{
                    background: '#ffffff',
                    border: `2px solid ${REGION_COLORS[r.region]}`,
                    borderRadius: '16px',
                    padding: '20px',
                    boxShadow: '0 0 22px rgba(0,0,0,0.07)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 800, color: REGION_COLORS[r.region], fontFamily: 'Manrope, sans-serif' }}>
                      {r.region}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
                      {r.agentCount} agentes
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    {[
                      { label: 'Receita', value: formatRevenue(r.revenue), color: '#16a34a' },
                      { label: 'Win Rate', value: `${r.winRate}%`, color: '#b9915b' },
                      { label: 'Won Deals', value: r.wonDeals.toString(), color: '#0f1a45' },
                    ].map(({ label, value, color }) => (
                      <div key={label} style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '10px', fontWeight: 600, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>{label}</p>
                        <p style={{ fontSize: '18px', fontWeight: 800, color, fontFamily: 'Manrope, sans-serif' }}>{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Revenue bar chart by region */}
            <div
              style={{
                background: '#ffffff',
                border: '1px solid rgba(0,31,53,0.1)',
                borderRadius: '16px',
                padding: '28px',
                boxShadow: '0 0 22px rgba(0,0,0,0.07)',
              }}
            >
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#001f35', fontFamily: 'Manrope, sans-serif', marginBottom: '4px' }}>
                Benchmark por Região
              </h3>
              <p style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', marginBottom: '24px' }}>
                Receita Won por região
              </p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={stats.regionStats} margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
                  <XAxis
                    dataKey="region"
                    tick={{ fontSize: 12, fill: '#001f35', fontFamily: 'Manrope, sans-serif', fontWeight: 600 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tickFormatter={v => `$${(v / 1000).toFixed(0)}K`}
                    tick={{ fontSize: 11, fill: '#60708a', fontFamily: 'Inter, sans-serif' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<BarTooltip />} cursor={{ fill: 'rgba(0,31,53,0.04)' }} />
                  <Bar dataKey="revenue" radius={[8, 8, 0, 0]}>
                    {stats.regionStats.map(r => (
                      <Cell key={r.region} fill={REGION_COLORS[r.region]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              {/* Win rate comparison */}
              <div style={{ marginTop: '24px', borderTop: '1px solid rgba(0,31,53,0.06)', paddingTop: '20px' }}>
                <p style={{ fontSize: '12px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', marginBottom: '12px' }}>
                  Win Rate por Região
                </p>
                {stats.regionStats.map(r => (
                  <div key={r.region} style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{r.region}</span>
                      <span style={{ fontSize: '13px', fontWeight: 700, color: REGION_COLORS[r.region], fontFamily: 'Manrope, sans-serif' }}>{r.winRate}%</span>
                    </div>
                    <div style={{ height: '8px', background: '#f0f0f0', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${r.winRate}%`,
                          background: REGION_COLORS[r.region],
                          borderRadius: '9999px',
                          transition: 'width 0.4s ease',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
