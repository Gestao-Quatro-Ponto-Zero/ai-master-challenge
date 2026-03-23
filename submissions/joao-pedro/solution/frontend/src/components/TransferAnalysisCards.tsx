import { useMemo, useState } from 'react'
import { ArrowLeftRight, AlertTriangle, GitBranch, BarChart2, TrendingUp, Zap, Flame } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useTransferAnalysis } from '@/hooks/useTransferAnalysis'
import { useSellers } from '@/hooks/useSellers'
import { cn } from '@/lib/utils'
import type { TransferDeal } from '@/types'

type Scope = 'squad' | 'geral'

type Props = {
  managerName?: string
}

// =============================================================================
// VISUAL CONSTANTS (alinhados ao Pipeline Analysis)
// =============================================================================

const chartCardClass =
  'col-span-2 w-full min-w-0 max-w-full rounded-2xl border border-neutral-100 ' +
  'shadow-[0_2px_12px_rgba(0,0,0,0.04)] h-80 sm:h-96 shrink-0 ' +
  'bg-white flex flex-col overflow-hidden p-4 sm:p-5 min-h-0'

const GOLD = '#bd9762'
const DARK = '#0f172a'

// =============================================================================
// STAT CARD
// =============================================================================

type StatCardProps = {
  icon: React.ReactNode
  value: string | number
  label: string
  subtitle: string
  accent?: boolean
}

function StatCard({ icon, value, label, subtitle, accent }: StatCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-neutral-100/90 bg-white/95 p-4 shadow-[0_1px_8px_rgba(0,0,0,0.03)] min-h-[118px]">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-100">
        <span className={accent ? 'text-amber-500' : 'text-[#bd9762]'}>{icon}</span>
      </div>
      <p className="text-xl font-bold tabular-nums tracking-tight leading-none text-neutral-900">
        {value}
      </p>
      <div className="mt-auto space-y-0.5">
        <p className="text-[11px] font-semibold uppercase tracking-wide leading-snug text-neutral-900">
          {label}
        </p>
        <p className="text-[10px] leading-snug text-neutral-500">{subtitle}</p>
      </div>
    </div>
  )
}

// =============================================================================
// CHART 1: Razões para transferência
// =============================================================================

const REASON_CATEGORIES: { key: string; label: string; match: (s: string) => boolean }[] = [
  { key: 'load',     label: 'Carga de trabalho',      match: (s) => s.includes('Carga') },
  { key: 'product',  label: 'WR no produto',           match: (s) => s.includes('win rate em') },
  { key: 'sector',   label: 'WR no setor',             match: (s) => s.includes('setor') },
  { key: 'cycle',    label: 'Ciclo mais rápido',       match: (s) => s.includes('Ciclo') },
  { key: 'pipeline', label: 'Pipeline ativo',          match: (s) => s.includes('Pipeline') },
  { key: 'capacity', label: 'Maior capacidade',        match: (s) => s.includes('dedicar') || s.includes('focada') },
  { key: 'free',     label: 'Libera foco',             match: (s) => s.includes('Libera') },
]

type ReasonDatum = { label: string; count: number; pct: number }

function categorizeReasons(deals: TransferDeal[]): ReasonDatum[] {
  const counters: Record<string, number> = {}
  let total = 0

  for (const deal of deals) {
    const whyList = (deal.details?.why_this_helps as string[] | undefined) ?? []
    for (const reason of whyList) {
      const cat = REASON_CATEGORIES.find((c) => c.match(reason))
      if (cat) {
        counters[cat.key] = (counters[cat.key] ?? 0) + 1
        total += 1
      }
    }
  }

  return REASON_CATEGORIES
    .map((c) => ({
      label: c.label,
      count: counters[c.key] ?? 0,
      pct: total > 0 ? Math.round(((counters[c.key] ?? 0) / total) * 100) : 0,
    }))
    .filter((r) => r.count > 0)
    .sort((a, b) => b.count - a.count)
}

