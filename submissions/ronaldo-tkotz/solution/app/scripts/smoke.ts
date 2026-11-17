/**
 * Smoke test — proves the engine is wired to the real warehouse and grounded.
 * Asserts numbers verified by hand during the discovery pass. Run under node/tsx
 * (better-sqlite3 is a native module and does not load under the bun runtime).
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

// 1. Schema is reachable and complete.
const schema = schemaSnapshot();
check("table count", schema.length, 8);

// 2. Grounded macro numbers (verified in discovery).
const macro = runQuery(METRICS.total_arr.sql).rows[0] as { accounts: number; total_arr: number };
check("account count", macro.accounts, 500);
check("total ARR", macro.total_arr, 180652200);

const ent = runQuery(
  "SELECT SUM(arr_usd) AS v FROM accounts WHERE segment='Enterprise'",
).rows[0] as { v: number };
check("Enterprise ARR", ent.v, 133972800);

// 3. The signature story: 12 critical-health Enterprise renewals inside 120 days.
const cliff = runQuery(METRICS.renewal_cliff.sql);
check("renewal-cliff accounts", cliff.rowCount, 12);

// 4. Read-only guard actually blocks writes.
let blocked = false;
try {
  runQuery("DELETE FROM accounts");
} catch {
  blocked = true;
}
check("write blocked by guard", blocked, true);

console.log(failures === 0 ? "\nSMOKE OK" : `\nSMOKE FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
