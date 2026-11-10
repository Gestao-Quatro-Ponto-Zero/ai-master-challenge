import type { Category, SimilarCase, TriageResult, TriageStatus } from "@/lib/types"

/** Tempos medidos pelo fluxo 1 do n8n (triage_runs.step_ms). */
export interface StepMs {
  classificacao?: number
  redacao?: number
}

/**
 * Resposta do POST /api/triage como o Console usa: o contrato da base (TriageResult) + métricas lidas
 * de triage_runs depois da chamada. No modo offline não existe registro de triagem (triage_run_id = null).
 */
export type ConsoleTriageResult = Omit<TriageResult, "triage_run_id"> & {
  triage_run_id: number | null
  ds2_id: number | null
  ticket_text: string
  step_ms: StepMs | null
  tokens_in: number | null
  tokens_out: number | null
  cost_usd: number | null
  /** tempo do n8n medido no próprio fluxo */
  n8n_latency_ms: number | null
}

/** Item do histórico da sessão (localStorage). Só o necessário para a lista. */
export interface HistoryEntry {
  at: string
  triage_run_id: number | null
  ds2_id: number | null
  excerpt: string
  level: 1 | 2 | 3
  category: Category
  true_category: Category | null
  offline: boolean
}

/** Item da fila de revisão (hitl_queue + triage_runs), sem embedding. */
export interface QueueItem {
  id: number
  triage_run_id: number
  status: "pending" | "approved" | "edited" | "rejected"
  draft_text: string
  checks: string[]
  final_text: string | null
  final_category: Category | null
  reviewer: string | null
  review_note: string | null
  created_at: string
  decided_at: string | null
  ticket_text: string
  category: Category
  confidence: number
  level_reason: string | null
  similar_cases: SimilarCase[]
  ds2_id: number | null
}

/** Alerta da caixa (notifications), com o texto exato que iria para o Slack. */
export interface InboxItem {
  id: number
  kind: "level3_alert" | "heartbeat_failure" | "usage_alert"
  title: string
  body: string
  read_at: string | null
  assigned_to: string | null
  assigned_at: string | null
  created_at: string
  triage_run_id: number | null
  ticket_text: string | null
  category: Category | null
  summary: string | null
  risk_signals: string[]
  suggested_owner: string | null
}

export interface NeighborTicket {
  id: number
  excerpt: string
  similarity: number
}

export interface HitlApiResult {
  hitl_id: number
  decision: "approve" | "edit" | "reject"
  triage_run_id: number
  triage_status: TriageStatus
  resolution_id: number | null
  neighbor: NeighborTicket | null
}

/** Ticket do holdout sorteado (sem o rótulo real, revelado só depois da triagem). */
export interface HoldoutTicket {
  id: number
  document: string
}
