"use client"

import { Check, ChevronDown, Hash, Loader2, UserRoundCheck } from "lucide-react"
import { useRouter } from "next/navigation"
import { Fragment, useState } from "react"
import { toast } from "sonner"

import { ApiFailure, errorMessage, postJson } from "@/components/console/api"
import { CategoryChip } from "@/components/console/category"
import { DemoResetButton } from "@/components/console/demo-reset-button"
import type { InboxItem } from "@/components/console/types"
import { Button } from "@/components/ui/button"
import { fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

type Filter = "tickets" | "sistema"

const KIND_LABEL: Record<InboxItem["kind"], string> = {
  level3_alert: "Somente humano",
  heartbeat_failure: "Heartbeat",
  usage_alert: "Uso do app",
}

/** Console › Caixa (PRD §4.6): alertas com o texto exato que iria para o Slack. Sem dourado nesta tela. */
export function InboxView({ items, initialId }: { items: InboxItem[]; initialId: number | null }) {
  const initial = items.find((i) => i.id === initialId)
  const [filter, setFilter] = useState<Filter>(initial && initial.kind !== "level3_alert" ? "sistema" : "tickets")
  const tickets = items.filter((i) => i.kind === "level3_alert")
  const system = items.filter((i) => i.kind !== "level3_alert")
  const list = filter === "tickets" ? tickets : system
  const unread = (arr: InboxItem[]) => arr.filter((i) => !i.read_at).length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div role="tablist" aria-label="Tipo de alerta" className="inline-flex rounded-full border border-border bg-surface p-1">
          {(
            [
              ["tickets", "Tickets", unread(tickets)],
              ["sistema", "Sistema", unread(system)],
            ] as const
          ).map(([value, label, n]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={filter === value}
              onClick={() => setFilter(value)}
              className={cn("rounded-full px-3.5 py-1.5 text-sm font-medium transition-all", filter === value ? "bg-text-1 text-bg" : "text-text-3 hover:text-text-1")}
            >
              {label}
              {n ? <span className="ml-1.5 font-mono text-xs opacity-80">{n}</span> : null}
            </button>
          ))}
        </div>
        <DemoResetButton />
      </div>
      <p className="text-sm text-text-2">
        {filter === "tickets"
          ? "Tickets que a IA encaminhou para uma pessoa: categoria sensível, termo de risco ou confiança baixa. A IA resumiu e avisou o time, sem responder ao cliente."
          : "Alertas do sistema: falha no heartbeat diário do banco e sinais do monitoramento de uso."}
      </p>
      {list.length ? (
        <ul className="grid gap-4 lg:grid-cols-2">
          {list.map((item) => (
            <InboxCard key={item.id} item={item} highlight={item.id === initialId} />
          ))}
        </ul>
      ) : (
        <div className="rounded-xl border border-dashed border-border p-6 text-sm text-text-2">
          {filter === "tickets" ? "Nenhum alerta de ticket. Uma triagem que caia em Somente humano aparece aqui." : "Nenhum alerta do sistema."}
        </div>
      )}
    </div>
  )
}

