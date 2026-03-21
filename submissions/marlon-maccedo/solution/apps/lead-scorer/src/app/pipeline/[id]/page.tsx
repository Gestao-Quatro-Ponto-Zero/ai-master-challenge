import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getDeal } from '@/lib/queries'
import { generateDealAction } from '@/lib/insights'
import { getOpenRouterApiKey } from '@/lib/env'
import { ScoreBadge } from '@/components/ScoreBadge'
import { ScoreBreakdown } from '@/components/ScoreBreakdown'
import type { Deal } from '@/types'

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

      <Suspense fallback={<ActionCardSkeleton />}>
        <ActionCardAsync deal={deal} />
      </Suspense>
    </div>
  )
}

async function ActionCardAsync({ deal }: { deal: Deal }) {
  const { actions, fromLLM } = await generateDealAction(deal)
  const hasKey = Boolean(getOpenRouterApiKey())
  const showApiFailure = hasKey && !fromLLM
  return <ActionCard actions={actions} fromLLM={fromLLM} showApiFailure={showApiFailure} />
}

function ActionCard({
  actions,
  fromLLM,
  showApiFailure,
}: {
  actions: string[]
  fromLLM: boolean
  showApiFailure: boolean
}) {
  return (
    <div className="space-y-3">
      {showApiFailure && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-900 flex items-start gap-2">
          <span className="text-base shrink-0">⚠️</span>
          <span>
            Não foi possível gerar sugestões via IA (falha na API OpenRouter ou resposta inválida). Exibindo
            próximos passos heurísticos. Confira créditos em{' '}
            <a href="https://openrouter.ai" className="underline font-medium" target="_blank" rel="noreferrer">
              openrouter.ai
            </a>
            .
          </span>
        </div>
      )}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">Próximos passos</p>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          fromLLM
            ? 'bg-violet-100 text-violet-700'
            : 'bg-gray-100 text-gray-500'
        }`}>
          {fromLLM ? 'IA' : 'Baseado nos dados'}
        </span>
      </div>
      <ul className="space-y-2">
        {actions.map((action, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
            <span className="mt-0.5 text-gray-400 shrink-0">→</span>
            <span>{action}</span>
          </li>
        ))}
      </ul>
      </div>
    </div>
  )
}

function ActionCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
      <div className="h-3 bg-gray-200 rounded w-24 mb-3" />
      <div className="space-y-2">
        <div className="h-4 bg-gray-100 rounded w-full" />
        <div className="h-4 bg-gray-100 rounded w-4/5" />
      </div>
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
