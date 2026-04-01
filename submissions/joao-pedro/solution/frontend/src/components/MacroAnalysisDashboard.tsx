import { useMemo } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { CircleCheck, Clock, Divide, HelpCircle, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fetchPipelineTimeMedians, fetchWonValueOverTime, type PipelineSummaryScope } from '@/api/analysis'
import { useDeals } from '@/hooks/useDeals'
import { useSellers } from '@/hooks/useSellers'
import ProspectingHealthHorizontalChart from '@/components/charts/ProspectingHealthHorizontalChart'
import WonValueOverTimeChart from '@/components/charts/WonValueOverTimeChart'
import { buildProspectingHealthData } from '@/lib/buildProspectingHealthData'
import type { Deal, PipelineTimeMedians, WonValuePoint } from '@/types'

/** Cor das barras do gráfico "Saúde do Pipeline: Prospecting". */
const MACRO_PROSPECTING_HEALTH_BAR = '#bd9762'

const TIME_METRIC_TOOLTIP = {
  ratio: 'Quantas vezes o pipeline está além da mediana Won',
  engaging: 'Tempo mediano dos deals abertos atualmente',
  won: 'Tempo mediano dos deals ganhos',
} as const

function formatMedianDays(value: number | null | undefined) {
  if (value == null) return '—'
  return `${value.toLocaleString('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 0 })} dias`
}

function formatRatio(value: number | null | undefined) {
  if (value == null) return '—'
  return `${value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}×`
}

export type MacroScope = 'geral' | 'squad'

type Props = {
  managerName: string
  scope: MacroScope
  onScopeChange: (scope: MacroScope) => void
}

function mergeWonSeries(pointsList: WonValuePoint[][]): WonValuePoint[] {
  const map = new Map<string, { value: number; count: number }>()
  for (const series of pointsList) {
    for (const p of series) {
      const cur = map.get(p.date) ?? { value: 0, count: 0 }
      cur.value += p.value
      cur.count += p.count
      map.set(p.date, cur)
    }
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, v]) => ({ date, value: v.value, count: v.count }))
}

function MacroTimeMetricCard({
  Icon,
  topRight,
  valueDisplay,
  label,
  subtitle,
  tooltip,
}: {
  Icon: LucideIcon
  topRight: string
  valueDisplay: string
  label: string
  subtitle: string
  tooltip: string
}) {
  return (
    <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#bd9762]/10 text-[#bd9762]">
          <Icon className="h-4 w-4" strokeWidth={2} aria-hidden />
        </div>
        <div className="flex min-w-0 flex-1 items-start justify-end gap-1">
          {topRight ? (
            <span className="pt-0.5 text-right text-[10px] font-semibold tabular-nums text-neutral-400 leading-tight max-w-[5rem]">
              {topRight}
            </span>
          ) : null}
          <button
            type="button"
            className="shrink-0 rounded p-0.5 text-neutral-300 transition-colors hover:text-neutral-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400"
            title={tooltip}
            aria-label={tooltip}
          >
            <HelpCircle className="h-3.5 w-3.5" strokeWidth={1.75} />
          </button>
        </div>
      </div>
      <p className="text-xl font-bold tabular-nums tracking-tight text-neutral-900">{valueDisplay}</p>
      <div>
        <p className="text-sm font-medium text-neutral-700">{label}</p>
        <p className="text-xs text-neutral-400 mt-0.5">{subtitle}</p>
      </div>
    </div>
  )
}

