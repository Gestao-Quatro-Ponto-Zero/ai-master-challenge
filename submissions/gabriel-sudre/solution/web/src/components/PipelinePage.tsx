import { useState, useMemo, useCallback } from 'react'
import { useData } from './Dashboard'
import { DealCard } from './DealCard'
import { FocusSection } from './FocusSection'
import { NewDealModal } from './NewDealModal'
import { DealCompare } from './DealCompare'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { Flame, Zap, Snowflake, Download, ChevronUp, ChevronDown, Plus, GitCompareArrows } from 'lucide-react'

function exportCSV(deals: any[], filename: string) {
  const headers = ['Score', 'Stage', 'Conta', 'Produto', 'Vendedor', 'Escritorio', 'Valor Potencial', 'Data Engajamento']
  const rows = deals.map((d) => [
    d.score,
    d.deal_stage,
    d.account_name,
    d.product_name,
    d.agent_name,
    d.regional_office || '',
    d.potential_value || 0,
    d.engage_date ? new Date(d.engage_date).toLocaleDateString('pt-BR') : '',
  ])
  const csv = [headers, ...rows].map((r) => r.map((v: any) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

type FilterCategory = 'stage' | 'product' | 'agent' | 'office'

export function PipelinePage() {
  const { deals, filters, reload } = useData()
  const [expandedZone, setExpandedZone] = useState<string | null>(null)
  const [showNewDeal, setShowNewDeal] = useState(false)
  const [showCompare, setShowCompare] = useState(false)
  const [activeFilters, setActiveFilters] = useState<Record<FilterCategory, string[]>>({
    stage: [],
    product: [],
    agent: [],
    office: [],
  })
  const [expandedFilter, setExpandedFilter] = useState<FilterCategory | null>(null)

  const toggleFilter = useCallback((category: FilterCategory, value: string) => {
    setActiveFilters((prev) => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter((x) => x !== value)
        : [...prev[category], value],
    }))
  }, [])

  const clearFilters = useCallback(() => {
    setActiveFilters({ stage: [], product: [], agent: [], office: [] })
  }, [])

  const filtered = useMemo(() => deals.filter((d) => {
    if (activeFilters.stage.length > 0 && !activeFilters.stage.includes(d.deal_stage)) return false
    if (activeFilters.product.length > 0 && !activeFilters.product.includes(d.product_name)) return false
    if (activeFilters.agent.length > 0 && !activeFilters.agent.includes(d.agent_name)) return false
    if (activeFilters.office.length > 0 && !activeFilters.office.includes(d.regional_office)) return false
    return true
  }), [deals, activeFilters])

  const hasActiveFilter = Object.values(activeFilters).some((v) => v.length > 0)

  const topFocus = filtered.slice(0, 5)
  const hotDeals = filtered.filter((d) => d.score >= 55)
  const warmDeals = filtered.filter((d) => d.score >= 40 && d.score < 55)
  const coldDeals = filtered.filter((d) => d.score < 40)

  const zones = [
    { id: 'hot', label: 'Alta Prioridade', icon: Flame, deals: hotDeals, color: 'var(--success)', bg: 'rgba(22,163,74,0.05)', border: 'rgba(22,163,74,0.20)', desc: 'Maior probabilidade de fechamento. Aja agora.' },
    { id: 'warm', label: 'Atenção', icon: Zap, deals: warmDeals, color: 'var(--g4-gold)', bg: 'rgba(185,145,91,0.06)', border: 'rgba(185,145,91,0.20)', desc: 'Oportunidades com potencial. Precisam de acompanhamento.' },
    { id: 'cold', label: 'Baixa Prioridade', icon: Snowflake, deals: coldDeals, color: 'var(--danger)', bg: 'rgba(220,38,38,0.04)', border: 'rgba(220,38,38,0.15)', desc: 'Risco alto ou pouco potencial. Reavalie o investimento de tempo.' },
  ]

  const filterSections: { key: FilterCategory; label: string; options: string[] }[] = [
    { key: 'stage', label: 'Etapa', options: filters?.stages || [] },
    { key: 'product', label: 'Produto', options: filters?.products || [] },
    { key: 'agent', label: 'Vendedor', options: filters?.agents || [] },
    { key: 'office', label: 'Escrit\u00f3rio', options: filters?.offices || [] },
  ]

  return (
    <div className="space-y-6">
      {showNewDeal && (
        <NewDealModal
          onClose={() => setShowNewDeal(false)}
          onCreated={() => { setShowNewDeal(false); reload() }}
        />
      )}
      {showCompare && <DealCompare onClose={() => setShowCompare(false)} />}

      {/* Filter bar */}
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          {filterSections.map((section) => (
            <button
              key={section.key}
              onClick={() => setExpandedFilter(expandedFilter === section.key ? null : section.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                activeFilters[section.key].length > 0
                  ? 'border-[var(--accent)] text-[var(--accent)] bg-[var(--accent)]/10'
                  : expandedFilter === section.key
                    ? 'border-[var(--accent)]/50 text-[var(--text-primary)] bg-[var(--bg-secondary)]'
                    : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30'
              }`}
            >
              {section.label}
              {activeFilters[section.key].length > 0 && (
                <span className="bg-[var(--accent)] text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                  {activeFilters[section.key].length}
                </span>
              )}
              <span className="text-[10px]">{expandedFilter === section.key ? '\u25B2' : '\u25BC'}</span>
            </button>
          ))}

          {hasActiveFilter && (
            <button
              onClick={clearFilters}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 hover:text-red-300 transition-colors"
            >
              Limpar filtros
            </button>
          )}

          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs text-[var(--text-secondary)]">{filtered.length} oportunidades</span>
            <button
              onClick={() => setShowCompare(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--g4-gold)]/50 hover:text-[var(--g4-gold)] transition-colors flex items-center gap-1.5"
            >
              <GitCompareArrows size={14} strokeWidth={2} />
              Comparar
            </button>
            <button
              onClick={() => setShowNewDeal(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--g4-gold)] text-[var(--g4-deep)] hover:bg-[var(--accent-hover)] transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <Plus size={14} strokeWidth={2} />
              Nova Oportunidade
            </button>
            <button
              onClick={() => exportCSV(filtered, `pipeline-${new Date().toISOString().slice(0, 10)}.csv`)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]/50 hover:text-[var(--accent)] transition-colors flex items-center gap-1.5"
            >
              <Download size={14} strokeWidth={2} />
              Exportar CSV
            </button>
          </div>
        </div>

        {/* Expanded filter options */}
        {expandedFilter && (
          <div className="flex flex-wrap gap-1.5 p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
            {filterSections.find((s) => s.key === expandedFilter)?.options.map((opt) => (
              <button
                key={opt}
                onClick={() => toggleFilter(expandedFilter, opt)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                  activeFilters[expandedFilter].includes(opt)
                    ? 'border-[var(--accent)] text-[var(--accent)] bg-[var(--accent)]/10'
                    : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30'
                }`}
              >
                {expandedFilter === 'stage' ? stageLabel(opt) : opt}
              </button>
            ))}
            {(filterSections.find((s) => s.key === expandedFilter)?.options.length || 0) === 0 && (
              <span className="text-xs text-[var(--text-secondary)]">Nenhuma op\u00e7\u00e3o dispon\u00edvel</span>
            )}
          </div>
        )}
      </div>

      <FocusSection deals={topFocus} />

      {zones.map((zone) => (
        <section key={zone.id}>
          <div className="flex items-center justify-between p-4 rounded-xl cursor-pointer transition-colors"
            style={{ background: zone.bg, border: `1px solid ${zone.border}` }}
            onClick={() => setExpandedZone(expandedZone === zone.id ? null : zone.id)}
          >
            <div className="flex items-center gap-3">
              <zone.icon size={22} strokeWidth={1.8} style={{ color: zone.color }} />
              <div>
                <h3 className="font-bold" style={{ color: zone.color }}>{zone.label} — {zone.deals.length} oportunidades</h3>
                <p className="text-xs text-[var(--text-secondary)]">{zone.desc}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium" style={{ color: zone.color }}>
                {formatCurrency(zone.deals.reduce((s, d) => s + (d.potential_value || 0), 0))}
              </span>
              {expandedZone === zone.id ? <ChevronUp size={18} className="text-[var(--text-muted)]" /> : <ChevronDown size={18} className="text-[var(--text-muted)]" />}
            </div>
          </div>
          {expandedZone === zone.id && zone.deals.length > 0 && (
            <div className="mt-2 space-y-2">
              {zone.deals.map((d) => <DealCard key={d.id} deal={d} onClassified={reload} />)}
            </div>
          )}
        </section>
      ))}
    </div>
  )
}
