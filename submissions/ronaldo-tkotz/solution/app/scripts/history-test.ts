/**
 * history-test — headless proof of the workspace spine (chat history).
 *
 * Exercises the appdb conversation/message layer end to end against a throwaway
 * DB: create → append turns → list → restore (parse round-trip) → isolation →
 * rename → UPSERT idempotency → delete (FK cascade). No browser, no LLM.
 *
 * Run: `bun run history-test` (shells to tsx — better-sqlite3 is native).
 */
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

// Point appdb at a fresh throwaway DB BEFORE importing it (env read lazily).
const tmp = path.join(os.tmpdir(), `veta-history-test-${process.pid}.sqlite`);
for (const f of [tmp, `${tmp}-wal`, `${tmp}-shm`]) if (fs.existsSync(f)) fs.rmSync(f);
process.env.APP_DB_PATH = tmp;

import {
  appdb,
  createConversation,
  listConversations,
  getConversation,
  renameConversation,
  deleteConversation,
  appendMessage,
  getMessages,
} from "../src/engine/appdb";

// Synchronous sleep so writes land on distinct millisecond timestamps —
// reflects real usage (turns are seconds apart), unlike a <1ms test tick.
const sleep = (ms: number): void => {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
};

let passed = 0;
const checks: string[] = [];
function ok(label: string, cond: boolean): void {
  if (!cond) {
    console.error(`✗ ${label}`);
    console.error("\nHISTORY FAILED");
    process.exit(1);
  }
  passed++;
  checks.push(label);
}

const USER_A = "user-a";
const USER_B = "user-b";

// A realistic assistant Turn — steps with SQL + rows, citedSql, a markdown-table answer.
const userTurn = { v: 1, role: "user", tid: "u-1", text: "Which accounts are at risk of churning?" };
const assistantTurn = {
  v: 1,
  role: "assistant",
  tid: "a-1",
  status: "done",
  answer: "**23 accounts** are critical.\n\n| Account | ARR |\n|---|---|\n| Pioneerbridge | $2.86M |",
  citedSql: ["SELECT * FROM accounts WHERE health_score < 40"],
  model: "deepseek-chat",
  steps: [
    {
      index: 0,
      tool: "query_warehouse",
      sql: "SELECT * FROM accounts WHERE health_score < 40",
      rowCount: 23,
      columns: ["account", "arr_usd"],
      rows: [{ account: "Pioneerbridge", arr_usd: 2860000 }],
      isError: false,
    },
  ],
};

// ── 1. Schema: the three spine tables exist, each with a nullable user_id (ISC-67)
const db = appdb();
const tables = (db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all() as { name: string }[]).map(
  (r) => r.name,
);
ok("ISC-67: conversations table exists", tables.includes("conversations"));
ok("ISC-67: messages table exists", tables.includes("messages"));
ok("ISC-67: saved_insights table exists", tables.includes("saved_insights"));
ok("SP05: users table exists", tables.includes("users"));
// The two list-level tables carry user_id for SP05 scoping.
for (const t of ["conversations", "saved_insights"]) {
  const cols = db.prepare(`PRAGMA table_info(${t})`).all() as { name: string; notnull: number }[];
  const uid = cols.find((c) => c.name === "user_id");
  ok(`SP05: ${t}.user_id exists`, Boolean(uid));
}
// messages scope through their conversation (FK), not a redundant user_id.
{
  const cols = db.prepare(`PRAGMA table_info(messages)`).all() as { name: string; notnull: number }[];
  const cid = cols.find((c) => c.name === "conversation_id");
  ok("ISC-67: messages.conversation_id is NOT NULL (scopes via the conversation)", Boolean(cid) && cid!.notnull === 1);
}

// ── 2. Create + append two turns, keyed by stable turn_id with seq order
const convA = createConversation({ title: "Which accounts are at risk of churning?", userId: USER_A });
ok("create returns a uuid id", typeof convA.id === "string" && convA.id.length >= 16);
ok("SP05: create stores owner user_id", convA.user_id === USER_A);
appendMessage({ conversationId: convA.id, userId: USER_A, turnId: "u-1", seq: 0, role: "user", payload: userTurn });
appendMessage({ conversationId: convA.id, userId: USER_A, turnId: "a-1", seq: 1, role: "assistant", payload: assistantTurn });

