import "server-only"

import { connection } from "next/server"

import { supabaseServer } from "@/lib/supabase"
import type { OpsSummary } from "@/lib/types"

/** Dados vivos da operação: sempre no request (chamar dentro de <Suspense>). */

export async function getOpsSummary(): Promise<OpsSummary> {
  await connection()
  const { data, error } = await supabaseServer().from("v_ops_summary").select("*").single()
  if (error) throw new Error(`v_ops_summary: ${error.message}`)
  return data as OpsSummary
}

/** Contagens para os badges da navegação (fila pendente + caixa não lida). */
export async function getNavCounts(): Promise<{ fila: number; caixa: number }> {
  await connection()
  const db = supabaseServer()
  const [fila, caixa] = await Promise.all([
    db.from("hitl_queue").select("id", { count: "exact", head: true }).eq("status", "pending"),
    db.from("notifications").select("id", { count: "exact", head: true }).is("read_at", null),
  ])
  return { fila: fila.count ?? 0, caixa: caixa.count ?? 0 }
}

export async function getLastHeartbeat(): Promise<{ ran_at: string; source: string; ok: boolean } | null> {
  await connection()
  const { data } = await supabaseServer().from("heartbeat").select("ran_at, source, ok").order("ran_at", { ascending: false }).limit(1).maybeSingle()
  return data ?? null
}
