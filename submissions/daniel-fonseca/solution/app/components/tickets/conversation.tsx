"use client"

import { ArrowLeft, Bot, Check, ChevronDown, Loader2, Lock, Send, Sparkles, UserRound, X } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { CATEGORY_BG, CategoryChip, ConfidenceBar } from "@/components/console/category"
import type { NeighborTicket } from "@/components/console/types"
import { PathBadge } from "@/components/shared/path-badge"
import type { TicketItem } from "@/components/tickets/types"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { fmt } from "@/lib/format"
import { pathFromLevel } from "@/lib/paths"
import { CATEGORIES, type Category } from "@/lib/types"
import { cn } from "@/lib/utils"

const CATEGORY_ITEMS = CATEGORIES.map((c) => ({ value: c, label: c }))
const time = (iso: string) => new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })

export interface ConversationActions {
  decide: (t: TicketItem, decision: "approve" | "edit" | "reject", finalText: string | null, category: Category | null) => Promise<boolean>
  reply: (t: TicketItem, text: string) => Promise<boolean>
  tryNeighbor: (n: NeighborTicket) => void
}

/** Ticket em triagem: a mensagem do cliente e as etapas, até a resposta do fluxo. */
export function PendingConversation({ text, onBack }: { text: string; onBack: () => void }) {
  return (
    <Shell onBack={onBack} header={<span className="inline-flex items-center gap-2 text-sm font-medium text-text-2"><Loader2 className="size-4 animate-spin" aria-hidden /> Triando…</span>}>
      <CustomerBubble text={text} at={new Date().toISOString()} />
      <SystemCard>
        <p className="flex items-center gap-2 text-sm text-text-2">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Embedding do ticket, busca dos 50 casos mais parecidos, regra de decisão e redação. Leva alguns segundos.
        </p>
      </SystemCard>
    </Shell>
  )
}

export function Conversation({
  ticket,
  edited,
  canWrite,
  neighbor,
  actions,
  onBack,
}: {
  ticket: TicketItem
  edited: number | null
  canWrite: boolean
  neighbor: NeighborTicket | null
  actions: ConversationActions
  onBack: () => void
}) {
  const path = pathFromLevel(ticket.level)
  const pendingDraft = ticket.level === 2 && ticket.draft?.status === "pending" && !ticket.human_reply
  const composer = canWrite && !ticket.human_reply && (pendingDraft || ticket.level === 3)

  return (
    <Shell
      onBack={onBack}
      scrollKey={`${ticket.id}-${ticket.draft?.status ?? ""}-${ticket.human_reply ? 1 : 0}`}
      header={
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5">
          <PathBadge path={path} size="sm" />
          {ticket.category ? <CategoryChip category={ticket.category} /> : null}
          <span className="font-mono text-xs text-text-3">triagem #{ticket.id > 0 ? ticket.id : "offline"}</span>
          {ticket.true_category ? (
            <span className="text-xs text-text-3">
              Categoria real: {ticket.true_category} {ticket.true_category === ticket.category ? "✓" : "✗"}
            </span>
          ) : null}
          {edited ? <span className="rounded-full border border-border px-2 py-0.5 text-[11px] text-text-3">editado do ticket real #{edited}</span> : null}
        </div>
      }
      footer={composer ? <Composer ticket={ticket} onSend={(text) => actions.reply(ticket, text)} /> : null}
    >
      <CustomerBubble text={ticket.ticket_text} at={ticket.created_at} />
      <TriageDetails ticket={ticket} />

      {ticket.level === 1 && ticket.response_text ? (
        <OutBubble who="ai" label="Agente de IA · resposta automática" at={ticket.created_at} text={ticket.response_text} note="Enviada ao cliente. Adaptada de uma solução validada por humanos." />
      ) : null}

      {ticket.level === 2 && ticket.draft ? <DraftBlock ticket={ticket} canWrite={canWrite} actions={actions} neighbor={neighbor} /> : null}

      {ticket.level === 3 && ticket.human_summary ? (
        <SystemCard>
          <p className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">
            <Lock className="size-3.5" aria-hidden /> Nota interna · só para a equipe
          </p>
          <p className="text-sm leading-relaxed text-text-1">{ticket.human_summary.summary}</p>
          {ticket.human_summary.risk_signals.length ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ticket.human_summary.risk_signals.map((r) => (
                <span key={r} className="rounded-full border border-alert/40 px-2 py-0.5 text-xs text-text-2">
                  {r}
                </span>
              ))}
            </div>
          ) : null}
          {ticket.human_summary.suggested_owner ? <p className="mt-3 text-xs text-text-3">Time sugerido: {ticket.human_summary.suggested_owner}</p> : null}
          <p className="mt-3 text-xs text-text-3">A IA não respondeu ao cliente. O aviso foi para o Slack (simulado).</p>
        </SystemCard>
      ) : null}

      {ticket.human_reply ? (
        <OutBubble
          who="human"
          label="Atendente"
          at={ticket.human_reply_at ?? ticket.created_at}
          text={ticket.human_reply}
          note={ticket.level === 2 ? "Resposta do atendente. O rascunho da IA foi recusado e não entra na base de conhecimento." : "Resposta do atendente."}
        />
      ) : null}

      {!canWrite && (pendingDraft || (ticket.level === 3 && !ticket.human_reply)) ? (
        <p className="text-center text-xs text-text-3">Ticket offline: a triagem rodou só no banco, sem registro. Envie de novo quando o fluxo voltar.</p>
      ) : null}
    </Shell>
  )
}

