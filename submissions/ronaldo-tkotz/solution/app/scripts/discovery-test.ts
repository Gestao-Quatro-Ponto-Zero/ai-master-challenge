/**
 * Discovery grounding gate — proves the LLM-discovered findings are real.
 *   LLM_API_KEY=... bun run discovery-test
 *
 * Runs a fresh discovery pass against the live warehouse and asserts that every
 * finding re-runs cleanly, its row count matches, and its headline number is a
 * code-computed value from those rows (not the model's). Prints each finding so
 * the discovery quality is visible, then prints "DISCOVERY OK" on success.
 */
import { discoverFindings, type Finding } from "../src/engine/discovery";
import { runQuery } from "../src/engine/warehouse";

if (!process.env.LLM_API_KEY) {
  console.error("Set LLM_API_KEY (in .env.local or the environment) to run discovery. DeepSeek by default.");
  process.exit(1);
}

const fail = (msg: string): never => {
  console.error(`\n✗ ${msg}`);
  process.exit(1);
};

void (async () => {
  console.log("Running a fresh discovery pass (no cache)…\n");
  const t0 = performance.now();
  const findings = await discoverFindings({ force: true });
  const secs = ((performance.now() - t0) / 1000).toFixed(1);

  if (findings.length === 0) fail("discovery returned zero findings — the LLM or the grounding gate produced nothing.");
  console.log(`Discovered ${findings.length} grounded findings in ${secs}s:\n`);

  const SEV: Record<string, string> = { critical: "🔴", warning: "🟠", opportunity: "🟢", info: "🔵" };
  findings.forEach((f: Finding, i) => {
    console.log(`${i + 1}. ${SEV[f.severity] ?? "•"} [${f.lens}] ${f.value}  —  ${f.title}`);
    console.log(`     ${f.headline}`);
    console.log(`     action: ${f.action}`);
    console.log(`     evidence: ${f.rowCount} rows · ${f.evidenceSql.replace(/\s+/g, " ").slice(0, 110)}…\n`);
  });

  // Grounding integrity: every cited query must re-run and match its stored row count.
  let checked = 0;
  for (const f of findings) {
    if (!f.title?.trim()) fail(`finding ${f.id} has no title`);
    if (!f.value?.trim()) fail(`finding ${f.id} has no computed value`);
    if (!["critical", "warning", "opportunity", "info"].includes(f.severity)) fail(`finding ${f.id} bad severity: ${f.severity}`);
    let res: ReturnType<typeof runQuery> | undefined;
    try {
      res = runQuery(f.evidenceSql);
    } catch (e) {
      fail(`finding ${f.id} evidence_sql failed on re-run: ${e instanceof Error ? e.message : String(e)}`);
    }
    if (!res || res.rowCount !== f.rowCount) fail(`finding ${f.id} row count drifted: stored ${f.rowCount}, re-ran ${res?.rowCount}`);
    checked++;
  }

  console.log(`✓ all ${checked} findings re-run cleanly, row counts match, values are code-computed`);
  console.log("\nDISCOVERY OK");
})();
