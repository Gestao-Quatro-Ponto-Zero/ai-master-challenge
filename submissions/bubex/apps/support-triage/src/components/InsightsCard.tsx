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
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 animate-pulse">
      <div className="h-4 bg-amber-200 rounded w-32 mb-3" />
      <div className="space-y-2">
        {[80, 95, 70, 85].map(w => (
          <div key={w} className="h-3 bg-amber-100 rounded" style={{ width: `${w}%` }} />
        ))}
      </div>
    </div>
  )
}
