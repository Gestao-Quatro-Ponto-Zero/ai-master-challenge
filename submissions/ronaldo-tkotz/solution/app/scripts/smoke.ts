/**
 * Smoke test — proves the engine is wired to the real RavenStack warehouse and grounded.
 * Asserts numbers checked against the database during the process (decisions.md).
 * Run under node/tsx (better-sqlite3 is a native module and does not load under the bun runtime).
 *
 *   bun run smoke   ->   tsx scripts/smoke.ts
 */
import { runQuery, schemaSnapshot } from "../src/engine/warehouse";
import { METRICS } from "../src/engine/metrics";

let failures = 0;
function check(label: string, actual: unknown, expected: unknown) {
  const ok = actual === expected;
  if (!ok) failures++;
  console.log(`${ok ? "✓" : "✗"} ${label}: got ${actual}${ok ? "" : ` (expected ${expected})`}`);
}

// 1. Schema is reachable: source tables, views and data-quality tables.
const schema = schemaSnapshot();
check("schema objects (tables + views)", schema.length, 15);

// 2. Grounded base numbers.
const base = runQuery(METRICS.base_resumo.sql).rows[0] as {
  contas: number;
  assinaturas: number;
  contas_com_evento: number;
  eventos_churn: number;
};
check("accounts", base.contas, 500);
check("subscriptions", base.assinaturas, 5000);
check("accounts with a churn event", base.contas_com_evento, 352);
check("churn events", base.eventos_churn, 600);

// 3. The monthly series covers 24 months; 'features' is the top churn reason (114 events).
check("churn_mensal months", runQuery(METRICS.churn_mensal.sql).rowCount, 24);
const features = runQuery(METRICS.motivos_churn.sql).rows.find(
  (r) => (r as { reason_code: string }).reason_code === "features",
) as { eventos: number } | undefined;
check("churn events with reason 'features'", features?.eventos, 114);

// 4. Every metric in the catalog runs against the warehouse.
for (const id of Object.keys(METRICS)) {
  let ok = true;
  try {
    runQuery(METRICS[id].sql);
  } catch {
    ok = false;
  }
  check(`metric ${id} runs`, ok, true);
}

// 5. Read-only guard actually blocks writes.
let blocked = false;
try {
  runQuery("DELETE FROM accounts");
} catch {
  blocked = true;
}
check("write blocked by guard", blocked, true);

console.log(failures === 0 ? "\nSMOKE OK" : `\nSMOKE FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
