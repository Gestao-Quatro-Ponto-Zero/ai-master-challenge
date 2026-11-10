"use client"

import { Info } from "lucide-react"
import { useState } from "react"

import { Segmented } from "@/components/painel/segmented"
import { DIMENSIONS, METRICS, type DimensionData, type DimensionKey, type GroupStat, type Interval, type MetricKey, type Overall } from "@/components/painel/diagnostic-types"
import { Headline } from "@/components/shared/headline"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

const value = (g: GroupStat, m: MetricKey): number => (m === "hours" ? g.hours : m === "csat" ? g.csat : g[m])
const interval = (g: GroupStat, m: MetricKey): Interval => (m === "hours" ? g.hours_ci : m === "csat" ? g.csat_ci : m === "pct_open" ? g.pct_open_ci : g.pct_pending_ci)
const format = (v: number, m: MetricKey) => (m === "hours" ? fmt.hours(v) : m === "csat" ? fmt.dec(v, 2) : fmt.pct(v))
const sampleOf = (g: GroupStat, m: MetricKey) => (m === "hours" ? g.nCoherent : m === "csat" ? g.nClosed : g.n)
const sampleLabel: Record<MetricKey, string> = { pct_open: "tickets", pct_pending: "tickets", hours: "fechados coerentes", csat: "fechados" }

/** Domínio e ticks "redondos" do eixo de cada métrica. */
function axisFor(m: MetricKey, groups: GroupStat[]): { domain: [number, number]; ticks: number[] } {
  if (m === "csat") return { domain: [0, 5], ticks: [0, 1, 2, 3, 4, 5] }
  const hi = Math.max(...groups.map((g) => interval(g, m)[1]))
  const step = m === "hours" ? (hi > 10 ? 4 : 2) : hi > 0.5 ? 0.2 : 0.1
  const top = Math.ceil(hi / step) * step
  const ticks: number[] = []
  for (let t = 0; t <= top + 1e-9; t += step) ticks.push(Math.round(t * 1000) / 1000)
  return { domain: [0, top], ticks }
}

const pos = (v: number, [a, b]: [number, number]) => `${Math.max(0, Math.min(100, ((v - a) / (b - a)) * 100))}%`

export function DiagnosticExplorer({ dimensions, overall }: { dimensions: DimensionData[]; overall: Overall }) {
  const [metric, setMetric] = useState<MetricKey>("pct_open")
  const [dimension, setDimension] = useState<DimensionKey>("canal")
  const dim = dimensions.find((d) => d.key === dimension) ?? dimensions[0]
  const dimOptions = DIMENSIONS.map((d) => ({ value: d.key, label: d.label }))

  return (
    <section className="flex min-w-0 flex-col gap-5 rounded-xl border border-border bg-surface p-5 shadow-soft sm:p-6" aria-labelledby="fluxo-titulo">
      <Headline>
        <span id="fluxo-titulo">O gargalo está no processo inteiro: todos os cortes têm desempenho equivalente</span>
      </Headline>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
        <Segmented label="Métrica" options={METRICS.map((m) => ({ value: m.key, label: m.label }))} value={metric} onChange={setMetric} />
        <Segmented label="Dimensão" options={dimOptions} value={dimension} onChange={setDimension} />
        <SignificanceInfo dim={dim} metric={metric} />
      </div>
      <Bars dim={dim} metric={metric} overall={overall} />
    </section>
  )
}

/** Resultado do teste estatístico no hover de um ícone ⓘ (frase em linguagem simples + p-valor). */
function SignificanceInfo({ dim, metric }: { dim: DimensionData; metric: MetricKey }) {
  const t = dim.tests[metric]
  if (!t) return null
  const text = t.significant
    ? `${dim.subject} têm desempenho diferente: a diferença observada é maior do que o acaso produz.`
    : `${dim.subject} têm desempenho equivalente: a diferença observada está dentro do que o acaso produz.`
  const shared = metric === "pct_open" || metric === "pct_pending"
  return (
    <Tooltip>
      <TooltipTrigger
        aria-label={`Resultado do teste: ${text}`}
        className={cn(
          "mb-0.5 inline-flex size-8 items-center justify-center rounded-full border transition-colors",
          t.significant ? "border-alert/50 text-alert" : "border-border text-text-3 hover:text-text-1",
        )}
      >
        <Info className="size-4" aria-hidden />
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <span className="flex flex-col gap-1 text-left">
          <span>{text}</span>
          <span className="opacity-80">
            p = {fmt.dec(t.p, 2)} · {t.test}
            {shared ? " (um teste para a distribuição inteira do status)" : ""}
            {dim.key === "produto" ? ` · ${dim.totalGroups} produtos` : ""}
          </span>
        </span>
      </TooltipContent>
    </Tooltip>
  )
}

