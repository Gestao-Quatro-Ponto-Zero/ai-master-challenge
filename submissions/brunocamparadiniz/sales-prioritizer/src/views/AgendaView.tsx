import { Phone, DollarSign, TrendingUp, Clock, Zap } from 'lucide-react'
import type { ScoredDeal } from '../scoring'

type Tier = 'now' | 'today' | 'week'

function getTier(deal: ScoredDeal): Tier {
  if (deal.score >= 75 && !deal.stagnation.isStagnant) return 'now'
  if (deal.score >= 55 || (deal.stagnation.isStagnant && deal.list_price >= 4000)) return 'today'
  return 'week'
}

// Impact = expected revenue contribution = (win probability) × value
function impactScore(deal: ScoredDeal): number {
  return Math.round((deal.scoreBreakdown.winRate / 100) * deal.list_price)
}

const TIER_META: Record<Tier, { label: string; desc: string; border: string; dot: string }> = {
  now: {
    label: '🔴 Ligar Agora',
    desc: 'Score ≥ 75 e sem estagnação — janela de fechamento aberta',
    border: 'border-rose-200',
    dot: 'bg-rose-400',
  },
  today: {
    label: '🟡 Ainda Hoje',
    desc: 'Score ≥ 55 ou deal de alto valor estagnado',
    border: 'border-amber-200',
    dot: 'bg-amber-400',
  },
  week: {
    label: '🟢 Esta Semana',
    desc: 'Demais deals ativos — não urgentes, mas não esquecer',
    border: 'border-slate-200',
    dot: 'bg-slate-300',
  },
}

function AgendaCard({ rank, deal, impact }: { rank: number; deal: ScoredDeal; impact: number }) {
  const meta = TIER_META[getTier(deal)]

  return (
    <div className={`bg-white/70 border ${meta.border} rounded-xl p-4 flex gap-4 items-start`}
      style={{ boxShadow: '0 1px 4px 0 rgb(148 163 184 / 0.08)' }}>
      <div className="text-slate-300 font-mono text-sm w-6 text-right flex-shrink-0 pt-0.5">
        #{rank}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="font-semibold text-slate-800 text-sm">{deal.account}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            deal.deal_stage === 'Engaging'
              ? 'bg-blue-50 text-blue-600 border border-blue-100'
              : 'bg-purple-50 text-purple-600 border border-purple-100'
          }`}>{deal.deal_stage}</span>
          {deal.stagnation.isStagnant && (
            <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-100">
              <Clock size={10} />Estagnado {deal.stagnation.daysEngaging}d
            </span>
          )}
        </div>

        <p className="text-xs text-slate-500 leading-relaxed mb-2">{deal.justification}</p>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
          <span className="flex items-center gap-1"><Phone size={11} />{deal.sales_agent}</span>
          <span className="flex items-center gap-1"><DollarSign size={11} />${deal.list_price.toLocaleString()}</span>
          <span className="flex items-center gap-1"><TrendingUp size={11} />Win Rate {deal.scoreBreakdown.winRate}%</span>
          <span className="text-slate-300">desde {deal.engage_date}</span>
        </div>
      </div>

      <div className="flex-shrink-0 text-right min-w-[70px]">
        <div className="text-xs text-slate-400 mb-0.5">Impacto</div>
        <div className="text-slate-800 font-bold text-sm">${(impact / 1000).toFixed(1)}k</div>
        <div className="text-xs text-slate-400 mt-0.5">Score {deal.score}</div>
      </div>
    </div>
  )
}

export function AgendaView({ deals }: { deals: ScoredDeal[] }) {
  // Pre-rank all deals by impact (win_rate × value), then group by tier
  const ranked = [...deals]
    .map((d) => ({ deal: d, impact: impactScore(d), tier: getTier(d) }))
    .sort((a, b) => b.impact - a.impact)

  const groups: { tier: Tier; items: typeof ranked }[] = [
    { tier: 'now',   items: ranked.filter((r) => r.tier === 'now') },
    { tier: 'today', items: ranked.filter((r) => r.tier === 'today') },
    { tier: 'week',  items: ranked.filter((r) => r.tier === 'week') },
  ]

  const totalImpact = ranked.reduce((s, r) => s + r.impact, 0)
  let globalRank = 0

  return (
    <div className="space-y-8">
      {/* Summary bar */}
      <div className="glass-panel p-4">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <div>
            <p className="text-xs text-slate-400">Agenda de Impacto</p>
            <p className="text-slate-800 font-semibold text-sm mt-0.5">
              Quem ligar agora para maximizar o faturamento
            </p>
          </div>
          <div className="ml-auto flex gap-6 text-center">
            <div>
              <p className="text-slate-400 text-xs">Impacto total</p>
              <p className="text-slate-800 font-bold">${(totalImpact / 1000).toFixed(0)}k</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs">Ligar agora</p>
              <p className="text-rose-500 font-bold">{groups[0].items.length}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs">Ainda hoje</p>
              <p className="text-amber-500 font-bold">{groups[1].items.length}</p>
            </div>
          </div>
        </div>
        <p className="text-slate-400 text-xs mt-2 flex items-center gap-1">
          <Zap size={11} />
          Ordenado por Impacto = Win Rate × Valor do deal. Quanto maior, mais revenue esperado ao fechar.
        </p>
      </div>

      {groups.map(({ tier, items }) => {
        if (items.length === 0) return null
        const meta = TIER_META[tier]
        const tierImpact = items.reduce((s, r) => s + r.impact, 0)

        return (
          <section key={tier}>
            <div className="flex items-center gap-3 mb-3">
              <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${meta.dot}`} />
              <div>
                <h3 className="text-sm font-semibold text-slate-700">{meta.label}</h3>
                <p className="text-xs text-slate-400">{meta.desc} · {items.length} deals · ${(tierImpact / 1000).toFixed(0)}k impacto</p>
              </div>
            </div>
            <div className="space-y-2">
              {items.map(({ deal, impact }) => {
                globalRank++
                return <AgendaCard key={deal.opportunity_id} rank={globalRank} deal={deal} impact={impact} />
              })}
            </div>
          </section>
        )
      })}

      {ranked.length === 0 && (
        <div className="text-center text-slate-400 py-16">Nenhum deal encontrado com esses filtros.</div>
      )}
    </div>
  )
}
