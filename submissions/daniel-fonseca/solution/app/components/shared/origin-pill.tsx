import type { DataOrigin } from "@/lib/types"
import { cn } from "@/lib/utils"

const LABEL: Record<DataOrigin, string> = {
  medido: "medido",
  benchmark: "benchmark com fonte",
  premissa: "premissa",
  calculo: "cálculo",
}

/** Origem de cada número (ADR-0003): pill pequena e neutra, com link opcional para a fonte. */
export function OriginPill({ origin, href, className }: { origin: DataOrigin; href?: string; className?: string }) {
  const cls = cn(
    "inline-flex items-center rounded-full border border-border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-text-3",
    href && "hover:text-text-1 hover:border-text-3",
    className,
  )
  return href ? (
    <a href={href} target="_blank" rel="noreferrer" className={cls}>
      {LABEL[origin]}
    </a>
  ) : (
    <span className={cls}>{LABEL[origin]}</span>
  )
}
