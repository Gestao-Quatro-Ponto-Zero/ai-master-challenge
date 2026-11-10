"use client"

import { BellRing, Hash, X } from "lucide-react"
import { useEffect, useState } from "react"

import { markSlackSeen, type SlackEntry, useTicketsStore } from "@/components/tickets/store"
import type { SlackAlert } from "@/components/tickets/types"
import { fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

const CHANNEL = "#suporte-alertas"

/** Texto no formato do Slack (*negrito*, :emoji:) em elementos simples. */
function SlackText({ body }: { body: string }) {
  const lines = body.replace(/:rotating_light:/g, "🚨").split("\n")
  return (
    <div className="space-y-0.5 text-sm leading-relaxed text-text-1">
      {lines.map((line, i) => (
        <p key={i}>
          {line.split(/(\*[^*]+\*)/g).map((part, j) =>
            part.startsWith("*") && part.endsWith("*") && part.length > 2 ? <strong key={j}>{part.slice(1, -1)}</strong> : <span key={j}>{part}</span>,
          )}
        </p>
      ))}
    </div>
  )
}

function SlackCard({ alert, at, compact, onOpen }: { alert: SlackAlert; at: string; compact?: boolean; onOpen?: () => void }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs text-text-3">
        <span className="inline-flex items-center gap-1 font-semibold text-text-2">
          <Hash className="size-3.5" aria-hidden />
          {CHANNEL.slice(1)}
        </span>
        <span>·</span>
        <span>Triagem (n8n)</span>
        <span className="ml-auto tabular-nums">{fmt.relative(at)}</span>
      </div>
      <div className={cn("rounded-lg border-l-4 border-alert/70 bg-surface-2/60 px-3 py-2", compact && "line-clamp-4")}>
        <SlackText body={alert.body} />
      </div>
      {onOpen ? (
        <button type="button" onClick={onOpen} className="self-start text-xs font-medium text-text-2 underline underline-offset-4 hover:text-text-1">
          Abrir o ticket
        </button>
      ) : null}
    </div>
  )
}

/**
 * Notificação do Slack simulado (ADR-0015): aparece quando um ticket deste navegador cai em Somente humano.
 * No ambiente real, o nó Slack do fluxo 1 envia o mesmo texto ao canal.
 */
export function SlackToast({ entry, onClose, onOpen }: { entry: SlackEntry | null; onClose: () => void; onOpen: (id: number) => void }) {
  useEffect(() => {
    if (!entry) return
    const t = window.setTimeout(onClose, 10_000)
    return () => window.clearTimeout(t)
  }, [entry, onClose])
  if (!entry) return null
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-20 right-4 z-[60] w-[min(24rem,calc(100vw-2rem))] rounded-xl border border-border bg-surface p-4 shadow-soft motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-top-2"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">Simulação de mensagem no Slack</p>
        <button type="button" onClick={onClose} aria-label="Fechar" className="-m-1 rounded p-1 text-text-3 hover:text-text-1">
          <X className="size-4" aria-hidden />
        </button>
      </div>
      <SlackCard alert={entry} at={entry.at} compact onOpen={() => onOpen(entry.ticket_id)} />
    </div>
  )
}

/** Bolinha no canto inferior direito com o histórico das mensagens simuladas deste navegador. */
export function SlackBubble({ onOpen, hideOnMobile }: { onOpen: (id: number) => void; hideOnMobile?: boolean }) {
  const { slack } = useTicketsStore()
  const [open, setOpen] = useState(false)
  const unseen = slack.filter((s) => !s.seen).length

  function toggle() {
    if (!open) markSlackSeen()
    setOpen((v) => !v)
  }

  return (
    <>
      {open ? (
        <div className="fixed right-4 bottom-[calc(9.5rem+env(safe-area-inset-bottom))] z-[60] flex max-h-[min(32rem,70dvh)] w-[min(24rem,calc(100vw-2rem))] flex-col rounded-xl border border-border bg-surface shadow-soft md:bottom-24">
          <div className="flex items-start justify-between gap-3 border-b border-border p-4">
            <div>
              <p className="text-sm font-semibold text-text-1">Slack simulado · {CHANNEL}</p>
              <p className="mt-0.5 text-xs leading-relaxed text-text-3">Mensagens que o n8n enviaria ao Slack para os tickets deste navegador que caíram em Somente humano.</p>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Fechar" className="-m-1 rounded p-1 text-text-3 hover:text-text-1">
              <X className="size-4" aria-hidden />
            </button>
          </div>
          <div className="flex flex-col gap-5 overflow-y-auto p-4">
            {slack.length ? (
              slack.map((s) => (
                <SlackCard
                  key={`${s.ticket_id}-${s.at}`}
                  alert={s}
                  at={s.at}
                  onOpen={() => {
                    setOpen(false)
                    onOpen(s.ticket_id)
                  }}
                />
              ))
            ) : (
              <p className="text-sm leading-relaxed text-text-2">Nenhuma mensagem ainda. Adicione um ticket que caia em Somente humano (por exemplo, um pedido de RH) para ver o aviso.</p>
            )}
          </div>
        </div>
      ) : null}
      <button
        type="button"
        onClick={toggle}
        aria-label={`Slack simulado${unseen ? `, ${unseen} novas` : ""}`}
        aria-expanded={open}
        className={cn("fixed right-4 bottom-[calc(5.5rem+env(safe-area-inset-bottom))] z-[60] inline-flex size-12 items-center justify-center rounded-full bg-navy-600 text-white shadow-soft transition-transform hover:scale-105 md:bottom-6 dark:bg-surface-2 dark:text-text-1", hideOnMobile && "max-md:hidden")}
      >
        <BellRing className="size-5" aria-hidden />
        {unseen ? (
          <span className="absolute -top-1 -right-1 inline-flex min-w-5 items-center justify-center rounded-full bg-alert px-1.5 text-[10px] font-semibold leading-5 text-white">{unseen}</span>
        ) : null}
      </button>
    </>
  )
}
