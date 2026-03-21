import { Suspense } from 'react'
import { getAnalysisOutput } from '@/lib/analysis-output'
import { getOverview, getChurnByIndustry, getChurnByChannel } from '@/lib/queries'
import { DiagnosticInsightsCard, DiagnosticInsightsCardSkeleton } from '@/components/InsightsCard'

function PValueBadge({ p }: { p: number | null }) {
  if (p === null) return <span className="text-xs text-gray-400">n/a</span>
  const sig = p < 0.05
  return (
    <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${sig ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
      p={p.toFixed(3)}{sig ? ' ✓' : ''}
    </span>
  )
}

export default async function DiagnosticPage() {
  const [overview, industries, channels, analysis] = await Promise.all([
    getOverview(),
    getChurnByIndustry(),
    getChurnByChannel(),
    Promise.resolve(getAnalysisOutput()),
  ])

  const features = analysis?.featureAnalysis?.features ?? []
  const support  = analysis?.supportAnalysis
  const reasons  = analysis?.churnReasons?.reasonBreakdown ?? []
  const themes   = analysis?.churnReasons?.feedbackThemes ?? []

  const diagPayload = analysis ? {
    overview,
    topFeatures:   features.slice(0, 8),
    supportAnalysis: analysis.supportAnalysis,
    topReasons:    reasons.slice(0, 4),
    topIndustries: industries.slice(0, 3),
  } : null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Diagnóstico de Causa Raiz</h1>
        <p className="text-gray-500 text-sm mt-1">
          Cruzamento de 5 tabelas · {overview.totalAccounts.toLocaleString()} contas · churn rate {overview.churnRate}%
        </p>
      </div>

      {!analysis && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-sm text-yellow-800">
          <span className="font-semibold">Análise Python não encontrada.</span>{' '}
          Execute <code className="bg-yellow-100 px-1 rounded">python scripts/generate_analysis.py</code> para gerar os dados estatísticos.
        </div>
      )}

      {/* AI diagnostic insights */}
      {diagPayload && (
        <Suspense fallback={<DiagnosticInsightsCardSkeleton />}>
          <DiagnosticInsightsCard {...diagPayload} />
        </Suspense>
      )}

      {/* Support comparison — raw numbers only, no interpretation */}
      {support && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Suporte: Churned vs Retidos
            </h2>
            <span className="text-xs text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
              via análise Python
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              {
                label: 'Tickets por conta',
                churned: support.avgTicketsChurned.toFixed(1),
                retained: support.avgTicketsRetained.toFixed(1),
                higher: support.avgTicketsChurned > support.avgTicketsRetained,
              },
              {
                label: 'Resolução média (h)',
                churned: support.avgResolutionHoursChurned.toFixed(1),
                retained: support.avgResolutionHoursRetained.toFixed(1),
                higher: support.avgResolutionHoursChurned > support.avgResolutionHoursRetained,
              },
              {
                label: 'CSAT médio',
                churned: support.avgCsatChurned !== null ? support.avgCsatChurned.toFixed(2) : '—',
                retained: support.avgCsatRetained !== null ? support.avgCsatRetained.toFixed(2) : '—',
                higher: (support.avgCsatChurned ?? 0) < (support.avgCsatRetained ?? 0),
              },
              {
                label: 'Escalações (%)',
                churned: support.escalationRateChurned.toFixed(1),
                retained: support.escalationRateRetained.toFixed(1),
                higher: support.escalationRateChurned > support.escalationRateRetained,
              },
            ].map(({ label, churned, retained, higher }) => (
              <div key={label} className={`rounded-lg p-3 border ${higher ? 'border-red-100 bg-red-50' : 'border-gray-100 bg-gray-50'}`}>
                <p className="text-xs text-gray-500 mb-2">{label}</p>
                <div className="flex justify-between text-sm">
                  <div>
                    <p className="text-xs text-gray-400">Churned</p>
                    <p className={`font-bold ${higher ? 'text-red-700' : 'text-gray-800'}`}>{churned}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Retidos</p>
                    <p className="font-bold text-green-700">{retained}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature usage comparison — data only */}
      {features.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Uso de Features: Churned vs Retidos
            </h2>
            <span className="text-xs text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
              via análise Python · Mann-Whitney U
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Feature', 'Uso Médio Churned', 'Uso Médio Retidos', 'Delta (ret−ch)', 'Erro Churned', 'p-value'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {features.slice(0, 15).map(f => (
                  <tr key={f.feature} className="hover:bg-gray-50">
                    <td className="px-3 py-2.5 font-medium text-gray-800">{f.feature}</td>
                    <td className="px-3 py-2.5 text-gray-600">{f.avgCountChurned.toFixed(1)}</td>
                    <td className="px-3 py-2.5 text-gray-600">{f.avgCountRetained.toFixed(1)}</td>
                    <td className="px-3 py-2.5">
                      <span className={`text-xs font-mono font-semibold ${f.delta > 0 ? 'text-green-700' : f.delta < 0 ? 'text-red-700' : 'text-gray-500'}`}>
                        {f.delta > 0 ? '+' : ''}{f.delta.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-gray-500">{f.avgErrorChurned.toFixed(1)}</td>
                    <td className="px-3 py-2.5">
                      <PValueBadge p={f.pValue} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-3 italic">
            Delta = uso médio retidos − uso médio churned. p &lt; 0.05 indica diferença estatisticamente significativa (Mann-Whitney U).
          </p>
        </div>
      )}

      {/* Segment breakdowns — data only */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* By channel */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Churn por Canal de Aquisição</h2>
          <div className="space-y-3">
            {channels.map(s => (
              <div key={s.segment}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{s.segment}</span>
                  <div className="flex gap-2 items-center">
                    <span className="text-xs text-gray-400">{s.total} contas</span>
                    <span className="text-xs font-semibold text-gray-600">{s.churnRate}%</span>
                    <span className="text-xs text-gray-400">${s.mrrLost.toLocaleString()} perdidos</span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-400 rounded-full" style={{ width: `${Math.min(s.churnRate, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Churn reasons */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Motivos de Cancelamento</h2>
          <div className="space-y-3">
            {reasons.map(r => (
              <div key={r.reasonCode}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium capitalize">{r.reasonCode}</span>
                  <div className="flex gap-2 items-center">
                    <span className="text-xs text-gray-400">{r.count} casos</span>
                    <span className="text-xs font-semibold text-gray-600">{r.pct}%</span>
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-400 rounded-full" style={{ width: `${r.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feedback word frequency */}
      {themes.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Palavras-chave no Feedback de Cancelamento
          </h2>
          <div className="flex flex-wrap gap-2">
            {themes.map(t => (
              <span
                key={t.theme}
                className="px-3 py-1.5 rounded-full text-sm font-medium border bg-gray-50 text-gray-700 border-gray-200"
              >
                {t.theme} <span className="text-gray-400 text-xs">({t.count})</span>
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3 italic">
            Frequência de palavras extraída de {reasons.reduce((a, r) => a + r.count, 0)} registros de feedback_text em churn_events.
          </p>
        </div>
      )}
    </div>
  )
}
