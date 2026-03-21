import {
  getHeatmapData,
  getCreatorTierAnalysis,
  getEngagementByCategory,
  getEngagementByPlatform,
} from '@/lib/queries'
import { getAnalysisOutput } from '@/lib/analysis-output'
import EngagementBarChart from '@/components/EngagementBarChart'

const TIER_BADGE: Record<string, string> = {
  'nano (<10K)':    'bg-green-100 text-green-700',
  'micro (10K-100K)': 'bg-blue-100 text-blue-700',
  'macro (100K-1M)':  'bg-purple-100 text-purple-700',
  'mega (>1M)':       'bg-amber-100 text-amber-700',
}

export default async function PerformancePage() {
  const analysis = getAnalysisOutput()
  const efficiency = analysis?.creatorEfficiency ?? []

  const [heatmap, tiers, byCategory, byPlatform] = await Promise.all([
    getHeatmapData(),
    getCreatorTierAnalysis(),
    getEngagementByCategory(),
    getEngagementByPlatform(),
  ])

  const platforms    = [...new Set(heatmap.map(r => r.platform))].sort()
  const contentTypes = [...new Set(heatmap.map(r => r.contentType))].sort()
  const maxEngagement = Math.max(...heatmap.map(r => r.avgEngagementPct), 1)

  function getCell(platform: string, contentType: string) {
    return heatmap.find(r => r.platform === platform && r.contentType === contentType)
  }

  const categoryChartData = byCategory.map(r => ({ name: r.category, value: r.avgEngagementRate }))

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Performance</h1>
        <p className="text-gray-500 text-sm mt-1">Heatmap de engajamento · tiers de criadores</p>
      </div>

      {/* Heatmap */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 overflow-x-auto">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Heatmap — Plataforma × Tipo de Conteúdo (Engajamento %)
        </h2>
        <table className="min-w-full text-xs">
          <thead>
            <tr>
              <th className="text-left text-gray-400 font-medium py-1 pr-4 w-32">Plataforma</th>
              {contentTypes.map(ct => (
                <th key={ct} className="text-center text-gray-400 font-medium py-1 px-2 capitalize">{ct}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {platforms.map(platform => (
              <tr key={platform}>
                <td className="text-gray-700 font-medium py-1 pr-4">{platform}</td>
                {contentTypes.map(ct => {
                  const cell = getCell(platform, ct)
                  const opacity = cell ? cell.avgEngagementPct / maxEngagement : 0
                  return (
                    <td
                      key={ct}
                      className="py-1 px-2 text-center"
                      style={{ backgroundColor: `rgba(59,130,246,${opacity.toFixed(2)})` }}
                    >
                      <span className="text-gray-800 font-medium">
                        {cell ? `${cell.avgEngagementPct}%` : '—'}
                      </span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Creator Tiers */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Engajamento por Tier de Criador</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tiers.map(tier => {
            const eff = efficiency.find(e => e.tier === tier.tier)
            return (
              <div key={tier.tier} className="bg-white rounded-xl border border-gray-200 p-4">
                <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-2 ${TIER_BADGE[tier.tier] ?? 'bg-gray-100 text-gray-600'}`}>
                  {tier.tier}
                </span>
                <p className="text-2xl font-bold text-gray-900">{tier.avgEngagementRate}%</p>
                <p className="text-xs text-gray-400 mt-1">{tier.totalPosts.toLocaleString()} posts</p>
                <p className="text-xs text-gray-400">~{(tier.avgFollowers / 1000).toFixed(0)}K seguidores</p>
                {eff && (
                  <p className="text-xs text-blue-600 mt-1 font-medium">
                    {eff.avgEngPer1KFollowers.toFixed(4)} eng/1K seg
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Platform and Category charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Plataforma</h2>
          <EngagementBarChart
            data={byPlatform.map(r => ({ name: r.platform, value: r.avgEngagementRate }))}
            color="#3b82f6"
          />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Categoria</h2>
          <EngagementBarChart data={categoryChartData} color="#10b981" />
        </div>
      </div>
    </div>
  )
}
