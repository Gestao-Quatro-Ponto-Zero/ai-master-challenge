import {
  getSponsorshipComparison,
  getSponsorshipByCategory,
  getDisclosureTypeAnalysis,
  getSponsoredHeatmap,
} from '@/lib/queries'
import EngagementBarChart from '@/components/EngagementBarChart'

function delta(a: number, b: number) {
  const d = b - a
  return { value: Math.abs(d).toFixed(2), positive: d > 0 }
}

export default async function SponsorshipPage() {
  const [comparison, byCategory, disclosure, heatmapSponsored, heatmapOrganic] = await Promise.all([
    getSponsorshipComparison(),
    getSponsorshipByCategory(),
    getDisclosureTypeAnalysis(),
    getSponsoredHeatmap('TRUE'),
    getSponsoredHeatmap('FALSE'),
  ])

  const engagementDelta  = delta(comparison.avgEngagementOrganic, comparison.avgEngagementSponsored)
  const viewsDelta       = delta(comparison.avgViewsOrganic, comparison.avgViewsSponsored)
  const likesDelta       = delta(comparison.avgLikesOrganic, comparison.avgLikesSponsored)
  const sharesDelta      = delta(comparison.avgSharesOrganic, comparison.avgSharesSponsored)

  const sponsoredPlatforms    = [...new Set(heatmapSponsored.map(r => r.platform))].sort()
  const organicPlatforms      = [...new Set(heatmapOrganic.map(r => r.platform))].sort()
  const contentTypesSpon      = [...new Set(heatmapSponsored.map(r => r.contentType))].sort()
  const contentTypesOrg       = [...new Set(heatmapOrganic.map(r => r.contentType))].sort()
  const maxSpon = Math.max(...heatmapSponsored.map(r => r.avgEngagementPct), 1)
  const maxOrg  = Math.max(...heatmapOrganic.map(r => r.avgEngagementPct), 1)

  function DeltaBadge({ value, positive }: { value: string; positive: boolean }) {
    return (
      <span className={`text-xs font-medium ${positive ? 'text-green-600' : 'text-red-600'}`}>
        {positive ? '+' : '-'}{value}%
      </span>
    )
  }

  function MiniHeatmap({
    cells,
    platforms,
    contentTypes,
    max,
    title,
  }: {
    cells: typeof heatmapSponsored
    platforms: string[]
    contentTypes: string[]
    max: number
    title: string
  }) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-4 overflow-x-auto">
        <h3 className="text-xs font-semibold text-gray-600 mb-3">{title}</h3>
        <table className="text-xs w-full">
          <thead>
            <tr>
              <th className="text-left text-gray-400 font-medium py-1 pr-3 w-24">Platform</th>
              {contentTypes.map(ct => (
                <th key={ct} className="text-center text-gray-400 font-medium py-1 px-1 capitalize">{ct}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {platforms.map(platform => (
              <tr key={platform}>
                <td className="text-gray-700 font-medium py-1 pr-3">{platform}</td>
                {contentTypes.map(ct => {
                  const cell = cells.find(r => r.platform === platform && r.contentType === ct)
                  const opacity = cell ? cell.avgEngagementPct / max : 0
                  return (
                    <td
                      key={ct}
                      className="py-1 px-1 text-center"
                      style={{ backgroundColor: `rgba(59,130,246,${opacity.toFixed(2)})` }}
                    >
                      <span className="text-gray-800">{cell ? `${cell.avgEngagementPct}%` : '—'}</span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Patrocínios</h1>
        <p className="text-gray-500 text-sm mt-1">
          {comparison.organicCount.toLocaleString()} orgânicos · {comparison.sponsoredCount.toLocaleString()} patrocinados
        </p>
      </div>

      {/* Organic vs Sponsored cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Orgânico</h2>
          <p className="text-3xl font-bold text-green-600 mb-2">{comparison.avgEngagementOrganic}%</p>
          <div className="space-y-1 text-xs text-gray-500">
            <p>{comparison.organicCount.toLocaleString()} posts</p>
            <p>Avg views: {comparison.avgViewsOrganic.toLocaleString()}</p>
            <p>Avg likes: {comparison.avgLikesOrganic.toLocaleString()}</p>
            <p>Avg shares: {comparison.avgSharesOrganic.toLocaleString()}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Patrocinado</h2>
          <p className="text-3xl font-bold text-purple-600 mb-2">{comparison.avgEngagementSponsored}%</p>
          <div className="space-y-1 text-xs text-gray-500">
            <p>{comparison.sponsoredCount.toLocaleString()} posts</p>
            <p>Avg views: {comparison.avgViewsSponsored.toLocaleString()}</p>
            <p>Avg likes: {comparison.avgLikesSponsored.toLocaleString()}</p>
            <p>Avg shares: {comparison.avgSharesSponsored.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Delta table */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Delta: Patrocinado vs Orgânico</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
              <th className="text-left py-2 pr-4">Métrica</th>
              <th className="text-right py-2 pr-4">Orgânico</th>
              <th className="text-right py-2 pr-4">Patrocinado</th>
              <th className="text-right py-2">Delta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            <tr>
              <td className="py-2 pr-4 text-gray-700">Engajamento</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgEngagementOrganic}%</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgEngagementSponsored}%</td>
              <td className="py-2 text-right"><DeltaBadge {...engagementDelta} /></td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-700">Views médios</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgViewsOrganic.toLocaleString()}</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgViewsSponsored.toLocaleString()}</td>
              <td className="py-2 text-right"><DeltaBadge {...viewsDelta} /></td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-700">Likes médios</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgLikesOrganic.toLocaleString()}</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgLikesSponsored.toLocaleString()}</td>
              <td className="py-2 text-right"><DeltaBadge {...likesDelta} /></td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-700">Shares médios</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgSharesOrganic.toLocaleString()}</td>
              <td className="py-2 pr-4 text-right text-gray-600">{comparison.avgSharesSponsored.toLocaleString()}</td>
              <td className="py-2 text-right"><DeltaBadge {...sharesDelta} /></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Disclosure type */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Tipo de Disclosure (posts patrocinados)</h2>
        <div className="space-y-2">
          {disclosure.map(row => (
            <div key={row.disclosureType} className="flex items-center gap-3 text-sm">
              <span className="w-24 shrink-0 text-gray-600 capitalize">{row.disclosureType}</span>
              <span className="text-gray-800 font-medium">{row.avgEngagementRate}% eng.</span>
              <span className="text-gray-400 text-xs">{row.totalPosts.toLocaleString()} posts</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sponsor category chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Categoria de Patrocinador</h2>
        <EngagementBarChart
          data={byCategory.map(r => ({ name: r.sponsorCategory, value: r.avgEngagementRate }))}
          color="#8b5cf6"
        />
      </div>

      {/* Mini heatmaps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MiniHeatmap
          cells={heatmapSponsored}
          platforms={sponsoredPlatforms}
          contentTypes={contentTypesSpon}
          max={maxSpon}
          title="Patrocinado — Platform × Tipo"
        />
        <MiniHeatmap
          cells={heatmapOrganic}
          platforms={organicPlatforms}
          contentTypes={contentTypesOrg}
          max={maxOrg}
          title="Orgânico — Platform × Tipo"
        />
      </div>
    </div>
  )
}
