import Link from 'next/link'
import { getTeamStats } from '@/lib/queries'

export default async function TeamPage() {
  const stats = await getTeamStats()

  const byManager = stats.reduce<Record<string, typeof stats>>((acc, s) => {
    ;(acc[s.manager] ??= []).push(s)
    return acc
  }, {})

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Time</h1>
        <p className="text-gray-500 text-sm mt-1">Visão gerencial — pipeline por agente</p>
      </div>

      {Object.entries(byManager).map(([manager, agents]) => (
        <div key={manager}>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            {manager} · {agents[0].regional_office}
          </h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Agente', 'Deals', 'Pipeline ($)', 'Score médio', '🔥 Hot', '☀️ Warm', '❄️ Cold', 'Win rate'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {agents.map(a => (
                  <tr key={a.sales_agent} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link href={`/team/${encodeURIComponent(a.sales_agent)}`} className="text-blue-600 hover:underline font-medium">
                        {a.sales_agent}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{a.open_deals}</td>
                    <td className="px-4 py-3 text-gray-600">${a.pipeline_value.toLocaleString()}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{a.avg_score}</td>
                    <td className="px-4 py-3 text-red-600">{a.hot_deals}</td>
                    <td className="px-4 py-3 text-yellow-600">{a.warm_deals}</td>
                    <td className="px-4 py-3 text-blue-500">{a.cold_deals}</td>
                    <td className="px-4 py-3 text-gray-600">{a.win_rate_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}
