import { json, readJson } from "@/app/api/triage/_core"
import { getTickets, MAX_TOKENS } from "@/lib/queries/tickets"

/**
 * POST /api/tickets — lista da tela Tickets (ADR-0015): os de demonstração + os deste navegador.
 * Os tokens vão no corpo (não na URL), porque dão acesso aos tickets do visitante.
 */
export async function POST(req: Request) {
  const body = await readJson(req)
  const tokens = Array.isArray(body.tokens) ? body.tokens.filter((t): t is string => typeof t === "string").slice(0, MAX_TOKENS) : []
  try {
    return json({ tickets: await getTickets(tokens) })
  } catch {
    return json({ error: "Os tickets não carregaram. Tente de novo em instantes." }, 503)
  }
}
