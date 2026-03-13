import { useState, useMemo } from 'react'
import {
  Users, Filter, RefreshCw, ChevronDown, ChevronUp,
  Building2, Package, Calendar, DollarSign, Award, BarChart3, Clock,
  CalendarClock, ShieldCheck, List, Columns3, ScatterChart, CalendarDays,
  Sparkles, Star, Flame, Snowflake, CalendarCheck,
} from 'lucide-react'
import { type ScoredDeal } from './scoring'
import { usePipelineData } from './hooks/usePipelineData'
import { KanbanView } from './views/KanbanView'
import { MatrixView } from './views/MatrixView'
import { AgendaView } from './views/AgendaView'

type MomentFilter = '' | 'close-today' | 'reaquecer' | 'high-value'
type QuickFilter  = '' | 'top-priority' | 'cooling' | 'closing-soon'
type View = 'list' | 'kanban' | 'matrix' | 'agenda'

// ─── Score justification ──────────────────────────────────────────────────────
/**
 * Analyzes the four scoring components and returns a concise one-sentence
 * insight about the deal's two most influential factors (positive or negative).
 *
 * Factors are ranked by weighted contribution (value × weight).
 * The top driver and the bottom drag are surfaced in plain pt-BR language.
 */
function getScoreJustification(deal: ScoredDeal): string {
  const { winRate, recency, valueEfficiency, stageWeight } = deal.scoreBreakdown

  const factors = [
    {
      value: winRate, weight: 0.40,
      highText: `win rate histórico forte (${winRate}%)`,
      lowText:  `histórico de fechamento fraco (${winRate}%)`,
    },
    {
      value: recency, weight: 0.25,
      highText: `engajamento recente (${recency}/100)`,
      lowText:  `sem contato recente (${recency}/100)`,
    },
    {
      value: valueEfficiency, weight: 0.20,
      highText: `alto valor por tempo investido`,
      lowText:  `baixo valor por tempo investido`,
    },
    {
      value: stageWeight, weight: 0.15,
      highText: `em negociação ativa`,
      lowText:  `ainda em fase de prospecção`,
    },
  ]
    .map((f) => ({ ...f, contrib: f.value * f.weight }))
    .sort((a, b) => b.contrib - a.contrib)

  const best  = factors[0]
  const worst = factors[factors.length - 1]

  const bestStr  = best.value  >= 50 ? best.highText  : best.lowText
  const worstStr = worst.value <  50 ? worst.lowText  : worst.highText

  const bonuses: string[] = []
  if (deal.accountLoyaltyApplied) bonuses.push('cliente recorrente (+15 pts)')
  if (deal.managerBonusApplied) bonuses.push('manager top (+10 pts)')
  if (deal.isHotSector) bonuses.push('setor quente')
  if (deal.isHighConversionProduct) bonuses.push('produto alta conversão')

  const bonusStr = bonuses.length > 0 ? ` · ${bonuses.join(' · ')}` : ''

  if (best === worst) return `${bestStr}${bonusStr}`
  return `${bestStr} · ${worstStr}${bonusStr}`
}

