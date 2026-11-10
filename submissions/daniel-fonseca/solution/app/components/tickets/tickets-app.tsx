"use client"

import { MessageSquareText } from "lucide-react"
import { useRouter, useSearchParams } from "next/navigation"
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { errorMessage, getJson, postJson } from "@/components/console/api"
import type { ConsoleTriageResult, HitlApiResult, HoldoutTicket, NeighborTicket } from "@/components/console/types"
import { AddTicketDialog, type NewTicket } from "@/components/tickets/add-ticket-dialog"
import { Conversation, PendingConversation } from "@/components/tickets/conversation"
import { SlackBubble, SlackToast } from "@/components/tickets/slack"
import { addMine, addSlack, getTicketsState, markRead, type SlackEntry, tokenFor, useTicketsStore } from "@/components/tickets/store"
import { FILTERS, type Filter, type PendingItem, TicketList } from "@/components/tickets/ticket-list"
import type { TicketItem } from "@/components/tickets/types"
import type { Category } from "@/lib/types"
import { cn } from "@/lib/utils"

type TriageResponse = ConsoleTriageResult & { client_token?: string; true_category?: Category | null }

/** Ticket offline (n8n fora do ar): existe só nesta aba, com id negativo. */
function offlineItem(r: TriageResponse, tempId: number): TicketItem {
  return {
    id: tempId,
    created_at: new Date().toISOString(),
    is_demo: false,
    ds2_id: r.ds2_id,
    true_category: r.true_category ?? null,
    ticket_text: r.ticket_text,
    status: r.status,
    level: r.level,
    level_reason: r.level_reason,
    category: r.category,
    confidence: r.confidence,
    votes: r.votes ?? {},
    similar_cases: r.similar_cases ?? [],
    response_text: null,
    draft: null,
    human_summary: null,
    alert: null,
    human_reply: null,
    human_reply_at: null,
    step_ms: null,
    tokens_in: null,
    tokens_out: null,
    cost_usd: null,
    latency_ms: null,
  }
}

