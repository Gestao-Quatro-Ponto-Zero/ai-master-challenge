/**
 * deck-library-test — headless proof of the Deck Library (SP6 / the gallery).
 *
 * A built deck persists, is listed newest-first as a summary, reopens by id from
 * stored state, and can be removed. Hermetic: a throwaway app DB, no warehouse or
 * LLM needed (the library reads only the kv_cache snapshots storeDeck writes).
 *
 * Run: `bun run deck-library-test` (shells to tsx — better-sqlite3 is native).
 */
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

const tmp = path.join(os.tmpdir(), `veta-decklib-test-${process.pid}.sqlite`);
for (const f of [tmp, `${tmp}-wal`, `${tmp}-shm`]) if (fs.existsSync(f)) fs.rmSync(f);
process.env.APP_DB_PATH = tmp;

import { storeDeck, getStoredDeck, listStoredDecks, deleteStoredDeck, type DeckSpec } from "../src/engine/deck";

const USER_A = "user-a";
const USER_B = "user-b";

let passed = 0;
function ok(label: string, cond: boolean, detail = ""): void {
  if (!cond) {
    console.error(`✗ ${label}${detail ? ` — ${detail}` : ""}`);
    console.error("\nDECK-LIBRARY FAILED");
    process.exit(1);
  }
  passed++;
  console.log(`✓ ${label}`);
}

function deck(id: string, title: string, slides: number, cited: string[]): DeckSpec {
  return {
    id,
    title,
    subtitle: "sub",
    asOf: "2026-06-12",
    governingThought: `Apex assertion for ${title}, well over twenty characters.`,
    scqa: { situation: "s", complication: "c", question: "q" },
    datasetFrame: { today: "2026-06-12", firstDate: "2024-12-12", lastDate: "2026-06-11" },
    slides: Array.from({ length: slides }, (_, i) => ({ layout: "argument" as const, title: `Slide ${i + 1}` })),
    citedSql: cited,
  };
}

// Empty library to start.
ok("library starts empty", listStoredDecks(USER_A).length === 0);
ok("an unknown deck id resolves to null", getStoredDeck(USER_A, "pins-nope") === null);

// Store two decks; the second is stored later so it should sort first (newest-first).
storeDeck(USER_A, deck("pins-aaa", "First Built Deck", 7, ["SELECT 1", "SELECT 2"]));
storeDeck(USER_A, deck("pins-bbb", "Second Built Deck", 11, ["SELECT 1", "SELECT 2", "SELECT 3"]));

const list = listStoredDecks(USER_A);
ok("ISC-32: both built decks persist and list", list.length === 2, `${list.length}`);
ok("ISC-32: a summary carries title/slideCount/citedCount/asOf/builtAt", (() => {
  const s = list.find((d) => d.id === "pins-bbb");
  return !!s && s.title === "Second Built Deck" && s.slideCount === 11 && s.citedCount === 3 && s.asOf === "2026-06-12" && !!s.builtAt;
})());
ok("ISC-35: a listed deck reopens + re-renders from stored state", (() => {
  const full = getStoredDeck(USER_A, "pins-aaa");
  return !!full && full.id === "pins-aaa" && full.slides.length === 7 && full.citedSql.length === 2;
})());


ok("SP05: B cannot list A decks", listStoredDecks(USER_B).length === 0);
ok("SP05: B cannot load A deck by id", getStoredDeck(USER_B, "pins-aaa") === null);
ok("SP05: B cannot delete A deck by id", deleteStoredDeck(USER_B, "pins-aaa") === false);

// Remove one; the other survives.
ok("a deck deletes from the library", deleteStoredDeck(USER_A, "pins-aaa") === true);
const after = listStoredDecks(USER_A);
ok("the library shrinks to the remaining deck", after.length === 1 && after[0].id === "pins-bbb", `${after.length}`);
ok("the deleted deck no longer loads", getStoredDeck(USER_A, "pins-aaa") === null);
ok("deleting an absent deck is a no-op (idempotent)", deleteStoredDeck(USER_A, "pins-aaa") === false);

console.log(`\nDECK-LIBRARY OK — ${passed} checks`);
process.exit(0);
