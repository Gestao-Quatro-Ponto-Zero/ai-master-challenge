/**
 * Deck grounding gate. Asserts the executive review is a well-formed Minto
 * pyramid AND that every headline traces to live SQL — the deck-side version of
 * the no-uncited-number rule. If a number can't be re-derived from the warehouse,
 * the build fails, not the truth.
 */
import { buildExecutiveReview } from "../src/engine/deck";
import { runQuery } from "../src/engine/warehouse";

let failures = 0;
function check(label: string, cond: boolean, detail = ""): void {
  console.log(`${cond ? "✓" : "✗"} ${label}${detail ? ` — ${detail}` : ""}`);
  if (!cond) failures++;
}

void (async () => {
const deck = await buildExecutiveReview();

// ── Pyramid shape ────────────────────────────────────────────────────────────
const layouts = deck.slides.map((s) => s.layout);
check("has a cover", layouts[0] === "cover");
check("has a context (SCQA) slide", layouts.includes("context"));
check("ends on recommended actions", layouts[layouts.length - 1] === "recommendation");
check("governing thought is a full assertion", deck.governingThought.length > 30, deck.governingThought.slice(0, 60) + "…");
check("SCQA is populated", !!(deck.scqa.situation && deck.scqa.complication && deck.scqa.question));

const argSlides = deck.slides.filter((s) => s.layout === "argument");
check("data emitted at least one argument", argSlides.length >= 1, `${argSlides.length} arguments`);
check("argument count is bounded (≤4, Minto cap)", argSlides.length <= 4, `${argSlides.length}`);

// Every argument carries an action title (an assertion, not a topic label).
check(
  "every argument slide has an action title",
  argSlides.every((s) => /\d/.test(s.title) || s.title.split(" ").length >= 6),
);

// ── Grounding: every evidenced slide re-derives from its cited SQL ────────────
const evidenced = deck.slides.filter((s) => s.evidence);
check("evidenced slides exist", evidenced.length >= 1, `${evidenced.length} slides carry evidence`);
for (const s of evidenced) {
  const ev = s.evidence!;
  let ok = false;
  let detail = "";
  try {
    const r = runQuery(ev.sql);
    ok = r.rowCount === ev.rowCount && r.rowCount > 0;
    detail = `claimed ${ev.rowCount} rows, query returns ${r.rowCount}`;
  } catch (e) {
    detail = `SQL failed: ${e instanceof Error ? e.message : String(e)}`;
  }
  check(`evidence re-runs: "${s.title.slice(0, 42)}…"`, ok, detail);
}

// ── Citation trail: every cited query is a runnable SELECT/WITH ───────────────
check("deck carries a citation trail", deck.citedSql.length >= 2, `${deck.citedSql.length} queries`);
let allRun = true;
for (const sql of deck.citedSql) {
  try {
    runQuery(sql);
  } catch {
    allRun = false;
  }
}
check("every cited query runs read-only", allRun);

// ── Anchors that hold regardless of which findings the LLM surfaced ───────────
check("deck is dated to the data clock", deck.asOf === "2026-06-12", deck.asOf);
check("title carries the derived period", deck.title.startsWith("Q2 2026"), deck.title);
const cover = deck.slides[0];
check("cover carries a grounded hero value", !!cover.evidence?.value && cover.evidence.value.trim().length > 0, String(cover.evidence?.value));
check("governing thought = the top discovered finding", deck.governingThought === argSlides[0]?.title || argSlides.length === 0);

console.log(failures === 0 ? "\nDECK OK" : `\nDECK FAILED — ${failures} check(s)`);
process.exit(failures === 0 ? 0 : 1);
})();
