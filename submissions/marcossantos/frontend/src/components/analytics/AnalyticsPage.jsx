// components/analytics/AnalyticsPage.jsx
import { useState } from 'react'
import { useAnalytics } from '../../hooks/useApi'
import TeamRanking  from './TeamRanking'
import FunnelCharts from './FunnelCharts'
import AtRiskTable  from './AtRiskTable'

const TABS = [
  { id: 'team',    label: '👥 Time',           desc: 'Ranking e win rate por vendedor' },
  { id: 'funnel',  label: '📊 Funil',           desc: 'Conversão por stage e produto' },
  { id: 'at_risk', label: '⚠ Deals em Risco', desc: 'Pipeline parado acima da média' },
]

function TabBar({ active, onChange }) {
  return (
    <div style={{
      display: 'flex', gap: 4,
      background: 'var(--bg)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: 4,
      width: 'fit-content',
    }}>
      {TABS.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          style={{
            padding: '7px 16px',
            borderRadius: 6,
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'var(--font)',
            fontSize: 12,
            fontWeight: 600,
            transition: 'all 0.15s',
            background: active === t.id ? 'var(--surface)' : 'transparent',
            color:      active === t.id ? 'var(--text-primary)' : 'var(--text-muted)',
            boxShadow:  active === t.id ? 'var(--shadow-sm)' : 'none',
          }}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('team')
  const { data, loading, error }  = useAnalytics(activeTab)

  const currentTab = TABS.find(t => t.id === activeTab)

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Header da tela */}
      <div style={{
        background: 'var(--surface)', borderBottom: '1px solid var(--border)',
        padding: '14px 24px', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 600, margin: 0 }}>Analytics do Time</h1>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: '2px 0 0' }}>
            {currentTab?.desc}
          </p>
        </div>
        <TabBar active={activeTab} onChange={setActiveTab} />
      </div>

      {/* Conteúdo */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
        {loading && (
          <div className="state-container">
            <div className="spinner" />
            <p>Calculando analytics…</p>
          </div>
        )}

        {error && (
          <div className="state-container">
            <p style={{ color: '#DC2626' }}>⚠ Erro ao carregar: {error}</p>
          </div>
        )}

        {!loading && !error && data && (
          <>
            {activeTab === 'team'    && <TeamRanking  data={data} />}
            {activeTab === 'funnel'  && <FunnelCharts data={data} />}
            {activeTab === 'at_risk' && <AtRiskTable  data={data} />}
          </>
        )}
      </div>
    </div>
  )
}