// components/TopBar.jsx
import { Bell, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

function fmt(n) {
  if (!n) return '$0'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

function roleLabel(role) {
  if (role === 'admin')   return { label: 'Admin',   color: '#7C3AED', bg: '#F5F3FF' }
  if (role === 'manager') return { label: 'Manager', color: '#1D4ED8', bg: '#EFF6FF' }
  return                          { label: 'Agent',  color: '#065F46', bg: '#ECFDF5' }
}

export default function TopBar({ summary, filters, alertsData, onAlertsClick }) {
  const { user, logout } = useAuth()
  const hasFilter = Object.values(filters || {}).some(Boolean)
  const subtitle  = hasFilter
    ? `Filtrado · ${summary?.total ?? '—'} deals`
    : `Pipeline completo · ${summary?.total ?? '—'} deals ativos`

  const unseen = alertsData?.unseen || 0
  const role   = user ? roleLabel(user.role) : null

  return (
    <div className="top-bar">
      {/* Título */}
      <div className="top-bar-title">
        <h1>Pipeline de Vendas</h1>
        <p>{subtitle}</p>
      </div>

      {/* KPIs */}
      <div className="kpi-row">
        <div className="kpi-card">
          <span className="kpi-dot" style={{ background: '#DC2626' }} />
          <span className="kpi-label">Hot</span>
          <span className="kpi-value">{summary?.hot ?? '—'}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-dot" style={{ background: '#D97706' }} />
          <span className="kpi-label">Warm</span>
          <span className="kpi-value">{summary?.warm ?? '—'}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-dot" style={{ background: '#94A3B8' }} />
          <span className="kpi-label">Cold</span>
          <span className="kpi-value">{summary?.cold ?? '—'}</span>
        </div>

        <div className="kpi-divider" />

        <div className="kpi-pipeline">
          <span className="kpi-pipeline-label">Em pipeline</span>
          <span className="kpi-pipeline-value">{summary ? fmt(summary.pipeline_value) : '—'}</span>
        </div>

        <div className="kpi-divider" />

        {/* Sino de alertas */}
        <button
          onClick={onAlertsClick}
          title="Ver alertas"
          style={{
            position: 'relative',
            background: unseen > 0 ? 'var(--hot-bg)' : 'var(--bg)',
            border: `1px solid ${unseen > 0 ? 'var(--hot-border)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)',
            padding: '7px 10px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            color: unseen > 0 ? 'var(--hot)' : 'var(--text-muted)',
            transition: 'all 0.15s',
          }}
        >
          <Bell size={15} />
          {unseen > 0 && (
            <span style={{
              background: 'var(--hot)',
              color: '#fff',
              fontSize: 10,
              fontWeight: 700,
              borderRadius: 100,
              padding: '0px 5px',
              minWidth: 16,
              textAlign: 'center',
            }}>
              {unseen}
            </span>
          )}
        </button>

        <div className="kpi-divider" />

        {/* Usuário logado */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                {user.name}
              </span>
              <span style={{
                fontSize: 10, fontWeight: 600,
                color: role.color,
                background: role.bg,
                borderRadius: 100,
                padding: '0 6px',
              }}>
                {role.label}
              </span>
            </div>
            <button
              onClick={logout}
              title="Sair"
              style={{
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '7px',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                transition: 'all 0.15s',
              }}
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}