function MacroDashboardRightColumn({
  deals,
  timeMedians,
  timeLoading,
}: {
  deals: Deal[]
  timeMedians?: PipelineTimeMedians | null
  timeLoading: boolean
}) {
  const openValue = deals
    .filter((d) => d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)

  const openValueProspecting = deals
    .filter((d) => d.deal_stage === 'Prospecting')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)

  const openValueEngaging = deals
    .filter((d) => d.deal_stage === 'Engaging')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)

  return (
    <div className="flex flex-col gap-5 h-full p-5">
      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValue.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Prospecting + Engaging)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma da estimativa em aberto dos deals no escopo</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValueProspecting.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Prospecting)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma no escopo selecionado</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValueEngaging.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Engaging)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma no escopo selecionado</p>
          </div>
        </div>
      </div>

      {/* Medianas / ratio — GET /analysis/pipeline/time-medians */}
      <div className="flex flex-col gap-3 border-t border-neutral-100 pt-4">
        {timeLoading ? (
          <>
            <div className="h-[120px] rounded-2xl bg-neutral-100 animate-pulse" />
            <div className="grid grid-cols-2 gap-3">
              <div className="h-[120px] rounded-2xl bg-neutral-100 animate-pulse" />
              <div className="h-[120px] rounded-2xl bg-neutral-100 animate-pulse" />
            </div>
          </>
        ) : (
          (() => {
            const tm = timeMedians
            const cc = tm?.cohort_counts
            const ratio = tm?.engaging_to_won_ratio
            const ratioTop = ratio != null && ratio > 1 ? 'acima do ideal' : ''
            return (
              <>
                <MacroTimeMetricCard
                  Icon={Divide}
                  topRight={ratioTop}
                  valueDisplay={formatRatio(ratio)}
                  label="Ratio Engaging / Won"
                  subtitle="Mediana Engaging ÷ mediana Won"
                  tooltip={TIME_METRIC_TOOLTIP.ratio}
                />
                <div className="grid grid-cols-2 gap-3 min-w-0">
                  <MacroTimeMetricCard
                    Icon={Clock}
                    topRight={cc != null ? `n=${cc.engaging.toLocaleString('pt-BR')}` : ''}
                    valueDisplay={formatMedianDays(tm?.engaging_median_days)}
                    label="Mediana Engaging"
                    subtitle="Dias no pipeline"
                    tooltip={TIME_METRIC_TOOLTIP.engaging}
                  />
                  <MacroTimeMetricCard
                    Icon={CircleCheck}
                    topRight={cc != null ? `n=${cc.won.toLocaleString('pt-BR')}` : ''}
                    valueDisplay={formatMedianDays(tm?.won_median_days)}
                    label="Mediana Won"
                    subtitle="Dias no pipeline"
                    tooltip={TIME_METRIC_TOOLTIP.won}
                  />
                </div>
              </>
            )
          })()
        )}
      </div>
    </div>
  )
}

const KPI_ICONS: { icon: React.ReactNode; label: string; sub: string }[] = [
  {
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
    label: 'Deals Ativos',
    sub: 'Prospecting + Engaging',
  },
  {
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
    label: 'Prospecting',
    sub: 'Deals em prospecção',
  },
  {
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    label: 'Engaging',
    sub: 'Deals em negociação',
  },
  {
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    ),
    label: 'Ticket Médio',
    sub: 'Média dos deals Won (histórico)',
  },
  {
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </svg>
    ),
    label: 'Win Rate',
    sub: 'Won / fechados no escopo',
  },
]

