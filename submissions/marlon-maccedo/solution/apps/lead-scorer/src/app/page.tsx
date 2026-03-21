import { getDashboardStats } from '@/lib/queries'

function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n}`
}

function pct(n: number, total: number) {
  return total === 0 ? 0 : Math.round((n / total) * 100)
}

// ── Primitives ────────────────────────────────────────────────────────────────

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

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{children}</h2>
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default async function DashboardPage() {
  const s = await getDashboardStats()

  const maxRegionValue   = Math.max(...s.byRegion.map(r => r.value))
  const maxProductValue  = Math.max(...s.byProduct.map(p => p.value))
  const maxAgingDeals    = Math.max(...s.byAging.map(a => a.deals))

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Visão geral do pipeline — {s.total} deals abertos</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <KpiCard label="Pipeline total"  value={fmt(s.pipelineValue)} />
        <KpiCard label="Score médio"     value={s.avgScore} sub="de 100" />
        <KpiCard label="Hot"  value={s.hot}  sub={`${pct(s.hot,  s.total)}% do pipeline`} accent="text-red-600" />
        <KpiCard label="Warm" value={s.warm} sub={`${pct(s.warm, s.total)}% do pipeline`} accent="text-yellow-500" />
        <KpiCard label="Cold" value={s.cold} sub={`${pct(s.cold, s.total)}% do pipeline`} accent="text-blue-500" />
        <KpiCard label="Engaging" value={s.engaging} sub={`${pct(s.engaging, s.total)}% dos deals`} accent="text-purple-600" />
      </div>

      {/* Score distribution + Stage split */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Distribuição de score</SectionTitle>
          <div className="flex h-6 rounded-full overflow-hidden gap-0.5">
            <div className="bg-red-500"    style={{ width: `${pct(s.hot,  s.total)}%` }} title={`Hot: ${s.hot}`} />
            <div className="bg-yellow-400" style={{ width: `${pct(s.warm, s.total)}%` }} title={`Warm: ${s.warm}`} />
            <div className="bg-blue-400"   style={{ width: `${pct(s.cold, s.total)}%` }} title={`Cold: ${s.cold}`} />
          </div>
          <div className="flex gap-6 mt-3 text-sm">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> Hot {pct(s.hot, s.total)}%</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400 inline-block" /> Warm {pct(s.warm, s.total)}%</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" /> Cold {pct(s.cold, s.total)}%</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Stage</SectionTitle>
          <div className="space-y-3">
            {[
              { label: 'Engaging',    value: s.engaging,    color: 'bg-purple-500' },
              { label: 'Prospecting', value: s.prospecting, color: 'bg-gray-400'   },
            ].map(row => (
              <div key={row.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{row.label}</span>
                  <span className="text-gray-400">{row.value} · {pct(row.value, s.total)}%</span>
                </div>
                <Bar value={row.value} max={s.total} color={row.color} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* By region + By product */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Pipeline por região</SectionTitle>
          <div className="space-y-3">
            {s.byRegion.map(r => (
              <div key={r.region}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{r.region}</span>
                  <span className="text-gray-400">{fmt(r.value)} · {r.deals} deals</span>
                </div>
                <Bar value={r.value} max={maxRegionValue} color="bg-indigo-400" />
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Pipeline por produto</SectionTitle>
          <div className="space-y-3">
            {s.byProduct.map(p => (
              <div key={p.product}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{p.product}</span>
                  <span className="text-gray-400">{fmt(p.value)} · {p.deals} deals</span>
                </div>
                <Bar value={p.value} max={maxProductValue} color="bg-emerald-400" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Aging + Top agents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Aging do pipeline</SectionTitle>
          <div className="space-y-3">
            {s.byAging.map(b => (
              <div key={b.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className={`text-gray-700 ${b.label.startsWith('200') ? 'text-red-500 font-medium' : ''}`}>{b.label}</span>
                  <span className="text-gray-400">{b.deals} deals · {pct(b.deals, s.total)}%</span>
                </div>
                <Bar value={b.deals} max={maxAgingDeals}
                  color={b.label.startsWith('200') ? 'bg-red-400' : 'bg-amber-300'} />
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <SectionTitle>Top 10 agentes por score médio</SectionTitle>
          <div className="space-y-2">
            {s.topAgents.map((a, i) => (
              <div key={a.agent} className="flex items-center gap-3 text-sm">
                <span className="w-5 text-right text-gray-300 text-xs font-mono">{i + 1}</span>
                <span className="flex-1 text-gray-800 truncate">{a.agent}</span>
                <span className="text-gray-400 text-xs">{a.deals} deals</span>
                {a.hot > 0 && (
                  <span className="text-red-500 text-xs font-medium">{a.hot} hot</span>
                )}
                <span className={`w-8 text-right font-bold tabular-nums ${
                  a.avgScore >= 70 ? 'text-red-600' :
                  a.avgScore >= 40 ? 'text-yellow-600' : 'text-blue-500'
                }`}>{a.avgScore}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
