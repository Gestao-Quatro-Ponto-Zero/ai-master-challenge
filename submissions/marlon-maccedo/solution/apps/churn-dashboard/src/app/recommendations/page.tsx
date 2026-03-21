import { Suspense } from 'react'
import { getOverview, getChurnByIndustry, getChurnByChannel, getChurnByPlan } from '@/lib/queries'
import { getAnalysisOutput } from '@/lib/analysis-output'
import { generateRecommendations, type ChurnInsightsPayload } from '@/lib/insights'
import { getOpenRouterApiKey } from '@/lib/env'

const EFFORT_COLOR: Record<string, string> = {
  baixo: 'bg-green-100 text-green-700',
  médio: 'bg-yellow-100 text-yellow-700',
  alto:  'bg-red-100 text-red-700',
}

async function RecommendationsContent({ payload }: { payload: ChurnInsightsPayload }) {
  const hasKey = Boolean(getOpenRouterApiKey())
  const reco = await generateRecommendations(payload)

  if (!reco) {
    if (hasKey) {
      return (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-sm text-amber-900 flex items-center gap-3">
          <span className="text-lg">⚠️</span>
          <span>
            Não foi possível gerar recomendações agora (falha na API OpenRouter ou resposta inválida). Confira a key e os logs no Railway.
          </span>
        </div>
      )
    }
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-sm text-gray-500 flex items-center gap-3">
        <span className="text-gray-400 text-lg">🔑</span>
        <span>
          Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para gerar recomendações de retenção via IA.
          Sem análise por IA, não é possível gerar ações priorizadas com base nos dados.
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold text-gray-900">Ações Prioritárias de Retenção</h2>
        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">gerado por IA com dados reais</span>
      </div>

      <div className="space-y-3">
        {reco.actions.map(action => (
          <div key={action.priority} className="bg-white rounded-xl border border-gray-200 p-5 flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600">
              {action.priority}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                  {action.segment}
                </span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${EFFORT_COLOR[action.effort] ?? 'bg-gray-100 text-gray-600'}`}>
                  esforço {action.effort}
                </span>
              </div>
              <p className="text-sm font-medium text-gray-800 mb-1">{action.action}</p>
              <p className="text-xs text-gray-500">
                Impacto estimado: <span className="font-semibold text-green-700">{action.mrrImpact}</span>
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-red-50 border border-red-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-red-800 mb-3">O Que NÃO Fazer</h3>
        <ul className="space-y-2">
          {reco.notToDo.map((item, i) => (
            <li key={i} className="flex gap-2 text-sm text-red-700">
              <span className="flex-shrink-0 mt-0.5">✗</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function RecoSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-48" />
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 flex gap-4">
          <div className="w-8 h-8 rounded-full bg-gray-200 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-3 bg-gray-200 rounded w-32" />
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-3 bg-gray-200 rounded w-48" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default async function RecommendationsPage() {
  const [overview, industries, channels, plans] = await Promise.all([
    getOverview(),
    getChurnByIndustry(),
    getChurnByChannel(),
    getChurnByPlan(),
  ])

  const analysis = getAnalysisOutput()

  const payload: ChurnInsightsPayload = {
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
    topReasons: analysis?.churnReasons?.reasonBreakdown?.slice(0, 3) ?? [],
    atRiskCount: analysis?.atRiskAccounts?.length ?? 0,
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Recomendações</h1>
        <p className="text-gray-500 text-sm mt-1">
          Ações geradas por IA com base nos dados reais · churn rate {overview.churnRate}% ·{' '}
          ${overview.mrrChurned.toLocaleString()} em MRR cancelado
        </p>
      </div>

      {/* Data context for AI */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Pior Indústria</p>
          <p className="font-semibold text-gray-800">{industries[0]?.segment ?? '—'}</p>
          <p className="text-xs text-gray-500">{industries[0]?.churnRate ?? 0}% · ${(industries[0]?.mrrLost ?? 0).toLocaleString()} perdidos</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Pior Canal</p>
          <p className="font-semibold text-gray-800">{channels[0]?.segment ?? '—'}</p>
          <p className="text-xs text-gray-500">{channels[0]?.churnRate ?? 0}% churn rate</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Principal Motivo</p>
          <p className="font-semibold text-gray-800 capitalize">
            {analysis?.churnReasons?.reasonBreakdown?.[0]?.reasonCode ?? '—'}
          </p>
          <p className="text-xs text-gray-500">
            {analysis?.churnReasons?.reasonBreakdown?.[0]?.pct ?? 0}% dos cancelamentos
          </p>
        </div>
      </div>

      <Suspense fallback={<RecoSkeleton />}>
        <RecommendationsContent payload={payload} />
      </Suspense>

      <p className="text-xs text-gray-400 italic">
        Recomendações geradas por IA com base no dataset RavenStack (sintético). Validar com dados de produção antes de priorizar investimentos.
      </p>
    </div>
  )
}
