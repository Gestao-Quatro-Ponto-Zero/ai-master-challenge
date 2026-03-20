import { getOverview, getBottlenecks, getChannelStats, getTypeStats } from '@/lib/queries'

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

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const w = max === 0 ? 0 : Math.round((value / max) * 100)
  return (
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${w}%` }} />
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

export default async function DiagnosticPage() {
  const [overview, bottlenecks, channelStats, typeStats] = await Promise.all([
    getOverview(),
    getBottlenecks(),
    getChannelStats(),
    getTypeStats(),
  ])

  const avgHours = overview.avgResolutionHours
  const worstBottleneck = bottlenecks[0]
  const bestChannel = [...channelStats].sort((a, b) => b.avgCsat - a.avgCsat)[0]
  const worstChannel = [...channelStats].sort((a, b) => a.avgCsat - b.avgCsat)[0]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Diagnóstico Operacional</h1>
        <p className="text-gray-500 text-sm mt-1">
          {overview.totalTickets.toLocaleString()} tickets analisados · Dataset: customer_support_tickets.csv
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

      {/* Insight destaque */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
        <p className="text-sm font-semibold text-amber-800 mb-1">Achados principais</p>
        <ul className="text-sm text-amber-700 space-y-1 list-disc list-inside">
          <li>
            <strong>{overview.backlogRate}% dos tickets não estão resolvidos</strong> — {overview.openTickets} abertos
            + {overview.pendingTickets} aguardando resposta do cliente.
          </li>
          <li>
            <strong>CSAT médio é {overview.avgCsat}/5</strong> — abaixo do benchmark típico de 3.5.
            {worstChannel && ` Canal mais crítico: ${worstChannel.channel} (${worstChannel.avgCsat}).`}
          </li>
          <li>
            <strong>Chat tem o melhor CSAT ({bestChannel?.avgCsat})</strong> mas representa
            apenas {pct(channelStats.find(c => c.channel === bestChannel?.channel)?.total ?? 0, overview.totalTickets)}% do volume.
          </li>
          <li>
            <strong>Pior gargalo:</strong> {worstBottleneck?.channel} + {worstBottleneck?.type} —
            {' '}{worstBottleneck?.n} tickets com média de {worstBottleneck?.avgHours}h de resolução.
          </li>
        </ul>
      </div>

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
                  <div className="bg-gray-200 rounded-full flex-1" title={`Abertos/pendentes`} />
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
        Nota: dataset sintético — `Ticket Description` contém placeholders não substituídos
        (ex: <code>{'{product_purchased}'}</code>). Timestamps de resolução podem estar invertidos;
        usamos <code>ABS(DATE_DIFF)</code> para corrigir.
      </p>
    </div>
  )
}
