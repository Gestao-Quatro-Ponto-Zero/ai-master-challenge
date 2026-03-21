import { Suspense } from 'react'
import {
  getOverview,
  getEngagementByPlatform,
  getSponsorshipComparison,
  getCreatorTierAnalysis,
} from '@/lib/queries'
import {
  generateStrategyRecommendations,
  type SocialInsightsPayload,
  type StrategyOutput,
} from '@/lib/insights'
import { getOpenRouterApiKey } from '@/lib/env'
import { ApiFailureBanner, NoApiKeyBanner, StrategySkeleton } from '@/components/SocialInsightsCard'

const EFFORT_COLOR: Record<string, string> = {
  baixo: 'bg-green-100 text-green-700',
  médio: 'bg-yellow-100 text-yellow-700',
  alto:  'bg-red-100 text-red-700',
}

async function StrategyContent({ payload }: { payload: SocialInsightsPayload }) {
  const hasKey = Boolean(getOpenRouterApiKey())
  const strategy = await generateStrategyRecommendations(payload)

  if (!strategy) {
    if (hasKey) {
      return <ApiFailureBanner context="as recomendações estratégicas" />
    }
    return <NoApiKeyBanner />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold text-gray-900">Recomendações Estratégicas</h2>
        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">gerado por IA com dados reais</span>
      </div>

      <div className="space-y-3">
        {strategy.recommendations.map(rec => (
          <div key={rec.priority} className="bg-white rounded-xl border border-gray-200 p-5 flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600">
              {rec.priority}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                  {rec.platform}
                </span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${EFFORT_COLOR[rec.effort] ?? 'bg-gray-100 text-gray-600'}`}>
                  esforço {rec.effort}
                </span>
              </div>
              <p className="text-sm font-medium text-gray-800 mb-1">{rec.action}</p>
              <p className="text-xs text-gray-500">
                Impacto esperado: <span className="font-semibold text-green-700">{rec.kpiImpact}</span>
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-red-50 border border-red-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-red-800 mb-3">O Que NÃO Fazer</h3>
        <ul className="space-y-2">
          {strategy.notToDo.map((item, i) => (
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

export default async function StrategyPage() {
  const [overview, byPlatform, sponsorship, tiers] = await Promise.all([
    getOverview(),
    getEngagementByPlatform(),
    getSponsorshipComparison(),
    getCreatorTierAnalysis(),
  ])

  const bestTier = tiers[0]?.tier ?? 'nano (<10K)'

  const payload: SocialInsightsPayload = {
    overview,
    topPlatform: byPlatform[0],
    sponsorship,
    bestCreatorTier: bestTier,
  }

  const sponsoredPct = overview.totalPosts > 0
    ? Math.round(overview.sponsoredCount / overview.totalPosts * 100)
    : 0

  const engDelta = (sponsorship.avgEngagementSponsored - sponsorship.avgEngagementOrganic).toFixed(2)
  const engDeltaPositive = sponsorship.avgEngagementSponsored > sponsorship.avgEngagementOrganic

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Estratégia</h1>
        <p className="text-gray-500 text-sm mt-1">
          Recomendações geradas por IA com base nos {overview.totalPosts.toLocaleString()} posts analisados
        </p>
      </div>

      {/* Context grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Melhor Plataforma</p>
          <p className="font-semibold text-gray-800">{byPlatform[0]?.platform ?? '—'}</p>
          <p className="text-xs text-gray-500">{byPlatform[0]?.avgEngagementRate ?? 0}% engajamento</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Melhor Tier de Criador</p>
          <p className="font-semibold text-gray-800">{bestTier}</p>
          <p className="text-xs text-gray-500">{tiers[0]?.avgEngagementRate ?? 0}% engajamento</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Delta Patrocínio</p>
          <p className={`font-semibold ${engDeltaPositive ? 'text-green-600' : 'text-red-600'}`}>
            {engDeltaPositive ? '+' : ''}{engDelta}%
          </p>
          <p className="text-xs text-gray-500">{sponsoredPct}% posts patrocinados</p>
        </div>
      </div>

      <Suspense fallback={<StrategySkeleton />}>
        <StrategyContent payload={payload} />
      </Suspense>

      <p className="text-xs text-gray-400 italic">
        Recomendações geradas por IA com base no dataset Kaggle (CC0). Validar com dados reais antes de priorizar investimentos.
      </p>
    </div>
  )
}
