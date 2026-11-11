"use client"

import { useEffect, useState } from "react"

import { getTicketsState, useTicketsStore } from "@/components/tickets/store"

/** Contador de não lidos de Tickets na navegação (ADR-0015). Calculado no navegador: o "Não lido" é por navegador. */
export function TicketsBadge() {
  const { read } = useTicketsStore()
  const [ids, setIds] = useState<number[] | null>(null)

  useEffect(() => {
    let alive = true
    const load = () =>
      fetch("/api/tickets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tokens: getTicketsState().mine.map((m) => m.token) }) })
        .then((r) => (r.ok ? r.json() : { tickets: [] }))
        .then((d: { tickets?: { id: number }[] }) => alive && setIds((d.tickets ?? []).map((t) => t.id)))
        .catch(() => alive && setIds([]))
    load()
    window.addEventListener("tickets-list-change", load)
    return () => {
      alive = false
      window.removeEventListener("tickets-list-change", load)
    }
  }, [])

  const unread = ids ? ids.filter((id) => !read.includes(id)).length : 0
  if (!unread) return null
  return (
    <span className="inline-flex min-w-5 items-center justify-center rounded-full bg-text-1 px-1.5 text-[10px] font-semibold leading-5 text-bg" aria-label={`${unread} não lidos`}>
      {unread}
    </span>
  )
}