function Bars({ dim, metric, overall }: { dim: DimensionData; metric: MetricKey; overall: Overall }) {
  const [hover, setHover] = useState<string | null>(null)
  const groups = [...dim.groups].sort((a, b) => (a.isOther ? 1 : b.isOther ? -1 : value(b, metric) - value(a, metric)))
  const { domain, ticks } = axisFor(metric, groups)
  const ref = metric === "hours" ? overall.hours : metric === "csat" ? overall.csat : overall[metric]
  const active = groups.find((g) => g.value === hover)
  const metricLabel = METRICS.find((m) => m.key === metric)!.label

  return (
    <div className="flex flex-col gap-2">
      <div role="list" aria-label={`${metricLabel} por ${dim.label.toLowerCase()}, com intervalo de confiança de 95%`} className="flex flex-col">
        {groups.map((g) => {
          const v = value(g, metric)
          const [lo, hi] = interval(g, metric)
          const label = g.isOther ? `Outros (${g.otherCount} produtos)` : g.value
          return (
            <div
              key={g.value}
              role="listitem"
              tabIndex={0}
              onMouseEnter={() => setHover(g.value)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(g.value)}
              onBlur={() => setHover(null)}
              aria-label={`${label}: ${format(v, metric)}, intervalo de ${format(lo, metric)} a ${format(hi, metric)}, ${fmt.int(sampleOf(g, metric))} ${sampleLabel[metric]}`}
              className={cn("grid grid-cols-[minmax(84px,30%)_1fr_64px] items-center gap-3 rounded-md px-1 py-1.5 outline-none sm:grid-cols-[180px_1fr_72px]", hover === g.value && "bg-surface-2/70")}
            >
              <span className="truncate text-sm text-text-2" title={label}>
                {label}
              </span>
              <div className="relative h-5">
                <div className="absolute inset-y-0 border-l border-dashed border-text-3/60" style={{ left: pos(ref, domain) }} aria-hidden />
                <div
                  className={cn("absolute top-1/2 h-3 -translate-y-1/2 rounded-r-[4px] bg-cat-hardware transition-opacity", hover && hover !== g.value ? "opacity-50" : "opacity-90")}
                  style={{ left: 0, width: pos(v, domain) }}
                  aria-hidden
                />
                <div className="absolute top-1/2 h-px -translate-y-1/2 bg-text-1" style={{ left: pos(lo, domain), width: `calc(${pos(hi, domain)} - ${pos(lo, domain)})` }} aria-hidden>
                  <span className="absolute -top-[5px] left-0 h-[11px] w-px bg-text-1" />
                  <span className="absolute -top-[5px] right-0 h-[11px] w-px bg-text-1" />
                </div>
              </div>
              <span className="text-right font-sans text-sm font-semibold tabular-nums text-text-1">{format(v, metric)}</span>
            </div>
          )
        })}
      </div>
      <div className="grid grid-cols-[minmax(84px,30%)_1fr_64px] gap-3 px-1 sm:grid-cols-[180px_1fr_72px]" aria-hidden>
        <span />
        <div className="relative h-4 font-mono text-[10px] text-text-3">
          {ticks.map((t, i) => (
            <span key={t} className={cn("absolute", i === 0 ? "left-0" : i === ticks.length - 1 ? "right-0" : "-translate-x-1/2", ticks.length > 4 && i % 2 === 1 && "hidden sm:inline")} style={i === 0 || i === ticks.length - 1 ? undefined : { left: pos(t, domain) }}>
              {metric === "csat" ? fmt.dec(t, 1) : metric === "hours" ? fmt.hours(t, 0) : fmt.pct(t, 0)}
            </span>
          ))}
        </div>
        <span />
      </div>
      <p className="min-h-10 text-xs leading-relaxed text-text-3" aria-live="polite">
        {active ? (
          <>
            <span className="font-semibold text-text-1">{active.isOther ? `Outros (${active.otherCount} produtos)` : active.value}</span>: {format(value(active, metric), metric)} · IC 95% {format(interval(active, metric)[0], metric)} a{" "}
            {format(interval(active, metric)[1], metric)} · {fmt.int(sampleOf(active, metric))} {sampleLabel[metric]}
          </>
        ) : (
          <>
            Linha tracejada: valor geral ({format(ref, metric)}). Traço preto: intervalo de confiança de 95%.
            {metric === "hours" ? " Tempo da 1ª resposta até a resolução, só nos registros em que a resolução vem depois da resposta." : null}
            {metric === "csat" ? " Nota de 1 a 5, só nos tickets fechados." : null}
            {dim.key === "produto" ? ` Mostra os 10 maiores dos ${dim.totalGroups} produtos; o restante está em Outros.` : null}
          </>
        )}
      </p>
    </div>
  )
}
