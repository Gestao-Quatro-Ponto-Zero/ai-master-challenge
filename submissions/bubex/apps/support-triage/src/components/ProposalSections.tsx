import { generateProposal, type InsightsPayload } from '@/lib/insights'

export async function ProposalAutomation(payload: InsightsPayload) {
  const { automationItems } = await generateProposal(payload)
  const hasAI = !!process.env.OPENROUTER_API_KEY

  const toAutomate = automationItems.filter(i => i.automate)
  const notAutomate = automationItems.filter(i => !i.automate)

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">O que automatizar — e o que não</h2>
        <span className={`text-xs px-2 py-0.5 rounded-full ${hasAI ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
          {hasAI ? 'gerado por IA' : 'calculado dos dados'}
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-sm font-semibold text-green-700 mb-2">Automatizar</p>
          <div className="space-y-2">
            {toAutomate.map((item, i) => (
              <div key={i} className="bg-green-50 rounded-lg p-3">
                <p className="text-sm font-medium text-green-800">{item.title}</p>
                <p className="text-xs text-green-600 mt-0.5">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-sm font-semibold text-red-700 mb-2">NÃO automatizar</p>
          <div className="space-y-2">
            {notAutomate.map((item, i) => (
              <div key={i} className="bg-red-50 rounded-lg p-3">
                <p className="text-sm font-medium text-red-800">{item.title}</p>
                <p className="text-xs text-red-600 mt-0.5">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

export async function ProposalLimitations(payload: InsightsPayload) {
  const { limitations } = await generateProposal(payload)
  const hasAI = !!process.env.OPENROUTER_API_KEY

  return (
    <section className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-2">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-amber-800 uppercase tracking-wide">Limitações honestas</h2>
        <span className={`text-xs px-2 py-0.5 rounded-full ${hasAI ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
          {hasAI ? 'gerado por IA' : 'calculado dos dados'}
        </span>
      </div>
      <ul className="text-sm text-amber-700 space-y-1 list-disc list-inside">
        {limitations.map((l, i) => <li key={i}>{l}</li>)}
      </ul>
    </section>
  )
}

export function ProposalSectionSkeleton({ label }: { label: string }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-4 h-4 rounded-full border-2 border-gray-300 border-t-transparent animate-spin" />
        <p className="text-sm font-semibold text-gray-500">Gerando {label} com IA…</p>
      </div>
      <div className="space-y-2 animate-pulse">
        {[85, 70, 90, 75].map(w => (
          <div key={w} className="h-3 bg-gray-100 rounded-full" style={{ width: `${w}%` }} />
        ))}
      </div>
    </section>
  )
}
