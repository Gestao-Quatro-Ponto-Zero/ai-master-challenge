// components/Sidebar.jsx
import { BarChart2 } from 'lucide-react'

function Select({ label, value, onChange, options, placeholder }) {
  return (
    <div className="sidebar-filter-group">
      <span className="sidebar-filter-label">{label}</span>
      <select
        className="sidebar-select"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map(o => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  )
}

export default function Sidebar({ filters, setFilters, filterOptions, summary }) {
  const set = (key) => (val) => setFilters(prev => ({ ...prev, [key]: val }))
  const hasAnyFilter = Object.values(filters).some(Boolean)

  const stats = summary
    ? [
        { label: 'Hot',  value: summary.hot,  color: '#DC2626' },
        { label: 'Warm', value: summary.warm, color: '#D97706' },
        { label: 'Cold', value: summary.cold, color: '#64748B' },
      ]
    : []

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <BarChart2 size={16} color="#fff" />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-title">Lead Scorer</span>
          <span className="sidebar-logo-sub">Sales Intelligence</span>
        </div>
      </div>

      {/* Filtros */}
      <div className="sidebar-section">
        <div className="sidebar-section-label">Filtros</div>

        <Select
          label="Vendedor"
          value={filters.agent}
          onChange={set('agent')}
          options={filterOptions?.agents || []}
          placeholder="Todos os vendedores"
        />
        <Select
          label="Manager"
          value={filters.manager}
          onChange={set('manager')}
          options={filterOptions?.managers || []}
          placeholder="Todos os managers"
        />
        <Select
          label="Região"
          value={filters.region}
          onChange={set('region')}
          options={filterOptions?.regions || []}
          placeholder="Todas as regiões"
        />
        <Select
          label="Stage"
          value={filters.stage}
          onChange={set('stage')}
          options={filterOptions?.stages || []}
          placeholder="Todos os stages"
        />
        <Select
          label="Produto"
          value={filters.product}
          onChange={set('product')}
          options={filterOptions?.products || []}
          placeholder="Todos os produtos"
        />

        {hasAnyFilter && (
          <button
            className="reset-btn"
            onClick={() => setFilters({ agent: '', manager: '', region: '', stage: '', product: '' })}
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Divisória */}
      {summary && (
        <>
          <div className="sidebar-divider" />

          <div className="sidebar-section">
            <div className="sidebar-section-label">Pipeline atual</div>
          </div>

          <div className="sidebar-stats">
            {stats.map(s => (
              <div key={s.label} className="sidebar-stat-item">
                <span className="sidebar-stat-dot" style={{ background: s.color }} />
                <span className="sidebar-stat-name">{s.label}</span>
                <span className="sidebar-stat-value">{s.value}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </aside>
  )
}