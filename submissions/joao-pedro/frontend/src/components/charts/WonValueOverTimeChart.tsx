import { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { useWonValueOverTime } from '@/hooks/useWonValueOverTime'
import type { WonValuePoint } from '@/types'

const FILTERS = [
  { label: '7d', days: 7 },
  { label: '15d', days: 15 },
  { label: '30d', days: 30 },
  { label: '60d', days: 60 },
] as const

function fmt(value: number) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}k`
  return `$${value.toFixed(0)}`
}

function fmtDate(date: string) {
  const d = new Date(date + 'T00:00:00')
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

type FilterDays = 7 | 15 | 30 | 60 | null

interface CustomTooltipProps {
  active?: boolean
  payload?: { value: number; payload: WonValuePoint }[]
  label?: string
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  const { value, count, date } = payload[0].payload
  return (
    <div className="rounded-xl border border-neutral-100 bg-white px-3 py-2 shadow-md text-xs">
      <p className="inline-flex w-fit items-center rounded-full bg-emerald-50 px-2 py-0.5 font-semibold tabular-nums text-emerald-600">
        {fmt(value)}
      </p>
      <p className="text-neutral-400 mt-0.5">{count} deal{count !== 1 ? 's' : ''} · {fmtDate(date)}</p>
    </div>
  )
}

interface Props {
  sellerName?: string
  /** Série já agregada (ex.: Macro Analysis). Quando definido, ignora `sellerName` e não busca na API. */
  mergedPoints?: WonValuePoint[] | null
  mergedLoading?: boolean
}

export default function WonValueOverTimeChart({
  sellerName,
  mergedPoints: mergedPointsProp,
  mergedLoading,
}: Props) {
  const [activeDays, setActiveDays] = useState<FilterDays>(null)
  const useFetch = mergedPointsProp === undefined
  const { data, isLoading: fetchLoading } = useWonValueOverTime(sellerName ?? '', {
    enabled: useFetch && Boolean(sellerName),
  })

  const dataPoints: WonValuePoint[] =
    mergedPointsProp !== undefined ? (mergedPointsProp ?? []) : (data?.points ?? [])

  const isLoading = mergedPointsProp !== undefined ? Boolean(mergedLoading) : fetchLoading

  const points: WonValuePoint[] = useMemo(() => {
    if (!dataPoints.length) return []
    if (activeDays === null) return dataPoints

    const dateRangeMax =
      mergedPointsProp !== undefined
        ? dataPoints[dataPoints.length - 1]?.date
        : data?.date_range?.max
    if (!dateRangeMax) return dataPoints

    const maxDate = new Date(dateRangeMax + 'T00:00:00')
    const cutoff = new Date(maxDate)
    cutoff.setDate(cutoff.getDate() - activeDays)

    return dataPoints.filter((p) => new Date(p.date + 'T00:00:00') >= cutoff)
  }, [data, dataPoints, activeDays, mergedPointsProp])

  const totalValue = useMemo(() => points.reduce((s, p) => s + p.value, 0), [points])
  const totalDeals = useMemo(() => points.reduce((s, p) => s + p.count, 0), [points])

  const windowLabel = useMemo(() => {
    if (!points.length) return null
    const first = fmtDate(points[0].date)
    const last = fmtDate(points[points.length - 1].date)
    return first === last ? first : `${first} – ${last}`
  }, [points])

  return (
    <div className="flex flex-col h-full p-6 gap-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Valor Convertido</p>
            {!isLoading && windowLabel && (
              <span className="text-[10px] text-neutral-400 font-normal">{windowLabel}</span>
            )}
          </div>
          {isLoading ? (
            <div className="mt-1 h-6 w-24 rounded-md bg-neutral-100 animate-pulse" />
          ) : (
            <p className="mt-0.5 inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-xl font-bold tabular-nums text-emerald-600">
              {fmt(totalValue)}
            </p>
          )}
          {!isLoading && (
            <p className="text-[11px] text-neutral-400 mt-0.5">{totalDeals} deal{totalDeals !== 1 ? 's' : ''} no período</p>
          )}
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={() => setActiveDays(null)}
            className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
              activeDays === null
                ? 'bg-neutral-900 text-white'
                : 'text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700'
            }`}
          >
            Tudo
          </button>
          {FILTERS.map(({ label, days }) => (
            <button
              key={days}
              type="button"
              onClick={() => setActiveDays(days)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                activeDays === days
                  ? 'bg-neutral-900 text-white'
                  : 'text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0">
        {isLoading ? (
          <div className="h-full w-full rounded-xl bg-neutral-50 animate-pulse" />
        ) : points.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-xs text-neutral-400">Sem dados no período</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={fmtDate}
                tick={{ fontSize: 10, fill: '#a3a3a3' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tickFormatter={fmt}
                tick={{ fontSize: 10, fill: '#a3a3a3' }}
                axisLine={false}
                tickLine={false}
                width={48}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#bd9762"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#bd9762', strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