function InboxCard({ item, highlight }: { item: InboxItem; highlight: boolean }) {
  const router = useRouter()
  const [busy, setBusy] = useState<null | "read" | "assign">(null)
  const [showSlack, setShowSlack] = useState(highlight)

  async function act(action: "read" | "assign") {
    setBusy(action)
    try {
      await postJson("/api/inbox", { id: item.id, action })
      toast.success(action === "assign" ? "Alerta assumido por você (visitante)." : "Marcado como lido.")
      router.refresh()
    } catch (err) {
      toast.error(errorMessage(err))
      if (err instanceof ApiFailure && err.status === 409) router.refresh()
    } finally {
      setBusy(null)
    }
  }

  return (
    <li
      id={`alerta-${item.id}`}
      className={cn("flex flex-col gap-3 rounded-xl border bg-surface p-5 shadow-soft", highlight ? "border-text-3" : "border-border", item.read_at && "bg-surface/70")}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 text-xs font-medium text-text-3">
          {!item.read_at ? <span className="size-2 rounded-full bg-text-1" aria-label="não lido" /> : null}
          {KIND_LABEL[item.kind]}
          {item.triage_run_id ? <span className="font-mono">· triagem #{item.triage_run_id}</span> : null}
        </span>
        <span className="font-mono text-xs text-text-3">{fmt.relative(item.created_at)}</span>
      </div>
      <h3 className={cn("text-base leading-snug text-text-1", item.read_at ? "font-medium" : "font-semibold")}>{item.title}</h3>
      {item.category ? <CategoryChip category={item.category} /> : null}
      {item.summary ? <p className="text-sm leading-relaxed text-text-2">{item.summary}</p> : null}
      {item.risk_signals.length ? (
        <ul className="flex flex-wrap gap-1.5" aria-label="Sinais de risco">
          {item.risk_signals.map((s) => (
            <li key={s} className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2">
              {s}
            </li>
          ))}
        </ul>
      ) : null}
      {item.suggested_owner ? <p className="text-xs text-text-3">Time sugerido: {item.suggested_owner}</p> : null}
      {item.ticket_text ? (
        <details className="group">
          <summary className="flex cursor-pointer list-none items-center gap-1 text-xs font-medium text-text-3 hover:text-text-1 [&::-webkit-details-marker]:hidden">
            Ticket original
            <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" aria-hidden />
          </summary>
          <p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-line rounded-lg bg-surface-2 p-3 font-mono text-xs leading-relaxed text-text-1">{item.ticket_text}</p>
        </details>
      ) : null}

      <div className="border-t border-border pt-3">
        <button
          type="button"
          onClick={() => setShowSlack((v) => !v)}
          aria-expanded={showSlack}
          className="inline-flex items-center gap-1 text-xs font-medium text-text-2 hover:text-text-1"
        >
          <ChevronDown className={cn("size-3.5 transition-transform", showSlack && "rotate-180")} aria-hidden />
          {showSlack ? "Ocultar mensagem do Slack" : "Ver mensagem do Slack"}
        </button>
        {showSlack ? <SlackPreview body={item.body} createdAt={item.created_at} /> : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {item.assigned_to ? (
          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-text-1">
            <UserRoundCheck className="size-4" aria-hidden />
            Assumido por {item.assigned_to}
            {item.assigned_at ? <span className="font-mono text-xs font-normal text-text-3">· {fmt.relative(item.assigned_at)}</span> : null}
          </span>
        ) : (
          <Button size="sm" onClick={() => act("assign")} disabled={Boolean(busy)} className="h-8 px-3">
            {busy === "assign" ? <Loader2 className="animate-spin" aria-hidden /> : <UserRoundCheck aria-hidden />}
            Assumir
          </Button>
        )}
        {!item.read_at ? (
          <Button variant="ghost" size="sm" onClick={() => act("read")} disabled={Boolean(busy)} className="h-8 px-3">
            {busy === "read" ? <Loader2 className="animate-spin" aria-hidden /> : <Check aria-hidden />}
            Marcar como lida
          </Button>
        ) : (
          <span className="text-xs text-text-3">lida</span>
        )}
      </div>
    </li>
  )
}

const EMOJI: Record<string, string> = { rotating_light: "🚨", warning: "⚠️", red_circle: "🔴", white_check_mark: "✅", bell: "🔔" }

/** Renderiza o mrkdwn do Slack (*negrito* e :emoji:) a partir do texto exato gravado em notifications.body. */
function SlackPreview({ body, createdAt }: { body: string; createdAt: string }) {
  const time = new Date(createdAt).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-border">
      <div className="flex items-center gap-1.5 border-b border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text-2">
        <Hash className="size-3.5" aria-hidden />
        suporte-alertas
      </div>
      <div className="flex gap-3 p-3">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-text-1 font-mono text-xs font-semibold text-bg" aria-hidden>
          n8n
        </span>
        <div className="min-w-0 text-sm leading-relaxed text-text-1">
          <p className="text-xs">
            <span className="font-semibold">Triagem Inteligente</span> <span className="rounded bg-surface-2 px-1 text-[10px] text-text-3">APP</span>{" "}
            <span className="text-text-3">{time}</span>
          </p>
          <div className="mt-1 break-words">
            {body.split("\n").map((line, i) => (
              <p key={i}>{renderMrkdwn(line)}</p>
            ))}
          </div>
        </div>
      </div>
      <p className="border-t border-border px-3 py-2 text-xs text-text-3">No ambiente real, enviado pelo nó Slack do n8n.</p>
      <details className="border-t border-border px-3 py-2">
        <summary className="cursor-pointer text-xs text-text-3 hover:text-text-1">Texto bruto (mrkdwn)</summary>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-text-2">{body}</pre>
      </details>
    </div>
  )
}

function renderMrkdwn(line: string) {
  const withEmoji = line.replace(/:([a-z0-9_+-]+):/g, (m, name: string) => EMOJI[name] ?? m)
  return withEmoji.split(/(\*[^*\n]+\*)/g).map((part, i) =>
    part.startsWith("*") && part.endsWith("*") && part.length > 2 ? <strong key={i}>{part.slice(1, -1)}</strong> : <Fragment key={i}>{part}</Fragment>,
  )
}
