"use client"

import { RotateCcw } from "lucide-react"
import { useState } from "react"

import { OriginPill } from "@/components/shared/origin-pill"
import { Slider } from "@/components/ui/slider"
import { fmt } from "@/lib/format"
import { computeRoi, ROI_BOUNDS, type RoiInputs } from "@/lib/roi"
import type { DataOrigin } from "@/lib/types"

type EditableKey = "annualVolume" | "handleMinutes" | "hourlyCost" | "autonomyShare"

export interface PremiseMeta {
  key: EditableKey
  label: string
  origin: DataOrigin
  source: string
  href?: string
}

const UNIT: Record<EditableKey, { suffix: string; scale: number; digits: number }> = {
  annualVolume: { suffix: "tickets/ano", scale: 1, digits: 0 },
  handleMinutes: { suffix: "min/ticket", scale: 1, digits: 1 },
  hourlyCost: { suffix: "R$/hora", scale: 1, digits: 2 },
  autonomyShare: { suffix: "% dos elegíveis", scale: 100, digits: 1 },
}

export function RoiCalculator({ defaults, premises, eligibleRule, autonomyRule }: { defaults: RoiInputs; premises: PremiseMeta[]; eligibleRule: string; autonomyRule: string }) {
  const [inputs, setInputs] = useState<RoiInputs>(defaults)
  const r = computeRoi(inputs)
  const edited = (k: EditableKey) => Math.abs(inputs[k] - defaults[k]) > 1e-9
  const anyEdited = premises.some((p) => edited(p.key))
  const set = (k: EditableKey, v: number) => setInputs((s) => ({ ...s, [k]: v }))

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <section aria-labelledby="premissas" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-soft sm:p-6">
        <div className="flex items-center justify-between gap-3">
          <h2 id="premissas" className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">
            Premissas
          </h2>
          {anyEdited ? (
            <button type="button" onClick={() => setInputs(defaults)} className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs text-text-2 hover:text-text-1">
              <RotateCcw className="size-3.5" aria-hidden /> Restaurar padrões
            </button>
          ) : null}
        </div>
        {premises.map((p) => (
          <PremiseControl key={p.key} meta={p} value={inputs[p.key]} edited={edited(p.key)} onChange={(v) => set(p.key, v)} />
        ))}
      </section>

      <section aria-labelledby="resultado" className="flex flex-col gap-6">
        <div className="rounded-xl border border-border bg-surface p-5 shadow-soft sm:p-7">
          <h2 id="resultado" className="sr-only">
            Resultado
          </h2>
          <p className="font-serif text-2xl leading-snug text-text-1 sm:text-3xl" aria-live="polite">
            Nos casos em que a IA teria autonomia, a economia seria de aproximadamente{" "}
            <span className="font-sans font-semibold whitespace-nowrap text-gold tabular-nums">{fmt.brl(Math.round(r.savingsBrl / 100) * 100)} por ano</span>.
          </p>
          <dl className="mt-6 grid gap-4 border-t border-border pt-5 sm:grid-cols-3">
            <Stat label="Horas de atendente por ano" value={fmt.int(r.hoursSaved)} hint={`${fmt.int(r.automatedTickets)} tickets resolvidos com autonomia`} />
            <Stat label="Atendentes em tempo integral liberados" value={fmt.dec(r.ftesFreed, 2)} hint="horas ÷ 1.976 h/ano (38 h × 52 semanas)" />
            <Stat label="Custo por ticket" value={`${fmt.brl(r.costPerTicketBefore, 2)} → ${fmt.brl(r.costPerTicketAfter, 2)}`} hint="custo de atendente ÷ volume, antes e depois" />
          </dl>
        </div>

        <div className="flex flex-col gap-3 rounded-xl border border-border bg-surface-2/60 p-5">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">Como calculamos</p>
          <p className="font-mono text-sm leading-relaxed text-text-1">
            {fmt.int(inputs.annualVolume)} tickets × {fmt.pct(inputs.eligibleShare)} elegíveis × {fmt.pct(inputs.autonomyShare)} com autonomia × {fmt.dec(inputs.handleMinutes, 1)} min × {fmt.brl(inputs.hourlyCost, 2)}/h
            {" = "}
            <span className="font-semibold">{fmt.brl(r.savingsBrl)}</span>
          </p>
          <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-text-2">
            <li>
              <span className="font-medium text-text-1">{fmt.pct(inputs.eligibleShare)} elegíveis</span> (medido no DS1): {eligibleRule}.
            </li>
            <li>
              <span className="font-medium text-text-1">{fmt.pct(defaults.autonomyShare)} com autonomia</span> (medido no holdout do DS2): {autonomyRule}.
            </li>
            <li>
              Juntos, {fmt.pct(r.automatedShare)} do volume total seguem pela Resposta automática. A Revisão humana entra no cálculo sem ganho de tempo.
            </li>
          </ul>
        </div>
      </section>
    </div>
  )
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-sm text-text-2">{label}</dt>
      <dd className="text-2xl font-semibold tracking-tight text-text-1 tabular-nums">{value}</dd>
      <dd className="text-xs leading-relaxed text-text-3">{hint}</dd>
    </div>
  )
}

function PremiseControl({ meta, value, edited, onChange }: { meta: PremiseMeta; value: number; edited: boolean; onChange: (v: number) => void }) {
  const u = UNIT[meta.key]
  const b = ROI_BOUNDS[meta.key]
  const shown = Number((value * u.scale).toFixed(u.digits))
  const id = `premissa-${meta.key}`
  const commit = (raw: string) => {
    const n = Number(raw.replace(",", "."))
    if (Number.isFinite(n)) onChange(Math.min(b.max, Math.max(b.min, n / u.scale)))
  }
  const sliderMax = meta.key === "annualVolume" ? 100_000 : meta.key === "hourlyCost" ? 80 : meta.key === "handleMinutes" ? 30 : 1

  return (
    <div className="flex flex-col gap-2.5 border-t border-border pt-4 first-of-type:border-t-0 first-of-type:pt-0">
      <div className="flex items-start justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-text-1">
          {meta.label}
        </label>
        <OriginPill origin={edited ? "premissa" : meta.origin} href={edited ? undefined : meta.href} />
      </div>
      <div className="flex items-center gap-3">
        <input
          id={id}
          key={shown}
          type="number"
          inputMode="decimal"
          defaultValue={shown}
          min={b.min * u.scale}
          max={b.max * u.scale}
          step={meta.key === "annualVolume" ? 1000 : meta.key === "autonomyShare" ? 0.1 : b.step}
          onBlur={(e) => commit(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit(e.currentTarget.value)
          }}
          className="h-9 w-32 rounded-md border border-input bg-bg px-2.5 font-sans text-base font-semibold tabular-nums text-text-1"
        />
        <span className="text-sm text-text-3">{u.suffix}</span>
      </div>
      <Slider
        aria-label={meta.label}
        min={b.min}
        max={Math.max(sliderMax, value)}
        step={b.step}
        value={value}
        onValueChange={(v) => onChange(Array.isArray(v) ? v[0] : (v as number))}
      />
      <p className="text-xs leading-relaxed text-text-3">
        {edited ? "Valor ajustado na tela. " : null}
        {meta.source}
      </p>
    </div>
  )
}
