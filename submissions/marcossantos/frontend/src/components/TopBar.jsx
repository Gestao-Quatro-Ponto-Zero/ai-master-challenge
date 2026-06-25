// components/TopBar.jsx

function fmt(n) {
  if (!n) return '$0'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

export default function TopBar({ summary, filters }) {
  const hasFilter = Object.values(filters || {}).some(Boolean)
  const subtitle = hasFilter
    ? `Filtrado · ${summary?.total ?? '—'} deals`
    : `Pipeline completo · ${summary?.total ?? '—'} deals ativos`

  return (
    <div className="top-bar">
      <div className="top-bar-title">
        <h1>Pipeline de Vendas</h1>
        <p>{subtitle}</p>
      </div>

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
      </div>
    </div>
  )
}