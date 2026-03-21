import { generateInsights, generateDiagnosticInsights, type ChurnInsightsPayload, type DiagnosticInsightsPayload } from '@/lib/insights'

// ── Overview insights card ────────────────────────────────────────────────────

export async function InsightsCard(payload: ChurnInsightsPayload) {
  const insights = await generateInsights(payload)

  if (!insights) {
    return <NoApiKeyBanner context="insights da visão geral" />
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-semibold text-amber-800">Achados principais</p>
        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">gerado por IA</span>
      </div>
      <ul className="text-sm text-amber-700 space-y-1.5 list-disc list-inside">
        {insights.map((insight, i) => (
          <li key={i}>{insight}</li>
        ))}
      </ul>
    </div>
  )
}

// ── Diagnostic insights card ──────────────────────────────────────────────────

export async function DiagnosticInsightsCard(payload: DiagnosticInsightsPayload) {
  const insights = await generateDiagnosticInsights(payload)

  if (!insights) {
    return <NoApiKeyBanner context="análise de causa raiz" />
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-semibold text-blue-800">Causa raiz — análise por IA</p>
        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">gerado por IA</span>
      </div>
      <ul className="text-sm text-blue-700 space-y-1.5 list-disc list-inside">
        {insights.map((insight, i) => (
          <li key={i}>{insight}</li>
        ))}
      </ul>
    </div>
  )
}

// ── No API key banner ─────────────────────────────────────────────────────────

function NoApiKeyBanner({ context }: { context: string }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-500 flex items-center gap-3">
      <span className="text-gray-400 text-lg">🔑</span>
      <span>
        Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para ativar {context} via IA.
      </span>
    </div>
  )
}

// ── Skeletons ─────────────────────────────────────────────────────────────────

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

export function DiagnosticInsightsCardSkeleton() {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
        <p className="text-sm font-semibold text-blue-700">Analisando causa raiz…</p>
      </div>
      <div className="space-y-2 animate-pulse">
        {[90, 75, 85].map(w => (
          <div key={w} className="h-3 bg-blue-200 rounded-full" style={{ width: `${w}%` }} />
        ))}
      </div>
    </div>
  )
}