// ── 3. Restore round-trip: payload_json parses back to the identical Turn (ISC-68, ISC-76)
const msgs = getMessages(convA.id, USER_A);
ok("ISC-70: getMessages returns 2 rows ordered by seq", msgs.length === 2 && msgs[0].seq === 0 && msgs[1].seq === 1);
const restoredUser = JSON.parse(msgs[0].payload_json);
const restoredAsst = JSON.parse(msgs[1].payload_json);
ok("ISC-68: user payload round-trips text", restoredUser.text === userTurn.text);
ok("ISC-68: assistant payload round-trips answer", restoredAsst.answer === assistantTurn.answer);
ok("ISC-76: structured steps survive (SQL + rows)", restoredAsst.steps[0].sql === assistantTurn.steps[0].sql && restoredAsst.steps[0].rows[0].arr_usd === 2860000);
ok("ISC-76: citedSql array survives", Array.isArray(restoredAsst.citedSql) && restoredAsst.citedSql[0] === assistantTurn.citedSql[0]);

// ── 4. UPSERT idempotency: re-persisting the same turn_id overwrites, no dup
appendMessage({ conversationId: convA.id, userId: USER_A, turnId: "a-1", seq: 1, role: "assistant", payload: { ...assistantTurn, answer: "edited" } });
const msgs2 = getMessages(convA.id, USER_A);
ok("UPSERT on (conversation_id, turn_id) — no duplicate row", msgs2.length === 2);
ok("UPSERT overwrites payload", JSON.parse(msgs2[1].payload_json).answer === "edited");

// ── 5. Second conversation + isolation (ISC-75): A never sees B's messages
sleep(3); // real conversations are created minutes apart, not the same tick
const convB = createConversation({ title: "Enterprise NPS trend", userId: USER_B });
appendMessage({ conversationId: convB.id, userId: USER_B, turnId: "b-1", seq: 0, role: "user", payload: { v: 1, role: "user", tid: "b-1", text: "NPS?" } });
const aTurns = getMessages(convA.id, USER_A).map((m) => m.turn_id);
const bTurns = getMessages(convB.id, USER_B).map((m) => m.turn_id);
ok("ISC-75: conversation A and B message sets are disjoint", aTurns.every((t) => !bTurns.includes(t)) && bTurns.every((t) => !aTurns.includes(t)));

// ── 6. List newest-first by updated_at (ISC-69). B was written most recently.
const list = listConversations(USER_A);
ok("SP05: A list returns only A conversations", list.length === 1 && list[0].id === convA.id);
ok("SP05: B list returns only B conversation", listConversations(USER_B).length === 1 && listConversations(USER_B)[0].id === convB.id);

// ── 7. Rename bumps title + updated_at, reorders to front (ISC-73)
sleep(3); // the rename happens after B's activity, so it bumps A to the front
renameConversation(convA.id, USER_A, "Churn risk — renamed");
ok("ISC-73: rename updates the title", getConversation(convA.id, USER_A)!.title === "Churn risk — renamed");
ok("ISC-73: rename bumps updated_at to front of list", listConversations(USER_A)[0].id === convA.id);


// ── SP05. Cross-user direct-id lookups/updates return null/false
ok("SP05: B cannot fetch A conversation by id", getConversation(convA.id, USER_B) === null);
ok("SP05: B cannot read A messages by id", getMessages(convA.id, USER_B).length === 0);
ok("SP05: B cannot rename A conversation", renameConversation(convA.id, USER_B, "pwned") === false);
ok("SP05: B cannot delete A conversation", deleteConversation(convA.id, USER_B) === false);

// ── 8. Delete cascades to messages (ISC-74)
const delMsgCount = getMessages(convA.id, USER_A).length;
ok("precondition: A has messages before delete", delMsgCount === 2);
deleteConversation(convA.id, USER_A);
ok("ISC-74: deleted conversation is gone", getConversation(convA.id, USER_A) === null);
ok("ISC-74: messages cascade-deleted with the conversation", getMessages(convA.id, USER_A).length === 0);
ok("ISC-74: other conversation (B) survives", getConversation(convB.id, USER_B) !== null && getMessages(convB.id, USER_B).length === 1);

// Clean up the throwaway DB.
db.close();
for (const f of [tmp, `${tmp}-wal`, `${tmp}-shm`]) if (fs.existsSync(f)) fs.rmSync(f);

console.log(checks.map((c) => `✓ ${c}`).join("\n"));
console.log(`\nHISTORY OK — ${passed} checks`);
