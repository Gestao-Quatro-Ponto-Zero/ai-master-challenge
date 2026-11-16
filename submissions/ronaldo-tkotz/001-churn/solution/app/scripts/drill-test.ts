/**
 * drill-test — the grounded contract of the chart drill-down composer.
 *
 * Drill-down works by composing a natural-language follow-up that the AGENT turns
 * into cited SQL. The one thing we must guarantee deterministically (the agent's SQL
 * is verified live in Chrome) is that the COMPOSED QUESTION is grounded-by-construction:
 *   • it names the RAW clicked value (no formatted/abbreviated display text),
 *   • it filters on the GROUPING dimension (spec.x), never the measure,
 *   • it contains no SQL — the agent writes + cites the filter,
 *   • an empty click composes nothing (the caller no-ops).
 * These are exactly the two silent-failure risks the commitment-boundary advisor flagged.
 */
import { composeDrillQuestion } from "../src/app/components/charts/drill";
import type { ChartSpec } from "../src/engine/tools";

let checks = 0;
const ok = (cond: boolean, msg: string) => {
  if (!cond) {
    console.error(`✗ ${msg}`);
    process.exit(1);
  }
  checks++;
  console.log(`✓ ${msg}`);
};

// A categorical chart: ARR (measure) grouped by segment (grouping dimension).
const categorical: ChartSpec = {
  type: "column",
  title: "Total ARR by Customer Segment",
  x: "segment",
  y: ["arr"],
  data: [{ segment: "Enterprise", arr: 134_000_000 }],
};
const q1 = composeDrillQuestion(categorical, "Enterprise");
ok(q1.includes('"Enterprise"'), "categorical drill names the raw clicked value verbatim");
ok(/filter to just that segment/i.test(q1), "categorical drill filters on the GROUPING dimension (segment)");
ok(!/\barr\s*=\s*/i.test(q1) && !/=\s*134/.test(q1), "categorical drill never equates the MEASURE value (no axis mismatch)");
ok(!/\bWHERE\b|\bSELECT\b|\bGROUP BY\b/i.test(q1), "drill question contains NO SQL — the agent writes + cites it");
ok(q1.includes('"Total ARR by Customer Segment"'), "drill carries the chart title for context");

// Raw-value fidelity: a value with special characters passes through unformatted.
const odd: ChartSpec = { type: "bar", title: "X", x: "account", y: ["arr"], data: [] };
ok(composeDrillQuestion(odd, "O'Brien & Co.").includes(`"O'Brien & Co."`), "raw value with apostrophe/ampersand passes through unformatted");

// Scatter: a point is an entity, not a value of the numeric x-axis.
const scatter: ChartSpec = { type: "scatter", title: "Health vs ARR", x: "arr_usd", y: ["health_score"], data: [] };
const q2 = composeDrillQuestion(scatter, "ACC-1291");
ok(/data point "ACC-1291"/.test(q2), "scatter drill names the entity as a data point");
ok(!/that arr usd/i.test(q2), "scatter drill does NOT phrase the filter as the numeric x-axis (the F3 fix)");
ok(!/\bWHERE\b/i.test(q2), "scatter drill contains no SQL");

// Empty / whitespace label composes nothing — the caller no-ops (no broken `= ''` filter).
ok(composeDrillQuestion(categorical, "") === "", "empty label composes nothing");
ok(composeDrillQuestion(categorical, "   ") === "", "whitespace-only label composes nothing");

console.log(`\nDRILL OK — ${checks} checks`);
