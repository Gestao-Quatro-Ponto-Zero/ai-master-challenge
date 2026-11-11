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

export async function getLastHeartbeat(): Promise<{ ran_at: string; source: string; ok: boolean } | null> {
  await connection()
  const { data } = await supabaseServer().from("heartbeat").select("ran_at, source, ok").order("ran_at", { ascending: false }).limit(1).maybeSingle()
  return data ?? null
}
