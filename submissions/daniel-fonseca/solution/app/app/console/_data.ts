import "server-only"

import { connection } from "next/server"

import type { HoldoutTicket, InboxItem, QueueItem } from "@/components/console/types"
import { supabaseServer } from "@/lib/supabase"
import type { Category, SimilarCase } from "@/lib/types"

/** Leituras do Console: sempre frescas (chamar dentro de <Suspense>). Nunca selecionam o embedding. */

type TriageJoin = {
  ticket_text: string
  category: Category
  confidence: number
  level_reason: string | null
  similar_cases: SimilarCase[] | null
  ds2_id: number | null
}
const one = <T,>(v: T | T[] | null | undefined): T | null => (Array.isArray(v) ? (v[0] ?? null) : (v ?? null))

const QUEUE_COLUMNS =
  "id, triage_run_id, status, draft_text, checks, final_text, final_category, reviewer, review_note, created_at, decided_at, triage_runs(ticket_text, category, confidence, level_reason, similar_cases, ds2_id)"

function toQueueItem(r: Record<string, unknown>): QueueItem {
  const t = one(r.triage_runs as TriageJoin | TriageJoin[] | null)
  return {
    id: r.id as number,
    triage_run_id: r.triage_run_id as number,
    status: r.status as QueueItem["status"],
    draft_text: r.draft_text as string,
    checks: Array.isArray(r.checks) ? (r.checks as string[]) : [],
    final_text: (r.final_text as string | null) ?? null,
    final_category: (r.final_category as Category | null) || null,
    reviewer: (r.reviewer as string | null) ?? null,
    review_note: (r.review_note as string | null) ?? null,
    created_at: r.created_at as string,
    decided_at: (r.decided_at as string | null) ?? null,
    ticket_text: t?.ticket_text ?? "",
    category: (t?.category ?? "Miscellaneous") as Category,
    confidence: t?.confidence ?? 0,
    level_reason: t?.level_reason ?? null,
    similar_cases: (t?.similar_cases ?? []).slice(0, 5),
    ds2_id: t?.ds2_id ?? null,
  }
}

export async function getQueue(): Promise<{ pending: QueueItem[]; decided: QueueItem[] }> {
  await connection()
  const db = supabaseServer()
  const [p, d] = await Promise.all([
    db.from("hitl_queue").select(QUEUE_COLUMNS).eq("status", "pending").order("created_at", { ascending: true }).limit(50),
    db.from("hitl_queue").select(QUEUE_COLUMNS).neq("status", "pending").order("decided_at", { ascending: false }).limit(30),
  ])
  if (p.error) throw new Error(`hitl_queue: ${p.error.message}`)
  return { pending: (p.data ?? []).map(toQueueItem), decided: (d.data ?? []).map(toQueueItem) }
}

export async function getInbox(): Promise<InboxItem[]> {
  await connection()
  const { data, error } = await supabaseServer()
    .from("notifications")
    .select("id, kind, title, body, payload, read_at, assigned_to, assigned_at, created_at, triage_run_id, triage_runs(ticket_text, category)")
    .order("created_at", { ascending: false })
    .limit(60)
  if (error) throw new Error(`notifications: ${error.message}`)
  return (data ?? []).map((r) => {
    const t = one(r.triage_runs as { ticket_text: string; category: Category } | { ticket_text: string; category: Category }[] | null)
    const p = (r.payload ?? {}) as { summary?: string; risk_signals?: string[]; suggested_owner?: string }
    return {
      id: r.id,
      kind: r.kind,
      title: r.title,
      body: r.body,
      read_at: r.read_at,
      assigned_to: r.assigned_to,
      assigned_at: r.assigned_at,
      created_at: r.created_at,
      triage_run_id: r.triage_run_id,
      ticket_text: t?.ticket_text ?? null,
      category: t?.category ?? null,
      summary: typeof p.summary === "string" ? p.summary : null,
      risk_signals: Array.isArray(p.risk_signals) ? p.risk_signals.filter((s) => typeof s === "string") : [],
      suggested_owner: typeof p.suggested_owner === "string" ? p.suggested_owner : null,
    } satisfies InboxItem
  })
}

/** Ticket do holdout pedido por link direto (?ds2=), por exemplo o vizinho do efeito "aprendeu". */
export async function getHoldoutById(id: number): Promise<HoldoutTicket | null> {
  await connection()
  if (!Number.isInteger(id) || id <= 0) return null
  const { data } = await supabaseServer().from("ds2_tickets").select("id, document").eq("id", id).eq("split", "test").maybeSingle()
  return (data as HoldoutTicket | null) ?? null
}
