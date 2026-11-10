import { isCategory, json, readJson, tooMany } from "@/app/api/triage/_core"
import type { HitlApiResult, NeighborTicket } from "@/components/console/types"
import { callN8n, N8nUnavailable } from "@/lib/n8n"
import { supabaseServer } from "@/lib/supabase"
import type { HitlDecisionResult } from "@/lib/types"
import { checkLimit, detectFlag, ipHash, logUsage } from "@/lib/usage"

/**
 * POST /api/hitl — repassa a decisão da fila ao fluxo 2 do n8n (PRD §4.5).
 * Sem login: o revisor fica registrado como "visitante" (+ ip_hash em usage_events).
 * Depois de aprovar, devolve o ticket de teste mais parecido (efeito "aprendeu").
 */
const ROUTE = "/api/hitl"
const DECISIONS = ["approve", "edit", "reject"] as const

export async function POST(req: Request) {
  const t0 = Date.now()
  const ms = () => Date.now() - t0
  const body = await readJson(req)

  const hitlId = Number(body.hitl_id)
  const decision = DECISIONS.find((d) => d === body.decision)
  const finalText = typeof body.final_text === "string" ? body.final_text.trim() : ""
  const finalCategory = isCategory(body.final_category) ? body.final_category : ""
  const note = typeof body.note === "string" ? body.note.trim().slice(0, 500) : ""
  const flag = detectFlag(`${finalText} ${note}`)

  const invalid =
    !Number.isInteger(hitlId) || hitlId <= 0
      ? "hitl_id inválido."
      : !decision
        ? "Decisão inválida: use aprovar, editar e aprovar ou rejeitar."
        : decision === "edit" && !finalText
          ? "Edite o texto antes de aprovar."
          : finalText.length > 4000
            ? "O texto final passa de 4.000 caracteres."
            : null
  if (invalid) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "client_error", status_code: 400, latency_ms: ms(), flag })
    return json({ error: invalid }, 400)
  }

  const limit = await checkLimit("hitl", ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "rate_limited", status_code: 429, latency_ms: ms(), flag })
    return tooMany(limit.message, limit.retryAfter)
  }

  try {
    const { status, data } = await callN8n<HitlDecisionResult & { error?: string }>("hitl-decision", {
      hitl_id: hitlId,
      decision,
      ...(decision === "edit" ? { final_text: finalText } : {}),
      ...(finalCategory ? { final_category: finalCategory } : {}),
      ...(note ? { note } : {}),
      reviewer: "visitante",
    })
    if (status === 409) {
      await logUsage(req, { route: ROUTE, action: "hitl", outcome: "client_error", status_code: 409, latency_ms: ms(), flag })
      return json({ error: "Este item já foi decidido. A fila foi atualizada." }, 409)
    }
    if (status !== 200) {
      await logUsage(req, { route: ROUTE, action: "hitl", outcome: "client_error", status_code: status, latency_ms: ms(), flag })
      return json({ error: data?.error ?? "A decisão não foi aceita." }, status >= 400 ? status : 502)
    }

    let neighbor: NeighborTicket | null = null
    if (decision !== "reject" && data.triage_run_id) {
      const { data: rows } = await supabaseServer().rpc("nearest_holdout_ticket", { p_triage_run_id: data.triage_run_id })
      const row = (Array.isArray(rows) ? rows[0] : rows) as { id: number; document: string; similarity: number } | undefined
      if (row) neighbor = { id: row.id, excerpt: row.document.slice(0, 280), similarity: row.similarity }
    }

    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "ok", status_code: 200, latency_ms: ms(), triage_run_id: data.triage_run_id, flag })
    const result: HitlApiResult = {
      hitl_id: data.hitl_id,
      decision: data.decision,
      triage_run_id: data.triage_run_id,
      triage_status: data.triage_status,
      resolution_id: data.resolution_id ?? null,
      neighbor,
    }
    return json(result)
  } catch (err) {
    if (!(err instanceof N8nUnavailable)) throw err
    await logUsage(req, { route: ROUTE, action: "hitl", outcome: "offline", status_code: 503, latency_ms: ms(), flag })
    return json({ error: "A aprovação está indisponível agora. O item continua pendente; tente novamente em instantes." }, 503)
  }
}
