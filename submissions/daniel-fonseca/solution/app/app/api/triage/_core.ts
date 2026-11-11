import "server-only"

import type { ConsoleTriageResult } from "@/components/console/types"
import { callN8n } from "@/lib/n8n"
import { supabaseServer } from "@/lib/supabase"
import { CATEGORIES, SENSITIVE_CATEGORIES, type Category, type Level, type SimilarCase, type TriageResult } from "@/lib/types"

/** Resposta JSON padronizada das rotas do Console. */
export function json(body: unknown, status = 200, headers?: Record<string, string>) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store", ...headers } })
}

export function tooMany(message: string | undefined, retryAfter: number | undefined) {
  return json(
    { error: message ?? "Limite de uso atingido. Tente novamente mais tarde.", retry_after: retryAfter },
    429,
    retryAfter ? { "Retry-After": String(retryAfter) } : undefined,
  )
}

/** Lê o corpo JSON sem lançar: corpo inválido vira objeto vazio e cai na validação. */
export async function readJson(req: Request): Promise<Record<string, unknown>> {
  try {
    const body = await req.json()
    return body && typeof body === "object" && !Array.isArray(body) ? (body as Record<string, unknown>) : {}
  } catch {
    return {}
  }
}

export function isCategory(v: unknown): v is Category {
  return typeof v === "string" && (CATEGORIES as readonly string[]).includes(v)
}

/** Ticket do holdout: só o split de teste entra no Console. */
export async function getHoldoutTicket(id: number): Promise<{ id: number; document: string; topic_group: Category } | null> {
  const { data } = await supabaseServer().from("ds2_tickets").select("id, document, topic_group").eq("id", id).eq("split", "test").maybeSingle()
  return (data as { id: number; document: string; topic_group: Category } | null) ?? null
}

interface RunMetrics {
  step_ms: ConsoleTriageResult["step_ms"]
  tokens_in: number | null
  tokens_out: number | null
  cost_usd: number | null
  latency_ms: number | null
}

/** Métricas gravadas pelo n8n em triage_runs (nunca o embedding). */
async function getRunMetrics(id: number): Promise<RunMetrics | null> {
  const { data } = await supabaseServer().from("triage_runs").select("step_ms, tokens_in, tokens_out, cost_usd, latency_ms").eq("id", id).maybeSingle()
  if (!data) return null
  return { ...data, cost_usd: data.cost_usd == null ? null : Number(data.cost_usd) } as RunMetrics
}

export type RunOutcome =
  | { kind: "ok"; result: ConsoleTriageResult }
  | { kind: "client_error"; status: number; error: string }

/**
 * Chama o fluxo 1 do n8n e completa a resposta com as métricas de triage_runs.
 * Lança N8nUnavailable (timeout, rede, 5xx): o chamador decide o modo offline.
 */
export async function runTriage(input: { ticket_text: string; source: "console" | "holdout"; ds2_id?: number }, owner: { client_token?: string; is_demo?: boolean } = {}): Promise<RunOutcome> {
  const { status, data } = await callN8n<TriageResult & { error?: string }>("triage", input)
  if (status !== 200 || !data?.triage_run_id) {
    return { kind: "client_error", status: status >= 400 ? status : 502, error: data?.error ?? "A triagem não pôde ser concluída." }
  }
  // Dono do ticket (ADR-0015): o token do navegador ou a marca de demonstração. O n8n não conhece o token.
  if (owner.client_token || owner.is_demo) {
    await supabaseServer()
      .from("triage_runs")
      .update({ ...(owner.client_token ? { client_token: owner.client_token } : {}), ...(owner.is_demo ? { is_demo: true } : {}) })
      .eq("id", data.triage_run_id)
  }
  const metrics = await getRunMetrics(data.triage_run_id)
  return {
    kind: "ok",
    result: {
      ...data,
      similar_cases: (data.similar_cases ?? []).slice(0, 5),
      ds2_id: input.ds2_id ?? null,
      ticket_text: input.ticket_text,
      step_ms: metrics?.step_ms ?? null,
      tokens_in: metrics?.tokens_in ?? null,
      tokens_out: metrics?.tokens_out ?? null,
      cost_usd: metrics?.cost_usd ?? null,
      n8n_latency_ms: metrics?.latency_ms ?? null,
    },
  }
}

/* Mesmos limiares do fluxo 1 (nó "Aplicar política de 3 níveis", docs/n8n-flows.md). */
const LIMIAR_AUTO = 0.9
const LIMIAR_HUMANO = 0.5
const LIMIAR_SENSIVEL = 0.3
const TERMOS_BLOQUEIO = ["salary", "payroll", "bonus", "termination", "dismissal", "resignation", "lawsuit", "legal", "harassment", "sick leave", "maternity"]

/**
 * Modo offline (PRD §4.4): classificação direto no Supabase (classify_holdout_ticket), sem n8n e sem
 * redação. O caminho é o indicado pela mesma regra de limiares; nada é gravado nem enviado.
 */
export async function classifyOffline(ticket: { id: number; document: string }): Promise<ConsoleTriageResult | null> {
  const { data, error } = await supabaseServer().rpc("classify_holdout_ticket", { p_ds2_id: ticket.id })
  const row = (Array.isArray(data) ? data[0] : data) as
    | { category: Category; confidence: number; sensitive_share: number; votes: Partial<Record<Category, number>>; similar_cases: SimilarCase[] }
    | undefined
  if (error || !row) return null
  const text = ticket.document.toLowerCase()
  const blocked = TERMOS_BLOQUEIO.some((t) => text.includes(t))
  const pct = (n: number) => n.toFixed(2)
  let level: Level
  let reason: string
  if (SENSITIVE_CATEGORIES.includes(row.category)) [level, reason] = [3, `Categoria sensível: ${row.category}`]
  else if (row.sensitive_share >= LIMIAR_SENSIVEL) [level, reason] = [3, `Votos em categorias sensíveis: ${Math.round(row.sensitive_share * 100)}%`]
  else if (blocked) [level, reason] = [3, "Termo da lista de bloqueio no texto"]
  else if (row.confidence < LIMIAR_HUMANO) [level, reason] = [3, `Confiança baixa (${pct(row.confidence)})`]
  else if (row.confidence >= LIMIAR_AUTO) [level, reason] = [1, `Confiança alta (${pct(row.confidence)}) e solução validada da categoria`]
  else [level, reason] = [2, `Confiança intermediária (${pct(row.confidence)})`]

  return {
    triage_run_id: null,
    status: "received",
    level,
    level_reason: reason,
    category: row.category,
    confidence: row.confidence,
    sensitive_share: row.sensitive_share,
    votes: row.votes ?? {},
    similar_cases: (row.similar_cases ?? []).slice(0, 5),
    resolutions: [],
    response_text: null,
    resolution_id: null,
    hitl: null,
    notification: null,
    offline: true,
    ds2_id: ticket.id,
    ticket_text: ticket.document,
    step_ms: null,
    tokens_in: null,
    tokens_out: null,
    cost_usd: null,
    n8n_latency_ms: null,
  }
}
