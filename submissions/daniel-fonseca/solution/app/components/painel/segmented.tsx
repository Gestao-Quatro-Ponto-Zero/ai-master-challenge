"use client"

import { cn } from "@/lib/utils"

/** Seletor segmentado local (estado em memória), no estilo do toggle interno das áreas. */
export function Segmented<V extends string>({
  label,
  options,
  value,
  onChange,
  size = "sm",
}: {
  label: string
  options: { value: V; label: string }[]
  value: V
  onChange: (v: V) => void
  size?: "sm" | "xs"
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">{label}</span>
      <div role="radiogroup" aria-label={label} className="inline-flex w-fit max-w-full overflow-x-auto rounded-full border border-border bg-surface-2/60 p-0.5">
        {options.map((o) => {
          const active = o.value === value
          return (
            <button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange(o.value)}
              className={cn(
                "shrink-0 rounded-full font-medium transition-colors",
                size === "sm" ? "px-3 py-1 text-sm" : "px-2.5 py-0.5 text-xs",
                active ? "bg-surface text-text-1 shadow-soft" : "text-text-3 hover:text-text-1",
              )}
            >
              {o.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
