import {
  getAudienceByPlatform,
  getGenderByPlatform,
  getEngagementByAgeGroup,
} from '@/lib/queries'

const AGE_COLORS: Record<string, string> = {
  '18-24':  '#3b82f6',
  '19-25':  '#3b82f6',
  '25-34':  '#8b5cf6',
  '35-44':  '#10b981',
  '45-54':  '#f59e0b',
  '50+':    '#ef4444',
  '55+':    '#ef4444',
  'other':  '#9ca3af',
}

const GENDER_COLORS: Record<string, string> = {
  male:   '#3b82f6',
  female: '#ec4899',
  other:  '#9ca3af',
}

function StackedBar({
  groups,
  colorMap,
}: {
  groups: { label: string; pct: number }[]
  colorMap: Record<string, string>
}) {
  return (
    <div className="flex h-5 rounded-full overflow-hidden w-full">
      {groups.map(g => (
        <div
          key={g.label}
          title={`${g.label}: ${g.pct}%`}
          style={{
            width: `${g.pct}%`,
            backgroundColor: colorMap[g.label.toLowerCase()] ?? colorMap['other'] ?? '#9ca3af',
          }}
        />
      ))}
    </div>
  )
}

export default async function AudiencePage() {
  const [audienceAge, audienceGender, ageEngagement] = await Promise.all([
    getAudienceByPlatform(),
    getGenderByPlatform(),
    getEngagementByAgeGroup(),
  ])

  // Build platform → age groups map
  const platforms = [...new Set(audienceAge.map(r => r.platform))].sort()
  const ageByPlatform = platforms.map(platform => {
    const rows = audienceAge.filter(r => r.platform === platform)
    const total = rows.reduce((s, r) => s + r.totalPosts, 0)
    const groups = rows.map(r => ({
      label: r.ageGroup,
      pct: Math.round((r.totalPosts / total) * 100),
    }))
    return { platform, groups }
  })

  // Build platform → gender map
  const genderPlatforms = [...new Set(audienceGender.map(r => r.platform))].sort()
  const genderByPlatform = genderPlatforms.map(platform => {
    const rows = audienceGender.filter(r => r.platform === platform)
    const total = rows.reduce((s, r) => s + r.totalPosts, 0)
    const groups = rows.map(r => ({
      label: r.gender,
      pct: Math.round((r.totalPosts / total) * 100),
    }))
    return { platform, groups }
  })

  // Legend for age colors
  const ageLabels = [...new Set(audienceAge.map(r => r.ageGroup))]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audiência</h1>
        <p className="text-gray-500 text-sm mt-1">Distribuição etária e de gênero por plataforma</p>
      </div>

      {/* Age distribution */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Distribuição Etária por Plataforma</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          {ageLabels.map(label => (
            <span key={label} className="flex items-center gap-1 text-xs text-gray-600">
              <span
                className="inline-block w-3 h-3 rounded-sm"
                style={{ backgroundColor: AGE_COLORS[label] ?? AGE_COLORS['other'] }}
              />
              {label}
            </span>
          ))}
        </div>
        <div className="space-y-3">
          {ageByPlatform.map(({ platform, groups }) => (
            <div key={platform} className="flex items-center gap-3">
              <span className="text-xs text-gray-600 w-24 shrink-0">{platform}</span>
              <div className="flex-1">
                <StackedBar groups={groups} colorMap={AGE_COLORS} />
              </div>
              <div className="flex gap-1 text-xs text-gray-400 w-48 shrink-0">
                {groups.slice(0, 3).map(g => (
                  <span key={g.label}>{g.label}: {g.pct}%</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gender distribution */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Distribuição de Gênero por Plataforma</h2>
        <div className="flex gap-4 mb-4">
          {Object.entries(GENDER_COLORS).map(([label, color]) => (
            <span key={label} className="flex items-center gap-1 text-xs text-gray-600">
              <span className="inline-block w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
              {label}
            </span>
          ))}
        </div>
        <div className="space-y-3">
          {genderByPlatform.map(({ platform, groups }) => (
            <div key={platform} className="flex items-center gap-3">
              <span className="text-xs text-gray-600 w-24 shrink-0">{platform}</span>
              <div className="flex-1">
                <StackedBar groups={groups} colorMap={GENDER_COLORS} />
              </div>
              <div className="flex gap-2 text-xs text-gray-400 w-48 shrink-0">
                {groups.map(g => (
                  <span key={g.label} className="capitalize">{g.label}: {g.pct}%</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Age × Engagement */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Engajamento por Faixa Etária</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
              <th className="text-left py-2 pr-4">Faixa Etária</th>
              <th className="text-right py-2 pr-4">Engajamento Médio</th>
              <th className="text-right py-2">Total Posts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {ageEngagement.map(row => (
              <tr key={row.ageGroup}>
                <td className="py-2 pr-4 text-gray-700">{row.ageGroup}</td>
                <td className="py-2 pr-4 text-right font-semibold text-blue-600">{row.avgEngagementRate}%</td>
                <td className="py-2 text-right text-gray-500">{row.totalPosts.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
