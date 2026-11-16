/**
 * CLI proof of the grounded analyst loop.
 *   LLM_API_KEY=... bun run ask "your question"
 * Prints the answer, the SQL it actually ran (citations), and the tool trace.
 */
import { ask } from "../src/engine/agent";

const question =
  process.argv.slice(2).join(" ").trim() ||
  "Which accounts are most at risk before their renewal, and what's the dollar exposure?";

if (!process.env.LLM_API_KEY) {
  console.error("Set LLM_API_KEY (in .env.local or the environment) to run the analyst loop. DeepSeek by default.");
  process.exit(1);
}

void (async () => {
  const result = await ask(question);

  console.log(`\nQ: ${question}\n`);
  console.log(`${result.answer}\n`);
  console.log(`— model: ${result.model} · steps: ${result.steps} · tool calls: ${result.toolCalls.length}`);
  if (result.citedSql.length) {
    console.log(`\nGrounded in ${result.citedSql.length} quer${result.citedSql.length === 1 ? "y" : "ies"}:`);
    result.citedSql.forEach((sql, i) => console.log(`  [${i + 1}] ${sql.replace(/\s+/g, " ").slice(0, 120)}…`));
  }
})();
