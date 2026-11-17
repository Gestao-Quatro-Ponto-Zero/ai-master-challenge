/**
 * saved-insights-test — headless proof of the deck tray (pins).
 *
 * Covers the phase-2 invariants: idempotent pin (dedupe by source), pins outlive
 * a deleted conversation (FK SET NULL), self-contained cited_sql, order-only
 * reorder, rename, remove. Throwaway DB, no browser, no LLM.
 *
 * Run: `bun run saved-insights-test` (shells to tsx — better-sqlite3 is native).
 */
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

const tmp = path.join(os.tmpdir(), `veta-pins-test-${process.pid}.sqlite`);
for (const f of [tmp, `${tmp}-wal`, `${tmp}-shm`]) if (fs.existsSync(f)) fs.rmSync(f);
process.env.APP_DB_PATH = tmp;

import {
  appdb,
  createConversation,
  deleteConversation,
  createSavedInsight,
  listSavedInsights,
  renameSavedInsight,
  deleteSavedInsight,
  reorderSavedInsights,
} from "../src/engine/appdb";

const USER_A = "user-a";
const USER_B = "user-b";

let passed = 0;
const checks: string[] = [];
function ok(label: string, cond: boolean): void {
  if (!cond) {
    console.error(`✗ ${label}`);
    console.error("\nPINS FAILED");
    process.exit(1);
  }
  passed++;
  checks.push(label);
}

// ── Schema: phase-2 shape — conversation_id nullable, FK SET NULL, dedup key
const db = appdb();
const cols = db.prepare("PRAGMA table_info(saved_insights)").all() as { name: string; notnull: number }[];
ok("ISC-80: saved_insights has source_kind + source_id", cols.some((c) => c.name === "source_kind") && cols.some((c) => c.name === "source_id"));
ok("SP05: saved_insights.user_id is NOT NULL", cols.find((c) => c.name === "user_id")!.notnull === 1);
ok("ISC-80: conversation_id is nullable", cols.find((c) => c.name === "conversation_id")!.notnull === 0);
const fk = db.prepare("PRAGMA foreign_key_list(saved_insights)").all() as { on_delete: string; table: string }[];
ok("ISC-80: FK to conversations is ON DELETE SET NULL", fk.some((f) => f.table === "conversations" && f.on_delete === "SET NULL"));

// ── Pin a chat turn (with provenance) — stores the whole grounded turn
const conv = createConversation({ title: "Churn risk", userId: USER_A });
const pin1 = createSavedInsight({
  sourceKind: "turn",
  sourceId: "turn-abc",
  userId: USER_A,
  conversationId: conv.id,
  question: "Who is at risk of churning?",
  answer: "23 accounts critical, $40.9M ARR.",
  citedSql: ["SELECT * FROM accounts WHERE health_score < 40", "SELECT SUM(arr_usd) FROM accounts WHERE health_score < 40"],
  title: "Churn risk — 23 accounts",
});
ok("ISC-81: pin stores question + answer", pin1.question === "Who is at risk of churning?" && pin1.answer === "23 accounts critical, $40.9M ARR.");
ok("ISC-87: pin stores its own cited_sql_json (self-contained)", JSON.parse(pin1.cited_sql_json!).length === 2);
ok("ISC-81: pin links provenance conversation_id", pin1.conversation_id === conv.id);

// ── Idempotency — pinning the same source twice yields ONE row
const pin1again = createSavedInsight({ sourceKind: "turn", sourceId: "turn-abc", userId: USER_A, conversationId: conv.id, question: "dup", answer: "dup", citedSql: [] });
ok("ISC-82: re-pinning the same source returns the same row", pin1again.id === pin1.id);
ok("ISC-82: re-pin does not overwrite (DO NOTHING keeps original)", pin1again.answer === "23 accounts critical, $40.9M ARR.");
ok("ISC-82: only one pin exists for that source", listSavedInsights(USER_A).filter((p) => p.source_id === "turn-abc").length === 1);