function Shell({ header, footer, onBack, scrollKey, children }: { header: React.ReactNode; footer?: React.ReactNode; onBack: () => void; scrollKey?: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  // abre e acompanha a conversa pela última mensagem, como num chat
  useEffect(() => {
    const el = ref.current
    if (el) el.scrollTop = el.scrollHeight
  }, [scrollKey])
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <button type="button" onClick={onBack} aria-label="Voltar para a lista" className="-ml-1 rounded-full p-1.5 text-text-2 hover:bg-surface-2 md:hidden">
          <ArrowLeft className="size-5" aria-hidden />
        </button>
        {header}
      </div>
      <div ref={ref} className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto bg-surface-2/30 p-4 sm:p-6">{children}</div>
      {footer}
    </div>
  )
}

function CustomerBubble({ text, at }: { text: string; at: string }) {
  return (
    <div className="flex max-w-[85%] flex-col gap-1 self-start">
      <span className="flex items-center gap-1.5 text-xs text-text-3">
        <UserRound className="size-3.5" aria-hidden /> Cliente · {time(at)}
      </span>
      <div className="rounded-2xl rounded-tl-sm border border-border bg-surface px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-text-1 shadow-soft">{text}</div>
    </div>
  )
}

function OutBubble({ who, label, at, text, note, dashed }: { who: "ai" | "human"; label: string; at: string; text: string; note?: string; dashed?: boolean }) {
  const Icon = who === "ai" ? Bot : UserRound
  return (
    <div className="flex max-w-[85%] flex-col items-end gap-1 self-end">
      <span className="flex items-center gap-1.5 text-xs text-text-3">
        <Icon className="size-3.5" aria-hidden /> {label} · {time(at)}
      </span>
      <div
        className={cn(
          "rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
          dashed ? "border border-dashed border-path-review bg-surface text-text-1" : "bg-navy-600 text-white dark:bg-surface dark:text-text-1 dark:border dark:border-border",
        )}
      >
        {text}
      </div>
      {note ? <span className="text-right text-xs text-text-3">{note}</span> : null}
    </div>
  )
}

