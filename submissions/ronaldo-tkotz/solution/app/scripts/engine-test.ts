/**
 * Engine test — verifies the tool layer and the proactive insight feed against
 * the real warehouse. No API key needed (this exercises everything except the
 * Claude loop). Run under node/tsx: `bun run engine-test`.
 */
import { toolByName, openaiToolDefs } from "../src/engine/tools";
import { cachedInsights } from "../src/engine/insights";

let failures = 0;
function check(label: string, ok: boolean, detail = "") {
  if (!ok) failures++;
  console.log(`${ok ? "✓" : "✗"} ${label}${ok ? "" : `  ${detail}`}`);
}

// 1. query_warehouse tool returns grounded rows.
const q = toolByName.query_warehouse.handler({ sql: "SELECT COUNT(*) AS n FROM accounts" }) as {
  rows: { n: number }[];
  sql: string;
};
check("query_warehouse → 500 accounts", q.rows[0].n === 500, `got ${q.rows[0].n}`);
check("query_warehouse carries its SQL", typeof q.sql === "string" && q.sql.includes("FROM accounts"));

// 2. read-only guard rejects a write through the tool.
let blocked = false;
try {
  toolByName.query_warehouse.handler({ sql: "DROP TABLE accounts" });
} catch {
  blocked = true;
}
check("query_warehouse blocks a write", blocked);

// 3. run_metric runs a vetted metric.
const seg = toolByName.run_metric.handler({ id: "arr_by_segment" }) as {
  rows: { segment: string; arr: number }[];
};
const ent = seg.rows.find((r) => r.segment === "Enterprise");
check("run_metric arr_by_segment → Enterprise $133.97M", ent?.arr === 133972800, `got ${ent?.arr}`);

// 4. list_metrics + tool defs are coherent.
const metrics = toolByName.list_metrics.handler({}) as { id: string }[];
check("list_metrics returns the vetted set", metrics.length >= 6, `got ${metrics.length}`);
check("openai tool defs expose all tools", openaiToolDefs().length === Object.keys(toolByName).length);

// 5. make_chart echoes a renderable spec.
const chart = toolByName.make_chart.handler({
  type: "bar",
  x: "segment",
  y: ["arr"],
  data: seg.rows,
}) as { chart: { type: string } };
check("make_chart returns a chart spec", chart.chart.type === "bar");

// 6. proactive insights are discovery-driven (LLM at runtime) — covered end to end
//    by `bun run discovery-test`. Here we only check the warm-cache adapter shape
//    without invoking the model: cachedInsights() is sync and returns the cached
//    feed or null, and any cached insight must carry its grounding SQL.
const cached = cachedInsights();
check("cachedInsights() returns an array or null (no LLM)", cached === null || Array.isArray(cached));
if (cached) {
  check("every cached insight carries evidence SQL", cached.every((i) => i.evidenceSql.includes("SELECT")));
  console.log(`\n  → warm cache: ${cached.length} insight(s); e.g. ${cached[0]?.headline ?? "—"}`);
} else {
  console.log("\n  → insight cache cold (run discovery-test to populate); skipped content checks");
}

console.log(failures === 0 ? "\nENGINE OK" : `\nENGINE FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
