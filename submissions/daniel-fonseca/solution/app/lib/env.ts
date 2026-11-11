import "server-only"

/** Variáveis de ambiente do servidor. Nenhuma delas chega ao navegador (sem prefixo NEXT_PUBLIC_). */
function required(name: string): string {
  const value = process.env[name]
  if (!value) throw new Error(`Variável de ambiente ausente: ${name}`)
  return value
}

function intOr(name: string, fallback: number): number {
  const n = Number(process.env[name])
  return Number.isFinite(n) && n > 0 ? n : fallback
}

export const env = {
  supabaseUrl: () => required("SUPABASE_URL"),
  supabaseServiceRoleKey: () => required("SUPABASE_SERVICE_ROLE_KEY"),
  n8nBaseUrl: () => required("N8N_BASE_URL").replace(/\/+$/, ""),
  n8nWebhookSecret: () => required("N8N_WEBHOOK_SECRET"),
  ipHashSalt: () => required("IP_HASH_SALT"),
  /** Interruptor manual do texto livre (PRD §8). Só muda por instrução do Daniel. */
  freeTextEnabled: () => (process.env.FREE_TEXT_ENABLED ?? "true").toLowerCase() !== "false",
}

/** Limites de uso (PRD §8). Valores padrão = proposta inicial; ajustáveis por variável de ambiente. */
export const rateLimits = {
  triage_free_text: { perIpHour: intOr("RATE_FREE_TEXT_IP_HOUR", 10), perIpDay: intOr("RATE_FREE_TEXT_IP_DAY", 20), globalDay: intOr("RATE_FREE_TEXT_GLOBAL_DAY", 300) },
  triage_holdout: { perIpHour: intOr("RATE_HOLDOUT_IP_HOUR", 30), perIpDay: intOr("RATE_HOLDOUT_IP_DAY", 60), globalDay: intOr("RATE_HOLDOUT_GLOBAL_DAY", 600) },
  hitl: { perIpHour: intOr("RATE_HITL_IP_HOUR", 30), perIpDay: intOr("RATE_HITL_IP_DAY", 120), globalDay: intOr("RATE_HITL_GLOBAL_DAY", 300) },
  inbox: { perIpHour: intOr("RATE_INBOX_IP_HOUR", 60), perIpDay: intOr("RATE_INBOX_IP_DAY", 200), globalDay: intOr("RATE_INBOX_GLOBAL_DAY", 1000) },
  demo_reset: { perIpHour: intOr("RATE_RESET_IP_HOUR", 3), perIpDay: intOr("RATE_RESET_IP_DAY", 3), globalDay: intOr("RATE_RESET_GLOBAL_DAY", 10) },
} as const

export type LimitedAction = keyof typeof rateLimits
