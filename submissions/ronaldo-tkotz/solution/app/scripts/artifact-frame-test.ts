/**
 * artifact-frame-test — headless unit proof for the chat Artifact Layer (Stream A).
 *
 * Pure logic only (no DB, no warehouse, no LLM): the shape-gating that feeds the
 * toolbar's type switcher, the projection transform (sort correctness, line/area
 * sort-skip, non-mutation of grounded rows), the one display-number parser, and the
 * markdown-table cell→object conversion behind a markdown-table pin.
 *
 * Run: `bun run artifact-frame-test` (shells to node/tsx — matches every other test).
 */
import { allowedChartTypes, applyTransform, parseDisplayNumber } from "../src/engine/parts";
import type { ChartSpec } from "../src/engine/tools";
import { chartSpecFromRows, markdownRowsToTablePayload, sortMarkdownBody } from "../src/app/components/artifacts/helpers";

let passed = 0;
function ok(label: string, cond: boolean, detail = ""): void {
  if (!cond) {
    console.error(`✗ ${label}${detail ? ` — ${detail}` : ""}`);
    console.error("\nARTIFACT-FRAME FAILED");
    process.exit(1);
  }
  passed++;
  console.log(`✓ ${label}`);
}
const has = (arr: readonly string[], v: string): boolean => arr.includes(v);

// ── 1. allowedChartTypes gating on 4 shapes ──────────────────────────────────
{
  // Shape A — one y, few rows, non-numeric category x.
  const a = allowedChartTypes({
    x: "segment",
    y: ["arr"],
    data: [{ segment: "Ent", arr: 10 }, { segment: "Mid", arr: 20 }, { segment: "SMB", arr: 30 }, { segment: "Gov", arr: 40 }],
  });
  ok("A: bar/column offered (rows≤50)", has(a, "bar") && has(a, "column"));
  ok("A: pie/donut/radar offered (1-y, few rows, non-neg)", has(a, "pie") && has(a, "donut") && has(a, "radar"));
  ok("A: line/area offered (rows≥2)", has(a, "line") && has(a, "area"));
  ok("A: scatter NOT offered (x non-numeric)", !has(a, "scatter"));
  ok("A: stacked/combo NOT offered (needs ≥2 y)", !has(a, "stacked") && !has(a, "combo"));

  // Shape B — two y series.
  const b = allowedChartTypes({
    x: "month",
    y: ["new_arr", "churn_arr"],
    data: [{ month: "Jan", new_arr: 5, churn_arr: 1 }, { month: "Feb", new_arr: 6, churn_arr: 2 }, { month: "Mar", new_arr: 7, churn_arr: 3 }],
  });
  ok("B: stacked offered (≥2 y, rows≤50)", has(b, "stacked"));
  ok("B: combo offered (exactly 2 y)", has(b, "combo"));
  ok("B: pie/donut NOT offered (needs 1 y)", !has(b, "pie") && !has(b, "donut"));

  // Shape C — numeric x (correlation).
  const c = allowedChartTypes({
    x: "seats",
    y: ["arr"],
    data: [{ seats: 10, arr: 1 }, { seats: 20, arr: 2 }, { seats: 30, arr: 3 }],
  });
  ok("C: scatter offered (x numeric)", has(c, "scatter"));

  // Shape D — 60 rows.
  const d = allowedChartTypes({
    x: "day",
    y: ["v"],
    data: Array.from({ length: 60 }, (_, i) => ({ day: `d${i}`, v: i })),
  });
  ok("D: bar/column NOT offered (rows>50)", !has(d, "bar") && !has(d, "column"));
  ok("D: pie/radar NOT offered (too many rows)", !has(d, "pie") && !has(d, "radar"));
  ok("D: line/area still offered (rows≥2)", has(d, "line") && has(d, "area"));
}

