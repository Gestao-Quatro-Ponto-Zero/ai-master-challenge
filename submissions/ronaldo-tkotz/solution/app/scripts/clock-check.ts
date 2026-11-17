/**
 * Proves the runtime data clock derives the exact temporal anchors that used to
 * be hardcoded across the engine — so the migration is a no-op for THIS dataset
 * (no regression) while being fully derived (any rotated dataset re-anchors).
 */
import { dataClock } from "../src/engine/calendar";

const c = dataClock();

// The values that were previously hardcoded literals in metrics.ts / dashboard.ts.
const expect: Record<string, string | null> = {
  today: "2026-06-12",
  partialMonth: "2026-06",
  lastFullMonth: "2026-05",
  windowStart: "2025-06-01",
  windowEnd: "2026-06-01",
  adoptionStart: "2025-01-01",
};

let ok = true;
for (const [k, v] of Object.entries(expect)) {
  const got = (c as unknown as Record<string, unknown>)[k];
  const pass = got === v;
  if (!pass) ok = false;
  console.log(`${pass ? "OK " : "XX "} ${k.padEnd(14)} ${String(got)}${pass ? "" : `  (expected ${v})`}`);
}
console.log(`-- info  firstDate=${c.firstDate}  lastDate=${c.lastDate}`);
console.log(ok ? "CLOCK OK — derived anchors match the known dataset frame" : "CLOCK MISMATCH");
process.exit(ok ? 0 : 1);
