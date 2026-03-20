import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getDeal } from '@/lib/queries'
import { ScoreBadge } from '@/components/ScoreBadge'
import { ScoreBreakdown } from '@/components/ScoreBreakdown'

export default async function DealPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const deal = await getDeal(id)
  if (!deal) notFound()

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link href="/pipeline" className="text-sm text-gray-400 hover:text-gray-600">← Pipeline</Link>
        <span className="font-mono text-sm text-gray-400">{deal.opportunity_id}</span>
        <ScoreBadge score={deal.score} />
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{deal.account}</h1>
        <p className="text-gray-500 text-sm">{deal.product} · {deal.deal_stage}</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <InfoCard label="Agente" value={deal.sales_agent} sub={`${deal.regional_office} · ${deal.manager}`} />
        <InfoCard label="Valor esperado" value={`$${deal.sales_price.toLocaleString()}`} sub={`Série ${deal.series}`} />
        <InfoCard label="Conta" value={deal.account} sub={`${deal.sector} · $${deal.revenue.toLocaleString()}M rev.`} />
        <InfoCard label="Dias no pipeline" value={String(deal.days_in_pipeline)} sub={`Desde ${deal.engage_date}`} />
      </div>

      <ScoreBreakdown deal={deal} />
    </div>
  )
}

function InfoCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="font-semibold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
    </div>
  )
}