// ── 2. applyTransform: sort correctness + line/area skip + non-mutation ───────
{
  const base: ChartSpec = {
    type: "column",
    title: "ARR by segment",
    x: "segment",
    y: ["arr"],
    data: [{ segment: "Mid", arr: 20 }, { segment: "Ent", arr: 40 }, { segment: "SMB", arr: 10 }],
  };
  const originalOrder = base.data.map((r) => r.segment);

  const desc = applyTransform(base, { sortBy: "value", sortDir: "desc" });
  ok("sort value desc orders by y[0] descending", desc.data.map((r) => r.arr).join(",") === "40,20,10");
  ok("sort returns a NEW data array (non-mutating)", desc.data !== base.data);
  ok("input spec.data left untouched after sort", base.data.map((r) => r.segment).join(",") === originalOrder.join(","));

  const asc = applyTransform(base, { sortBy: "value", sortDir: "asc" });
  ok("sort value asc orders ascending", asc.data.map((r) => r.arr).join(",") === "10,20,40");

  const byLabel = applyTransform(base, { sortBy: "label", sortDir: "asc" });
  ok("sort label asc orders alphabetically", byLabel.data.map((r) => r.segment).join(",") === "Ent,Mid,SMB");

  // line/area must NOT value-sort (they stay x-ordered upstream in ChartView).
  const lineSpec: ChartSpec = { ...base, type: "line" };
  const lineSorted = applyTransform(lineSpec, { sortBy: "value", sortDir: "desc" });
  ok("line skips the value-sort (stays x-ordered upstream)", lineSorted.data.map((r) => r.segment).join(",") === originalOrder.join(","));
  const areaSorted = applyTransform({ ...base, type: "area" }, { sortBy: "value", sortDir: "desc" });
  ok("area skips the value-sort", areaSorted.data.map((r) => r.segment).join(",") === originalOrder.join(","));

  // Type-only transform re-projects without touching rows.
  const asBar = applyTransform(base, { type: "bar" });
  ok("type-only transform changes type, preserves row order", asBar.type === "bar" && asBar.data.map((r) => r.segment).join(",") === originalOrder.join(","));
}

// ── 3. parseDisplayNumber on the mandated cells ──────────────────────────────
{
  ok('parseDisplayNumber("$21.9M") = 21_900_000', parseDisplayNumber("$21.9M") === 21_900_000, String(parseDisplayNumber("$21.9M")));
  ok('parseDisplayNumber("84%") = 84', parseDisplayNumber("84%") === 84);
  ok('parseDisplayNumber("1,234") = 1234', parseDisplayNumber("1,234") === 1234);
  ok('parseDisplayNumber("2026-01") = null (a date, not a magnitude)', parseDisplayNumber("2026-01") === null);
  ok('parseDisplayNumber("n/a") = null', parseDisplayNumber("n/a") === null);
}

// ── 4. markdown-table cell→object conversion (+ sort, + evidence→chart build) ─
{
  const rows = [
    ["Account", "ARR"],
    ["Acme", "$1.2M"],
    ["Globex", "$800K"],
  ];
  const payload = markdownRowsToTablePayload(rows);
  ok("markdown payload columns = header cells", payload.columns.join(",") === "Account,ARR");
  ok("markdown payload rows = body cells keyed by header", payload.rows.length === 2 && payload.rows[0].Account === "Acme" && payload.rows[0].ARR === "$1.2M");
  ok("markdown payload keys the second row too", payload.rows[1].Globex === undefined && payload.rows[1].Account === "Globex");

  // Blank header gets a stable fallback key so no cell is dropped.
  const blank = markdownRowsToTablePayload([["", "ARR"], ["x", "$1"]]);
  ok("blank header → stable fallback column key", blank.columns[0] === "col1" && blank.rows[0].col1 === "x");

  // Body sort by the $ column (magnitude), non-mutating.
  const body = rows.slice(1);
  const sorted = sortMarkdownBody(body, 1, "desc");
  ok("markdown body sorts by magnitude ($1.2M > $800K)", sorted[0][0] === "Acme" && sorted[1][0] === "Globex");
  ok("markdown body sort is non-mutating", body[0][0] === "Acme" && body !== sorted);

  // Evidence rows → grounded chart spec (x = category, y = numeric).
  const spec = chartSpecFromRows(["segment", "arr_usd"], [{ segment: "Ent", arr_usd: 40 }, { segment: "SMB", arr_usd: 10 }], "Result set");
  ok("chartSpecFromRows picks non-numeric category as x", spec.x === "segment");
  ok("chartSpecFromRows picks numeric column(s) as y", spec.y.join(",") === "arr_usd");
  ok("chartSpecFromRows defaults type to column when allowed", spec.type === "column");
}

console.log(`\nARTIFACT-FRAME OK — ${passed} checks passed`);
