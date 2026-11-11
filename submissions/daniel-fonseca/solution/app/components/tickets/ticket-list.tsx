"use client"

import { Loader2, MoreHorizontal, Plus, RefreshCcw } from "lucide-react"
import { Popover } from "@base-ui/react/popover"

import { PathBadge } from "@/components/shared/path-badge"
import type { TicketItem } from "@/components/tickets/types"
import { Button } from "@/components/ui/button"
import { fmt } from "@/lib/format"
import { pathFromLevel } from "@/lib/paths"
import type { PathKey } from "@/lib/types"
import { cn } from "@/lib/utils"

export type Filter = "todas" | "auto" | "revisao" | "humano"
export const FILTERS: { value: Filter; label: string; path?: PathKey }[] = [
  { value: "todas", label: "Todas" },
  { value: "auto", label: "Resposta automática", path: "auto" },
  { value: "revisao", label: "Revisão humana", path: "review" },
  { value: "humano", label: "Somente humano", path: "human" },
]

export interface PendingItem {
  tempId: number
  text: string
  at: string
}

/** Estado curto do ticket, na linha da lista. */
function stateOf(t: TicketItem): string | null {
  if (t.human_reply) return "respondido pelo atendente"
  if (t.level === 2 && t.draft?.status === "pending") return "aguardando validação"
  if (t.level === 2 && t.draft) return t.draft.status === "rejected" ? "rascunho rejeitado" : "aprovado"
  if (t.level === 3) return "aguardando atendente"
  return null
}

export function TicketList({
  tickets,
  pending,
  loading,
  filter,
  onFilter,
  selected,
  onSelect,
  unread,
  edited,
  onAdd,
  onReset,
  resetting,
}: {
  tickets: TicketItem[]
  pending: PendingItem[]
  loading: boolean
  filter: Filter
  onFilter: (f: Filter) => void
  selected: number | null
  onSelect: (id: number) => void
  unread: (t: TicketItem) => boolean
  edited: (id: number) => number | null
  onAdd: () => void
  onReset: () => void
  resetting: boolean
}) {
  const path = FILTERS.find((f) => f.value === filter)?.path
  const shown = path ? tickets.filter((t) => pathFromLevel(t.level) === path) : tickets

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex flex-col gap-3 border-b border-border p-3">
        <div className="flex items-center gap-2">
          <Button onClick={onAdd} className="flex-1">
            <Plus aria-hidden /> Adicionar ticket
          </Button>
          <Popover.Root>
            <Popover.Trigger render={<Button variant="outline" size="icon" aria-label="Mais opções" />}>
              <MoreHorizontal aria-hidden />
            </Popover.Trigger>
            <Popover.Portal>
              <Popover.Positioner side="bottom" align="end" sideOffset={6} className="z-50">
                <Popover.Popup className="w-72 rounded-xl border border-border bg-surface p-1.5 shadow-soft outline-none">
                  <button type="button" onClick={onReset} disabled={resetting} className="flex w-full items-start gap-2 rounded-lg px-3 py-2.5 text-left hover:bg-surface-2 disabled:opacity-60">
                    {resetting ? <Loader2 className="mt-0.5 size-4 animate-spin" aria-hidden /> : <RefreshCcw className="mt-0.5 size-4 text-text-3" aria-hidden />}
                    <span className="flex flex-col gap-0.5">
                      <span className="text-sm font-medium text-text-1">Restaurar demonstração</span>
                      <span className="text-xs leading-snug text-text-3">Cria tickets de demonstração novos quando faltam rascunhos pendentes. Não apaga nada.</span>
                    </span>
                  </button>
                </Popover.Popup>
              </Popover.Positioner>
            </Popover.Portal>
          </Popover.Root>
        </div>
        <div role="radiogroup" aria-label="Filtrar por caminho" className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              role="radio"
              aria-checked={filter === f.value}
              onClick={() => onFilter(f.value)}
              className={cn(
                "shrink-0 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                filter === f.value ? "border-transparent bg-text-1 text-bg" : "border-border text-text-2 hover:text-text-1",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <ul className="min-h-0 flex-1 overflow-y-auto" aria-label="Tickets, do mais recente ao mais antigo">
        {pending.map((p) => (
          <li key={p.tempId}>
            <button type="button" onClick={() => onSelect(p.tempId)} className={cn("flex w-full flex-col gap-1.5 border-b border-border px-4 py-3 text-left", selected === p.tempId && "bg-surface-2")}>
              <span className="inline-flex items-center gap-2 text-xs font-medium text-text-2">
                <Loader2 className="size-3.5 animate-spin" aria-hidden /> Triando…
              </span>
              <span className="line-clamp-2 text-sm text-text-1">{p.text}</span>
            </button>
          </li>
        ))}
        {shown.map((t) => {
          const isUnread = unread(t)
          const state = stateOf(t)
          const ed = edited(t.id)
          return (
            <li key={t.id}>
              <button
                type="button"
                onClick={() => onSelect(t.id)}
                aria-current={selected === t.id ? "true" : undefined}
                className={cn("flex w-full flex-col gap-1.5 border-b border-border px-4 py-3 text-left transition-colors hover:bg-surface-2/60", selected === t.id && "bg-surface-2")}
              >
                <span className="flex items-center gap-2">
                  <PathBadge path={pathFromLevel(t.level)} size="sm" />
                  {isUnread ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-1">
                      <span className="size-2 rounded-full bg-alert" aria-hidden /> Não lido
                    </span>
                  ) : null}
                  <span className="ml-auto shrink-0 text-[11px] tabular-nums text-text-3">{fmt.relative(t.created_at)}</span>
                </span>
                <span className={cn("line-clamp-2 text-sm", isUnread ? "font-medium text-text-1" : "text-text-2")}>{t.ticket_text}</span>
                <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-text-3">
                  {t.category ? <span>{t.category}</span> : null}
                  {state ? <span>· {state}</span> : null}
                  {ed ? <span>· editado</span> : null}
                  {t.is_demo ? <span>· demonstração</span> : null}
                  {t.id < 0 ? <span>· offline</span> : null}
                </span>
              </button>
            </li>
          )
        })}
        {!loading && !shown.length && !pending.length ? (
          <li className="px-4 py-8 text-center text-sm leading-relaxed text-text-3">
            {tickets.length ? "Nenhum ticket neste caminho." : "Nenhum ticket ainda. Adicione um ticket ou restaure a demonstração."}
          </li>
        ) : null}
        {loading && !tickets.length ? (
          <li className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-text-3">
            <Loader2 className="size-4 animate-spin" aria-hidden /> Carregando tickets…
          </li>
        ) : null}
      </ul>
    </div>
  )
}
