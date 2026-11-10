import "server-only"

import { cacheLife } from "next/cache"

import { supabaseServer } from "@/lib/supabase"

/**
 * Resultados da análise (tabelas analysis_*, carregadas por scripts/load_analysis.py a partir de
 * solution/analysis/output/). Mudam só quando os scripts rodam de novo → cache de horas.
 */

export interface DiagnosticCut {
  dimension: "canal" | "prioridade" | "tipo" | "assunto" | "produto"
  value: string
  n: number
  pct_open: number
  pct_pending: number
  n_closed: number
  csat_mean: number
  csat_ci_low: number
  csat_ci_high: number
  hours_median_coherent: number
  pct_incoherent: number
}

export async function getDiagnosticCuts(): Promise<DiagnosticCut[]> {
  "use cache"
  cacheLife("hours")
  const { data, error } = await supabaseServer().from("analysis_diagnostic_cuts").select("*").order("dimension").order("n", { ascending: false })
  if (error) throw new Error(`analysis_diagnostic_cuts: ${error.message}`)
  return data as DiagnosticCut[]
}

/**
 * Um JSON de solution/analysis/output/ (chave = nome do arquivo sem extensão):
 * app_summary, rag_only_policy, classifier_eval, zero_shot_eval, rag_llm_eval, rag_improvements,
 * ensemble_eval, blocklist_eval, db_rag_validation, cost_premises.
 */
export async function getMetric<T = Record<string, unknown>>(key: string): Promise<T> {
  "use cache"
  cacheLife("hours")
  const { data, error } = await supabaseServer().from("analysis_metrics").select("payload").eq("key", key).single()
  if (error) throw new Error(`analysis_metrics[${key}]: ${error.message}`)
  return data.payload as T
}

export interface SensitiveExample {
  ds2_id: number
  kind: "sensitive_hr" | "sensitive_admin"
  note: string
  document: string
  topic_group: string
}

export async function getSensitiveExamples(): Promise<SensitiveExample[]> {
  "use cache"
  cacheLife("hours")
  const { data, error } = await supabaseServer()
    .from("analysis_examples")
    .select("ds2_id, kind, note, ds2_tickets(document, topic_group)")
    .order("kind")
  if (error) throw new Error(`analysis_examples: ${error.message}`)
  return (data ?? []).map((r) => {
    const t = (Array.isArray(r.ds2_tickets) ? r.ds2_tickets[0] : r.ds2_tickets) as { document: string; topic_group: string }
    return { ds2_id: r.ds2_id, kind: r.kind, note: r.note, document: t.document, topic_group: t.topic_group }
  })
}
