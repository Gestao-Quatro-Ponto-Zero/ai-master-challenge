import { ScoreBadge } from './ScoreBadge'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'

interface Deal {
  id: number
  score: number
  account_name: string
  product_name: string
  deal_stage: string
  agent_name: string
  potential_value: number
  engage_date: string | null
}

export function DealsTable({ deals }: { deals: Deal[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--bg-secondary)] text-[var(--text-secondary)] text-left">
            <th className="px-4 py-3">Score</th>
            <th className="px-4 py-3">Conta</th>
            <th className="px-4 py-3">Produto</th>
            <th className="px-4 py-3">Etapa</th>
            <th className="px-4 py-3">Vendedor</th>
            <th className="px-4 py-3 text-right">Valor Potencial</th>
            <th className="px-4 py-3">Data Engaging</th>
          </tr>
        </thead>
        <tbody>
          {deals.map((d) => (
            <tr key={d.id} className="border-t border-[var(--border)] hover:bg-[var(--bg-secondary)]/50 transition-colors">
              <td className="px-4 py-3"><ScoreBadge score={d.score} /></td>
              <td className="px-4 py-3 font-medium">{d.account_name}</td>
              <td className="px-4 py-3">{d.product_name}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  d.deal_stage === 'Engaging' ? 'bg-[var(--engaging-bg)] text-[var(--engaging-text)] font-semibold' : 'bg-[var(--prospecting-bg)] text-[var(--prospecting-text)] font-semibold'
                }`}>
                  {stageLabel(d.deal_stage)}
                </span>
              </td>
              <td className="px-4 py-3">{d.agent_name}</td>
              <td className="px-4 py-3 text-right font-medium">
                {formatCurrency(d.potential_value)}
              </td>
              <td className="px-4 py-3 text-[var(--text-secondary)]">
                {d.engage_date ? new Date(d.engage_date).toLocaleDateString('pt-BR') : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
