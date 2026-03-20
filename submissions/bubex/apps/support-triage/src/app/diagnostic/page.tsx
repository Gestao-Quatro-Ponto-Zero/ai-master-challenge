import { Suspense } from 'react'
import { getOverview, getBottlenecks, getChannelStats, getTypeStats } from '@/lib/queries'
import { getDiagnosticOutput } from '@/lib/notebook-output'
import { InsightsCard, InsightsCardSkeleton } from '@/components/InsightsCard'

function pct(n: number, total: number) {
  return total === 0 ? 0 : Math.round((n / total) * 100)
}

function KpiCard({ label, value, sub, accent }: {
  label: string; value: string | number; sub?: string; accent?: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 px-5 py-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent ?? 'text-gray-900'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function CsatBadge({ csat }: { csat: number }) {
  const color = csat >= 3.5 ? 'bg-green-100 text-green-700'
              : csat >= 2.5 ? 'bg-yellow-100 text-yellow-700'
              : 'bg-red-100 text-red-700'
  return <span className={`text-xs font-medium px-2 py-0.5 rounded ${color}`}>{csat}</span>
}

function HoursBadge({ hours, median }: { hours: number; median: number }) {
  const isHigh = hours > median * 1.1
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${isHigh ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
      {hours}h
    </span>
  )
}

const PRIORITY_ORDER = ['Critical', 'High', 'Medium', 'Low']
const PRIORITY_COLOR: Record<string, string> = {
  Critical: 'bg-red-500',
  High:     'bg-orange-400',
  Medium:   'bg-yellow-400',
  Low:      'bg-green-400',
}
const PRIORITY_TEXT: Record<string, string> = {
  Critical: 'text-red-700',
  High:     'text-orange-700',
  Medium:   'text-yellow-700',
  Low:      'text-green-700',
}

export default async function DiagnosticPage() {
  const [overview, bottlenecks, channelStats, typeStats, notebookData] = await Promise.all([
    getOverview(),
    getBottlenecks(),
    getChannelStats(),
    getTypeStats(),
    Promise.resolve(getDiagnosticOutput()),
  ])

  const avgHours = overview.avgResolutionHours
  const worstBottleneck = bottlenecks[0]

  const priorityRows = notebookData?.priority
    ? [...notebookData.priority].sort(
        (a, b) => PRIORITY_ORDER.indexOf(a.priority) - PRIORITY_ORDER.indexOf(b.priority)
      )
    : null

  const waste = notebookData?.waste ?? null
  const csatDrivers = notebookData?.csat_drivers ?? null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Diagnóstico Operacional</h1>
        <p className="text-gray-500 text-sm mt-1">
          {overview.totalTickets.toLocaleString()} tickets analisados · Dataset 1: customer_support_tickets.csv
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <KpiCard label="Total de tickets"     value={overview.totalTickets.toLocaleString()} />
        <KpiCard label="Backlog"              value={`${overview.backlogRate}%`}
          sub={`${(overview.openTickets + overview.pendingTickets).toLocaleString()} não resolvidos`}
          accent="text-red-600" />
        <KpiCard label="Fechados"             value={overview.closedTickets.toLocaleString()}
          sub={`${pct(overview.closedTickets, overview.totalTickets)}% do total`} />
        <KpiCard label="Resolução média"      value={`${overview.avgResolutionHours}h`}
          sub="tickets fechados" />
        <KpiCard label="CSAT médio"           value={`${overview.avgCsat}/5`}
          sub="escala 1–5"
          accent={overview.avgCsat < 3 ? 'text-red-600' : 'text-yellow-600'} />
        <KpiCard label="Pior combinação"      value={`${worstBottleneck?.avgHours}h`}
          sub={`${worstBottleneck?.channel} + ${worstBottleneck?.type}`}
          accent="text-red-600" />
      </div>

      {/* Insight destaque — gerado por IA sobre os dados reais */}
      <Suspense fallback={<InsightsCardSkeleton />}>
        <InsightsCard
          overview={overview}
          bottlenecks={bottlenecks}
          channelStats={channelStats}
          typeStats={typeStats}
        />
      </Suspense>

      {/* Channel breakdown + Type breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Por canal</h2>
          <div className="space-y-4">
            {channelStats.map(c => (
              <div key={c.channel}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{c.channel}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">{c.total} tickets</span>
                    <HoursBadge hours={c.avgHours} median={avgHours} />
                    <CsatBadge csat={c.avgCsat} />
                  </div>
                </div>
                <div className="flex gap-1 h-2">
                  <div className="bg-green-400 rounded-full" style={{ width: `${pct(c.closed, c.total)}%` }} title={`Fechados: ${c.closed}`} />
                  <div className="bg-gray-200 rounded-full flex-1" title="Abertos/pendentes" />
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{pct(c.closed, c.total)}% resolvidos</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Por tipo</h2>
          <div className="space-y-4">
            {typeStats.map(t => (
              <div key={t.type}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{t.type}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">{t.total}</span>
                    <HoursBadge hours={t.avgHours} median={avgHours} />
                    <CsatBadge csat={t.avgCsat} />
                  </div>
                </div>
                <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
                  <div className="bg-green-400" style={{ width: `${pct(t.closed, t.total)}%` }} title="Fechado" />
                  <div className="bg-blue-300" style={{ width: `${pct(t.pending, t.total)}%` }} title="Pendente" />
                  <div className="bg-gray-200 flex-1" title="Aberto" />
                </div>
                <div className="flex gap-3 text-xs text-gray-400 mt-0.5">
                  <span className="text-green-600">{pct(t.closed, t.total)}% fechado</span>
                  <span className="text-blue-500">{pct(t.pending, t.total)}% pendente</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Priority breakdown — from notebook analysis */}
      {priorityRows ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Por prioridade</h2>
            <span className="text-xs text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
              via notebook Python
            </span>
          </div>
          <div className="space-y-4">
            {priorityRows.map(p => {
              const barColor = PRIORITY_COLOR[p.priority] ?? 'bg-gray-400'
              const textColor = PRIORITY_TEXT[p.priority] ?? 'text-gray-700'
              const maxVol = Math.max(...priorityRows.map(r => r.volume))
              return (
                <div key={p.priority}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className={`font-medium ${textColor}`}>{p.priority}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-xs">{p.volume.toLocaleString()} tickets</span>
                      <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                        {p.avg_resolution_h}h
                      </span>
                      <CsatBadge csat={p.avg_csat} />
                    </div>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${barColor}`}
                      style={{ width: `${Math.round((p.volume / maxVol) * 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">{p.resolution_rate}% resolvidos</p>
                </div>
              )
            })}
          </div>
          {/* Priority paradox callout */}
          {(() => {
            const critical = priorityRows.find(r => r.priority === 'Critical')
            const low      = priorityRows.find(r => r.priority === 'Low')
            if (!critical || !low) return null
            return (
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                <span className="font-semibold">Paradoxo da prioridade:</span>{' '}
                tickets Critical têm CSAT {critical.avg_csat} vs {low.avg_csat} em tickets Low.
                Clientes com problemas críticos têm expectativas mais altas — mesmo com SLA cumprido,
                o impacto do problema resulta em satisfação similar ou inferior.
              </div>
            )
          })()}
        </div>
      ) : null}

      {/* What impacts CSAT — from notebook */}
      {csatDrivers ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">O que impacta o CSAT?</h2>
            <span className="text-xs text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
              via notebook Python
            </span>
          </div>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Tempo de resolução', r: csatDrivers.pearson_r, p: csatDrivers.pearson_p },
                { label: 'Canal', r: null, p: csatDrivers.kruskal_channel_p },
                { label: 'Tipo de ticket', r: null, p: csatDrivers.kruskal_type_p },
                { label: 'Prioridade', r: null, p: csatDrivers.kruskal_priority_p },
              ].map(({ label, r, p }) => {
                const sig = p < 0.05
                return (
                  <div key={label} className={`rounded-lg p-3 border ${sig ? 'border-green-200 bg-green-50' : 'border-gray-100 bg-gray-50'}`}>
                    <p className="text-xs text-gray-500 mb-1">{label}</p>
                    {r !== null && (
                      <p className="font-mono text-xs text-gray-700">r = {r.toFixed(4)}</p>
                    )}
                    <p className={`font-mono text-xs ${sig ? 'text-green-700 font-semibold' : 'text-gray-500'}`}>
                      p = {p.toFixed(4)}
                    </p>
                    <p className={`text-xs mt-1 ${sig ? 'text-green-700' : 'text-gray-400'}`}>
                      {sig ? 'significativo' : 'não significativo'}
                    </p>
                  </div>
                )
              })}
            </div>
            <p className="text-xs text-gray-500 italic bg-gray-50 rounded-lg p-3">
              {csatDrivers.conclusion}
            </p>
          </div>
        </div>
      ) : null}

      {/* Waste estimation — from notebook */}
      {waste ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Desperdício estimado</h2>
            <span className="text-xs text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
              via notebook Python
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Mediana de resolução</p>
              <p className="text-xl font-bold text-gray-800">{waste.median_hours}h</p>
              <p className="text-xs text-gray-400">baseline eficiente</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Média atual</p>
              <p className="text-xl font-bold text-red-600">{waste.mean_hours}h</p>
              <p className="text-xs text-gray-400">+{(waste.mean_hours - waste.median_hours).toFixed(1)}h acima da mediana</p>
            </div>
            <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
              <p className="text-xs text-gray-400 mb-1">Excesso/ano</p>
              <p className="text-xl font-bold text-amber-700">{waste.annual_excess_hours.toLocaleString()}h</p>
              <p className="text-xs text-gray-400">{waste.annual_volume.toLocaleString()} tickets/ano projetados</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 border border-green-100">
              <p className="text-xs text-gray-400 mb-1">Custo recuperável</p>
              <p className="text-xl font-bold text-green-700">
                R${(waste.annual_cost_brl / 1_000_000).toFixed(1)}M
              </p>
              <p className="text-xs text-gray-400">a R$35/h (agente CLT)</p>
            </div>
          </div>
          <p className="text-xs text-gray-400 italic">
            Premissas: volume anual de {waste.annual_volume.toLocaleString()} tickets (conforme enunciado),
            excesso calculado sobre tickets acima da mediana ({waste.above_median_pct}% do total),
            custo de R$35/h. Validar com dados de produção.
          </p>
        </div>
      ) : null}

      {/* Bottleneck table */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Gargalos — Canal × Tipo (ordenado por tempo de resolução)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Canal', 'Tipo', 'Tickets', 'Tempo médio', 'CSAT'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {bottlenecks.map((b, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{b.channel}</td>
                  <td className="px-4 py-3 text-gray-600">{b.type}</td>
                  <td className="px-4 py-3 text-gray-500">{b.n}</td>
                  <td className="px-4 py-3">
                    <HoursBadge hours={b.avgHours} median={avgHours} />
                  </td>
                  <td className="px-4 py-3">
                    <CsatBadge csat={b.avgCsat} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data quality note */}
      <p className="text-xs text-gray-400 italic">
        Nota: dataset sintético — <code>Ticket Description</code> contém placeholders não substituídos
        (ex: <code>{'{product_purchased}'}</code>). Timestamps de resolução podem estar invertidos;
        usamos <code>ABS(DATE_DIFF)</code> para corrigir.
        {notebookData && ` · ${notebookData.data_quality.same_day_timestamps_pct}% dos tickets têm timestamps no mesmo dia.`}
      </p>
    </div>
  )
}
