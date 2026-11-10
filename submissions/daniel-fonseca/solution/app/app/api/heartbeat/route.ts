import { supabaseServer } from "@/lib/supabase"
import { env } from "@/lib/env"
import { logUsage } from "@/lib/usage"

/**
 * Keep-alive do Supabase (ADR-0006). Chamado pelo Vercel Cron (12:00 UTC, vercel.json) e, como
 * redundância, pelo fluxo 3 do n8n (?source=n8n). Ambos enviam "Authorization: Bearer <CRON_SECRET>".
 * Faz uma escrita e uma leitura reais no banco.
 */
export async function GET(req: Request) {
  if (req.headers.get("authorization") !== `Bearer ${env.cronSecret()}`) {
    return Response.json({ error: "não autorizado" }, { status: 401 })
  }
  const source = new URL(req.url).searchParams.get("source") === "n8n" ? "n8n" : "vercel-cron"
  const t0 = Date.now()
  const db = supabaseServer()
  const { error } = await db.from("heartbeat").insert({ source, ok: true, detail: "keep-alive" })
  const { count } = await db.from("ds2_tickets").select("id", { count: "exact", head: true })
  const ok = !error
  await logUsage(req, { route: "/api/heartbeat", action: "heartbeat", outcome: ok ? "ok" : "server_error", status_code: ok ? 200 : 500, latency_ms: Date.now() - t0 })
  if (!ok) return Response.json({ ok: false, error: error?.message }, { status: 500 })
  return Response.json({ ok: true, source, ds2_tickets: count, ran_at: new Date().toISOString() })
}