function SystemCard({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-2xl rounded-xl border border-border bg-surface p-4">{children}</div>
}

/** "Detalhes da triagem": motivo, votos, casos parecidos, tempos, tokens e custo (recolhível). */
function TriageDetails({ ticket }: { ticket: TicketItem }) {
  const [open, setOpen] = useState(false)
  const votes = Object.entries(ticket.votes ?? {})
    .map(([c, v]) => [c as Category, Number(v)] as const)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
  const total = Object.values(ticket.votes ?? {}).reduce((a, b) => a + Number(b), 0) || 1
  return (
    <div className="mx-auto w-full max-w-2xl rounded-xl border border-border bg-surface">
      <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} className="flex w-full items-center gap-2 px-4 py-3 text-left">
        <Sparkles className="size-4 shrink-0 text-text-3" aria-hidden />
        <span className="min-w-0 flex-1 text-sm text-text-2">
          <span className="font-medium text-text-1">Detalhes da triagem</span>
          {ticket.level_reason ? <span className="text-text-3"> · {ticket.level_reason}</span> : null}
        </span>
        <ChevronDown className={cn("size-4 shrink-0 text-text-3 transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      {open ? (
        <div className="flex flex-col gap-5 border-t border-border px-4 py-4">
          {ticket.category && ticket.confidence != null ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-2">
                <CategoryChip category={ticket.category} />
                <span className="text-sm font-semibold tabular-nums text-text-1">confiança {fmt.dec(ticket.confidence, 2)}</span>
              </div>
              <ConfidenceBar value={ticket.confidence} />
            </div>
          ) : null}
          {votes.length ? (
            <div className="flex flex-col gap-1.5">
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">Votos dos 50 casos mais parecidos (peso pela similaridade)</p>
              {votes.map(([c, v]) => (
                <div key={c} className="grid grid-cols-[140px_1fr_44px] items-center gap-2 text-xs">
                  <span className="truncate text-text-2">{c}</span>
                  <span className="h-2 overflow-hidden rounded-full bg-surface-2">
                    <span className={cn("block h-full rounded-full", CATEGORY_BG[c] ?? "bg-text-3")} style={{ width: `${(v / total) * 100}%` }} />
                  </span>
                  <span className="text-right tabular-nums text-text-2">{fmt.pct(v / total, 0)}</span>
                </div>
              ))}
            </div>
          ) : null}
          {ticket.similar_cases.length ? (
            <div className="flex flex-col gap-2">
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">Os 5 casos mais parecidos</p>
              <ul className="flex flex-col gap-2">
                {ticket.similar_cases.map((c) => (
                  <li key={c.id} className="rounded-lg bg-surface-2/60 px-3 py-2">
                    <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                      <CategoryChip category={c.category} className="text-xs" />
                      <span className="tabular-nums text-text-3">similaridade {fmt.dec(c.similarity, 2)}</span>
                    </div>
                    <p className="line-clamp-2 text-xs leading-relaxed text-text-2">{c.snippet}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <dl className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
            <Stat label="Classificação" value={ticket.step_ms?.classificacao != null ? fmt.ms(ticket.step_ms.classificacao) : ticket.id < 0 ? "no banco" : "—"} />
            <Stat label="Redação (LLM)" value={ticket.step_ms?.redacao != null ? fmt.ms(ticket.step_ms.redacao) : ticket.id < 0 ? "não executada" : "—"} />
            <Stat label="Tokens" value={ticket.tokens_in != null ? `${fmt.int(ticket.tokens_in)} + ${fmt.int(ticket.tokens_out ?? 0)}` : "—"} />
            <Stat label="Custo OpenAI" value={ticket.cost_usd != null ? fmt.usd(ticket.cost_usd, 4) : "—"} />
          </dl>
        </div>
      ) : null}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-text-3">{label}</dt>
      <dd className="font-mono tabular-nums text-text-1">{value}</dd>
    </div>
  )
}

/** Revisão humana: o rascunho da IA para validar (Aprovar · Editar e aprovar · Rejeitar). */
function DraftBlock({ ticket, canWrite, actions, neighbor }: { ticket: TicketItem; canWrite: boolean; actions: ConversationActions; neighbor: NeighborTicket | null }) {
  const d = ticket.draft!
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(d.draft_text)
  const [category, setCategory] = useState<Category | null>(ticket.category)
  const [busy, setBusy] = useState<string | null>(null)

  async function run(decision: "approve" | "edit" | "reject") {
    setBusy(decision)
    const finalCat = category && category !== ticket.category ? category : null
    const ok = await actions.decide(ticket, decision, decision === "edit" ? text.trim() : null, finalCat)
    setBusy(null)
    if (ok) setEditing(false)
  }

  if (d.status !== "pending") {
    if (d.status === "rejected") {
      return ticket.human_reply ? null : <p className="text-center text-xs text-text-3">Rascunho da IA rejeitado pelo atendente. O ticket volta para atendimento manual.</p>
    }
    return (
      <>
        <OutBubble
          who="human"
          label={d.status === "edited" ? "Atendente · editado e aprovado" : "Atendente · aprovado"}
          at={d.decided_at ?? ticket.created_at}
          text={d.final_text ?? d.draft_text}
          note={`Enviada ao cliente. A solução entrou na base de conhecimento${d.final_category && d.final_category !== ticket.category ? ` como ${d.final_category}` : ""}.`}
        />
        {neighbor ? (
          <div className="mx-auto w-full max-w-2xl rounded-xl border border-ok/40 bg-surface p-4">
            <p className="text-sm font-medium text-text-1">Esta solução agora atende tickets parecidos.</p>
            <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-text-2">
              Ticket real #{neighbor.id} (similaridade {fmt.dec(neighbor.similarity, 2)}): “{neighbor.excerpt}”
            </p>
            <Button size="sm" variant="outline" className="mt-3" onClick={() => actions.tryNeighbor(neighbor)}>
              Testar com este ticket
            </Button>
          </div>
        ) : null}
      </>
    )
  }

  return (
    <div className="flex max-w-[85%] flex-col items-end gap-2 self-end">
      <span className="flex items-center gap-1.5 text-xs text-text-3">
        <Bot className="size-3.5" aria-hidden /> Agente de IA · rascunho aguardando validação
      </span>
      {editing ? (
        <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} maxLength={4000} className="w-[min(36rem,80vw)] bg-surface" aria-label="Editar o rascunho" />
      ) : (
        <div className="rounded-2xl rounded-tr-sm border border-dashed border-path-review bg-surface px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-text-1">{d.draft_text}</div>
      )}
      {d.checks.length ? (
        <div className="w-full rounded-xl border border-border bg-surface p-3">
          <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">Antes de aprovar, confira</p>
          <ul className="space-y-1 text-xs leading-relaxed text-text-2">
            {d.checks.map((c) => (
              <li key={c} className="flex gap-2">
                <Check className="mt-0.5 size-3.5 shrink-0 text-text-3" aria-hidden />
                {c}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {canWrite ? (
        <div className="flex w-full flex-wrap items-center justify-end gap-2">
          <Select items={CATEGORY_ITEMS} value={category ?? undefined} onValueChange={(v) => v && setCategory(v as Category)}>
            <SelectTrigger className="h-8 w-48" aria-label="Corrigir a categoria">
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
          <Button size="sm" variant="ghost" onClick={() => run("reject")} disabled={Boolean(busy)}>
            {busy === "reject" ? <Loader2 className="animate-spin" aria-hidden /> : <X aria-hidden />} Rejeitar
          </Button>
          {editing ? (
            <Button size="sm" variant="outline" onClick={() => run("edit")} disabled={Boolean(busy) || text.trim().length < 2}>
              {busy === "edit" ? <Loader2 className="animate-spin" aria-hidden /> : <Check aria-hidden />} Salvar e aprovar
            </Button>
          ) : (
            <Button size="sm" variant="outline" onClick={() => setEditing(true)} disabled={Boolean(busy)}>
              Editar
            </Button>
          )}
          <Button size="sm" onClick={() => run("approve")} disabled={Boolean(busy) || editing}>
            {busy === "approve" ? <Loader2 className="animate-spin" aria-hidden /> : <Check aria-hidden />} Aprovar
          </Button>
        </div>
      ) : null}
    </div>
  )
}

/** Campo do atendente (Revisão humana e Somente humano). Na Revisão humana, enviar recusa o rascunho. */
function Composer({ ticket, onSend }: { ticket: TicketItem; onSend: (text: string) => Promise<boolean> }) {
  const [text, setText] = useState("")
  const [busy, setBusy] = useState(false)
  async function send() {
    if (text.trim().length < 2) return
    setBusy(true)
    const ok = await onSend(text.trim())
    setBusy(false)
    if (ok) setText("")
  }
  return (
    <div className="border-t border-border bg-surface p-3">
      <div className="flex items-end gap-2">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send()
          }}
          rows={2}
          maxLength={4000}
          placeholder={ticket.level === 2 ? "Escreva a resposta do atendente. Ao enviar, o rascunho da IA conta como recusado." : "Escreva a resposta do atendente ao cliente."}
          aria-label="Resposta do atendente"
          className="min-h-11 flex-1 resize-none"
        />
        <Button onClick={send} disabled={busy || text.trim().length < 2} aria-label="Enviar resposta" className="h-11">
          {busy ? <Loader2 className="animate-spin" aria-hidden /> : <Send aria-hidden />}
          <span className="hidden sm:inline">Enviar</span>
        </Button>
      </div>
    </div>
  )
}
