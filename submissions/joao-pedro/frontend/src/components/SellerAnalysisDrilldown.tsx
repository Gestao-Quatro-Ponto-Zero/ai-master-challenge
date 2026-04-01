import { useEffect, useMemo, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  Activity,
  BarChart2,
  HelpCircle,
  Layers,
  Percent,
  Search,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { fetchDeals } from '@/api/deals'
import { fetchBenchmarks, type PipelineSummaryScope } from '@/api/analysis'
import SellerAlertsBlock from '@/components/SellerAlertsBlock'
import { fetchSellers } from '@/api/sellers'
import { cn } from '@/lib/utils'
import type { Deal } from '@/types'

/** Alinhado ao Pipeline Analysis: ícone dourado + texto de métrica em preto neutro. */
const SELLER_METRIC_ICON_COLOR_CLASS = 'text-[#bd9762]'
const SELLER_METRIC_TEXT_CLASS = 'text-neutral-900'

const sellerMiniCardClass =
  'rounded-xl border border-neutral-100/90 bg-white/95 shadow-[0_1px_8px_rgba(0,0,0,0.03)]'

const SELLER_KPI_TOOLTIP = {
  engaging:
    'Quantidade de deals em Engaging listados para este vendedor (mesmos da tabela abaixo)',
  score: 'Média do score dos deals Engaging exibidos na tabela',
  winRate: 'Win rate histórico do vendedor e diferença em pontos percentuais vs win rate global',
  active: 'Total de deals ativos (Prospecção + Engajamento) do vendedor na base',
  prospecting: 'Quantidade de deals em Prospecting atribuídos ao vendedor',
} as const

type Props = {
  managerName?: string
}

type SellerMiniMetricProps = {
  Icon: LucideIcon
  topRight: string
  valueDisplay: string
  label: string
  subtitle: string
  tooltip: string
}

/** Mesma hierarquia visual dos mini-cards de medianas no Pipeline Analysis */
function SellerMiniMetricCard({
  Icon,
  topRight,
  valueDisplay,
  label,
  subtitle,
  tooltip,
}: SellerMiniMetricProps) {
  return (
    <div className={`${sellerMiniCardClass} flex flex-col p-3 sm:p-4 min-h-[118px]`}>
      <div className="flex items-start justify-between gap-2">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-100"
          aria-hidden
        >
          <Icon
            className={cn(
              'h-[14px] w-[14px] stroke-[1.65]',
              SELLER_METRIC_ICON_COLOR_CLASS,
            )}
          />
        </div>
        <div className="flex items-start gap-0.5 min-w-0 justify-end">
          {topRight ? (
            <span
              className={`pt-0.5 text-[10px] font-semibold tabular-nums tracking-tight text-right leading-tight max-w-[6.5rem] ${SELLER_METRIC_TEXT_CLASS}`}
            >
              {topRight}
            </span>
          ) : null}
          <button
            type="button"
            className="shrink-0 -mr-0.5 rounded p-0.5 text-neutral-300 transition-colors hover:text-neutral-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:ring-offset-1"
            title={tooltip}
            aria-label={tooltip}
          >
            <HelpCircle className="h-3.5 w-3.5" strokeWidth={1.75} />
          </button>
        </div>
      </div>

      <p
        className={`mt-3 text-xl font-bold tabular-nums tracking-tight leading-none ${SELLER_METRIC_TEXT_CLASS}`}
      >
        {valueDisplay}
      </p>

      <div className="mt-auto pt-3 space-y-0.5">
        <p className={`text-[11px] font-semibold uppercase tracking-wide leading-snug ${SELLER_METRIC_TEXT_CLASS}`}>
          {label}
        </p>
        <p className={`text-[10px] leading-snug ${SELLER_METRIC_TEXT_CLASS}`}>{subtitle}</p>
      </div>
    </div>
  )
}

function MetricCell({ value }: { value: number }) {
  const v = Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0))
  return (
    <div className="flex items-center gap-2 min-w-[104px]">
      <div className="flex-1 h-2 min-w-[48px] rounded-full bg-neutral-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-[#bd9762]"
          style={{ width: `${v}%` }}
        />
      </div>
      <span
        className={`text-[11px] tabular-nums w-7 shrink-0 text-right ${SELLER_METRIC_TEXT_CLASS}`}
      >
        {Math.round(v)}
      </span>
    </div>
  )
}

