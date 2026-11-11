import "server-only"

import type { HumanSummary, TicketDraft, TicketItem } from "@/components/tickets/types"
import { supabaseServer } from "@/lib/supabase"
import type { Category, Level, SimilarCase, TriageStatus } from "@/lib/types"

/** Leituras da tela Tickets (ADR-0015). Só o servidor lê, com a service role; o embedding nunca sai. */

const COLUMNS =
  "id, created_at, is_demo, ds2_id, ticket_text, status, level, level_reason, category, confidence, votes, similar_cases, response_text, human_summary, alert_title, alert_body, human_reply, human_reply_at, step_ms, tokens_in, tokens_out, cost_usd, latency_ms, hitl_queue(id, status, draft_text, checks, final_text, final_category, decided_at), ds2_tickets(topic_group)"

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
export const MAX_TOKENS = 50
const DEMO_LIMIT = 30

export const isToken = (v: unknown): v is string => typeof v === "string" && UUID.test(v)

const one = <T,>(v: T | T[] | null | undefined): T | null => (Array.isArray(v) ? (v[0] ?? null) : (v ?? null))

function toSummary(v: unknown): HumanSummary | null {
  if (!v || typeof v !== "object") return null
  const s = v as Record<string, unknown>
  if (typeof s.summary !== "string" || !s.summary) return null
  return {
    summary: s.summary,
    risk_signals: Array.isArray(s.risk_signals) ? s.risk_signals.filter((x): x is string => typeof x === "string") : [],
    suggested_owner: typeof s.suggested_owner === "string" ? s.suggested_owner : "",
  }
}

function toItem(r: Record<string, unknown>): TicketItem {
  const h = one(r.hitl_queue as Record<string, unknown> | Record<string, unknown>[] | null)
  const draft: TicketDraft | null = h
    ? {
        hitl_id: h.id as number,
        status: h.status as TicketDraft["status"],
        draft_text: h.draft_text as string,
        checks: Array.isArray(h.checks) ? (h.checks as string[]) : [],
        final_text: (h.final_text as string | null) ?? null,
        final_category: ((h.final_category as Category | null) || null) as Category | null,
        decided_at: (h.decided_at as string | null) ?? null,
      }
    : null
  return {
    id: r.id as number,
    created_at: r.created_at as string,
    is_demo: Boolean(r.is_demo),
    ds2_id: (r.ds2_id as number | null) ?? null,
    true_category: (one(r.ds2_tickets as { topic_group: Category } | { topic_group: Category }[] | null)?.topic_group ?? null) as Category | null,
    ticket_text: r.ticket_text as string,
    status: r.status as TriageStatus,
    level: (r.level as Level | null) ?? null,
    level_reason: (r.level_reason as string | null) ?? null,
    category: (r.category as Category | null) ?? null,
    confidence: r.confidence == null ? null : Number(r.confidence),
    votes: (r.votes as TicketItem["votes"]) ?? {},
    similar_cases: ((r.similar_cases as SimilarCase[] | null) ?? []).slice(0, 5),
    response_text: (r.response_text as string | null) ?? null,
    draft,
    human_summary: toSummary(r.human_summary),
    alert: r.alert_title && r.alert_body ? { title: r.alert_title as string, body: r.alert_body as string } : null,
    human_reply: (r.human_reply as string | null) ?? null,
    human_reply_at: (r.human_reply_at as string | null) ?? null,
    step_ms: (r.step_ms as TicketItem["step_ms"]) ?? null,
    tokens_in: (r.tokens_in as number | null) ?? null,
    tokens_out: (r.tokens_out as number | null) ?? null,
    cost_usd: r.cost_usd == null ? null : Number(r.cost_usd),
    latency_ms: (r.latency_ms as number | null) ?? null,
  }
}

/** Tickets de demonstração (compartilhados) + os do navegador (pelos tokens), do mais recente ao mais antigo. */
export async function getTickets(tokens: string[]): Promise<TicketItem[]> {
  const db = supabaseServer()
  const valid = [...new Set(tokens.filter(isToken))].slice(0, MAX_TOKENS)
  const [demo, mine] = await Promise.all([
    db.from("triage_runs").select(COLUMNS).eq("is_demo", true).order("created_at", { ascending: false }).limit(DEMO_LIMIT),
    valid.length ? db.from("triage_runs").select(COLUMNS).in("client_token", valid).order("created_at", { ascending: false }) : Promise.resolve({ data: [], error: null }),
  ])
  if (demo.error) throw new Error(`triage_runs: ${demo.error.message}`)
  if (mine.error) throw new Error(`triage_runs: ${mine.error.message}`)
  const byId = new Map<number, TicketItem>()
  for (const r of [...(demo.data ?? []), ...(mine.data ?? [])]) byId.set(r.id as number, toItem(r as Record<string, unknown>))
  return [...byId.values()].sort((a, b) => b.created_at.localeCompare(a.created_at))
}

/** Um ticket, se o pedido tem o token dele ou se ele é de demonstração. */
export async function getTicketForWrite(id: number, token: string | null): Promise<TicketItem | null> {
  let q = supabaseServer().from("triage_runs").select(COLUMNS).eq("id", id)
  q = token && isToken(token) ? q.or(`is_demo.eq.true,client_token.eq.${token}`) : q.eq("is_demo", true)
  const { data } = await q.maybeSingle()
  return data ? toItem(data as Record<string, unknown>) : null
}
