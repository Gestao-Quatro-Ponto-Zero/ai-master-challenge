import "server-only"

import { createHash } from "node:crypto"

import { env, rateLimits, type LimitedAction } from "@/lib/env"
import { supabaseServer } from "@/lib/supabase"

export type UsageAction = LimitedAction | "heartbeat"
export type UsageOutcome = "ok" | "rate_limited" | "client_error" | "server_error" | "offline" | "disabled"

/** IP do visitante (Vercel envia x-forwarded-for). Só o hash com sal é gravado (PRD §8). */
export function clientIp(req: Request): string {
  const fwd = req.headers.get("x-forwarded-for")
  return (fwd?.split(",")[0] ?? req.headers.get("x-real-ip") ?? "0.0.0.0").trim()
}

export function ipHash(req: Request): string {
  return createHash("sha256").update(`${clientIp(req)}|${env.ipHashSalt()}`).digest("hex")
}

function shortUa(req: Request): string | null {
  const ua = req.headers.get("user-agent")
  return ua ? ua.slice(0, 160) : null
}

/** Padrões de tentativa de prompt injection: só marcam o evento para o monitoramento (PRD §8.1). */
const INJECTION = [
  /ignore (all |any )?(previous|prior|above) (instructions|prompts?)/i,
  /(system|developer) prompt/i,
  /(reveal|show|print|leak).{0,30}(prompt|instructions|api[ _-]?key|secret|token)/i,
  /\bjailbreak\b/i,
  /you are now/i,
]
export function detectFlag(text: string | undefined | null): string | null {
  if (!text) return null
  return INJECTION.some((re) => re.test(text)) ? "prompt_injection" : null
}

export interface LimitCheck {
  allowed: boolean
  retryAfter?: number
  message?: string
}

/** Conta eventos aceitos em usage_events e aplica os limites por IP (hora/dia) e global (dia). */
export async function checkLimit(action: LimitedAction, hash: string): Promise<LimitCheck> {
  const limits = rateLimits[action]
  const db = supabaseServer()
  const now = Date.now()
  const hourAgo = new Date(now - 3600_000).toISOString()
  const dayAgo = new Date(now - 86_400_000).toISOString()
  const base = () => db.from("usage_events").select("id", { count: "exact", head: true }).eq("action", action).eq("outcome", "ok")
  const [ipHour, ipDay, globalDay] = await Promise.all([
    base().eq("ip_hash", hash).gte("ts", hourAgo),
    base().eq("ip_hash", hash).gte("ts", dayAgo),
    base().gte("ts", dayAgo),
  ])
  if ((ipHour.count ?? 0) >= limits.perIpHour)
    return { allowed: false, retryAfter: 3600, message: `Limite de ${limits.perIpHour} por hora atingido para este acesso. Tente novamente mais tarde.` }
  if ((ipDay.count ?? 0) >= limits.perIpDay)
    return { allowed: false, retryAfter: 86_400, message: `Limite diário de ${limits.perIpDay} atingido para este acesso.` }
  if ((globalDay.count ?? 0) >= limits.globalDay)
    return { allowed: false, retryAfter: 86_400, message: "O limite diário de uso da demonstração foi atingido. Tente novamente amanhã." }
  return { allowed: true }
}

export interface UsageEvent {
  route: string
  action: UsageAction
  outcome: UsageOutcome
  status_code: number
  latency_ms?: number
  triage_run_id?: number | null
  flag?: string | null
}

/** Grava o evento; falha de gravação nunca derruba a resposta ao visitante. */
export async function logUsage(req: Request, ev: UsageEvent): Promise<void> {
  try {
    await supabaseServer().from("usage_events").insert({ ...ev, ip_hash: ipHash(req), ua: shortUa(req) })
  } catch {
    /* sem log não há o que fazer além de seguir */
  }
}
