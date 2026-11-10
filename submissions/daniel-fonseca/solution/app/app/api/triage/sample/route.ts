import { isCategory, json, tooMany } from "@/app/api/triage/_core"
import { supabaseServer } from "@/lib/supabase"
import { checkLimit, ipHash, logUsage } from "@/lib/usage"

/**
 * GET /api/triage/sample?categoria=Storage — sorteia um ticket do holdout (split test), sem o rótulo real.
 * GET /api/triage/sample?id=123 — devolve esse ticket do holdout.
 * Aplica o limite da triagem de holdout e registra só o bloqueio (429): o sorteio é uma leitura barata e
 * não consome a cota de triagens, que conta apenas as triagens feitas.
 */
export async function GET(req: Request) {
  const raw = new URL(req.url).searchParams.get("categoria")
  const category = raw && isCategory(raw) ? raw : null
  const limit = await checkLimit("triage_holdout", ipHash(req))
  if (!limit.allowed) {
    await logUsage(req, { route: "/api/triage/sample", action: "triage_holdout", outcome: "rate_limited", status_code: 429 })
    return tooMany(limit.message, limit.retryAfter)
  }
  // ?id=N: um ticket específico do holdout (o vizinho do efeito "aprendeu", ADR-0015)
  const id = Number(new URL(req.url).searchParams.get("id"))
  if (Number.isInteger(id) && id > 0) {
    const { data } = await supabaseServer().from("ds2_tickets").select("id, document").eq("id", id).eq("split", "test").maybeSingle()
    return data ? json({ id: data.id, document: data.document }) : json({ error: "Ticket não encontrado no conjunto de teste." }, 404)
  }
  const { data, error } = await supabaseServer().rpc("random_holdout_ticket", { p_category: category })
  const row = (Array.isArray(data) ? data[0] : data) as { id: number; document: string } | undefined
  if (error || !row) return json({ error: "Não foi possível sortear um ticket agora." }, 503)
  return json({ id: row.id, document: row.document })
}
