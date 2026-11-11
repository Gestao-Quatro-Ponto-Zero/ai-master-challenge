import type { Category } from "@/lib/types"
import { cn } from "@/lib/utils"

/** Cor de cada categoria (tokens --cat-*, PRD §6). O rótulo vai sempre escrito ao lado. */
export const CATEGORY_BG: Record<Category, string> = {
  Hardware: "bg-cat-hardware",
  "HR Support": "bg-cat-hr",
  Access: "bg-cat-access",
  Miscellaneous: "bg-cat-misc",
  Storage: "bg-cat-storage",
  Purchase: "bg-cat-purchase",
  "Internal Project": "bg-cat-project",
  "Administrative rights": "bg-cat-admin",
}

export function CategoryChip({ category, className }: { category: Category; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-sm font-medium text-text-1", className)}>
      <span className={cn("size-2.5 shrink-0 rounded-full", CATEGORY_BG[category] ?? "bg-text-3")} aria-hidden />
      {category}
    </span>
  )
}

/** Barra de confiança (0–1) em navy/texto, sem dourado. */
export function ConfidenceBar({ value, className }: { value: number; className?: string }) {
  const pct = Math.max(0, Math.min(1, value))
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-surface-2", className)} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pct * 100)} aria-label="Confiança">
      <div className="h-full rounded-full bg-text-1" style={{ width: `${pct * 100}%` }} />
    </div>
  )
}
