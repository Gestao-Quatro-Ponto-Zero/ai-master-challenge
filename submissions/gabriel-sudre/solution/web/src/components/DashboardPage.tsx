import { useData } from './Dashboard'
import { MetricCards } from './MetricCards'
import { HealthScore } from './HealthScore'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts'

const COLORS = ['#6366f1', '#8b5cf6', '#22c55e', '#f59e0b']

export function DashboardPage() {
  const { metrics, deals, history, ranking, health } = useData()

  // Stage distribution
  const stageCounts: Record<string, number> = {}
  deals.forEach((d) => { stageCounts[d.deal_stage] = (stageCounts[d.deal_stage] || 0) + 1 })
  const stageData = Object.entries(stageCounts).map(([name, value]) => ({ name: stageLabel(name), value }))

  // Score zones
  const scoreRanges = [
    { name: 'Alta (55+)', count: deals.filter((d) => d.score >= 55).length, color: '#22c55e' },
    { name: 'Média (40-54)', count: deals.filter((d) => d.score >= 40 && d.score < 55).length, color: '#f59e0b' },
    { name: 'Baixa (<40)', count: deals.filter((d) => d.score < 40).length, color: '#ef4444' },
  ]

  // Products
  const productValues: Record<string, number> = {}
  deals.forEach((d) => { productValues[d.product_name] = (productValues[d.product_name] || 0) + (d.potential_value || 0) })
  const productData = Object.entries(productValues).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)

  // Monthly evolution
  const monthly: Record<string, { won: number; lost: number; revenue: number }> = {}
  history.forEach((d) => {
    if (!d.close_date) return
    const month = d.close_date.substring(0, 7)
    if (!monthly[month]) monthly[month] = { won: 0, lost: 0, revenue: 0 }
    if (d.deal_stage === 'Won') { monthly[month].won += 1; monthly[month].revenue += d.close_value || 0 }
    else { monthly[month].lost += 1 }
  })
  const evolutionData = Object.entries(monthly).sort(([a], [b]) => a.localeCompare(b))
    .map(([month, data]) => ({ month: month.slice(5), ...data }))

  // Top accounts
  const acctValues: Record<string, { value: number; deals: number }> = {}
  deals.forEach((d) => {
    if (!acctValues[d.account_name]) acctValues[d.account_name] = { value: 0, deals: 0 }
    acctValues[d.account_name].value += d.potential_value || 0
    acctValues[d.account_name].deals += 1
  })
  const topAccounts = Object.entries(acctValues).map(([name, d]) => ({ name, ...d })).sort((a, b) => b.value - a.value).slice(0, 8)

  const tt = {
    contentStyle: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' },
    labelStyle: { color: 'var(--text-primary)' },
  }

  return (
    <div className="space-y-6">
      {/* Health + KPIs */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1">
          {health && <HealthScore health={health} />}
        </div>
        <div className="lg:col-span-3">
          {metrics && <MetricCards metrics={metrics} />}
        </div>
      </div>

      {/* Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-4">Distribuição por Prioridade</h3>
          <div className="space-y-3">
            {scoreRanges.map((r) => (
              <div key={r.name} className="flex items-center gap-3">
                <span className="text-xs w-20 text-right font-medium" style={{ color: r.color }}>{r.name}</span>
                <div className="flex-1 h-7 rounded-lg bg-[var(--bg-primary)] overflow-hidden">
                  <div className="h-full rounded-lg flex items-center px-2 transition-all" style={{
                    width: `${deals.length > 0 ? (r.count / deals.length) * 100 : 0}%`,
                    background: `${r.color}25`, borderLeft: `3px solid ${r.color}`, minWidth: r.count > 0 ? '40px' : '0',
                  }}>
                    <span className="text-xs font-bold" style={{ color: r.color }}>{r.count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-2">Pipeline por Stage</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={stageData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70} strokeWidth={0}>
                {stageData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip {...tt} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-1">
            {stageData.map((s, i) => (
              <span key={s.name} className="text-[10px] flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                {s.name} ({s.value})
              </span>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-2">Potencial por Produto</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={productData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip {...tt} formatter={(v) => formatCurrency(Number(v))} />
              <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-1">Evolução Mensal</h3>
          <p className="text-[10px] text-[var(--text-secondary)] mb-3">Ganhos vs Perdidos ao longo do tempo</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={evolutionData} margin={{ left: -10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip {...tt} />
              <Bar dataKey="won" name="Ganhos" fill="#22c55e" radius={[2, 2, 0, 0]} />
              <Bar dataKey="lost" name="Perdidos" fill="#ef4444" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-1">Top Contas por Potencial</h3>
          <p className="text-[10px] text-[var(--text-secondary)] mb-3">Contas com maior valor em pipeline ativo</p>
          <div className="space-y-2">
            {topAccounts.map((a, i) => (
              <div key={a.name} className="flex items-center gap-3">
                <span className="text-xs text-[var(--text-secondary)] w-4 text-right">{i + 1}</span>
                <div className="flex-1 min-w-0"><p className="text-sm font-medium truncate">{a.name}</p></div>
                <span className="text-xs text-[var(--text-secondary)]">{a.deals} deals</span>
                <span className="text-sm font-bold text-[var(--accent)]">{formatCurrency(a.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team ranking */}
      {ranking.length > 0 && (
        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <h3 className="text-sm font-bold mb-1">Performance do Time</h3>
          <p className="text-[10px] text-[var(--text-secondary)] mb-3">Ranking por score médio dos deals ativos</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[var(--text-secondary)] text-left text-xs">
                  <th className="pb-2 pr-4">#</th><th className="pb-2 pr-4">Vendedor</th>
                  <th className="pb-2 pr-4">Escritório</th><th className="pb-2 pr-4">Taxa Conv.</th>
                  <th className="pb-2 pr-4">Deals</th><th className="pb-2 pr-4">Score Médio</th>
                  <th className="pb-2 text-right">Potencial</th>
                </tr>
              </thead>
              <tbody>
                {ranking.slice(0, 10).map((a, i) => (
                  <tr key={a.agent} className="border-t border-[var(--border)]">
                    <td className="py-2 pr-4 text-xs text-[var(--text-secondary)]">{i + 1}</td>
                    <td className="py-2 pr-4 font-medium">{a.agent}</td>
                    <td className="py-2 pr-4 text-[var(--text-secondary)]">{a.office}</td>
                    <td className="py-2 pr-4">
                      <span className={a.win_rate >= 65 ? 'text-[var(--success)] font-semibold' : a.win_rate >= 50 ? 'text-[var(--warning)]' : 'text-[var(--danger)] font-semibold'}>
                        {a.win_rate}%
                      </span>
                    </td>
                    <td className="py-2 pr-4">{a.active_deals}</td>
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-[var(--bg-primary)] overflow-hidden">
                          <div className="h-full rounded-full" style={{
                            width: `${a.avg_score}%`,
                            background: a.avg_score >= 55 ? 'var(--success)' : a.avg_score >= 40 ? 'var(--warning)' : 'var(--danger)',
                          }} />
                        </div>
                        <span className="text-xs">{a.avg_score}</span>
                      </div>
                    </td>
                    <td className="py-2 text-right font-medium text-[var(--accent)]">
                      {formatCurrency(a.potential)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
