import { classifyOffline, getHoldoutTicket, json, readJson, runTriage, tooMany } from "@/app/api/triage/_core"
import { env } from "@/lib/env"
import { N8nUnavailable } from "@/lib/n8n"
import { checkLimit, detectFlag, ipHash, logUsage } from "@/lib/usage"

/**
 * POST /api/triage (PRD §4.4 e §8).
 * - mode "holdout": recebe só ds2_id; o texto vem de ds2_tickets (split test). Texto do cliente é ignorado.
 * - mode "free_text": inglês, até 4.000 caracteres, só com FREE_TEXT_ENABLED.
 * Em N8nUnavailable: holdout cai no modo offline (classify_holdout_ticket); texto livre responde 503.
 */
export const maxDuration = 45

const ROUTE = "/api/triage"
const MAX_CHARS = 4000
const MIN_CHARS = 15

export async function POST(req: Request) {
  const t0 = Date.now()
  const body = await readJson(req)
  const mode = body.mode
  const ms = () => Date.now() - t0

  if (mode !== "holdout" && mode !== "free_text") {
    return json({ error: "Informe mode = holdout ou free_text." }, 400)
  }
  const action = mode === "holdout" ? "triage_holdout" : "triage_free_text"

  // 1. Entrada
  let ticketText: string
  let ds2Id: number | undefined
  let trueCategory: Awaited<ReturnType<typeof getHoldoutTicket>> = null
  let flag: string | null = null

  if (mode === "holdout") {
    const id = Number(body.ds2_id)
    if (!Number.isInteger(id) || id <= 0) return json({ error: "ds2_id inválido." }, 400)
    trueCategory = await getHoldoutTicket(id)
    if (!trueCategory) {
      await logUsage(req, { route: ROUTE, action, outcome: "client_error", status_code: 404, latency_ms: ms() })
      return json({ error: "Ticket não encontrado no conjunto de teste." }, 404)
    }
    ticketText = trueCategory.document
    ds2Id = id
  } else {
    if (!env.freeTextEnabled()) {
      await logUsage(req, { route: ROUTE, action, outcome: "disabled", status_code: 503, latency_ms: ms() })
      return json({ error: "O texto livre está pausado no momento. Use o sorteio de tickets do conjunto de teste." }, 503)
    }
    const text = typeof body.ticket_text === "string" ? body.ticket_text.trim() : ""
    flag = detectFlag(text)
    if (text.length < MIN_CHARS || text.length > MAX_CHARS) {
      await logUsage(req, { route: ROUTE, action, outcome: "client_error", status_code: 400, latency_ms: ms(), flag })
      return json({ error: `Escreva o ticket em inglês, entre ${MIN_CHARS} e ${MAX_CHARS.toLocaleString("pt-BR")} caracteres.` }, 400)
    }
    ticketText = text
  }

  // 2. Limite de uso
  const limit = await checkLimit(action, ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: ROUTE, action, outcome: "rate_limited", status_code: 429, latency_ms: ms(), flag })
    return tooMany(limit.message, limit.retryAfter)
  }

  // 3. Triagem pelo n8n, com modo offline para o holdout
  try {
    const out = await runTriage({ ticket_text: ticketText, source: mode === "holdout" ? "holdout" : "console", ds2_id: ds2Id })
    if (out.kind === "client_error") {
      await logUsage(req, { route: ROUTE, action, outcome: "client_error", status_code: out.status, latency_ms: ms(), flag })
      return json({ error: out.error }, out.status)
    }
    const latency = ms()
    await logUsage(req, { route: ROUTE, action, outcome: "ok", status_code: 200, latency_ms: latency, triage_run_id: out.result.triage_run_id, flag })
    return json({ ...out.result, true_category: trueCategory?.topic_group ?? null, offline: false, latency_ms: latency })
  } catch (err) {
    if (!(err instanceof N8nUnavailable)) throw err
    if (mode === "free_text") {
      await logUsage(req, { route: ROUTE, action, outcome: "offline", status_code: 503, latency_ms: ms(), flag })
      return json({ error: "O fluxo de triagem está indisponível agora. O texto livre volta assim que ele responder; o sorteio funciona em modo offline." }, 503)
    }
    const offline = await classifyOffline({ id: ds2Id!, document: ticketText })
    if (!offline) {
      await logUsage(req, { route: ROUTE, action, outcome: "server_error", status_code: 503, latency_ms: ms() })
      return json({ error: "A triagem está indisponível agora. Tente novamente em instantes." }, 503)
    }
    const latency = ms()
    await logUsage(req, { route: ROUTE, action, outcome: "offline", status_code: 200, latency_ms: latency })
    return json({ ...offline, true_category: trueCategory?.topic_group ?? null, offline: true, latency_ms: latency })
  }
}
