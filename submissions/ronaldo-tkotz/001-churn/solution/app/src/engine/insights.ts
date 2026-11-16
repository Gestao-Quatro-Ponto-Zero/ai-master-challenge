/**
 * Proactive insights — the feed that surfaces the stories unasked.
 *
 * These no longer come from a fixed catalog of detectors we authored. They are
 * whatever the discovery engine (discovery.ts) found in the connected data at
 * runtime — the LLM picks the lenses; our code grounds every number. This module
 * is a thin adapter from a grounded Finding to the Insight shape the UI consumes.
 */
import { discoverFindings, reanalyzeFindings, getCachedFindings, type Finding } from "./discovery";

export type Severity = "critical" | "warning" | "opportunity" | "info";

export interface Insight {
  id: string;
  severity: Severity;
  title: string; // short lens label for the card heading
  headline: string;
  metric: string;
  evidenceSql: string;
  rows: Record<string, unknown>[];
}

function toInsight(f: Finding): Insight {
  return {
    id: f.id,
    severity: f.severity,
    title: f.lens,
    headline: f.headline,
    metric: f.id,
    evidenceSql: f.evidenceSql,
    rows: f.rows.slice(0, 5),
  };
}

/**
 * Warm-cache insights — synchronous, no LLM. Returns the already-discovered feed
 * for the connected dataset, or null if nothing has been discovered yet (cold).
 * The page uses this to render instantly when warm.
 */
export function cachedInsights(): Insight[] | null {
  const findings = getCachedFindings();
  return findings ? findings.map(toInsight) : null;
}

/** The discovery-driven feed (cached, or a fresh LLM pass if cold). */
export async function detectInsights(): Promise<Insight[]> {
  const findings = await discoverFindings();
  return findings.map(toInsight);
}

/** Force a fresh discovery pass — the "Re-analyze" control. */
export async function reanalyzeInsights(): Promise<Insight[]> {
  const findings = await reanalyzeFindings();
  return findings.map(toInsight);
}
