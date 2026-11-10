import { getHoldoutTicket, json, runTriage, tooMany } from "@/app/api/triage/_core"
import { N8nUnavailable } from "@/lib/n8n"
import { supabaseServer } from "@/lib/supabase"
import { checkLimit, ipHash, logUsage } from "@/lib/usage"

/**
 * POST /api/demo/reset — restaura a demonstração (PRD §8) sem apagar nenhum dado.
 * Se a fila tiver menos de 3 pendentes, dispara triagens de tickets do holdout que caem em Revisão humana
 * e uma de Somente humano, pulando os tickets que já estão pendentes na fila ou na caixa.
 * Ids verificados na construção do fluxo 1 (docs/n8n-flows.md).
 */
export const maxDuration = 60

const ROUTE = "/api/demo/reset"
const MIN_PENDING = 3
const REVIEW_IDS = [79, 177, 253, 268, 282, 285]
const HUMAN_IDS = [7, 137]

export async function POST(req: Request) {
  const t0 = Date.now()
  const ms = () => Date.now() - t0
  const db = supabaseServer()

  const [{ data: pendingRows }, { data: openAlerts }] = await Promise.all([
    db.from("hitl_queue").select("id, triage_runs(ds2_id)").eq("status", "pending"),
    db.from("notifications").select("id, triage_runs(ds2_id)").eq("kind", "level3_alert").is("assigned_to", null),
  ])
  const ds2Of = (r: { triage_runs: unknown }) => {
    const t = (Array.isArray(r.triage_runs) ? r.triage_runs[0] : r.triage_runs) as { ds2_id: number | null } | null
    return t?.ds2_id ?? null
  }
  const pending = pendingRows ?? []
  if (pending.length >= MIN_PENDING) {
    // Nada a fazer: o evento fica registrado sem consumir a cota (só "ok" conta no limite).
    await logUsage(req, { route: ROUTE, action: "demo_reset", outcome: "disabled", status_code: 200, latency_ms: ms() })
    return json({ created: 0, pending: pending.length, message: `A fila já tem ${pending.length} itens pendentes. Nada foi criado.` })
  }

  const limit = await checkLimit("demo_reset", ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: ROUTE, action: "demo_reset", outcome: "rate_limited", status_code: 429, latency_ms: ms() })
    return tooMany(limit.message, limit.retryAfter)
  }

  const pendingDs2 = new Set(pending.map(ds2Of))
  const alertDs2 = new Set((openAlerts ?? []).map(ds2Of))
  const review = REVIEW_IDS.filter((id) => !pendingDs2.has(id)).slice(0, MIN_PENDING - pending.length)
  const human = HUMAN_IDS.find((id) => !alertDs2.has(id))
  const ids = human ? [...review, human] : review

  const runs = await Promise.allSettled(
    ids.map(async (id) => {
      const ticket = await getHoldoutTicket(id)
      if (!ticket) return null
      const out = await runTriage({ ticket_text: ticket.document, source: "holdout", ds2_id: id })
      return out.kind === "ok" ? { ds2_id: id, triage_run_id: out.result.triage_run_id, level: out.result.level } : null
    }),
  )
  const created = runs.flatMap((r) => (r.status === "fulfilled" && r.value ? [r.value] : []))
  const offline = runs.some((r) => r.status === "rejected" && r.reason instanceof N8nUnavailable)

  if (!created.length) {
    await logUsage(req, { route: ROUTE, action: "demo_reset", outcome: offline ? "offline" : "server_error", status_code: 503, latency_ms: ms() })
    return json({ error: "O fluxo de triagem está indisponível agora. Tente restaurar a demonstração em instantes." }, 503)
  }
  await logUsage(req, { route: ROUTE, action: "demo_reset", outcome: "ok", status_code: 200, latency_ms: ms(), triage_run_id: created[0].triage_run_id })
  const toQueue = created.filter((c) => c.level === 2).length
  const toInbox = created.filter((c) => c.level === 3).length
  return json({ created: created.length, to_queue: toQueue, to_inbox: toInbox, runs: created, message: `${toQueue} na fila e ${toInbox} na caixa.` })
}
