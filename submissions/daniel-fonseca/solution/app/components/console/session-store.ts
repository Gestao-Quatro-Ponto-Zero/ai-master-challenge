"use client"

import { useSyncExternalStore } from "react"

import type { HistoryEntry } from "@/components/console/types"

/**
 * Histórico do visitante no navegador (PRD §4.4): as 10 últimas triagens e a acurácia acumulada nos
 * tickets do holdout. Fica só no localStorage deste navegador.
 */
const KEY = "console.triagem.v1"
const EVENT = "console-triagem-change"
const MAX = 10

export interface SessionState {
  history: HistoryEntry[]
  holdoutTotal: number
  holdoutHits: number
}
const EMPTY: SessionState = { history: [], holdoutTotal: 0, holdoutHits: 0 }

let cachedRaw: string | null = null
let cachedValue: SessionState = EMPTY

function read(): SessionState {
  let raw: string | null = null
  try {
    raw = window.localStorage.getItem(KEY)
  } catch {
    raw = null
  }
  if (raw === cachedRaw) return cachedValue
  cachedRaw = raw
  try {
    const parsed = raw ? (JSON.parse(raw) as SessionState) : EMPTY
    cachedValue = { history: Array.isArray(parsed.history) ? parsed.history : [], holdoutTotal: parsed.holdoutTotal ?? 0, holdoutHits: parsed.holdoutHits ?? 0 }
  } catch {
    cachedValue = EMPTY
  }
  return cachedValue
}

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb)
  window.addEventListener(EVENT, cb)
  return () => {
    window.removeEventListener("storage", cb)
    window.removeEventListener(EVENT, cb)
  }
}

export function useSessionState(): SessionState {
  return useSyncExternalStore(subscribe, read, () => EMPTY)
}

export function recordTriage(entry: HistoryEntry) {
  const current = read()
  const next: SessionState = {
    history: [entry, ...current.history].slice(0, MAX),
    holdoutTotal: current.holdoutTotal + (entry.true_category ? 1 : 0),
    holdoutHits: current.holdoutHits + (entry.true_category && entry.true_category === entry.category ? 1 : 0),
  }
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* navegador sem armazenamento: o histórico some ao recarregar */
  }
  window.dispatchEvent(new Event(EVENT))
}

export function clearSession() {
  try {
    window.localStorage.removeItem(KEY)
  } catch {
    /* sem armazenamento */
  }
  window.dispatchEvent(new Event(EVENT))
}
