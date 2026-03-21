import { generateInsights, type InsightsPayload } from '@/lib/insights'

export async function ProposalDiagnosis(payload: InsightsPayload) {
  const insights = await generateInsights(payload)

  if (!insights) {
    return (
      <section className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-500 flex items-center gap-3">
        <span className="text-gray-400 text-lg">🔑</span>
        <span>Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para ativar diagnóstico via IA.</span>
      </section>
    )
  }

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Diagnóstico resumido</h2>
        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">gerado por IA</span>
      </div>
      <ul className="space-y-2 text-sm text-gray-700">
        {insights.map((insight, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-red-500 font-bold mt-0.5 shrink-0">→</span>
            <span>{insight}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function ProposalDiagnosisSkeleton() {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-3">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-4 h-4 rounded-full border-2 border-gray-300 border-t-transparent animate-spin" />
        <p className="text-sm font-semibold text-gray-500">Gerando diagnóstico com IA…</p>
      </div>
      <div className="space-y-2 animate-pulse">
        {[90, 75, 85].map(w => (
          <div key={w} className="h-3 bg-gray-100 rounded-full" style={{ width: `${w}%` }} />
        ))}
      </div>
    </section>
  )
}
