import { Suspense } from 'react'
import { getOverview, getChurnByIndustry, getChurnByChannel, getChurnByPlan, getChurnTimeline } from '@/lib/queries'
import { getAnalysisOutput } from '@/lib/analysis-output'
import { InsightsCard, InsightsCardSkeleton } from '@/components/InsightsCard'
import { ChurnTrendChart } from '@/components/ChurnTrendChart'

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

export default async function OverviewPage() {
  const [overview, industries, channels, plans, timeline] = await Promise.all([
    getOverview(),
    getChurnByIndustry(),
    getChurnByChannel(),
    getChurnByPlan(),
    getChurnTimeline(),
  ])

  const analysis = getAnalysisOutput()
  const atRiskCount = analysis?.atRiskAccounts?.length ?? 0
  const topReasons  = analysis?.churnReasons?.reasonBreakdown ?? []

  // Build payload for AI insights
  const insightsPayload = {
    overview,
    topIndustries: industries.slice(0, 3),
    topChannels:   channels.slice(0, 3),
    topPlans:      plans.slice(0, 3),
    supportAnalysis: analysis?.supportAnalysis ?? {
      avgTicketsChurned: 0,
      avgTicketsRetained: 0,
      avgResolutionHoursChurned: 0,
      avgResolutionHoursRetained: 0,
      avgCsatChurned: null,
      avgCsatRetained: null,
      escalationRateChurned: 0,
      escalationRateRetained: 0,
    },
    topReasons: topReasons.slice(0, 3),
    atRiskCount,
  }

  // Peak month
  const peakMonth = [...timeline].sort((a, b) => b.count - a.count)[0]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Visão Geral — Diagnóstico de Churn</h1>
        <p className="text-gray-500 text-sm mt-1">
          {overview.totalAccounts.toLocaleString()} contas analisadas · 5 tabelas RavenStack
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Churn Rate"
          value={`${overview.churnRate}%`}
          sub={`${overview.churnedAccounts} contas canceladas`}
          accent="text-red-600"
        />
        <KpiCard
          label="MRR Perdido"
          value={`$${overview.mrrChurned.toLocaleString()}`}
          sub="receita cancelada"
          accent="text-red-500"
        />
        <KpiCard
          label="MRR Retido"
          value={`$${overview.mrrRetained.toLocaleString()}`}
          sub="receita ativa"
          accent="text-green-600"
        />
        <KpiCard
          label="MRR Médio Churned"
          value={`$${overview.avgMrrChurned.toLocaleString()}`}
          sub={`vs $${overview.avgMrrRetained.toLocaleString()} retidos`}
        />
        <KpiCard
          label="Contas em Risco"
          value={atRiskCount}
          sub="retidas com sinais de risco"
          accent={atRiskCount > 50 ? 'text-amber-600' : 'text-gray-900'}
        />
      </div>

      {/* AI Insights */}
      <Suspense fallback={<InsightsCardSkeleton />}>
        <InsightsCard {...insightsPayload} />
      </Suspense>

      {/* Trend chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Cancelamentos por Mês
          </h2>
          {peakMonth && (
            <span className="text-xs text-red-600 bg-red-50 border border-red-100 px-2 py-0.5 rounded-full">
              Pico: {peakMonth.month} ({peakMonth.count} cancelamentos)
            </span>
          )}
        </div>
        <ChurnTrendChart data={timeline} />
      </div>

      {/* Top segment snapshot */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* By industry */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Por Indústria</h2>
          <div className="space-y-3">
            {industries.slice(0, 5).map(s => (
              <div key={s.segment}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{s.segment}</span>
                  <div className="flex gap-2 items-center">
                    <span className="text-xs text-gray-400">{s.total}</span>
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${s.churnRate >= 40 ? 'bg-red-100 text-red-700' : s.churnRate >= 25 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {s.churnRate}%
                    </span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${s.churnRate >= 40 ? 'bg-red-400' : s.churnRate >= 25 ? 'bg-yellow-400' : 'bg-green-400'}`}
                    style={{ width: `${Math.min(s.churnRate, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By channel */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Por Canal de Aquisição</h2>
          <div className="space-y-3">
            {channels.slice(0, 5).map(s => (
              <div key={s.segment}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{s.segment}</span>
                  <div className="flex gap-2 items-center">
                    <span className="text-xs text-gray-400">{s.total}</span>
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${s.churnRate >= 40 ? 'bg-red-100 text-red-700' : s.churnRate >= 25 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {s.churnRate}%
                    </span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${s.churnRate >= 40 ? 'bg-red-400' : s.churnRate >= 25 ? 'bg-yellow-400' : 'bg-green-400'}`}
                    style={{ width: `${Math.min(s.churnRate, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By plan */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Por Plano</h2>
          <div className="space-y-3">
            {plans.slice(0, 5).map(s => (
              <div key={s.segment}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{s.segment}</span>
                  <div className="flex gap-2 items-center">
                    <span className="text-xs text-gray-400">{s.total}</span>
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${s.churnRate >= 40 ? 'bg-red-100 text-red-700' : s.churnRate >= 25 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {s.churnRate}%
                    </span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${s.churnRate >= 40 ? 'bg-red-400' : s.churnRate >= 25 ? 'bg-yellow-400' : 'bg-green-400'}`}
                    style={{ width: `${Math.min(s.churnRate, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Churn reasons */}
      {topReasons.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Motivos de Cancelamento
          </h2>
          <div className="space-y-3">
            {topReasons.map(r => (
              <div key={r.reasonCode}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium capitalize">{r.reasonCode}</span>
                  <div className="flex gap-3 items-center">
                    <span className="text-xs text-gray-400">{r.count} casos</span>
                    <span className="text-xs font-semibold text-gray-600">{r.pct}%</span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-400 rounded-full"
                    style={{ width: `${r.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
