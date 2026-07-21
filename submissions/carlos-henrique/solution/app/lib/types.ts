export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type DataRecord = Record<string, JsonValue>;

export interface Metric {
  label: string;
  value: number;
  context: string;
}

export interface ExplainData {
  what_was_observed?: string;
  why_it_appears_here?: string;
  evidence?: JsonValue;
  population?: string;
  denominator?: string | number;
  quality?: string;
  stability?: string;
  limitations?: JsonValue;
  authorized_next_step?: string;
  prohibited_interpretation?: string;
  provenance?: JsonValue;
}

export interface JourneySample {
  profile: string;
  account_key: string;
  selection_rationale: string;
  journey_scope: string;
  period: { start: string; end: string };
  outcome: string;
  taxonomy: string;
  quality: { population: string; coverage: number; confidence: string; stability: string; requires_data_review: boolean };
  event_count: number;
  distinct_event_types: number;
  timeline: Array<{ date: string; event: string; count: number }>;
  pattern_keys: string[];
  pattern_count: number;
  limitations: string[];
  explanation: ExplainData;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  properties: Record<string, JsonValue>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, JsonValue>;
}

export interface WatchlistItem {
  watchlist_item_key: string;
  account_key: string;
  queue: string;
  category: string;
  priority: string;
  evidence_strength: string;
  temporal_urgency: string;
  materiality: string;
  data_confidence: string;
  taxonomy: string;
  associated_mrr_band: string;
  requires_data_review: boolean;
  requires_human_review: boolean;
  rule: { id: string; name: string; version: string };
  quality_coverage: number;
  limitation_count: number;
  human_owner: string;
  authorized_investigation: string;
  prohibited_actions: string[];
  explanation: ExplainData;
}

export interface Experiment {
  experiment_id: string;
  name: string;
  queue: string;
  design: string;
  status: string;
  eligible_accounts: number;
  required_sample: number;
  primary_metric: string;
  mde: number;
  power: number;
  follow_up_days: number;
  contamination_risk: string;
  ethical_risk: string;
  causal_status: "UNTESTED";
  [key: string]: JsonValue;
}
