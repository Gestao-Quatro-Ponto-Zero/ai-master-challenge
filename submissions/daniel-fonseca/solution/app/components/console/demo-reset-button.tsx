"use client"

import { Loader2, RefreshCcw } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"

import { errorMessage, postJson } from "@/components/console/api"
import { Button } from "@/components/ui/button"

/** Restaurar demonstração (PRD §8): cria itens novos na fila e na caixa quando faltam pendentes. Não apaga nada. */
export function DemoResetButton({ className }: { className?: string }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)

  async function reset() {
    setBusy(true)
    try {
      const res = await postJson<{ created: number; message: string }>("/api/demo/reset", {})
      if (res.created) toast.success(`Demonstração restaurada: ${res.message}`)
      else toast.message(res.message)
      router.refresh()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={reset} disabled={busy} className={className}>
      {busy ? <Loader2 className="animate-spin" aria-hidden /> : <RefreshCcw aria-hidden />}
      {busy ? "Restaurando…" : "Restaurar demonstração"}
    </Button>
  )
}
