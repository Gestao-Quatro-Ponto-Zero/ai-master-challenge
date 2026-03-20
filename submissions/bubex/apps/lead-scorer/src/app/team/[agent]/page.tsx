import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getPipeline } from '@/lib/queries'
import { PipelineTable } from '@/components/PipelineTable'

export default async function AgentPage({ params }: { params: Promise<{ agent: string }> }) {
  const { agent } = await params
  const agentName = decodeURIComponent(agent)

  const all = await getPipeline()
  const deals = all.filter(d => d.sales_agent === agentName)
  if (!deals.length) notFound()

  const first = deals[0]
  const hot = deals.filter(d => d.score >= 70).length
  const totalValue = deals.reduce((s, d) => s + d.sales_price, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/team" className="text-sm text-gray-400 hover:text-gray-600">← Time</Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{agentName}</h1>
          <p className="text-gray-500 text-sm mt-1">{first.regional_office} · Manager: {first.manager}</p>
        </div>
        <div className="flex gap-4 text-sm">
          <Stat label="Deals abertos" value={deals.length} />
          <Stat label="Pipeline" value={`$${totalValue.toLocaleString()}`} />
          <Stat label="Deals hot" value={hot} highlight={hot > 0} />
          <Stat label="Win rate" value={`${first.win_rate_pct}%`} />
        </div>
      </div>

      <PipelineTable deals={deals} />
    </div>
  )
}

function Stat({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 px-4 py-3 text-center">
      <p className={`text-lg font-bold ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{label}</p>
    </div>
  )
}
