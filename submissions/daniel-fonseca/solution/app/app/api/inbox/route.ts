import { json, readJson, tooMany } from "@/app/api/triage/_core"
import { supabaseServer } from "@/lib/supabase"
import { checkLimit, ipHash, logUsage } from "@/lib/usage"

/**
 * POST /api/inbox — ações da caixa (PRD §4.6): { id, action: "read" | "assign" }.
 * "assign" grava assigned_to = "visitante" (sem login) e também marca como lida.
 */
const ROUTE = "/api/inbox"

export async function POST(req: Request) {
  const t0 = Date.now()
  const ms = () => Date.now() - t0
  const body = await readJson(req)
  const id = Number(body.id)
  const action = body.action === "read" || body.action === "assign" ? body.action : null
  if (!Number.isInteger(id) || id <= 0 || !action) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "client_error", status_code: 400, latency_ms: ms() })
    return json({ error: "Informe id e action = read ou assign." }, 400)
  }

  const limit = await checkLimit("inbox", ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "rate_limited", status_code: 429, latency_ms: ms() })
    return tooMany(limit.message, limit.retryAfter)
  }

  const db = supabaseServer()
  const { data: current } = await db.from("notifications").select("id, read_at, assigned_to").eq("id", id).maybeSingle()
  if (!current) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "client_error", status_code: 404, latency_ms: ms() })
    return json({ error: "Alerta não encontrado." }, 404)
  }
  if (action === "assign" && current.assigned_to) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "client_error", status_code: 409, latency_ms: ms() })
    return json({ error: "Este alerta já foi assumido." }, 409)
  }

  const now = new Date().toISOString()
  const patch = action === "read" ? { read_at: current.read_at ?? now } : { assigned_to: "visitante", assigned_at: now, read_at: current.read_at ?? now }
  let query = db.from("notifications").update(patch).eq("id", id)
  if (action === "assign") query = query.is("assigned_to", null)
  const { data, error } = await query.select("id, read_at, assigned_to, assigned_at").maybeSingle()
  if (error) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "server_error", status_code: 500, latency_ms: ms() })
    return json({ error: "Não foi possível atualizar o alerta." }, 500)
  }
  if (!data) {
    await logUsage(req, { route: ROUTE, action: "inbox", outcome: "client_error", status_code: 409, latency_ms: ms() })
    return json({ error: "Este alerta já foi assumido." }, 409)
  }
  await logUsage(req, { route: ROUTE, action: "inbox", outcome: "ok", status_code: 200, latency_ms: ms() })
  return json(data)
}
