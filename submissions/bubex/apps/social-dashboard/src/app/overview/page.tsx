import { Suspense } from 'react'
import {
  getOverview,
  getEngagementByPlatform,
  getEngagementByContentType,
  getEngagementByCategory,
} from '@/lib/queries'
import { generateOverviewInsights, type SocialInsightsPayload } from '@/lib/insights'
import { getAnalysisOutput } from '@/lib/analysis-output'
import { InsightsSkeleton } from '@/components/SocialInsightsCard'
import EngagementBarChart from '@/components/EngagementBarChart'

async function OverviewInsightsCard({ payload }: { payload: SocialInsightsPayload }) {
  const insights = await generateOverviewInsights(payload)

  if (!insights) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-sm text-gray-500 flex items-center gap-3">
        <span className="text-gray-400 text-lg">🔑</span>
        <span>
          Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para
          gerar achados automáticos a partir dos dados.
        </span>
      </div>
    )
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">Achados por IA</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-600">com dados reais</span>
      </div>
      <ul className="space-y-2">
        {insights.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm text-amber-800">
            <span className="flex-shrink-0 font-bold">{i + 1}.</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default async function OverviewPage() {
  const [overview, byPlatform, byType, byCategory] = await Promise.all([
    getOverview(),
    getEngagementByPlatform(),
    getEngagementByContentType(),
    getEngagementByCategory(),
  ])

  const sponsoredPct = overview.totalPosts > 0
    ? Math.round(overview.sponsoredCount / overview.totalPosts * 100)
    : 0

  const payload: SocialInsightsPayload = {
    overview,
    topPlatform: byPlatform[0],
    sponsorship: {
      avgEngagementOrganic: 0,
      avgEngagementSponsored: 0,
      avgViewsOrganic: 0,
      avgViewsSponsored: 0,
      avgLikesOrganic: 0,
      avgLikesSponsored: 0,
      avgSharesOrganic: 0,
      avgSharesSponsored: 0,
      organicCount: overview.organicCount,
      sponsoredCount: overview.sponsoredCount,
    },
    bestCreatorTier: 'nano (<10K)',
  }

  const analysis = getAnalysisOutput()
  const temporalData = analysis?.temporal.map(r => ({ name: r.month, value: r.totalPosts })) ?? []

  const platformChartData = byPlatform.map(r => ({ name: r.platform, value: r.avgEngagementRate }))
  const typeChartData = byType.map(r => ({ name: r.contentType, value: r.avgEngagementRate }))
  const maxCategoryRate = Math.max(...byCategory.map(r => r.avgEngagementRate), 1)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Visão Geral</h1>
        <p className="text-gray-500 text-sm mt-1">
          {overview.totalPosts.toLocaleString()} posts · {byPlatform.length} plataformas
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Total Posts</p>
          <p className="text-2xl font-bold text-gray-900">{overview.totalPosts.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Total Views</p>
          <p className="text-2xl font-bold text-gray-900">
            {(overview.totalViews / 1_000_000).toFixed(1)}M
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Engajamento Médio</p>
          <p className="text-2xl font-bold text-blue-600">{overview.avgEngagementRate}%</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">% Patrocinado</p>
          <p className="text-2xl font-bold text-purple-600">{sponsoredPct}%</p>
          <p className="text-xs text-gray-400">{overview.sponsoredCount.toLocaleString()} posts</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Orgânico</p>
          <p className="text-2xl font-bold text-green-600">{overview.organicCount.toLocaleString()}</p>
          <p className="text-xs text-gray-400">posts orgânicos</p>
        </div>
      </div>

      {/* AI Insights */}
      <Suspense fallback={<InsightsSkeleton />}>
        <OverviewInsightsCard payload={payload} />
      </Suspense>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Plataforma</h2>
          <EngagementBarChart data={platformChartData} color="#3b82f6" />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Tipo de Conteúdo</h2>
          <EngagementBarChart data={typeChartData} color="#8b5cf6" />
        </div>
      </div>

      {/* Temporal trend */}
      {temporalData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Volume de Posts por Mês</h2>
          <EngagementBarChart data={temporalData} color="#10b981" unit="" />
        </div>
      )}

      {/* Categories */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Categoria</h2>
        <div className="space-y-2">
          {byCategory.map(row => (
            <div key={row.category} className="flex items-center gap-3">
              <span className="text-xs text-gray-600 w-24 shrink-0 capitalize">{row.category}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(row.avgEngagementRate / maxCategoryRate) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-700 w-12 text-right">{row.avgEngagementRate}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
