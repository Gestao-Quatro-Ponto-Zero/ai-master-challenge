/**
 * Catalog probe — ISC-180: every Analyses-catalog question returns a grounded,
 * non-error answer. Runs the REAL analyst loop (same engine the chat face uses)
 * against the local warehouse; a question passes only if the answer is
 * non-empty AND cites at least one query. Serial on purpose — readable output
 * and no rate pressure on the LLM endpoint.
 *
 *   LLM_API_KEY=... bun run catalog-probe            # all 12
 *   LLM_API_KEY=... bun run catalog-probe qbr-brief  # one item by id
 */
import { ask } from "../src/engine/agent";
import { ANALYSES } from "../src/app/components/dashboard/analyses-catalog";

if (!process.env.LLM_API_KEY) {
  console.error("Set LLM_API_KEY (e.g. `set -a; source .env.local; set +a`) to run the analyst loop.");
  process.exit(1);
}

const only = process.argv[2]?.trim();
const items = ANALYSES.flatMap((g) => g.items.map((i) => ({ ...i, role: g.role }))).filter(
  (i) => !only || i.id === only,
);
if (items.length === 0) {
  console.error(`No catalog item matches id '${only}'.`);
  process.exit(1);
}

void (async () => {
  let failed = 0;
  for (const item of items) {
    const t0 = Date.now();
    try {
      const r = await ask(item.question);
      const grounded = (r.citedSql?.length ?? 0) > 0;
      const answered = (r.answer ?? "").trim().length > 40;
      const ok = grounded && answered;
      if (!ok) failed++;
      console.log(
        `${ok ? "PASS" : "FAIL"}  [${item.role}] ${item.id} — ${r.citedSql.length} queries, ${r.answer?.length ?? 0} chars, ${Math.round((Date.now() - t0) / 1000)}s${ok ? "" : "  <-- not grounded or too thin"}`,
      );
    } catch (e) {
      failed++;
      console.log(`FAIL  [${item.role}] ${item.id} — threw: ${e instanceof Error ? e.message : String(e)}`);
    }
  }
  console.log(`\nCATALOG PROBE: ${items.length - failed}/${items.length} grounded`);
  process.exit(failed > 0 ? 1 : 0);
})();
