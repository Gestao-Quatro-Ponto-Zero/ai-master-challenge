import { formatCurrency } from '../lib/format'

interface Metrics {
  active_deals: number
  win_rate: number
  avg_ticket: number
  at_risk: number
  total_potential: number
  total_won_value: number
}

export function MetricCards({ metrics }: { metrics: Metrics }) {
  const cards = [
    { label: 'Oportunidades Ativas', value: metrics.active_deals, fmt: (v: number) => String(v) },
    { label: 'Taxa de Conversão', value: metrics.win_rate, fmt: (v: number) => `${v}%` },
    { label: 'Ticket Médio', value: metrics.avg_ticket, fmt: (v: number) => formatCurrency(v) },
    { label: 'Em Risco', value: metrics.at_risk, fmt: (v: number) => String(v), danger: true },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] transition-shadow">
          <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">{c.label}</p>
          <p className={`text-2xl font-bold mt-2 ${c.danger && c.value > 0 ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]'}`}>
            {c.fmt(c.value)}
          </p>
        </div>
      ))}
    </div>
  )
}