// ── SP05: another user may pin the same natural source, and cannot mutate A's pin
const pin1b = createSavedInsight({ sourceKind: "turn", sourceId: "turn-abc", userId: USER_B, question: "same source", answer: "B copy", citedSql: [] });
ok("SP05: dedupe is per-user, not global", pin1b.id !== pin1.id && listSavedInsights(USER_B).length === 1);
ok("SP05: B cannot rename A's pin by id", renameSavedInsight(pin1.id, USER_B, "pwned") === false);
ok("SP05: B cannot delete A's pin by id", deleteSavedInsight(pin1.id, USER_B) === false);

// ── Pin a rail finding (no conversation, no turn) — dedups by (finding, id)
const pinF = createSavedInsight({ sourceKind: "finding", sourceId: "finding-nps", userId: USER_A, question: "Enterprise NPS", answer: "NPS fell 8.8 pts", citedSql: ["SELECT AVG(nps) FROM nps_responses"], title: "NPS collapse" });
ok("ISC-86: a finding can be pinned with null conversation_id", pinF.conversation_id === null && pinF.source_kind === "finding");
const pinFagain = createSavedInsight({ sourceKind: "finding", sourceId: "finding-nps", userId: USER_A, citedSql: [] });
ok("ISC-86/82: finding dedupes too (NULL conversation_id doesn't defeat dedupe)", pinFagain.id === pinF.id && listSavedInsights(USER_A).filter((p) => p.source_id === "finding-nps").length === 1);

// ── A third pin, then reorder (order-only, never deletes)
const pin3 = createSavedInsight({ sourceKind: "turn", sourceId: "turn-xyz", userId: USER_A, conversationId: conv.id, question: "Expansion?", answer: "$10M upside", citedSql: ["SELECT 1"] });
let list = listSavedInsights(USER_A);
ok("three pins exist, sort_order ascending", list.length === 3 && list[0].sort_order <= list[1].sort_order && list[1].sort_order <= list[2].sort_order);
// reverse the order
const reversed = [...list].reverse().map((p) => p.id);
reorderSavedInsights(USER_A, reversed);
list = listSavedInsights(USER_A);
ok("ISC-85: reorder sets the new order", list.map((p) => p.id).join(",") === reversed.join(","));
// reorder with a partial array (omit one) must NOT delete the omitted pin
reorderSavedInsights(USER_A, [pin3.id]);
ok("ISC-85: order-only reorder never deletes an omitted pin", listSavedInsights(USER_A).length === 3);

// ── Rename + remove
ok("ISC-85: rename updates the title", renameSavedInsight(pin1.id, USER_A, "Renewal cliff") && listSavedInsights(USER_A).find((p) => p.id === pin1.id)!.title === "Renewal cliff");
ok("ISC-85: delete removes the pin", deleteSavedInsight(pin3.id, USER_A) && listSavedInsights(USER_A).every((p) => p.id !== pin3.id));

// ── The key invariant: pins OUTLIVE their conversation (SET NULL, not cascade)
const before = listSavedInsights(USER_A).filter((p) => p.conversation_id === conv.id).length;
ok("precondition: pin1 still linked to the conversation", before === 1);
deleteConversation(conv.id, USER_A);
const survivor = listSavedInsights(USER_A).find((p) => p.id === pin1.id);
ok("ISC-80: deleting the conversation does NOT delete the pin", Boolean(survivor));
ok("ISC-80: the surviving pin's conversation_id is set to NULL", survivor!.conversation_id === null);
ok("ISC-87: the orphaned pin still has its cited_sql for re-grounding", JSON.parse(survivor!.cited_sql_json!).length === 2);

db.close();
for (const f of [tmp, `${tmp}-wal`, `${tmp}-shm`]) if (fs.existsSync(f)) fs.rmSync(f);

console.log(checks.map((c) => `✓ ${c}`).join("\n"));
console.log(`\nPINS OK — ${passed} checks`);
