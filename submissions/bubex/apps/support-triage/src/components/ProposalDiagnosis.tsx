import { generateInsights, type InsightsPayload } from '@/lib/insights'

export async function ProposalDiagnosis(payload: InsightsPayload) {
  const insights = await generateInsights(payload)
  const hasAI = !!process.env.OPENROUTER_API_KEY

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Diagnóstico resumido</h2>
        <span className={`text-xs px-2 py-0.5 rounded-full ${hasAI ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
          {hasAI ? 'gerado por IA' : 'calculado dos dados'}
        </span>
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
    <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-3 animate-pulse">
      <div className="h-4 bg-gray-100 rounded w-40 mb-3" />
      <div className="space-y-2">
        {[90, 75, 85].map(w => (
          <div key={w} className="h-3 bg-gray-100 rounded" style={{ width: `${w}%` }} />
        ))}
      </div>
    </section>
  )
}
