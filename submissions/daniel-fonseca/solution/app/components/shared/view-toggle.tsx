"use client"

import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useTransition } from "react"

import { cn } from "@/lib/utils"

export interface ViewOption<V extends string = string> {
  value: V
  label: string
}

/**
 * Toggle interno de cada área (controle segmentado menor, alinhado à esquerda). O estado fica na URL
 * (?visao=, ?aba=, ?secao=) para permitir links diretos (PRD §3). Precisa estar dentro de <Suspense>.
 */
export function ViewToggle<V extends string>({ param, options, defaultValue, label }: { param: string; options: ViewOption<V>[]; defaultValue: V; label: string }) {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()
  const [pending, startTransition] = useTransition()
  const current = (params.get(param) as V | null) ?? defaultValue

  function select(value: V) {
    const next = new URLSearchParams(params.toString())
    if (value === defaultValue) next.delete(param)
    else next.set(param, value)
    const qs = next.toString()
    startTransition(() => router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false }))
  }

  return (
    <div role="tablist" aria-label={label} className={cn("inline-flex w-fit max-w-full self-start overflow-x-auto rounded-full border border-border bg-surface p-1", pending && "opacity-80")}>
      {options.map((o) => {
        const active = o.value === current
        return (
          <button
            key={o.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => select(o.value)}
            className={cn(
              "shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium transition-all",
              active ? "bg-text-1 text-bg" : "text-text-3 hover:text-text-1",
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

/** Fallback do toggle enquanto a URL carrega (mesmo tamanho, sem salto de layout). */
export function ViewToggleFallback({ options }: { options: ViewOption[] }) {
  return (
    <div className="inline-flex w-fit max-w-full self-start overflow-x-auto rounded-full border border-border bg-surface p-1">
      {options.map((o, i) => (
        <span key={o.value} className={cn("rounded-full px-3.5 py-1.5 text-sm font-medium", i === 0 ? "bg-text-1 text-bg" : "text-text-3")}>
          {o.label}
        </span>
      ))}
    </div>
  )
}
