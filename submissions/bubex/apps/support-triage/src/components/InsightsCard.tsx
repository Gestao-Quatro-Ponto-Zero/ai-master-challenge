import { generateInsights, type InsightsPayload } from '@/lib/insights'

export async function InsightsCard(payload: InsightsPayload) {
  const insights = await generateInsights(payload)
  const hasAI = !!process.env.OPENROUTER_API_KEY

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-semibold text-amber-800">Achados principais</p>
        <span className={`text-xs px-2 py-0.5 rounded-full ${hasAI ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
          {hasAI ? 'gerado por IA' : 'calculado dos dados'}
        </span>
      </div>
      <ul className="text-sm text-amber-700 space-y-1.5 list-disc list-inside">
        {insights.map((insight, i) => (
          <li key={i}>{insight}</li>
        ))}
      </ul>
    </div>
  )
}

export function InsightsCardSkeleton() {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-4 h-4 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
        <p className="text-sm font-semibold text-amber-700">Gerando insights com IA…</p>
      </div>
      <div className="space-y-2 animate-pulse">
        {[82, 96, 71, 88].map(w => (
          <div key={w} className="h-3 bg-amber-200 rounded-full" style={{ width: `${w}%` }} />
        ))}
      </div>
    </div>
  )
}