/** Tela Tickets (ADR-0015): lista à esquerda, conversa à direita; no mobile, a conversa ocupa a tela. */
export function TicketsApp({ freeTextEnabled }: { freeTextEnabled: boolean }) {
  const router = useRouter()
  const params = useSearchParams()
  const store = useTicketsStore()
  const initialFilter = (FILTERS.find((f) => f.value === params.get("filtro"))?.value ?? "todas") as Filter

  const [tickets, setTickets] = useState<TicketItem[]>([])
  const [offline, setOffline] = useState<TicketItem[]>([])
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState<PendingItem[]>([])
  const [filter, setFilter] = useState<Filter>(initialFilter)
  const [selected, setSelected] = useState<number | null>(null)
  const [dialog, setDialog] = useState<{ open: boolean; initial: HoldoutTicket | null; n: number }>({ open: false, initial: null, n: 0 })
  const [neighbors, setNeighbors] = useState<Record<number, NeighborTicket>>({})
  const [toastEntry, setToastEntry] = useState<SlackEntry | null>(null)
  const [resetting, setResetting] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await postJson<{ tickets: TicketItem[] }>("/api/tickets", { tokens: getTicketsState().mine.map((m) => m.token) })
      setTickets(res.tickets)
      window.dispatchEvent(new Event("tickets-list-change"))
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // primeira carga: o setState acontece no retorno da requisição, fora do corpo do efeito
    const id = window.setTimeout(load, 0)
    return () => window.clearTimeout(id)
  }, [load])

  useEffect(() => {
    if (selected != null && selected > 0) markRead(selected)
  }, [selected])

  function changeFilter(f: Filter) {
    setFilter(f)
    const next = new URLSearchParams(params.toString())
    if (f === "todas") next.delete("filtro")
    else next.set("filtro", f)
    const qs = next.toString()
    router.replace(qs ? `/tickets?${qs}` : "/tickets", { scroll: false })
  }

  async function create(t: NewTicket) {
    const tempId = -Date.now()
    if (filter !== "todas") changeFilter("todas")
    setPending((p) => [{ tempId, text: t.ticket_text, at: new Date().toISOString() }, ...p])
    setSelected(tempId)
    try {
      const body = t.mode === "holdout" ? { mode: "holdout", ds2_id: t.ds2_id } : { mode: "free_text", ticket_text: t.ticket_text }
      const r = await postJson<TriageResponse>("/api/triage", body)
      if (r.triage_run_id && r.client_token) {
        addMine({ token: r.client_token, id: r.triage_run_id, at: new Date().toISOString(), ...(t.mode === "free_text" && t.edited_from ? { edited_from: t.edited_from } : {}) })
        if (r.level === 3 && r.alert) {
          const entry = { ticket_id: r.triage_run_id, title: r.alert.title, body: r.alert.body, at: new Date().toISOString() }
          addSlack(entry)
          setToastEntry({ ...entry, seen: false })
        }
        await load()
        setSelected(r.triage_run_id)
      } else {
        const item = offlineItem(r, tempId)
        setOffline((o) => [item, ...o])
        setSelected(tempId)
        toast.message("Fluxo de triagem fora do ar: a classificação rodou direto no banco, sem redação e sem registro.")
      }
    } catch (err) {
      toast.error(errorMessage(err))
      setSelected(null)
    } finally {
      setPending((p) => p.filter((x) => x.tempId !== tempId))
    }
  }

  async function decide(t: TicketItem, decision: "approve" | "edit" | "reject", finalText: string | null, category: Category | null) {
    try {
      const res = await postJson<HitlApiResult>("/api/hitl", {
        hitl_id: t.draft!.hitl_id,
        decision,
        ...(finalText ? { final_text: finalText } : {}),
        ...(category ? { final_category: category } : {}),
        client_token: tokenFor(getTicketsState(), t.id),
      })
      if (res.neighbor) setNeighbors((n) => ({ ...n, [t.id]: res.neighbor! }))
      toast.success(decision === "reject" ? "Rascunho rejeitado: o ticket volta para atendimento manual." : "Resposta aprovada e enviada ao cliente.")
      await load()
      return true
    } catch (err) {
      toast.error(errorMessage(err))
      await load()
      return false
    }
  }

  async function reply(t: TicketItem, text: string) {
    try {
      await postJson("/api/tickets/reply", { triage_run_id: t.id, client_token: tokenFor(getTicketsState(), t.id), text })
      toast.success(t.level === 2 ? "Resposta enviada. O rascunho da IA foi recusado." : "Resposta do atendente enviada.")
      await load()
      return true
    } catch (err) {
      toast.error(errorMessage(err))
      return false
    }
  }

  async function resetDemo() {
    setResetting(true)
    try {
      const res = await postJson<{ created: number; message: string }>("/api/demo/reset", {})
      if (res.created) toast.success(`Demonstração restaurada: ${res.message}`)
      else toast.message(res.message)
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setResetting(false)
    }
  }

  async function tryNeighbor(n: NeighborTicket) {
    try {
      const t = await getJson<HoldoutTicket>(`/api/triage/sample?id=${n.id}`)
      setDialog((d) => ({ open: true, initial: t, n: d.n + 1 }))
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const closeToast = useCallback(() => setToastEntry(null), [])

  function openTicket(id: number) {
    setToastEntry(null)
    setFilter("todas")
    setSelected(id)
  }

  const all = [...offline, ...tickets]
  const current = selected != null ? all.find((t) => t.id === selected) : undefined
  const currentPending = selected != null ? pending.find((p) => p.tempId === selected) : undefined
  const edited = (id: number) => store.mine.find((m) => m.id === id)?.edited_from ?? null
  const unread = (t: TicketItem) => t.id > 0 && t.id !== selected && !store.read.includes(t.id)
  const back = () => setSelected(null)

  return (
    <>
      <div className="grid h-[calc(100dvh-15rem)] min-h-[440px] overflow-hidden rounded-xl border border-border bg-surface shadow-soft md:h-[calc(100dvh-13rem)] md:grid-cols-[minmax(300px,380px)_1fr]">
        <div className="min-h-0 border-border md:border-r">
          <TicketList
            tickets={all}
            pending={pending}
            loading={loading}
            filter={filter}
            onFilter={changeFilter}
            selected={selected}
            onSelect={setSelected}
            unread={unread}
            edited={edited}
            onAdd={() => setDialog((d) => ({ open: true, initial: null, n: d.n + 1 }))}
            onReset={resetDemo}
            resetting={resetting}
          />
        </div>
        <div className={cn("min-h-0", selected != null ? "fixed inset-0 z-50 flex flex-col bg-surface md:static md:z-auto" : "hidden md:flex md:flex-col")}>
          {current ? (
            <Conversation
              key={current.id}
              ticket={current}
              edited={edited(current.id)}
              canWrite={current.id > 0}
              neighbor={neighbors[current.id] ?? null}
              actions={{ decide, reply, tryNeighbor }}
              onBack={back}
            />
          ) : currentPending ? (
            <PendingConversation text={currentPending.text} onBack={back} />
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
              <MessageSquareText className="size-8 text-text-3" aria-hidden />
              <p className="max-w-sm text-sm leading-relaxed text-text-2">
                Escolha um ticket para ver a conversa. Cada ticket mostra a mensagem do cliente e o que a triagem fez: resposta automática, rascunho para validar ou nota interna para o atendente.
              </p>
            </div>
          )}
        </div>
      </div>

      <AddTicketDialog key={dialog.n} open={dialog.open} onOpenChange={(open) => setDialog((d) => ({ ...d, open }))} initial={dialog.initial} freeTextEnabled={freeTextEnabled} onSubmit={create} />
      <SlackToast entry={toastEntry} onClose={closeToast} onOpen={openTicket} />
      <SlackBubble onOpen={openTicket} hideOnMobile={selected != null} />
    </>
  )
}
