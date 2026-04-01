import { useState, useMemo } from 'react'
import { useData } from './Dashboard'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { Download, ChevronLeft, ChevronRight, Trophy, XCircle, TrendingUp } from 'lucide-react'

function exportCSV(deals: any[], filename: string) {
  const headers = ['Status', 'Conta', 'Produto', 'Vendedor', 'Valor', 'Data Fechamento']
  const rows = deals.map((d) => [
    stageLabel(d.deal_stage),
    d.account_name,
    d.product_name,
    d.agent_name,
    d.close_value || 0,
    d.close_date ? new Date(d.close_date).toLocaleDateString('pt-BR') : '',
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

const PER_PAGE = 50

export function HistoryPage() {
  const { history } = useData()
  const [stageFilter, setStageFilter] = useState<string[]>([])
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    setPage(1)
    return stageFilter.length > 0
      ? history.filter((d) => stageFilter.includes(d.deal_stage))
      : history
  }, [history, stageFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE))
  const pageData = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)

  const totalWon = history.filter((d) => d.deal_stage === 'Won').length
  const totalLost = history.filter((d) => d.deal_stage === 'Lost').length
  const totalRevenue = history.filter((d) => d.deal_stage === 'Won').reduce((s, d) => s + (d.close_value || 0), 0)
  const avgTicket = totalWon > 0 ? totalRevenue / totalWon : 0
  const winRate = totalWon + totalLost > 0 ? ((totalWon / (totalWon + totalLost)) * 100).toFixed(1) : '0'

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <div className="flex items-center gap-2 mb-1">
            <Trophy size={14} className="text-[var(--won-text)]" />
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Ganhos</p>
          </div>
          <p className="text-xl font-bold text-[var(--won-text)]">{totalWon}</p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <div className="flex items-center gap-2 mb-1">
            <XCircle size={14} className="text-[var(--lost-text)]" />
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Perdidos</p>
          </div>
          <p className="text-xl font-bold text-[var(--lost-text)]">{totalLost}</p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-[var(--accent)]" />
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Taxa Conv.</p>
          </div>
          <p className="text-xl font-bold text-[var(--text-primary)]">{winRate}%</p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Ticket Médio</p>
          <p className="text-xl font-bold text-[var(--accent)]">{formatCurrency(avgTicket)}</p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Receita Total</p>
          <p className="text-xl font-bold text-[var(--accent)]">{formatCurrency(totalRevenue)}</p>
        </div>
      </div>

      {/* Filters + Actions */}
      <div className="flex gap-2 items-center">
        {['Won', 'Lost'].map((s) => (
          <button key={s}
            onClick={() => setStageFilter((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              stageFilter.length === 0 || stageFilter.includes(s)
                ? s === 'Won' ? 'border-[var(--won-text)] text-[var(--won-text)] bg-[var(--won-bg)]' : 'border-[var(--lost-text)] text-[var(--lost-text)] bg-[var(--lost-bg)]'
                : 'border-[var(--border)] text-[var(--text-secondary)]'
            }`}
          >
            {stageLabel(s)}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-[var(--text-secondary)]">{filtered.length} oportunidades</span>
          <button
            onClick={() => exportCSV(filtered, `historico-${new Date().toISOString().slice(0, 10)}.csv`)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]/50 hover:text-[var(--accent)] transition-colors flex items-center gap-1.5"
          >
            <Download size={14} strokeWidth={2} />
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-[var(--border)] shadow-[var(--shadow-sm)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[var(--bg-secondary)] text-[var(--text-secondary)] text-left text-xs uppercase tracking-wider">
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Conta</th>
              <th className="px-4 py-3">Produto</th>
              <th className="px-4 py-3">Vendedor</th>
              <th className="px-4 py-3 text-right">Valor</th>
              <th className="px-4 py-3">Fechamento</th>
            </tr>
          </thead>
          <tbody>
            {pageData.map((d) => (
              <tr key={d.id} className="border-t border-[var(--border)] hover:bg-[var(--bg-hover)] transition-colors">
                <td className="px-4 py-2.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    d.deal_stage === 'Won' ? 'bg-[var(--won-bg)] text-[var(--won-text)]' : 'bg-[var(--lost-bg)] text-[var(--lost-text)]'
                  }`}>{stageLabel(d.deal_stage)}</span>
                </td>
                <td className="px-4 py-2.5 font-medium">{d.account_name}</td>
                <td className="px-4 py-2.5 text-[var(--text-secondary)]">{d.product_name}</td>
                <td className="px-4 py-2.5 text-[var(--text-secondary)]">{d.agent_name}</td>
                <td className="px-4 py-2.5 text-right font-medium">{formatCurrency(d.close_value)}</td>
                <td className="px-4 py-2.5 text-[var(--text-secondary)]">
                  {d.close_date ? new Date(d.close_date).toLocaleDateString('pt-BR') : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="p-1.5 rounded-lg border border-[var(--border)] disabled:opacity-30 hover:bg-[var(--bg-hover)] transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-[var(--text-secondary)] px-3">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="p-1.5 rounded-lg border border-[var(--border)] disabled:opacity-30 hover:bg-[var(--bg-hover)] transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
