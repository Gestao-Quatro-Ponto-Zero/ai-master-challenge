"use client"

import { RefreshCw } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTransition } from "react"

import { cn } from "@/lib/utils"

/** Recarrega os dados vivos da tela (router.refresh refaz o render no servidor). */
export function RefreshButton() {
  const router = useRouter()
  const [pending, start] = useTransition()
  return (
    <button
      type="button"
      onClick={() => start(() => router.refresh())}
      disabled={pending}
      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-text-2 hover:text-text-1 disabled:opacity-60"
    >
      <RefreshCw className={cn("size-4", pending && "animate-spin")} aria-hidden />
      {pending ? "Atualizando…" : "Atualizar"}
    </button>
  )
}