function ReasonLabel(props: {
  x?: number | string
  y?: number | string
  width?: number | string
  height?: number | string
  value?: number
  index?: number
  data?: ReasonDatum[]
}) {
  const x = Number(props.x ?? 0)
  const y = Number(props.y ?? 0)
  const width = Number(props.width ?? 0)
  const height = Number(props.height ?? 0)
  const { index = 0, data = [] } = props
  const row = data[index]
  if (!row) return null
  return (
    <text x={x + width + 6} y={y + height / 2} dy="0.35em"
      fill="#525252" fontSize={11} fontWeight={600} className="tabular-nums">
      {row.pct}% · {row.count}
    </text>
  )
}

function ReasonsChart({ data }: { data: ReasonDatum[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center text-sm text-neutral-400">
        Nenhum dado de razões neste recorte
      </div>
    )
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        layout="vertical"
        data={data}
        margin={{ top: 4, right: 80, left: 4, bottom: 4 }}
        barCategoryGap="22%"
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={138}
          tick={{ fontSize: 10, fill: '#404040' }}
          tickLine={false}
          axisLine={{ stroke: '#d4d4d4' }}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245,245,245,0.6)' }}
          contentStyle={{ borderRadius: '10px', border: '1px solid #e5e5e5', fontSize: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          formatter={(value, _name, item) => {
            const p = item?.payload as ReasonDatum | undefined
            return [`${p?.count ?? value} ocorrências (${p?.pct ?? 0}% das razões)`, 'Frequência']
          }}
          labelFormatter={(label) => `Razão: ${label}`}
        />
        <Bar dataKey="count" name="count" fill={GOLD} radius={[0, 4, 4, 0]} maxBarSize={18}>
          <LabelList
            dataKey="count"
            content={(props) => (
              <ReasonLabel
                data={data}
                index={props.index}
                x={props.x as number | string | undefined}
                y={props.y as number | string | undefined}
                width={props.width as number | string | undefined}
                height={props.height as number | string | undefined}
              />
            )}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// =============================================================================
// CHART 2: Distribuição do impacto (ganho de viabilidade por deal)
// =============================================================================

const IMPACT_BUCKETS = [
  { key: '0–15',  label: '0–15 pts',  min: 0,   max: 15 },
  { key: '16–30', label: '16–30 pts', min: 16,  max: 30 },
  { key: '31–45', label: '31–45 pts', min: 31,  max: 45 },
  { key: '46+',   label: '46+ pts',   min: 46,  max: Infinity },
]

type ImpactDatum = { label: string; count: number }

function buildImpactData(deals: TransferDeal[]): ImpactDatum[] {
  const counters: Record<string, number> = Object.fromEntries(IMPACT_BUCKETS.map((b) => [b.key, 0]))

  for (const deal of deals) {
    const yourViab = (deal.details?.your_context as { viability?: number } | undefined)?.viability ?? 0
    const targetViab = (deal.details?.target_context as { viability?: number } | undefined)?.viability ?? 0
    const gain = Math.max(0, targetViab - yourViab)
    const bucket = IMPACT_BUCKETS.find((b) => gain >= b.min && gain <= b.max)
    if (bucket) counters[bucket.key] += 1
  }

  return IMPACT_BUCKETS.map((b) => ({ label: b.label, count: counters[b.key] }))
}

const IMPACT_COLORS = ['#e5e7eb', '#cbd5e1', GOLD, DARK]

function ImpactChart({ data }: { data: ImpactDatum[] }) {
  const total = data.reduce((s, d) => s + d.count, 0)
  if (total === 0) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center text-sm text-neutral-400">
        Nenhum dado de impacto neste recorte
      </div>
    )
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        barCategoryGap="28%"
        margin={{ top: 4, right: 8, left: 4, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
          width={32}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245,245,245,0.6)' }}
          contentStyle={{ borderRadius: '10px', border: '1px solid #e5e5e5', fontSize: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          formatter={(value) => [
            `${value} deal(s) · ${total > 0 ? Math.round((Number(value) / total) * 100) : 0}% do total`,
            'Deals',
          ]}
          labelFormatter={(label) => `Ganho de viabilidade: ${label}`}
        />
        <Bar dataKey="count" name="Deals" radius={[4, 4, 0, 0]} maxBarSize={60}>
          {data.map((_, i) => (
            <Cell key={i} fill={IMPACT_COLORS[i % IMPACT_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TransferAnalysisCards({ managerName }: Props) {
  const [scope, setScope] = useState<Scope>('squad')

  const { data: transfers, isLoading: loadingTransfers } = useTransferAnalysis()
  const { data: sellers = [], isLoading: loadingSellers } = useSellers()

  const activeScope: Scope = scope === 'squad' && managerName ? 'squad' : 'geral'

  const scopedDeals = useMemo(() => {
    if (!transfers || !sellers.length) return []
    const squadAgents = new Set(
      activeScope === 'squad'
        ? sellers.filter((s) => s.manager === managerName).map((s) => s.sales_agent)
        : sellers.map((s) => s.sales_agent)
    )
    return transfers.deals.filter((d) => squadAgents.has(d.sales_agent))
  }, [transfers, sellers, managerName, activeScope])

  const stats = useMemo(() => {
    if (!transfers) return null
    const critical = scopedDeals.filter((d) => d.action === 'TRANSFER')
    const consider = scopedDeals.filter((d) => d.action === 'CONSIDER_TRANSFER')
    const avgScore =
      scopedDeals.length > 0
        ? Math.round(scopedDeals.reduce((sum, d) => sum + d.score, 0) / scopedDeals.length)
        : 0
    return { total: scopedDeals.length, critical: critical.length, consider: consider.length, avgScore }
  }, [scopedDeals, transfers])

  const reasonsData = useMemo(() => categorizeReasons(scopedDeals), [scopedDeals])
  const impactData = useMemo(() => buildImpactData(scopedDeals), [scopedDeals])

  const impactSummary = useMemo(() => {
    if (!scopedDeals.length) return null
    let sumYour = 0, sumTarget = 0, highImpact = 0
    for (const deal of scopedDeals) {
      const your = (deal.details?.your_context as { viability?: number } | undefined)?.viability ?? 0
      const target = (deal.details?.target_context as { viability?: number } | undefined)?.viability ?? 0
      sumYour += your
      sumTarget += target
      if (target - your >= 20) highImpact += 1
    }
    const n = scopedDeals.length
    const avgYour = Math.round((sumYour / n) * 10) / 10
    const avgTarget = Math.round((sumTarget / n) * 10) / 10
    const avgDelta = Math.round((avgTarget - avgYour) * 10) / 10
    return { avgDelta, avgYour, avgTarget, highImpact }
  }, [scopedDeals])

  const isLoading = loadingTransfers || loadingSellers

  return (
    <div className="flex min-h-0 w-full min-w-0 max-w-full flex-col gap-6 p-6 sm:p-8">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Transfer Analysis</h2>
        <p className="text-sm text-neutral-500 mt-0.5">
          {activeScope === 'squad' && managerName
            ? `Deals com transferência recomendada no squad de ${managerName}`
            : 'Deals com transferência recomendada em toda a base'}
        </p>
      </div>

      {/* Scope toggle */}
      <div
        className="inline-flex w-fit shrink-0 self-start rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
        role="group"
        aria-label="Escopo de transferências"
      >
        <button
          type="button"
          disabled={!managerName}
          title={!managerName ? 'Selecione um manager no painel à esquerda' : undefined}
          onClick={() => setScope('squad')}
          className={cn(
            'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            scope === 'squad'
              ? 'bg-white text-neutral-900 shadow-sm'
              : 'text-neutral-500 hover:text-neutral-800',
            !managerName && 'cursor-not-allowed opacity-45 hover:text-neutral-500',
          )}
        >
          Squad
        </button>
        <button
          type="button"
          onClick={() => setScope('geral')}
          className={cn(
            'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            scope === 'geral'
              ? 'bg-white text-neutral-900 shadow-sm'
              : 'text-neutral-500 hover:text-neutral-800',
          )}
        >
          Geral
        </button>
      </div>

      {/* Stat cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[118px] animate-pulse rounded-xl bg-neutral-100" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard
            icon={<ArrowLeftRight className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={stats.total}
            label="Total de transfers"
            subtitle="TRANSFER + CONSIDER no escopo"
          />
          <StatCard
            icon={<AlertTriangle className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={stats.critical}
            label="Transfer crítico"
            subtitle="Score alto, ação imediata"
            accent
          />
          <StatCard
            icon={<GitBranch className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={stats.consider}
            label="Consider transfer"
            subtitle="Score médio, avaliação ativa"
          />
          <StatCard
            icon={<BarChart2 className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={stats.avgScore}
            label="Score médio"
            subtitle="Média dos deals de transferência"
          />
        </div>
      ) : null}

      {/* Charts */}
      <div className="grid min-w-0 max-w-full grid-cols-2 gap-x-4 gap-y-4 lg:grid-cols-4 lg:gap-x-5 lg:gap-y-4">

        {/* Chart 1: Razões para transferência */}
        <div className={chartCardClass}>
          <div className="shrink-0 space-y-0.5 pr-1">
            <h3 className="text-[15px] font-semibold leading-tight tracking-tight text-neutral-900">
              Razões para transferência
            </h3>
            <p className="text-xs text-neutral-500 leading-snug">
              Frequência dos motivos identificados nos deals do escopo
            </p>
            {!isLoading && (
              <p className="mt-1 text-[11px] tabular-nums text-neutral-400">
                {reasonsData.reduce((s, r) => s + r.count, 0)} razões · {scopedDeals.length} deals
              </p>
            )}
          </div>
          <div className="mt-3 min-h-0 flex-1 w-full h-[220px] sm:h-[240px]">
            {isLoading ? (
              <div className="h-full w-full animate-pulse rounded-xl bg-neutral-100" />
            ) : (
              <ReasonsChart data={reasonsData} />
            )}
          </div>
        </div>

        {/* Chart 2: Distribuição do impacto */}
        <div className={chartCardClass}>
          <div className="shrink-0 space-y-0.5 pr-1">
            <h3 className="text-[15px] font-semibold leading-tight tracking-tight text-neutral-900">
              Distribuição do impacto
            </h3>
            <p className="text-xs text-neutral-500 leading-snug">
              Ganho de viabilidade esperado por deal ao transferir (target − atual)
            </p>
            {!isLoading && (
              <p className="mt-1 text-[11px] tabular-nums text-neutral-400">
                {scopedDeals.length} deals · viabilidade 0–100
              </p>
            )}
          </div>
          <div className="mt-3 min-h-0 flex-1 w-full h-[220px] sm:h-[240px]">
            {isLoading ? (
              <div className="h-full w-full animate-pulse rounded-xl bg-neutral-100" />
            ) : (
              <ImpactChart data={impactData} />
            )}
          </div>
        </div>

      </div>

      {/* Impact summary mini-cards */}
      {!isLoading && impactSummary && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatCard
            icon={<TrendingUp className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={`${impactSummary.avgDelta > 0 ? '+' : ''}${impactSummary.avgDelta.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`}
            label="Δ Viabilidade Média"
            subtitle="Ganho médio ao transferir"
          />
          <StatCard
            icon={<Zap className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={`${impactSummary.avgYour.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} → ${impactSummary.avgTarget.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`}
            label="Viabilidade Média"
            subtitle="Atual → target esperado"
          />
          <StatCard
            icon={<Flame className="h-[14px] w-[14px] stroke-[1.65]" />}
            value={impactSummary.highImpact}
            label="Alto Impacto"
            subtitle="Deals com ganho ≥ 20 pts"
            accent
          />
        </div>
      )}

    </div>
  )
}
