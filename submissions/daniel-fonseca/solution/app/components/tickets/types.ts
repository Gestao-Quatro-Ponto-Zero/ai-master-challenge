import type { StepMs } from "@/components/console/types"
import type { Category, Level, SimilarCase, TriageStatus } from "@/lib/types"

/** Nota interna do caminho Somente humano (pt-BR), gerada pelo fluxo 1. */
export interface HumanSummary {
  summary: string
  risk_signals: string[]
  suggested_owner: string
}

/** Texto que iria para o Slack no caminho Somente humano. */
export interface SlackAlert {
  title: string
  body: string
}

/** Rascunho da Revisão humana (hitl_queue). */
export interface TicketDraft {
  hitl_id: number
  status: "pending" | "approved" | "edited" | "rejected"
  draft_text: string
  checks: string[]
  final_text: string | null
  final_category: Category | null
  decided_at: string | null
}

/**
 * Um ticket como a tela Tickets mostra (ADR-0015): a triagem (triage_runs) com o rascunho, a nota interna
 * e a resposta do atendente. Nunca traz o embedding nem o client_token.
 */
export interface TicketItem {
  id: number
  created_at: string
  is_demo: boolean
  ds2_id: number | null
  /** rótulo real do holdout, quando o ticket foi sorteado sem edição */
  true_category: Category | null
  ticket_text: string
  status: TriageStatus
  level: Level | null
  level_reason: string | null
  category: Category | null
  confidence: number | null
  votes: Partial<Record<Category, number>>
  similar_cases: SimilarCase[]
  response_text: string | null
  draft: TicketDraft | null
  human_summary: HumanSummary | null
  alert: SlackAlert | null
  human_reply: string | null
  human_reply_at: string | null
  step_ms: StepMs | null
  tokens_in: number | null
  tokens_out: number | null
  cost_usd: number | null
  latency_ms: number | null
}
