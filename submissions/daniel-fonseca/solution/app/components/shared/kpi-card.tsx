import { OriginPill } from "@/components/shared/origin-pill"
import type { DataOrigin } from "@/lib/types"
import { cn } from "@/lib/utils"

/**
 * Card de indicador. `protagonist` = o único número dourado da tela (regra Órbita).
 */
export function KpiCard({
  label,
  value,
  hint,
  origin,
  originHref,
  protagonist = false,
  className,
}: {
  label: string
  value: React.ReactNode
  hint?: React.ReactNode
  origin?: DataOrigin
  originHref?: string
  protagonist?: boolean
  className?: string
}) {
  return (
    <div className={cn("flex flex-col gap-2 rounded-xl border border-border bg-surface p-5 shadow-soft", className)}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-text-2">{label}</p>
        {origin ? <OriginPill origin={origin} href={originHref} /> : null}
      </div>
      <p className={cn("font-sans text-3xl font-semibold tracking-tight tabular-nums sm:text-4xl", protagonist ? "text-gold" : "text-text-1")}>{value}</p>
      {hint ? <p className="text-sm leading-relaxed text-text-3">{hint}</p> : null}
    </div>
  )
}
