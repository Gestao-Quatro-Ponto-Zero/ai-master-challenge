import type { ChartSpec } from "@/engine/tools";

/**
 * Compose the natural-language drill-down follow-up for a click on a chart element.
 *
 * Grounded-by-construction: the question names the RAW clicked value (the caller
 * passes the untruncated datum, never the formatted/abbreviated SVG text) and the
 * chart's GROUPING dimension (`spec.x`) — never the measure — so the agent filters
 * on the right axis. It contains NO SQL: the agent receives this as a question,
 * writes the filter query itself, and cites it (the grounding invariant). Returns
 * "" when there is nothing to drill (an empty/whitespace label), so the caller no-ops.
 *
 * Scatter is special-cased: a point is an individual entity (an account), not a
 * value of the numeric x-axis, so it drills "this record" rather than filtering on x.
 */
export function composeDrillQuestion(spec: ChartSpec, label: string): string {
  const value = String(label ?? "").trim();
  if (!value) return "";
  const xField = (spec.x || "").replace(/_/g, " ").trim();
  const metric = (spec.y?.[0] || "").replace(/_/g, " ").trim();
  const title = (spec.title || "").trim();
  const fromChart = `From the chart${title ? ` "${title}"` : ""}`;

  if (spec.type === "scatter") {
    return `${fromChart}, drill into the data point "${value}": filter to just that record and show the detail behind it — break down what drives its numbers, and chart the breakdown.`;
  }

  return (
    `${fromChart}${metric ? ` (${metric}${xField ? ` by ${xField}` : ""})` : ""}, drill into "${value}": ` +
    `filter to just that ${xField || "category"} and break ${metric || "it"} down one level finer — ` +
    `show the detail behind it, and chart the breakdown.`
  );
}
