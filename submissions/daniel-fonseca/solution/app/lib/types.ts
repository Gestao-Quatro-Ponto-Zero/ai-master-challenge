/**
 * Contratos compartilhados entre as frentes A (Painel) e B (Console). Espelham as tabelas do Supabase
 * (migrations 0003–0005) e as respostas dos webhooks do n8n (docs/n8n-flows.md).
 */

export const CATEGORIES = [
  "Hardware",
  "HR Support",
  "Access",
  "Miscellaneous",
  "Storage",
  "Purchase",
  "Internal Project",
  "Administrative rights",
] as const
export type Category = (typeof CATEGORIES)[number]
export const SENSITIVE_CATEGORIES: Category[] = ["HR Support", "Administrative rights"]

/** Nível interno (banco/ADRs) → caminho na interface (PRD §5). */
export type Level = 1 | 2 | 3
export type PathKey = "auto" | "review" | "human"

export type TriageStatus =
  | "received"
  | "auto_answered"
  | "pending_review"
  | "awaiting_human"
  | "answered_after_review"
  | "rejected"
  | "error"

export interface SimilarCase {
  id: number
  category: Category
  similarity: number
  snippet: string
}

export interface ValidatedResolution {
  id: number
  resolution_text: string
  similarity: number
  source: "playbook" | "hitl"
}

/** POST /api/triage — corpo aceito. */
export interface TriageRequest {
  mode: "holdout" | "free_text"
  /** obrigatório em mode = holdout */
  ds2_id?: number
  /** obrigatório em mode = free_text (inglês, até 4.000 caracteres) */
  ticket_text?: string
  /** ticket sorteado e editado pelo visitante: guarda a origem para a marca "editado" */
  edited_from?: number
}

/** Resposta do webhook do fluxo 1 (repassada pelo /api/triage) + campos do app. */
export interface TriageResult {
  triage_run_id: number
  status: TriageStatus
  level: Level
  level_reason: string
  category: Category
  confidence: number
  sensitive_share: number
  votes: Partial<Record<Category, number>>
  similar_cases: SimilarCase[]
  resolutions: ValidatedResolution[]
  response_text: string | null
  resolution_id: number | null
  hitl: { hitl_id: number; draft_text: string; checks: string[] } | null
  /** o fluxo 1 deixou de gravar na caixa (ADR-0015): sempre null */
  notification: null
  /** Somente humano: texto do Slack simulado e nota interna em pt-BR */
  alert?: { title: string; body: string } | null
  human_summary?: { summary: string; risk_signals: string[]; suggested_owner: string } | null
  /** preenchidos pelo app depois da chamada */
  true_category?: Category | null
  offline?: boolean
  latency_ms?: number
}

/** POST /api/hitl — corpo aceito. */
export interface HitlDecisionRequest {
  hitl_id: number
  decision: "approve" | "edit" | "reject"
  final_text?: string
  final_category?: Category | ""
  note?: string
}

export interface HitlDecisionResult {
  hitl_id: number
  decision: HitlDecisionRequest["decision"]
  triage_run_id: number
  triage_status: TriageStatus
  resolution_id: number | null
}

/** Linha de public.v_ops_summary. */
export interface OpsSummary {
  triagens: number
  automaticas: number
  revisao_humana: number
  somente_humano: number
  holdout_total: number
  holdout_acertos: number
  latencia_p50_ms: number | null
  latencia_p95_ms: number | null
  custo_usd_total: number
  hitl_aprovadas: number
  hitl_editadas: number
  hitl_rejeitadas: number
  hitl_pendentes: number
  hitl_tempo_medio_s: number | null
  base_playbook: number
  base_aprendidas: number
}

/** Origem de um número exibido (ADR-0003): sempre visível ao lado do valor. */
export type DataOrigin = "medido" | "benchmark" | "premissa" | "calculo"

export interface ApiError {
  error: string
  /** segundos até liberar, quando o limite de uso foi atingido */
  retry_after?: number
}