// ─── Circular score ring ──────────────────────────────────────────────────────
function ScoreRing({ score }: { score: number }) {
  const r = 17
  const circumference = 2 * Math.PI * r
  const progress = (score / 100) * circumference

  const stroke =
    score >= 80 ? '#10b981' :
    score >= 50 ? '#f59e0b' :
                  '#f43f5e'
  const textColor =
    score >= 80 ? 'text-emerald-600' :
    score >= 50 ? 'text-amber-500'   :
                  'text-rose-500'

  return (
    <div className="relative flex-shrink-0 w-12 h-12">
      <svg viewBox="0 0 40 40" className="w-full h-full -rotate-90">
        <circle cx="20" cy="20" r={r} fill="none" stroke="#f1f5f9" strokeWidth="3" />
        <circle
          cx="20" cy="20" r={r} fill="none"
          stroke={stroke} strokeWidth="3"
          strokeDasharray={`${progress} ${circumference}`}
          strokeLinecap="round"
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${textColor}`}>
        {score}
      </div>
    </div>
  )
}

// ─── Score breakdown bar ──────────────────────────────────────────────────────
function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>{label}</span>
        <span className="font-semibold text-slate-600">{value}</span>
      </div>
      <div
        className="h-1 rounded-full overflow-hidden"
        style={{ background: 'rgb(241 245 249 / 0.8)', boxShadow: 'inset 0 1px 2px 0 rgb(148 163 184 / 0.15)' }}
      >
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

// ─── Justification with bolded numbers ───────────────────────────────────────
function JustificationText({ text }: { text: string }) {
  const parts = text.split(/(\d+(?:\.\d+)?%|\$[\d,.]+|\d+\s*dias?)/g)
  return (
    <p className="text-[11px] text-slate-500 leading-relaxed">
      {parts.map((part, i) =>
        /(\d+(?:\.\d+)?%|\$[\d,.]+|\d+\s*dias?)/.test(part)
          ? <strong key={i} className="text-slate-700 font-semibold">{part}</strong>
          : part
      )}
    </p>
  )
}

// ─── Contextual CTA button ────────────────────────────────────────────────────
function CtaButton({ deal }: { deal: ScoredDeal }) {
  const [confirmed, setConfirmed] = useState(false)

  const isFollowUp = deal.scoreBreakdown.recency === 0
  const isManagerApproval = !isFollowUp && deal.score >= 75 && deal.list_price >= 4000

  if (!isFollowUp && !isManagerApproval) return null

  function handleClick() {
    setConfirmed(true)
    setTimeout(() => setConfirmed(false), 2500)
  }

  if (confirmed) {
    return (
      <span className="text-xs text-slate-500 px-3 py-1.5 rounded-xl bg-slate-100 font-medium">
        ✓ Enviado!
      </span>
    )
  }

  if (isFollowUp) {
    return (
      <button
        onClick={handleClick}
        className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-sm"
      >
        <CalendarClock size={13} />
        Agendar Follow-up
      </button>
    )
  }

  return (
    <button
      onClick={handleClick}
      className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-sm"
    >
      <ShieldCheck size={13} />
      Solicitar Aprovação de Manager
    </button>
  )
}

// ─── Daily Focus helpers ───────────────────────────────────────────────────────
/** Generates a concrete, one-sentence action phrase based on a deal's scoring signals. */
function getActionPhrase(deal: ScoredDeal): string {
  if (deal.stagnation.isStagnant && deal.deal_stage === 'Engaging') {
    return `Ligar agora — parado há ${deal.stagnation.daysEngaging}d (P75 = ${deal.stagnation.p75ThresholdDays}d)`
  }
  if (deal.scoreBreakdown.recency === 0) {
    return 'Retomar contato urgente — sem atividade detectada recentemente'
  }
  if (deal.score >= 80 && deal.deal_stage === 'Engaging' && !deal.stagnation.isStagnant) {
    return 'Avançar para proposta formal — deal quente com win rate alto'
  }
  if (deal.score >= 70 && deal.deal_stage === 'Prospecting') {
    return 'Mover para Engaging — score alto indica momento ideal para avançar'
  }
  if (deal.accountLoyaltyApplied && deal.score >= 60) {
    return 'Cliente recorrente com score sólido — preparar proposta personalizada'
  }
  return 'Priorizar esta semana — maior potencial no pipeline atual'
}

/** Returns the single highest-impact action a seller can take to raise this deal's score. */
function getScoreUpgradeTip(deal: ScoredDeal): string {
  if (deal.stagnation.isStagnant) {
    const recovery = Math.round(deal.score * 0.25)
    return `Reativar este deal removeria a penalidade de 20% (≈+${recovery} pts)`
  }
  if (deal.scoreBreakdown.recency < 30) {
    const delta = Math.round((100 - deal.scoreBreakdown.recency) * 0.25)
    return `Um contato hoje elevaria a recência para 100 (≈+${delta} pts)`
  }
  if (deal.deal_stage === 'Prospecting') {
    return 'Avançar para Engaging adicionaria +8 pts de estágio no score'
  }
  if (deal.scoreBreakdown.winRate < 40) {
    return 'Compartilhar cases de sucesso do setor pode elevar o win rate projetado'
  }
  return 'Deal bem posicionado — mantenha a cadência de contato ativa'
}

// ─── Daily Focus card ─────────────────────────────────────────────────────────
/**
 * Surfaces the 3 most urgent deals from the full pipeline (ignores active filters).
 * Urgency = score + bonus for stagnation (+20) + bonus for zero recency (+10).
 */
function DailyFocus({ deals }: { deals: ScoredDeal[] }) {
  if (deals.length === 0) return null

  const top3 = [...deals]
    .sort((a, b) => {
      const urgA = a.score + (a.stagnation.isStagnant ? 20 : 0) + (a.scoreBreakdown.recency < 20 ? 10 : 0)
      const urgB = b.score + (b.stagnation.isStagnant ? 20 : 0) + (b.scoreBreakdown.recency < 20 ? 10 : 0)
      return urgB - urgA
    })
    .slice(0, 3)

  return (
    <div className="glass-card p-4 border border-blue-100/60" style={{ background: 'linear-gradient(135deg, rgb(239 246 255 / 0.6), rgb(255 255 255 / 0.8))' }}>
      <div className="flex items-center gap-2 mb-3.5">
        <Flame size={14} className="text-blue-500" />
        <p className="text-sm font-bold text-slate-700 tracking-tight">Daily Focus</p>
        <p className="text-xs text-slate-400">— 3 deals para agir agora</p>
      </div>
      <div className="space-y-3">
        {top3.map((deal, i) => {
          const action = getActionPhrase(deal)
          const rankColors = [
            'bg-blue-600 text-white',
            'bg-slate-300 text-slate-700',
            'bg-slate-100 text-slate-400',
          ]
          const scoreColor =
            deal.score >= 80 ? 'text-emerald-700 bg-emerald-50 border-emerald-200' :
            deal.score >= 50 ? 'text-amber-700 bg-amber-50 border-amber-200' :
                               'text-rose-700 bg-rose-50 border-rose-200'
          return (
            <div key={deal.opportunity_id} className="flex items-start gap-2.5">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5 ${rankColors[i]}`}>
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-sm font-semibold text-slate-800 truncate">{deal.account}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border flex-shrink-0 ${scoreColor}`}>
                    {deal.score}
                  </span>
                  {deal.stagnation.isStagnant && (
                    <Clock size={11} className="text-amber-400 flex-shrink-0" />
                  )}
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">{action}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Deal card ────────────────────────────────────────────────────────────────
function DealCard({ deal }: { deal: ScoredDeal }) {
  const [expanded, setExpanded] = useState(false)

  const stageChip =
    deal.deal_stage === 'Engaging'
      ? 'text-blue-600 bg-white border border-blue-200'
      : 'text-purple-600 bg-white border border-purple-200'

  const cardBorder = deal.stagnation.isStagnant ? 'border-amber-200/80' : ''
  const insight = getScoreJustification(deal)

  return (
    <div className={`glass-card p-4 transition-all group ${cardBorder}`}>
      {/* Stagnation warning */}
      {deal.stagnation.isStagnant && (
        <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200/60 rounded-xl px-3 py-1.5 mb-3">
          <Clock size={12} className="flex-shrink-0 text-amber-400" />
          <span>
            <strong>Deal estagnado</strong> — <strong>{deal.stagnation.daysEngaging} dias</strong> em Engaging
            (P75 = <strong>{deal.stagnation.p75ThresholdDays} dias</strong>). Score reduzido em 20%.
          </span>
        </div>
      )}

      <div className="flex items-start gap-3">
        <ScoreRing score={deal.score} />

        <div className="flex-1 min-w-0">
          {/* Title row */}
          <div className="flex flex-wrap items-center gap-1.5 mb-1">
            <span className="font-semibold text-slate-800 text-sm">{deal.account}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${stageChip}`}>
              {deal.deal_stage}
            </span>
            <span className="text-xs text-slate-500 bg-white border border-slate-200 px-2 py-0.5 rounded-full">
              {deal.sector}
            </span>
            {deal.managerBonusApplied && (
              <span className="text-xs text-violet-600 bg-violet-50 border border-violet-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Star size={10} />Manager top
              </span>
            )}
            {deal.accountLoyaltyApplied && (
              <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Award size={10} />Cliente recorrente
              </span>
            )}
            {deal.isHotSector && (
              <span className="text-xs text-orange-600 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Flame size={10} />Setor Quente
              </span>
            )}
            {deal.isHighConversionProduct && (
              <span className="text-xs text-teal-600 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles size={10} />Produto Alta Conversão
              </span>
            )}
          </div>

          {/* Score insight — top 2 factors */}
          <p className="text-[11px] text-slate-500 leading-relaxed mb-1.5 italic">{insight}</p>

          {/* Full justification with bolded numbers */}
          <JustificationText text={deal.justification} />

          {/* Meta row */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400 mt-2 mb-3">
            <span className="flex items-center gap-1"><Users size={11} />{deal.sales_agent}</span>
            <span className="flex items-center gap-1"><Package size={11} />{deal.product}</span>
            <span className="flex items-center gap-1"><DollarSign size={11} />${deal.list_price.toLocaleString()}</span>
            <span className="flex items-center gap-1"><Calendar size={11} />desde {deal.engage_date}</span>
          </div>

          <CtaButton deal={deal} />

          {/* Score upgrade tip — visible on hover or when expanded */}
          <div className={`flex items-start gap-1.5 text-[10px] rounded-lg px-2.5 py-1.5 mt-2 border transition-opacity duration-150 ${
            expanded
              ? 'opacity-100 text-indigo-600 bg-indigo-50 border-indigo-100'
              : 'opacity-0 group-hover:opacity-100 text-indigo-500 bg-indigo-50/70 border-indigo-100/70'
          }`}>
            <Sparkles size={10} className="flex-shrink-0 mt-0.5" />
            <span>Dica: {getScoreUpgradeTip(deal)}</span>
          </div>
        </div>

        <button
          onClick={() => setExpanded((e) => !e)}
          className="text-slate-300 hover:text-slate-500 transition-colors flex-shrink-0 mt-0.5"
          aria-label="Expandir detalhes"
        >
          {expanded ? <ChevronUp size={17} /> : <ChevronDown size={17} />}
        </button>
      </div>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-100/80 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-3">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Score Breakdown</p>
            <ScoreBar label="Win Rate histórico" value={deal.scoreBreakdown.winRate} color="bg-blue-400" />
            <ScoreBar label="Recência do engajamento" value={deal.scoreBreakdown.recency} color="bg-emerald-400" />
            <ScoreBar label="Eficiência de valor" value={deal.scoreBreakdown.valueEfficiency} color="bg-amber-400" />
            <ScoreBar label="Estágio do deal" value={deal.scoreBreakdown.stageWeight} color="bg-purple-400" />
            {deal.accountLoyaltyApplied && (
              <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5">
                <Award size={11} />
                Bônus Account Loyalty: cliente com histórico de compra (+15 pts)
              </div>
            )}
            {deal.managerBonusApplied && (
              <div className="flex items-center gap-2 text-xs text-violet-600 bg-violet-50 border border-violet-100 rounded-lg px-2.5 py-1.5">
                <Star size={11} />
                Bônus Suporte Gerencial: manager acima da média (+10 pts)
              </div>
            )}
            {deal.productSeriesWinRate !== null && (
              <div className={`flex items-center gap-2 text-xs rounded-lg px-2.5 py-1.5 border ${deal.isHighConversionProduct ? 'text-teal-700 bg-teal-50 border-teal-100' : 'text-slate-500 bg-slate-50 border-slate-100'}`}>
                <Sparkles size={11} />
                Série {deal.series}: {Math.round(deal.productSeriesWinRate * 100)}% win rate histórico
                {deal.isHighConversionProduct ? ' · Alta Conversão' : ' · Baixa Conversão'}
              </div>
            )}
          </div>
          <div className="text-xs text-slate-400 space-y-2">
            <div className="flex justify-between"><span>Opportunity ID</span><span className="text-slate-700 font-mono text-[11px]">{deal.opportunity_id}</span></div>
            <div className="flex justify-between"><span>Manager</span><span className="text-slate-700">{deal.manager}</span></div>
            <div className="flex justify-between">
              <span>Regional</span>
              <span className="text-slate-700 flex items-center gap-1.5">
                {deal.regional_office}
                {deal.regionalWinRate !== null && (
                  <span className="text-[10px] font-semibold text-blue-500 bg-blue-50 border border-blue-100 px-1.5 py-0.5 rounded">
                    {Math.round(deal.regionalWinRate * 100)}% WR
                  </span>
                )}
              </span>
            </div>
            <div className="flex justify-between"><span>Série do produto</span><span className="text-slate-700">{deal.series}</span></div>
            <div className="flex justify-between"><span>Previsão de fechamento</span><span className="text-slate-700">{deal.close_date || '—'}</span></div>
            <div className="flex justify-between">
              <span>Dias em Engaging</span>
              <span className={deal.stagnation.isStagnant ? 'text-amber-500 font-semibold' : 'text-slate-700'}>
                {deal.stagnation.daysEngaging}d
              </span>
            </div>
            <div className="flex justify-between"><span>Threshold P75</span><span className="text-slate-700">{deal.stagnation.p75ThresholdDays}d</span></div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── KPI stat card ────────────────────────────────────────────────────────────
interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  iconBg: string
  iconColor: string
}

function StatCard({ icon, label, value, iconBg, iconColor }: StatCardProps) {
  return (
    <div className="glass-card p-4 flex items-center gap-3">
      <div className={`w-10 h-10 ${iconBg} rounded-xl flex items-center justify-center flex-shrink-0 ${iconColor}`}>
        {icon}
      </div>
      <div>
        <p className="text-slate-400 text-xs">{label}</p>
        <p className="text-slate-800 font-bold text-lg leading-tight">{value}</p>
      </div>
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const { deals, state } = usePipelineData()
  const [filterAgent, setFilterAgent] = useState('')
  const [filterManager, setFilterManager] = useState('')
  const [filterOffice, setFilterOffice] = useState('')
  const [filterStage, setFilterStage] = useState('')
  const [search, setSearch] = useState('')
  const [momentFilter, setMomentFilter] = useState<MomentFilter>('')
  const [quickFilter, setQuickFilter] = useState<QuickFilter>('')
  const [view, setView] = useState<View>('list')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 20

  const agents = useMemo(() => [...new Set(deals.map((d) => d.sales_agent))].sort(), [deals])
  const managers = useMemo(() => [...new Set(deals.map((d) => d.manager))].sort(), [deals])
  const offices = useMemo(() => [...new Set(deals.map((d) => d.regional_office))].sort(), [deals])

  const TODAY_MS = Date.now()
  const THIRTY_DAYS_MS = 30 * 86_400_000

  const filtered = useMemo(() => {
    return deals.filter((d) => {
      if (filterAgent && d.sales_agent !== filterAgent) return false
      if (filterManager && d.manager !== filterManager) return false
      if (filterOffice && d.regional_office !== filterOffice) return false
      if (filterStage && d.deal_stage !== filterStage) return false
      if (search && !d.account.toLowerCase().includes(search.toLowerCase()) &&
          !d.sales_agent.toLowerCase().includes(search.toLowerCase())) return false

      // Moment filters
      if (momentFilter === 'close-today' && !(d.score >= 75 && d.deal_stage === 'Engaging' && !d.stagnation.isStagnant)) return false
      if (momentFilter === 'reaquecer' && !(d.scoreBreakdown.recency === 0 || d.stagnation.isStagnant)) return false
      if (momentFilter === 'high-value' && d.list_price < 4000) return false

      // Quick filters
      if (quickFilter === 'top-priority' && d.score < 80) return false
      if (quickFilter === 'cooling' && !(d.scoreBreakdown.recency <= 30 || d.stagnation.isStagnant)) return false
      if (quickFilter === 'closing-soon') {
        if (!d.close_date) return false
        const closeMs = new Date(d.close_date).getTime()
        if (closeMs < TODAY_MS || closeMs > TODAY_MS + THIRTY_DAYS_MS) return false
      }

      return true
    })
  }, [deals, filterAgent, filterManager, filterOffice, filterStage, search, momentFilter, quickFilter])

  const paginated = filtered.slice(0, page * PAGE_SIZE)
  const hasMore = paginated.length < filtered.length
  const highPriority = filtered.filter((d) => d.score >= 80).length
  const totalValue = filtered.reduce((s, d) => s + d.list_price, 0)
  const hasActiveFilters = !!(filterAgent || filterManager || filterOffice || filterStage || search || momentFilter || quickFilter)

  function resetFilters() {
    setFilterAgent(''); setFilterManager(''); setFilterOffice('')
    setFilterStage(''); setSearch(''); setMomentFilter(''); setQuickFilter('')
    setPage(1)
  }

  function toggleMoment(key: MomentFilter) {
    setMomentFilter((prev) => prev === key ? '' : key)
    setQuickFilter('')
    setPage(1)
  }

  function toggleQuick(key: QuickFilter) {
    setQuickFilter((prev) => prev === key ? '' : key)
    setMomentFilter('')
    setPage(1)
  }

  const inputCls = "bg-white border border-slate-200/80 rounded-xl px-3 py-2 text-sm text-slate-700 placeholder-slate-300 focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100/80 transition-all"
  const inputStyle = { boxShadow: 'inset 0 1px 3px 0 rgb(148 163 184 / 0.12)' }

  // ── Loading ──
  if (state === 'loading' || state === 'idle') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="glass-card p-8 flex flex-col items-center gap-4">
          <RefreshCw size={30} className="animate-spin text-blue-400" />
          <p className="text-slate-700 font-medium">Carregando dados do pipeline…</p>
          <p className="text-slate-400 text-sm">Primeira vez pode levar alguns segundos</p>
        </div>
      </div>
    )
  }

  // ── Error ──
  if (state === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <p className="text-rose-500 font-medium">Erro ao carregar os dados.</p>
          <p className="text-slate-400 text-sm mt-1">Verifique os arquivos CSV em /data.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* ── Header ── */}
      <header className="sticky top-0 z-10 bg-white/60 backdrop-blur-xl border-b border-slate-200/50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between py-3.5">
            <div className="flex items-center gap-2.5">
              <Sparkles className="text-blue-500" size={20} />
              <div>
                <h1 className="font-bold text-base leading-none text-slate-800 tracking-tight">SalesMaster AI</h1>
                <p className="text-slate-400 text-xs mt-0.5">Priorização inteligente de deals</p>
              </div>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <BarChart3 size={13} className="text-slate-300" />
              {deals.length} deals ativos
            </div>
          </div>

          {/* View tabs */}
          <div className="flex gap-1 -mb-px">
            {(
              [
                { key: 'list',   label: 'Lista',   icon: <List size={13} /> },
                { key: 'kanban', label: 'Kanban',  icon: <Columns3 size={13} /> },
                { key: 'matrix', label: 'Matrix',  icon: <ScatterChart size={13} /> },
                { key: 'agenda', label: 'Agenda',  icon: <CalendarDays size={13} /> },
              ] as { key: View; label: string; icon: React.ReactNode }[]
            ).map(({ key, label, icon }) => (
              <button
                key={key}
                onClick={() => setView(key)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  view === key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                {icon}{label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-5">
        {/* Daily Focus — top 3 urgent deals */}
        <DailyFocus deals={deals} />

        {/* KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard icon={<Building2 size={17} />} label="Deals filtrados" value={filtered.length}
            iconBg="bg-blue-50" iconColor="text-blue-500" />
          <StatCard icon={<Award size={17} />} label="Alta prioridade (≥80)" value={highPriority}
            iconBg="bg-emerald-50" iconColor="text-emerald-500" />
          <StatCard icon={<DollarSign size={17} />} label="Valor total" value={`$${(totalValue / 1000).toFixed(0)}k`}
            iconBg="bg-amber-50" iconColor="text-amber-500" />
          <StatCard icon={<Users size={17} />} label="Vendedores" value={agents.length}
            iconBg="bg-violet-50" iconColor="text-violet-500" />
        </div>

        {/* Quick filters */}
        <div>
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Filtro Rápido</p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                {
                  key: 'top-priority' as QuickFilter,
                  label: 'Prioridade Máxima',
                  icon: <Flame size={13} />,
                  desc: 'Score ≥ 80 — deals com maior probabilidade de fechamento',
                  active: 'bg-emerald-600 border-emerald-500 text-white shadow-md shadow-emerald-100',
                },
                {
                  key: 'cooling' as QuickFilter,
                  label: 'Esfriando',
                  icon: <Snowflake size={13} />,
                  desc: 'Recência ≤ 30 ou deal estagnado — requer reativação',
                  active: 'bg-blue-500 border-blue-400 text-white shadow-md shadow-blue-100',
                },
                {
                  key: 'closing-soon' as QuickFilter,
                  label: 'Fechamento Próximo',
                  icon: <CalendarCheck size={13} />,
                  desc: 'Data de fechamento prevista nos próximos 30 dias',
                  active: 'bg-amber-500 border-amber-400 text-white shadow-md shadow-amber-100',
                },
              ]
            ).map(({ key, label, icon, desc, active }) => (
              <button
                key={key}
                onClick={() => toggleQuick(key)}
                title={desc}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                  quickFilter === key
                    ? active
                    : 'glass-card text-slate-600 hover:text-slate-800 hover:shadow-md'
                }`}
              >
                {icon}{label}
              </button>
            ))}
          </div>
        </div>

        {/* Momento buttons */}
        <div>
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Filtro de Momento</p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                { key: 'close-today', label: '🔥 Fechar Hoje', desc: 'Score ≥75, Engaging, sem estagnação' },
                { key: 'reaquecer',   label: '❄️ Reaquecer',   desc: 'Recência zero ou deal estagnado' },
                { key: 'high-value',  label: '🚀 High Value',   desc: 'Produto com preço ≥ $4.000' },
              ] as { key: MomentFilter; label: string; desc: string }[]
            ).map(({ key, label, desc }) => (
              <button
                key={key}
                onClick={() => toggleMoment(key)}
                title={desc}
                className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                  momentFilter === key
                    ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-100'
                    : 'glass-card text-slate-600 hover:text-slate-800 hover:shadow-md'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="glass-panel p-4 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
            <Filter size={14} className="text-slate-400" />
            Filtros
            {hasActiveFilters && (
              <button onClick={resetFilters} className="ml-auto text-xs text-blue-500 hover:text-blue-400 font-medium transition-colors">
                Limpar filtros
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
            <input
              type="text"
              placeholder="Buscar conta ou vendedor…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              className={`${inputCls} lg:col-span-2`}
              style={inputStyle}
            />
            {[
              { value: filterOffice,  onChange: (v: string) => { setFilterOffice(v);  setFilterAgent(''); setPage(1) }, opts: offices,   placeholder: 'Todas as regiões' },
              { value: filterManager, onChange: (v: string) => { setFilterManager(v); setFilterAgent(''); setPage(1) }, opts: managers,  placeholder: 'Todos os managers' },
              { value: filterAgent,   onChange: (v: string) => { setFilterAgent(v);                       setPage(1) }, opts: agents,    placeholder: 'Todos os vendedores' },
            ].map(({ value, onChange, opts, placeholder }) => (
              <select
                key={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className={inputCls}
                style={inputStyle}
              >
                <option value="">{placeholder}</option>
                {opts.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ))}
            <select
              value={filterStage}
              onChange={(e) => { setFilterStage(e.target.value); setPage(1) }}
              className={inputCls}
              style={inputStyle}
            >
              <option value="">Todos os estágios</option>
              <option value="Engaging">Engaging</option>
              <option value="Prospecting">Prospecting</option>
            </select>
          </div>
        </div>

        {/* View content */}
        {view === 'list' && (
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="text-center text-slate-400 py-16 text-sm">Nenhum deal encontrado com esses filtros.</div>
            ) : (
              <>
                {paginated.map((deal) => <DealCard key={deal.opportunity_id} deal={deal} />)}
                {hasMore && (
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    className="w-full py-3 glass-card text-slate-400 hover:text-slate-700 transition-all text-sm font-medium"
                  >
                    Carregar mais ({filtered.length - paginated.length} restantes)
                  </button>
                )}
              </>
            )}
          </div>
        )}

        {view === 'kanban' && (
          <KanbanView
            activeDeals={filtered}
            agentFilter={filterAgent}
            managerFilter={filterManager}
            officeFilter={filterOffice}
          />
        )}

        {view === 'matrix' && <MatrixView deals={filtered} />}
        {view === 'agenda' && <AgendaView deals={filtered} />}
      </main>
    </div>
  )
}
