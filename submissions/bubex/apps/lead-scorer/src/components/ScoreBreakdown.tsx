import type { Deal } from '@/types'

interface Row {
  label: string
  value: number
  detail: string
}

function rows(deal: Deal): Row[] {
  return [
    {
      label: 'Stage',
      value: deal.score_stage,
      detail: deal.deal_stage === 'Engaging' ? 'Engaging — em negociação ativa' : 'Prospecting — início de contato',
    },
    {
      label: 'Produto',
      value: deal.score_value,
      detail: `${deal.product} — preço de tabela $${deal.sales_price.toLocaleString()}`,
    },
    {
      label: 'Conta',
      value: deal.score_account,
      detail: `${deal.account} — receita $${deal.revenue.toLocaleString()}M (${deal.sector})`,
    },
    {
      label: 'Tempo no pipeline',
      value: deal.score_time,
      detail: `${deal.days_in_pipeline} dias desde engage${deal.score_time < 0 ? ' — deal esfriando' : ' — dentro do prazo'}`,
    },
    {
      label: 'Linha de produto',
      value: deal.score_series,
      detail: `Série ${deal.series}${deal.series === 'GTK' ? ' — produto premium' : deal.series === 'GTX' ? ' — linha principal' : ' — linha básica'}`,
    },
    {
      label: 'Agente',
      value: deal.score_agent,
      detail: `${deal.sales_agent} — win rate ${deal.win_rate_pct}% (${deal.won_count}W / ${deal.lost_count}L)`,
    },
  ]
}

export function ScoreBreakdown({ deal }: { deal: Deal }) {
  const components = rows(deal)

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-800">Score breakdown</h3>
        <span className="text-2xl font-bold text-gray-900">{deal.score}</span>
      </div>
      <div className="space-y-2">
        {components.map((row) => (
          <div key={row.label} className="flex items-center gap-3 text-sm">
            <span
              className={`w-10 text-right font-mono font-semibold shrink-0 ${
                row.value > 0 ? 'text-green-600' : row.value < 0 ? 'text-red-500' : 'text-gray-400'
              }`}
            >
              {row.value > 0 ? `+${row.value}` : row.value}
            </span>
            <div className="flex-1 min-w-0">
              <span className="font-medium text-gray-700">{row.label}</span>
              <span className="text-gray-400 ml-2">{row.detail}</span>
            </div>
          </div>
        ))}
        <div className="border-t border-gray-100 pt-2 flex items-center gap-3 text-sm font-semibold">
          <span className="w-10 text-right font-mono text-gray-900">{deal.score}</span>
          <span className="text-gray-800">Score final</span>
        </div>
      </div>
    </div>
  )
}
