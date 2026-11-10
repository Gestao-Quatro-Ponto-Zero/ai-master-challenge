"use client"

import { Loader2, Shuffle } from "lucide-react"
import { useState } from "react"

import { errorMessage, getJson } from "@/components/console/api"
import type { HoldoutTicket } from "@/components/console/types"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { CATEGORIES } from "@/lib/types"

const ALL = "todas"
const CATEGORY_ITEMS = [{ value: ALL, label: "Qualquer categoria" }, ...CATEGORIES.map((c) => ({ value: c, label: c }))]
const MIN = 15
const MAX = 4000

export type NewTicket = { mode: "holdout"; ds2_id: number; ticket_text: string } | { mode: "free_text"; ticket_text: string; edited_from?: number }

/**
 * "Adicionar ticket" (ADR-0015): sortear um ticket real do holdout ou escrever um, em inglês.
 * O ticket sorteado e editado vira texto livre, com a marca "editado".
 */
export function AddTicketDialog({
  open,
  onOpenChange,
  initial,
  freeTextEnabled,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  initial: HoldoutTicket | null
  freeTextEnabled: boolean
  onSubmit: (t: NewTicket) => void
}) {
  // o pai troca a key a cada abertura, então o estado começa de novo a partir de `initial`
  const [sample, setSample] = useState<HoldoutTicket | null>(initial)
  const [text, setText] = useState(initial?.document ?? "")
  const [category, setCategory] = useState<string>(ALL)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function draw() {
    setLoading(true)
    setError(null)
    try {
      const qs = category !== ALL ? `?categoria=${encodeURIComponent(category)}` : ""
      const t = await getJson<HoldoutTicket>(`/api/triage/sample${qs}`)
      setSample(t)
      setText(t.document)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const trimmed = text.trim()
  const edited = Boolean(sample) && trimmed !== sample!.document.trim()
  const asHoldout = Boolean(sample) && !edited
  const canSend = asHoldout || (freeTextEnabled && trimmed.length >= MIN && trimmed.length <= MAX)

  function send() {
    if (!canSend) return
    if (asHoldout) onSubmit({ mode: "holdout", ds2_id: sample!.id, ticket_text: sample!.document })
    else onSubmit({ mode: "free_text", ticket_text: trimmed, ...(sample ? { edited_from: sample.id } : {}) })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Adicionar ticket</DialogTitle>
          <DialogDescription>
            Sorteie um ticket real do conjunto de teste (que o modelo não viu) ou escreva um em inglês, a língua da base. A triagem decide o caminho em poucos segundos.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Select items={CATEGORY_ITEMS} value={category} onValueChange={(v) => v && setCategory(v)}>
              <SelectTrigger className="h-9 w-full sm:w-56" aria-label="Categoria real do ticket sorteado">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORY_ITEMS.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={draw} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" aria-hidden /> : <Shuffle aria-hidden />}
              Sortear ticket real
            </Button>
          </div>

          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            readOnly={!freeTextEnabled}
            maxLength={MAX}
            rows={7}
            className="min-h-36"
            placeholder={freeTextEnabled ? "Escreva o ticket em inglês, por exemplo: My laptop screen keeps flickering after the last update." : "Sorteie um ticket real para começar."}
            aria-label="Texto do ticket"
          />
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-text-3">
            <span>
              {sample && !edited ? `Ticket real #${sample.id}. A categoria real aparece depois da triagem.` : null}
              {edited ? `Editado a partir do ticket real #${sample!.id}: vai como texto livre, sem conferência da categoria real.` : null}
              {!sample && freeTextEnabled ? `Texto livre, entre ${MIN} e ${MAX.toLocaleString("pt-BR")} caracteres.` : null}
              {!freeTextEnabled ? "O texto livre está pausado no momento; o sorteio funciona normalmente." : null}
            </span>
            {freeTextEnabled ? <span className="tabular-nums">{text.length.toLocaleString("pt-BR")}/{MAX.toLocaleString("pt-BR")}</span> : null}
          </div>
          {error ? <p className="text-sm text-alert">{error}</p> : null}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={send} disabled={!canSend}>
            Enviar para a triagem
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
