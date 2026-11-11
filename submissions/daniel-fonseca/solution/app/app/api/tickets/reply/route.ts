import { json, readJson, tooMany } from "@/app/api/triage/_core"
import { callN8n, N8nUnavailable } from "@/lib/n8n"
import { getTicketForWrite } from "@/lib/queries/tickets"
import { supabaseServer } from "@/lib/supabase"
import type { HitlDecisionResult } from "@/lib/types"
import { checkLimit, detectFlag, ipHash, logUsage } from "@/lib/usage"

/**
 * POST /api/tickets/reply — resposta escrita pelo atendente (ADR-0015).
 * - Revisão humana: o rascunho conta como recusado (fluxo 2 com decision = reject) e a resposta fica
 *   registrada no ticket. Ela não entra na base de conhecimento (decisão do Daniel).
 * - Somente humano: a resposta só fica registrada.
 * Só vale para tickets de demonstração ou do próprio navegador (client_token).
 */
const ROUTE = "/api/tickets/reply"
const MAX = 4000

export async function POST(req: Request) {
  const t0 = Date.now()
  const ms = () => Date.now() - t0
  const body = await readJson(req)
  const id = Number(body.triage_run_id)
  const token = typeof body.client_token === "string" ? body.client_token : null
  const text = typeof body.text === "string" ? body.text.trim() : ""
  const flag = detectFlag(text)

  const invalid = !Number.isInteger(id) || id <= 0 ? "Ticket inválido." : text.length < 2 ? "Escreva a resposta antes de enviar." : text.length > MAX ? "A resposta passa de 4.000 caracteres." : null
  if (invalid) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "client_error", status_code: 400, latency_ms: ms(), flag })
    return json({ error: invalid }, 400)
  }

  const limit = await checkLimit("hitl", ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "rate_limited", status_code: 429, latency_ms: ms(), flag })
    return tooMany(limit.message, limit.retryAfter)
  }

  const ticket = await getTicketForWrite(id, token)
  const conflict = !ticket
    ? { status: 404, error: "Ticket não encontrado." }
    : ticket.human_reply
      ? { status: 409, error: "Este ticket já tem uma resposta do atendente." }
      : ticket.level === 1
        ? { status: 409, error: "Este ticket já foi respondido automaticamente." }
        : ticket.level === 2 && ticket.draft?.status !== "pending"
          ? { status: 409, error: "O rascunho deste ticket já foi decidido." }
          : null
  if (conflict) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "client_error", status_code: conflict.status, latency_ms: ms(), triage_run_id: ticket?.id, flag })
    return json({ error: conflict.error }, conflict.status)
  }

  if (ticket!.level === 2 && ticket!.draft) {
    try {
      const { status, data } = await callN8n<HitlDecisionResult & { error?: string }>("hitl-decision", {
        hitl_id: ticket!.draft.hitl_id,
        decision: "reject",
        note: "Recusado: o atendente escreveu a própria resposta.",
        reviewer: "visitante",
      })
      if (status === 409) return json({ error: "O rascunho deste ticket já foi decidido." }, 409)
      if (status !== 200) return json({ error: data?.error ?? "A recusa do rascunho não foi aceita." }, status >= 400 ? status : 502)
    } catch (err) {
      if (!(err instanceof N8nUnavailable)) throw err
      await logUsage(req, { route: ROUTE, action: "hitl", outcome: "offline", status_code: 503, latency_ms: ms(), flag })
      return json({ error: "O envio está indisponível agora. Tente novamente em instantes." }, 503)
    }
  }

  const at = new Date().toISOString()
  const { error } = await supabaseServer().from("triage_runs").update({ human_reply: text, human_reply_at: at, updated_at: at }).eq("id", id)
  if (error) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "server_error", status_code: 500, latency_ms: ms(), triage_run_id: id, flag })
    return json({ error: "A resposta não foi gravada. Tente de novo." }, 500)
  }
  await logUsage(req, { route: ROUTE, action: "hitl", outcome: "ok", status_code: 200, latency_ms: ms(), triage_run_id: id, flag })
  return json({ triage_run_id: id, human_reply: text, human_reply_at: at, rejected_draft: ticket!.level === 2 })
}
