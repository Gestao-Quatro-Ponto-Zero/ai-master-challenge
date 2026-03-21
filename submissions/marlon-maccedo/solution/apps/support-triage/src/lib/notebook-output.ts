import fs from 'fs'
import path from 'path'

const DATA = path.join(process.cwd(), 'data')

// ── Types ──────────────────────────────────────────────────────────────────────

export interface PriorityRow {
  priority: string
  volume: number
  avg_csat: number
  resolution_rate: number
  avg_resolution_h: number
}

export interface CsatDrivers {
  pearson_r: number
  pearson_p: number
  kruskal_channel_h: number; kruskal_channel_p: number
  kruskal_type_h: number;    kruskal_type_p: number
  kruskal_priority_h: number; kruskal_priority_p: number
  top_driver: string
  top_driver_r: number
  conclusion: string
}

export interface WasteStats {
  median_hours: number
  mean_hours: number
  above_median_pct: number
  avg_excess_hours: number
  annual_volume: number
  annual_excess_tickets: number
  annual_excess_hours: number
  annual_cost_brl: number
}

export interface HeatmapCell {
  channel: string
  type: string
  avg_hours: number
}

export interface DataQuality {
  same_day_timestamps_pct: number
  csat_is_uniform: boolean
  has_placeholder_text: boolean
}

export interface DiagnosticOutput {
  generated_at: string
  priority: PriorityRow[]
  csat_drivers: CsatDrivers
  waste: WasteStats
  bottleneck_heatmap: HeatmapCell[]
  data_quality: DataQuality
}

export interface CategoryAccuracy {
  category: string
  total: number
  correct: number
  accuracy: number
}

export interface FailureExample {
  text: string
  true_label: string
  keyword_pred: string
  llm_reasoning: string
}

export interface ClassifierOutput {
  generated_at: string
  overall_accuracy: number
  majority_baseline: number
  random_baseline: number
  lift_over_majority: number
  llm_accuracy_estimate: number
  per_category: CategoryAccuracy[]
  failure_examples: FailureExample[]
  total_tickets_evaluated: number
}

// ── Readers ───────────────────────────────────────────────────────────────────

function readJson<T>(filename: string): T | null {
  const p = path.join(DATA, filename)
  try {
    if (!fs.existsSync(p)) return null
    return JSON.parse(fs.readFileSync(p, 'utf-8')) as T
  } catch {
    return null
  }
}

export function getDiagnosticOutput(): DiagnosticOutput | null {
  return readJson<DiagnosticOutput>('diagnostic_output.json')
}

export function getClassifierOutput(): ClassifierOutput | null {
  return readJson<ClassifierOutput>('classifier_output.json')
}
