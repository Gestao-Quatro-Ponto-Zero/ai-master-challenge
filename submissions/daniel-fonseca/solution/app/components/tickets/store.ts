"use client"

import { useSyncExternalStore } from "react"

import type { SlackAlert } from "@/components/tickets/types"

/**
 * Estado da tela Tickets que fica só neste navegador (ADR-0015):
 * - mine: tokens dos tickets criados aqui (dão acesso a eles no servidor) e a marca "editado";
 * - read: ids já abertos (o resto aparece como "Não lido");
 * - slack: as mensagens simuladas do Slack geradas aqui.
 * Sem armazenamento (aba privada, bloqueio), tudo funciona e some ao recarregar.
 */
const KEY = "tickets.v1"
const EVENT = "tickets-store-change"
const MAX_MINE = 50
const MAX_SLACK = 30

export interface MineEntry {
  token: string
  id: number
  at: string
  /** ticket do holdout sorteado e editado antes do envio */
  edited_from?: number
}

export interface SlackEntry extends SlackAlert {
  ticket_id: number
  at: string
  seen: boolean
}

export interface TicketsState {
  mine: MineEntry[]
  read: number[]
  slack: SlackEntry[]
}

const EMPTY: TicketsState = { mine: [], read: [], slack: [] }
let memory: TicketsState = EMPTY
let cachedRaw: string | null | undefined
let cached: TicketsState = EMPTY

function read(): TicketsState {
  let raw: string | null = null
  try {
    raw = window.localStorage.getItem(KEY)
  } catch {
    return memory
  }
  if (raw === cachedRaw) return cached
  cachedRaw = raw
  try {
    const p = raw ? (JSON.parse(raw) as Partial<TicketsState>) : {}
    cached = {
      mine: Array.isArray(p.mine) ? p.mine : [],
      read: Array.isArray(p.read) ? p.read : [],
      slack: Array.isArray(p.slack) ? p.slack : [],
    }
  } catch {
    cached = EMPTY
  }
  return cached
}

function write(next: TicketsState) {
  memory = next
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    cachedRaw = undefined
    cached = next
  }
  window.dispatchEvent(new Event(EVENT))
}

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb)
  window.addEventListener(EVENT, cb)
  return () => {
    window.removeEventListener("storage", cb)
    window.removeEventListener(EVENT, cb)
  }
}

export function useTicketsStore(): TicketsState {
  return useSyncExternalStore(subscribe, read, () => EMPTY)
}

export function getTicketsState(): TicketsState {
  return read()
}

export function addMine(entry: MineEntry) {
  const s = read()
  write({ ...s, mine: [entry, ...s.mine.filter((m) => m.id !== entry.id)].slice(0, MAX_MINE), read: [...new Set([entry.id, ...s.read])] })
}

export function markRead(id: number) {
  const s = read()
  if (s.read.includes(id)) return
  write({ ...s, read: [id, ...s.read].slice(0, 500) })
}

export function addSlack(entry: Omit<SlackEntry, "seen">) {
  const s = read()
  write({ ...s, slack: [{ ...entry, seen: false }, ...s.slack.filter((x) => x.ticket_id !== entry.ticket_id)].slice(0, MAX_SLACK) })
}

export function markSlackSeen() {
  const s = read()
  if (s.slack.every((x) => x.seen)) return
  write({ ...s, slack: s.slack.map((x) => ({ ...x, seen: true })) })
}

export const tokenFor = (s: TicketsState, id: number) => s.mine.find((m) => m.id === id)?.token ?? null
