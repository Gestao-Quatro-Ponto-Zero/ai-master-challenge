import type { Reason, Tier } from './router'

export interface QueueTicket {
  id: string
  text: string
  label: string
  pred: string
  top: { queue: string; p: number }[]
  tier: Tier
  reason: Reason
  coverage: number
  similarity: number
  why: { term: string; weight: number }[]
  similar: { text: string; queue: string; similarity: number }[]
}

export interface TierStat {
  share: number
  precision: number | null
}

export interface StressScenario {
  id: string
  severity: 'extreme' | 'critical' | 'medium' | 'light'
  name: string
  evidence: string
  guardrail: string
  measured?: unknown
  without_guard?: Record<string, number>
  with_guard?: Record<string, number>
  [key: string]: unknown
}

export interface StressReport {
  baseline: {
    accuracy: number
    ece: number
    thresholds: { t_auto: number; t_assist: number; t_ood_similarity: number; c_min_coverage: number }
    confidence_only_tiers: Record<Tier, TierStat>
    tiers: Record<Tier, TierStat>
    assist_top2_accuracy: number
    guard_false_rejection: number
    reasons: Record<string, number>
  }
  scenarios: StressScenario[]
}

export interface LabReport {
  split: { train: number; val: number; test: number; seed: number }
  classes: string[]
  models: Record<string, { accuracy: number; macro_f1: number; weighted_f1: number; ece: number; fit_seconds: number; infer_ms_per_1k: number; per_class: Record<string, { precision: number; recall: number; f1: number; support: number }> }>
  size_tradeoff: { max_features: number; accuracy: number; macro_f1: number }[]
}