export default function MacroAnalysisDashboard({ managerName, scope, onScopeChange }: Props) {
  const { data: allSellers = [], isLoading: sellersLoading, isError: sellersError } = useSellers()
  const { data: allDeals = [], isLoading: dealsLoading } = useDeals({ all_stages: true })

  const scopeSellers = useMemo(() => {
    if (scope === 'geral') return allSellers
    return allSellers.filter((s) => s.manager === managerName)
  }, [allSellers, scope, managerName])

  const agentSet = useMemo(() => new Set(scopeSellers.map((s) => s.sales_agent)), [scopeSellers])

  const scopedDeals = useMemo(
    () => allDeals.filter((d) => agentSet.has(d.sales_agent)),
    [allDeals, agentSet],
  )

  const kpis = useMemo(() => {
    let active = 0
    let prospecting = 0
    let engaging = 0
    let sumWonTickets = 0
    let sumWonDeals = 0
    let sumWon = 0
    let sumClosed = 0

    for (const s of scopeSellers) {
      active += s.active_deals
      prospecting += s.prospecting
      engaging += s.active_deals - s.prospecting
      sumWonTickets += s.avg_ticket * s.won_deals
      sumWonDeals += s.won_deals
      sumWon += s.won_deals
      sumClosed += s.closed_deals
    }

    const ticketMedio = sumWonDeals > 0 ? sumWonTickets / sumWonDeals : null
    const winRate = sumClosed > 0 ? (sumWon / sumClosed) * 100 : null

    return {
      active,
      prospecting,
      engaging,
      ticketMedio,
      winRate,
    }
  }, [scopeSellers])

  const salesAgentsForWon = useMemo(() => scopeSellers.map((s) => s.sales_agent), [scopeSellers])

  const wonQueries = useQueries({
    queries: salesAgentsForWon.map((agent) => ({
      queryKey: ['wonValueOverTime', agent],
      queryFn: () => fetchWonValueOverTime(agent),
      enabled: salesAgentsForWon.length > 0,
    })),
  })

  const mergedWonPoints = useMemo(() => {
    const series = wonQueries.map((q) => q.data?.points ?? []).filter((p) => p.length > 0)
    return mergeWonSeries(series)
  }, [wonQueries])

  const wonLoading = wonQueries.some((q) => q.isLoading || q.isFetching)

  const kpiValues: (string | number)[] = useMemo(
    () => [
      kpis.active,
      kpis.prospecting,
      kpis.engaging,
      kpis.ticketMedio != null
        ? kpis.ticketMedio.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
        : '—',
      kpis.winRate != null ? kpis.winRate.toFixed(1) : '—',
    ],
    [kpis],
  )

  const kpiSuffix = ['', '', '', '', '%']

  const loading = sellersLoading || dealsLoading

  /** Recorte Geral vs Squad do manager (alinhado ao GET /analysis/pipeline/time-medians). */
  const apiScopeForPipeline: PipelineSummaryScope =
    scope === 'squad' && managerName ? 'squad' : 'geral'

  const timeMediansQuery = useQuery({
    queryKey: ['pipeline-time-medians', apiScopeForPipeline, managerName ?? ''],
    queryFn: () =>
      fetchPipelineTimeMedians({
        scope: apiScopeForPipeline,
        ...(apiScopeForPipeline === 'squad' && managerName ? { manager: managerName } : {}),
      }),
  })

  const timeLoading = timeMediansQuery.isLoading && !timeMediansQuery.data

  return (
    <div className="flex flex-col gap-6 flex-1 min-h-0">
      <div className="flex flex-col gap-3">
        <div>
          <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Macro Analysis</h2>
          <p className="text-sm text-neutral-500 mt-0.5">
            Visão agregada do pipeline — {scope === 'geral' ? 'empresa' : `squad (${managerName})`}
          </p>
        </div>
        <div
          className="inline-flex w-fit shrink-0 rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
          role="group"
          aria-label="Escopo das métricas"
        >
          <button
            type="button"
            disabled={!managerName}
            title={!managerName ? 'Selecione um manager no painel à esquerda' : undefined}
            onClick={() => onScopeChange('squad')}
            className={cn(
              'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              scope === 'squad' ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800',
              !managerName && 'cursor-not-allowed opacity-45 hover:text-neutral-500',
            )}
          >
            Squad
          </button>
          <button
            type="button"
            onClick={() => onScopeChange('geral')}
            className={cn(
              'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              scope === 'geral' ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800',
            )}
          >
            Geral
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 grid-rows-[auto_1fr] gap-4 flex-1 min-h-0">
        <div className="col-span-5 row-start-1 grid grid-cols-5 gap-4">
          {KPI_ICONS.map((k, i) => (
            <div
              key={k.label}
              className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3"
            >
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">{k.icon}</div>
              </div>
              <div>
                {loading ? (
                  <div className="h-8 w-24 rounded-md bg-neutral-100 animate-pulse" />
                ) : (
                  <p className="text-2xl font-bold text-neutral-900 tracking-tight">
                    {kpiValues[i]}
                    {kpiSuffix[i]}
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-neutral-700">{k.label}</p>
                <p className="text-xs text-neutral-400 mt-0.5">{k.sub}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-3 row-start-2 flex min-h-0 flex-col gap-4 min-w-0 self-stretch">
          <div className="min-h-[440px] shrink-0 rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
            <WonValueOverTimeChart mergedPoints={mergedWonPoints} mergedLoading={wonLoading} />
          </div>
          <div className="flex flex-col overflow-hidden rounded-2xl border border-neutral-100 bg-white p-4 shadow-[0_2px_12px_rgba(0,0,0,0.04)] sm:p-5">
            <div className="shrink-0 space-y-0.5 pr-1">
              <h3 className="text-[15px] font-semibold leading-tight tracking-tight text-neutral-900">
                Saúde do Pipeline: Prospecting
              </h3>
              <p className="text-xs leading-snug text-neutral-500">
                % do time por indicador (deals ativos = Prospecção + Engajamento; sobrecarga &gt; 100
                ativos)
              </p>
              {allSellers.length > 0 ? (
                <p className="mt-1 text-[11px] tabular-nums text-neutral-400">
                  Universo:{' '}
                  {(apiScopeForPipeline === 'squad' && managerName
                    ? allSellers.filter((s) => s.manager === managerName)
                    : allSellers
                  ).length.toLocaleString('pt-BR')}{' '}
                  vendedor(es)
                </p>
              ) : null}
            </div>
            <div className="mt-3 h-[380px] w-full shrink-0 sm:h-[400px]">
              {sellersLoading ? (
                <div className="h-full w-full animate-pulse rounded-xl bg-neutral-100" />
              ) : sellersError ? (
                <div className="flex h-full items-center justify-center text-xs text-neutral-400">
                  Não foi possível carregar o gráfico
                </div>
              ) : (
                <ProspectingHealthHorizontalChart
                  barColor={MACRO_PROSPECTING_HEALTH_BAR}
                  data={buildProspectingHealthData(allSellers, apiScopeForPipeline, managerName)}
                />
              )}
            </div>
          </div>
        </div>

        <div className="col-start-4 col-span-2 row-start-2 self-stretch min-h-[400px] rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] overflow-y-auto">
          {loading ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-24 rounded-xl bg-neutral-100 animate-pulse" />
              ))}
            </div>
          ) : (
            <MacroDashboardRightColumn
              deals={scopedDeals}
              timeMedians={timeMediansQuery.data}
              timeLoading={timeLoading}
            />
          )}
        </div>
      </div>
    </div>
  )
}