export default function SellerAnalysisDrilldown({ managerName }: Props) {
  const [scope, setScope] = useState<PipelineSummaryScope>('squad')
  const [selectedSeller, setSelectedSeller] = useState('')

  /** Lista de vendedores: squad só com manager; sem manager equivale a geral na API. */
  const apiScope: PipelineSummaryScope =
    scope === 'squad' && managerName ? 'squad' : 'geral'

  const sellersQuery = useQuery({
    queryKey: ['sellers', undefined],
    queryFn: () => fetchSellers(),
  })

  const pool = useMemo(() => {
    const list = sellersQuery.data ?? []
    const base =
      apiScope === 'squad' && managerName
        ? list.filter((s) => s.manager === managerName)
        : list
    return [...base].sort((a, b) => a.sales_agent.localeCompare(b.sales_agent, 'pt-BR'))
  }, [sellersQuery.data, apiScope, managerName])

  useEffect(() => {
    if (pool.length === 0) {
      setSelectedSeller('')
      return
    }
    setSelectedSeller((prev) => {
      if (prev && pool.some((s) => s.sales_agent === prev)) return prev
      return pool[0].sales_agent
    })
  }, [pool])

  const dealsQuery = useQuery({
    queryKey: ['deals', { sales_agent: selectedSeller }],
    queryFn: () => fetchDeals({ sales_agent: selectedSeller }),
    enabled: Boolean(selectedSeller),
    placeholderData: keepPreviousData,
  })

  const benchmarksQuery = useQuery({
    queryKey: ['benchmarks'],
    queryFn: fetchBenchmarks,
    enabled: Boolean(selectedSeller),
  })

  const dealsLoading = dealsQuery.isLoading && !dealsQuery.data
  const deals = dealsQuery.data ?? []

  const currentSeller = useMemo(
    () => pool.find((s) => s.sales_agent === selectedSeller),
    [pool, selectedSeller],
  )

  const avgScore = useMemo(() => {
    if (!deals.length) return null
    const sum = deals.reduce((acc, d) => acc + d.score, 0)
    return Math.round((sum / deals.length) * 10) / 10
  }, [deals])

  const winRateDeltaVsGlobal =
    currentSeller != null && benchmarksQuery.data != null
      ? Math.round((currentSeller.win_rate - benchmarksQuery.data.global_wr) * 10) / 10
      : null

  const winRateTopRight =
    benchmarksQuery.isLoading && currentSeller != null
      ? '…'
      : winRateDeltaVsGlobal != null
        ? `${winRateDeltaVsGlobal > 0 ? '↑ ' : winRateDeltaVsGlobal < 0 ? '↓ ' : ''}${winRateDeltaVsGlobal > 0 ? '+' : ''}${winRateDeltaVsGlobal.toLocaleString('pt-BR', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
          })} vs glob`
        : ''

  return (
    <div className="flex min-h-0 w-full min-w-0 max-w-full flex-col gap-6 p-6 sm:p-8">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Seller Analysis</h2>
        <p className="text-sm text-neutral-500 mt-0.5">
          Drill-down de deals em Engaging por vendedor
        </p>
      </div>

      <div
        className="inline-flex w-fit shrink-0 self-start rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
        role="group"
        aria-label="Escopo de vendedores"
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

      <section className="space-y-4 min-h-0" aria-labelledby="drilldown-heading">
        <h3
          id="drilldown-heading"
          className="flex items-center gap-2 text-base font-semibold text-neutral-900"
        >
          <Search className="h-4 w-4 shrink-0 text-neutral-500" strokeWidth={2} aria-hidden />
          Drill-Down por Vendedor
        </h3>

        <div className="max-w-xl space-y-1.5">
          <label htmlFor="seller-select" className="text-xs font-medium text-neutral-600">
            Vendedor
          </label>
          <select
            id="seller-select"
            value={selectedSeller}
            onChange={(e) => setSelectedSeller(e.target.value)}
            disabled={!pool.length || sellersQuery.isLoading}
            className="w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm text-neutral-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-400 focus:ring-offset-1 disabled:opacity-50"
          >
            {pool.map((s) => (
              <option key={s.sales_agent} value={s.sales_agent}>
                {s.sales_agent}
              </option>
            ))}
          </select>
        </div>

        {scope === 'squad' && !managerName ? (
          <p className="text-sm text-amber-800/90">
            Selecione um manager no painel à esquerda para usar o escopo Squad.
          </p>
        ) : null}

        {sellersQuery.isError ? (
          <p className="text-sm text-red-600">Não foi possível carregar a lista de vendedores.</p>
        ) : null}
      </section>

      {selectedSeller && !dealsQuery.isError && !dealsLoading ? (
        <div
          className="grid min-w-0 max-w-full grid-cols-2 gap-x-4 gap-y-3 items-stretch lg:grid-cols-5 lg:gap-x-5 lg:gap-y-3"
          aria-label="Resumo do vendedor"
        >
            <SellerMiniMetricCard
              Icon={Layers}
              topRight={`n=${deals.length.toLocaleString('pt-BR')}`}
              valueDisplay={deals.length.toLocaleString('pt-BR')}
              label="Deals em Engaging"
              subtitle="Na tabela abaixo"
              tooltip={SELLER_KPI_TOOLTIP.engaging}
            />
            <SellerMiniMetricCard
              Icon={BarChart2}
              topRight={`n=${deals.length.toLocaleString('pt-BR')}`}
              valueDisplay={
                avgScore != null
                  ? avgScore.toLocaleString('pt-BR', {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })
                  : '—'
              }
              label="Score médio"
              subtitle="Sobre deals Engaging"
              tooltip={SELLER_KPI_TOOLTIP.score}
            />
            <SellerMiniMetricCard
              Icon={Percent}
              topRight={winRateTopRight}
              valueDisplay={
                currentSeller != null
                  ? `${currentSeller.win_rate.toLocaleString('pt-BR', {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })}%`
                  : '—'
              }
              label="Win rate"
              subtitle="Histórico do vendedor"
              tooltip={SELLER_KPI_TOOLTIP.winRate}
            />
            <SellerMiniMetricCard
              Icon={Activity}
              topRight=""
              valueDisplay={
                currentSeller != null
                  ? currentSeller.active_deals.toLocaleString('pt-BR')
                  : '—'
              }
              label="Deals ativos"
              subtitle="Prospecção + Engajamento"
              tooltip={SELLER_KPI_TOOLTIP.active}
            />
            <SellerMiniMetricCard
              Icon={Target}
              topRight=""
              valueDisplay={
                currentSeller != null
                  ? currentSeller.prospecting.toLocaleString('pt-BR')
                  : '—'
              }
              label="Prospecting"
              subtitle="Deals em Prospecção"
              tooltip={SELLER_KPI_TOOLTIP.prospecting}
            />
        </div>
      ) : null}

      <section className="flex min-h-0 min-w-0 max-w-full flex-1 flex-col gap-3">
        <h4 className="text-sm font-semibold text-neutral-800">Deals deste Vendedor (Engaging)</h4>
        {sellersQuery.isLoading ? (
          <p className="text-sm text-neutral-400">Carregando vendedores…</p>
        ) : !selectedSeller ? (
          <p className="text-sm text-neutral-400">Escolha um vendedor para listar os deals.</p>
        ) : dealsQuery.isError ? (
          <p className="text-sm text-red-600">Não foi possível carregar os deals.</p>
        ) : dealsLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-neutral-100" />
            ))}
          </div>
        ) : (
          <div className="min-h-0 min-w-0 max-w-full overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm">
            {/* ~13 linhas visíveis; demais linhas com scroll vertical (cabeçalho fixo) */}
            <div className="max-h-[calc(2.75rem*13)] min-w-0 overflow-x-auto overflow-y-auto overscroll-y-contain">
              <table className="w-full min-w-[960px] text-left text-sm border-collapse">
                <thead className="sticky top-0 z-10">
                  <tr className="border-b border-neutral-200 bg-neutral-50/95 shadow-[0_1px_0_0_rgba(0,0,0,0.06)] backdrop-blur-sm">
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Deal ID
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Score
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Urg
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Prob%
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Val
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Viab
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Produto
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Dias
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 whitespace-nowrap">
                    Ação
                  </th>
                  <th className="px-3 py-2.5 font-semibold text-neutral-700 min-w-[220px]">
                    Mensagem
                  </th>
                </tr>
              </thead>
              <tbody>
                {deals.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-3 py-8 text-center text-neutral-400 text-sm">
                      Nenhum deal em Engaging para este vendedor.
                    </td>
                  </tr>
                ) : (
                  deals.map((row: Deal) => (
                    <tr
                      key={row.opportunity_id}
                      className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50/80"
                    >
                      <td className="px-3 py-2 font-mono text-xs text-neutral-800 max-w-[120px] truncate" title={row.opportunity_id}>
                        {row.opportunity_id}
                      </td>
                      <td className="px-3 py-2 tabular-nums text-neutral-900">
                        {row.score.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}
                      </td>
                      <td className="px-3 py-2">
                        <MetricCell value={row.urgency} />
                      </td>
                      <td className="px-3 py-2">
                        <MetricCell value={row.probability} />
                      </td>
                      <td className="px-3 py-2">
                        <MetricCell value={row.value} />
                      </td>
                      <td className="px-3 py-2">
                        <MetricCell value={row.viability} />
                      </td>
                      <td className="px-3 py-2 text-neutral-800 max-w-[140px] truncate" title={row.product}>
                        {row.product}
                      </td>
                      <td className="px-3 py-2 tabular-nums text-neutral-700">
                        {row.days_in_pipeline.toLocaleString('pt-BR')}
                      </td>
                      <td className="px-3 py-2">
                        <span className="inline-flex rounded-md bg-neutral-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-neutral-700">
                          {row.action}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-xs text-neutral-600 max-w-[320px]">
                        <span className="line-clamp-2" title={row.message}>
                          {row.message}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
              </table>
            </div>

            {selectedSeller ? <SellerAlertsBlock salesAgent={selectedSeller} /> : null}
          </div>
        )}
      </section>
    </div>
  )
}
