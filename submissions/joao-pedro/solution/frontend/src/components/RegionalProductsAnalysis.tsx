import { useState } from 'react'
import { AlertTriangle, CheckCircle, Map, Package } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { cn } from '@/lib/utils'
import { useRegionalAnalysis } from '@/hooks/useRegionalAnalysis'
import { useProductsAnalysis } from '@/hooks/useProductsAnalysis'
import type { RegionSummary, ProductSummary } from '@/types'

const cardClass =
  'rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)]'

/** Preenche a célula do grid; `flex-1` + `min-h-0` repassam altura ao Recharts. */
const chartShellLayoutClass =
  'w-full min-w-0 max-w-full rounded-2xl border border-neutral-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] ' +
  'flex min-h-0 flex-1 flex-col'

const chartCardClass =
  `${chartShellLayoutClass} bg-white overflow-hidden p-4 sm:p-5`

const METRIC_TEXT_CLASS = 'text-neutral-900'

type InsightCardProps = {
  variant: 'best' | 'worst'
  region: string
  win_rate: number
  avg_score: number
  avg_viability: number
  sellers_count: number
}

function RegionalInsightCard({
  variant,
  region,
  win_rate,
  avg_score,
  avg_viability,
  sellers_count,
}: InsightCardProps) {
  const isBest = variant === 'best'

  const metrics = [
    {
      label: 'Win Rate',
      value: `${win_rate.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`,
    },
    {
      label: 'Score Médio',
      value: avg_score.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
    },
    {
      label: 'Viab. Média',
      value: avg_viability.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
    },
    {
      label: 'Vendedores',
      value: sellers_count.toLocaleString('pt-BR'),
    },
  ]

  return (
    <div className={`${cardClass} flex flex-col p-5 sm:p-6 min-h-[188px]`}>
      <div className="flex items-start justify-between gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-100"
          aria-hidden
        >
          {isBest ? (
            <CheckCircle className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
          ) : (
            <AlertTriangle className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
          )}
        </div>
        <span className="pt-0.5 text-[10px] font-semibold uppercase tracking-wide rounded-md px-1.5 py-0.5 bg-neutral-100 text-[#bd9762]">
          {isBest ? 'Melhor Performance' : 'Precisa Atenção'}
        </span>
      </div>

      <p className={`mt-5 text-2xl font-bold tracking-tight leading-none ${METRIC_TEXT_CLASS}`}>
        {region}
      </p>

      <div className="mt-auto pt-4 space-y-1.5">
        {metrics.map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between gap-2">
            <span className="text-[11px] text-neutral-500 leading-snug">{label}</span>
            <span className={`text-[11px] font-semibold tabular-nums leading-snug ${METRIC_TEXT_CLASS}`}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}


type ProductInsightCardProps = {
  variant: 'best' | 'worst'
  product: string
  win_rate: number
  avg_ticket: number
  deals_engaging: number
}

function ProductInsightCard({ variant, product, win_rate, avg_ticket, deals_engaging }: ProductInsightCardProps) {
  const isBest = variant === 'best'

  const metrics = [
    {
      label: 'Win Rate',
      value: `${win_rate.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`,
    },
    {
      label: 'Ticket Médio',
      value: avg_ticket.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }),
    },
    {
      label: 'Deals Engaging',
      value: deals_engaging.toLocaleString('pt-BR'),
    },
  ]

  return (
    <div className={`${cardClass} flex flex-col p-5 sm:p-6 min-h-[188px]`}>
      <div className="flex items-start justify-between gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-100"
          aria-hidden
        >
          {isBest ? (
            <CheckCircle className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
          ) : (
            <AlertTriangle className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
          )}
        </div>
        <span className="pt-0.5 text-[10px] font-semibold uppercase tracking-wide rounded-md px-1.5 py-0.5 bg-neutral-100 text-[#bd9762]">
          {isBest ? 'Melhor Win Rate' : 'Menor Win Rate'}
        </span>
      </div>

      <p className={`mt-5 text-2xl font-bold tracking-tight leading-none ${METRIC_TEXT_CLASS}`}>
        {product}
      </p>

      <div className="mt-auto pt-4 space-y-1.5">
        {metrics.map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between gap-2">
            <span className="text-[11px] text-neutral-500 leading-snug">{label}</span>
            <span className={`text-[11px] font-semibold tabular-nums leading-snug ${METRIC_TEXT_CLASS}`}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function WinRateByRegionChart({
  regions,
  globalWr,
}: {
  regions: RegionSummary[]
  globalWr: number
}) {
  const data = regions.map((r) => ({
    region: r.region,
    win_rate: parseFloat(r.win_rate.toFixed(1)),
  }))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        barCategoryGap="28%"
        margin={{ top: 4, right: 8, left: -12, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis
          dataKey="region"
          tick={{ fontSize: 10, fill: '#737373' }}
          tickLine={false}
          axisLine={{ stroke: '#d4d4d4' }}
          interval={0}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#737373' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}%`}
          width={36}
          domain={[0, (dataMax: number) => Math.ceil(Math.max(dataMax, globalWr) * 1.15)]}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245,245,245,0.6)' }}
          contentStyle={{
            borderRadius: '10px',
            border: '1px solid #e5e5e5',
            fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
          formatter={(v) => [`${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`, 'Win Rate']}
          labelFormatter={(label) => `Região: ${label}`}
        />
        {globalWr > 0 && (
          <ReferenceLine
            y={parseFloat(globalWr.toFixed(1))}
            stroke="#bd9762"
            strokeDasharray="4 3"
            strokeWidth={1.5}
            label={{ value: 'Global', position: 'insideTopRight', fontSize: 9, fill: '#bd9762' }}
          />
        )}
        <Bar dataKey="win_rate" fill="#bd9762" radius={[4, 4, 0, 0]} maxBarSize={32} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function WinRateByProductChart({
  products,
  globalWr,
}: {
  products: ProductSummary[]
  globalWr: number
}) {
  const data = products.map((p) => ({
    product: p.product,
    win_rate: parseFloat(p.win_rate.toFixed(1)),
  }))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        barCategoryGap="28%"
        margin={{ top: 4, right: 8, left: -12, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis
          dataKey="product"
          tick={{ fontSize: 10, fill: '#737373' }}
          tickLine={false}
          axisLine={{ stroke: '#d4d4d4' }}
          interval={0}
          angle={data.length > 4 ? -18 : 0}
          textAnchor={data.length > 4 ? 'end' : 'middle'}
          height={data.length > 4 ? 44 : 28}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#737373' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}%`}
          width={36}
          domain={[0, (dataMax: number) => Math.ceil(Math.max(dataMax, globalWr) * 1.15)]}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245,245,245,0.6)' }}
          contentStyle={{
            borderRadius: '10px',
            border: '1px solid #e5e5e5',
            fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
          formatter={(v) => [`${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`, 'Win Rate']}
          labelFormatter={(label) => `Produto: ${label}`}
        />
        {globalWr > 0 && (
          <ReferenceLine
            y={parseFloat(globalWr.toFixed(1))}
            stroke="#bd9762"
            strokeDasharray="4 3"
            strokeWidth={1.5}
            label={{ value: 'Global', position: 'insideTopRight', fontSize: 9, fill: '#bd9762' }}
          />
        )}
        <Bar dataKey="win_rate" fill="#bd9762" radius={[4, 4, 0, 0]} maxBarSize={32} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function ProductOverviewPanel({ products, globalWr }: { products: ProductSummary[]; globalWr: number }) {
  return (
    <div className={chartCardClass}>
      <div className="flex items-start gap-3 shrink-0">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-100"
          aria-hidden
        >
          <Package className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
        </div>
        <div>
          <p className={`text-sm font-medium leading-snug ${METRIC_TEXT_CLASS}`}>
            Overview de Produtos
          </p>
          <p className="text-xs text-neutral-500 leading-snug mt-0.5">
            Win rate por produto
          </p>
        </div>
      </div>

      <div className="mt-3 flex min-h-0 flex-1">
        <WinRateByProductChart products={products} globalWr={globalWr} />
      </div>
    </div>
  )
}

function RegionOverviewPanel({ regions, globalWr }: { regions: RegionSummary[]; globalWr: number }) {
  return (
    <div className={chartCardClass}>
      <div className="flex items-start gap-3 shrink-0">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-100"
          aria-hidden
        >
          <Map className="h-[18px] w-[18px] stroke-[1.65] text-[#bd9762]" />
        </div>
        <div>
          <p className={`text-sm font-medium leading-snug ${METRIC_TEXT_CLASS}`}>
            Overview Regional
          </p>
          <p className="text-xs text-neutral-500 leading-snug mt-0.5">
            Win rate por região
          </p>
        </div>
      </div>

      <div className="mt-3 flex min-h-0 flex-1">
        <WinRateByRegionChart regions={regions} globalWr={globalWr} />
      </div>
    </div>
  )
}

type Props = {
  managerName?: string
}

export default function RegionalProductsAnalysis({ managerName }: Props) {
  const [scope, setScope] = useState<'squad' | 'geral'>('geral')

  const scopeParams =
    scope === 'squad' && managerName
      ? { scope: 'squad' as const, manager: managerName }
      : { scope: 'geral' as const }

  const { data: regionalData, isLoading: regionalLoading } = useRegionalAnalysis(scopeParams)
  const { data: productsData, isLoading: productsLoading } = useProductsAnalysis(scopeParams)

  const regions = regionalData?.regions ?? []

  return (
    <div className="flex h-full min-h-0 w-full min-w-0 max-w-full flex-1 flex-col gap-6 overflow-hidden p-6 sm:p-8">
      <div className="shrink-0">
        <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">
          Products & Regional Analysis
        </h2>
        <p className="text-sm text-neutral-500 mt-0.5">
          {managerName
            ? `Visão agregada do squad de ${managerName}`
            : 'Visão agregada do squad'}
        </p>
      </div>

      <div
        className="inline-flex w-fit shrink-0 self-start rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
        role="group"
        aria-label="Escopo regional e produtos"
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

      <div className="grid min-w-0 max-w-full shrink-0 grid-cols-2 gap-x-4 gap-y-3 items-stretch lg:grid-cols-4 lg:gap-x-5 lg:gap-y-3">
        {productsLoading ? (
          <>
            <div className="h-[188px] min-h-[188px] animate-pulse rounded-2xl bg-neutral-100" />
            <div className="h-[188px] min-h-[188px] animate-pulse rounded-2xl bg-neutral-100" />
          </>
        ) : productsData?.insights ? (
          <>
            <ProductInsightCard
              variant="best"
              product={productsData.insights.best_product.product}
              win_rate={productsData.insights.best_product.win_rate}
              avg_ticket={productsData.insights.best_product.avg_ticket}
              deals_engaging={productsData.insights.best_product.deals_engaging}
            />
            <ProductInsightCard
              variant="worst"
              product={productsData.insights.worst_product.product}
              win_rate={productsData.insights.worst_product.win_rate}
              avg_ticket={productsData.insights.worst_product.avg_ticket}
              deals_engaging={productsData.insights.worst_product.deals_engaging}
            />
          </>
        ) : (
          <>
            <div className={`${cardClass} min-h-[188px]`} aria-hidden />
            <div className={`${cardClass} min-h-[188px]`} aria-hidden />
          </>
        )}
        {regionalLoading ? (
          <>
            <div className="h-[188px] min-h-[188px] animate-pulse rounded-2xl bg-neutral-100" />
            <div className="h-[188px] min-h-[188px] animate-pulse rounded-2xl bg-neutral-100" />
          </>
        ) : regionalData?.insights ? (
          <>
            <RegionalInsightCard
              variant="best"
              region={regionalData.insights.best_region.region}
              win_rate={regionalData.insights.best_region.win_rate}
              avg_score={regionalData.insights.best_region.avg_score}
              avg_viability={regionalData.insights.best_region.avg_viability}
              sellers_count={regionalData.insights.best_region.sellers_count}
            />
            <RegionalInsightCard
              variant="worst"
              region={regionalData.insights.worst_region.region}
              win_rate={regionalData.insights.worst_region.win_rate}
              avg_score={regionalData.insights.worst_region.avg_score}
              avg_viability={regionalData.insights.worst_region.avg_viability}
              sellers_count={regionalData.insights.worst_region.sellers_count}
            />
          </>
        ) : (
          <>
            <div className={`${cardClass} min-h-[188px]`} aria-hidden />
            <div className={`${cardClass} min-h-[188px]`} aria-hidden />
          </>
        )}
      </div>

      <div className="flex min-h-0 flex-1 flex-col">
        <div className="grid h-full min-h-0 flex-1 grid-cols-1 grid-rows-2 gap-4 lg:grid-cols-2 lg:grid-rows-1 lg:gap-5">
          {productsLoading ? (
            <div className="min-h-[12rem] flex-1 animate-pulse rounded-2xl border border-neutral-100 bg-neutral-100" />
          ) : productsData?.products.length ? (
            <ProductOverviewPanel products={productsData.products} globalWr={productsData.global_wr} />
          ) : (
            <div className={`min-h-[12rem] flex-1 ${chartCardClass}`} aria-hidden />
          )}
          {regionalLoading ? (
            <div className="min-h-[12rem] flex-1 animate-pulse rounded-2xl border border-neutral-100 bg-neutral-100" />
          ) : regions.length > 0 ? (
            <RegionOverviewPanel regions={regions} globalWr={regionalData?.global_wr ?? 0} />
          ) : (
            <div className={`min-h-[12rem] flex-1 ${chartCardClass}`} aria-hidden />
          )}
        </div>
      </div>
    </div>
  )
}
