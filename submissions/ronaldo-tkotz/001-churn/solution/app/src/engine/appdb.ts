/**
 * App database — Veta's own read-write store, separate from the read-only
 * warehouse. Holds discovery cache plus per-user workspace state.
 * better-sqlite3 native binding → node/tsx runtime only.
 */
import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import type { ChartSpec } from "./tools"; // type-only — no runtime import cycle
import { isPartKind, type PinKind, type StoredChart, type TablePayload } from "./parts";

let _db: Database.Database | null = null;

const now = () => new Date().toISOString();
const PBKDF2_ITERATIONS = 210_000;
const PASSWORD_PREFIX = "pbkdf2_sha256";

function enc(s: string): Uint8Array<ArrayBuffer> {
  return new Uint8Array(new TextEncoder().encode(s));
}

function b64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(str: string): Uint8Array<ArrayBuffer> {
  const padded = str + "=".repeat((4 - (str.length % 4)) % 4);
  const bin = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  let diff = a.length ^ b.length;
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i++) diff |= (a[i] ?? 0) ^ (b[i] ?? 0);
  return diff === 0;
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export async function hashPassword(password: string, salt = crypto.getRandomValues(new Uint8Array(16))): Promise<string> {
  const key = await crypto.subtle.importKey("raw", enc(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations: PBKDF2_ITERATIONS },
    key,
    256,
  );
  return `${PASSWORD_PREFIX}$${PBKDF2_ITERATIONS}$${b64urlEncode(salt)}$${b64urlEncode(new Uint8Array(bits))}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [prefix, iterRaw, saltRaw, hashRaw] = stored.split("$");
  const iterations = Number(iterRaw);
  if (prefix !== PASSWORD_PREFIX || !Number.isInteger(iterations) || iterations < 100_000 || !saltRaw || !hashRaw) {
    return false;
  }
  try {
    const salt = b64urlDecode(saltRaw);
    const expected = b64urlDecode(hashRaw);
    const key = await crypto.subtle.importKey("raw", enc(password), "PBKDF2", false, ["deriveBits"]);
    const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, expected.length * 8);
    return timingSafeEqual(new Uint8Array(bits), expected);
  } catch {
    return false;
  }
}

function appDbPath(): string {
  return process.env.APP_DB_PATH || path.join(process.cwd(), "data", "app.sqlite");
}

function tableExists(db: Database.Database, name: string): boolean {
  return Boolean(db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?").get(name));
}

function legacyUserWorkRows(db: Database.Database): number {
  let count = 0;
  const countTable = (name: string, where = "1=1") => {
    if (!tableExists(db, name)) return;
    count += (db.prepare(`SELECT COUNT(*) AS n FROM ${name} WHERE ${where}`).get() as { n: number }).n;
  };
  countTable("conversations");
  countTable("messages");
  countTable("saved_insights");
  countTable("datasets", "COALESCE(is_default,0) = 0");
  if (tableExists(db, "kv_cache")) {
    count += (db.prepare("SELECT COUNT(*) AS n FROM kv_cache WHERE key LIKE 'deck:%'").get() as { n: number }).n;
  }
  return count;
}

function maybeMoveLegacyDb(dbPath: string): void {
  if (!fs.existsSync(dbPath)) return;
  let probe: Database.Database | null = null;
  try {
    probe = new Database(dbPath, { readonly: true, fileMustExist: true });
    const hasUsers = tableExists(probe, "users");
    if (hasUsers || legacyUserWorkRows(probe) === 0) return;
  } catch {
    return;
  } finally {
    probe?.close();
  }

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const legacy = dbPath.replace(/\.sqlite$/i, `.${stamp}.legacy.sqlite`);
  fs.renameSync(dbPath, legacy);
  for (const suffix of ["-wal", "-shm"]) {
    const side = `${dbPath}${suffix}`;
    if (fs.existsSync(side)) fs.renameSync(side, `${legacy}${suffix}`);
  }
  console.log(`[appdb] legacy pre-auth app DB contained user work; moved aside to ${legacy}`);
}

/** Lazily open the app DB (read-write) and ensure the schema exists. */
export function appdb(): Database.Database {
  if (!_db) {
    const dbPath = appDbPath();
    fs.mkdirSync(path.dirname(dbPath), { recursive: true });
    maybeMoveLegacyDb(dbPath);
    _db = new Database(dbPath);
    _db.pragma("journal_mode = WAL");
    _db.pragma("foreign_keys = ON");
    ensureSchema(_db);
  }
  return _db;
}

function ensureSchema(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id            TEXT PRIMARY KEY,
      email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password_hash TEXT NOT NULL,
      created_at    TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS kv_cache (
      key        TEXT PRIMARY KEY,
      value      TEXT NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS conversations (
      id         TEXT PRIMARY KEY,
      title      TEXT NOT NULL,
      user_id    TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS messages (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id TEXT    NOT NULL,
      turn_id         TEXT    NOT NULL,
      seq             INTEGER NOT NULL,
      role            TEXT    NOT NULL,
      payload_json    TEXT    NOT NULL,
      created_at      TEXT    NOT NULL,
      UNIQUE (conversation_id, turn_id),
      FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conv_seq ON messages(conversation_id, seq);
    CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
  `);
  ensureSavedInsights(db);
}

const SAVED_INSIGHTS_DDL = `
  CREATE TABLE IF NOT EXISTS saved_insights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_kind     TEXT    NOT NULL,
    source_id       TEXT    NOT NULL,
    conversation_id TEXT,
    user_id         TEXT    NOT NULL,
    question        TEXT,
    answer          TEXT,
    cited_sql_json  TEXT,
    chart_json      TEXT,
    title           TEXT,
    note            TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL,
    UNIQUE (user_id, source_kind, source_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
  );
`;

function indexColumns(db: Database.Database, indexName: string): string[] {
  return (db.prepare(`PRAGMA index_info(${indexName})`).all() as { name: string }[]).map((r) => r.name);
}

function savedInsightsNeedsRebuild(db: Database.Database): boolean {
  const cols = db.prepare("PRAGMA table_info(saved_insights)").all() as { name: string; notnull: number }[];
  if (cols.length === 0) return false;
  if (!cols.some((c) => c.name === "source_kind")) return true;
  if (!cols.some((c) => c.name === "chart_json")) return true;
  if (cols.find((c) => c.name === "user_id")?.notnull !== 1) return true;
  const uniqueIndexes = db.prepare("PRAGMA index_list(saved_insights)").all() as { name: string; unique: number }[];
  return !uniqueIndexes.some((idx) => idx.unique === 1 && indexColumns(db, idx.name).join(",") === "user_id,source_kind,source_id");
}

function ensureSavedInsights(db: Database.Database): void {
  const cols = db.prepare("PRAGMA table_info(saved_insights)").all() as { name: string }[];
  if (cols.length > 0 && savedInsightsNeedsRebuild(db)) {
    const n = (db.prepare("SELECT COUNT(*) AS n FROM saved_insights").get() as { n: number }).n;
    if (n > 0) {
      throw new Error("saved_insights uses a legacy unscoped schema with rows; fresh-DB boot should have moved this app DB aside.");
    }
    db.exec("DROP TABLE saved_insights");
  }
  db.exec(SAVED_INSIGHTS_DDL);
  // Artifact-layer columns — additive, idempotent, safe on a populated table.
  // table_json: the snapshot payload of a "table" part pin. dataset_id: which
  // dataset the pin was grounded against (deck build gates cross-dataset pins).
  const have = new Set((db.prepare("PRAGMA table_info(saved_insights)").all() as { name: string }[]).map((c) => c.name));
  if (!have.has("table_json")) db.exec("ALTER TABLE saved_insights ADD COLUMN table_json TEXT");
  if (!have.has("dataset_id")) db.exec("ALTER TABLE saved_insights ADD COLUMN dataset_id TEXT");
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_saved_insights_user_order ON saved_insights(user_id, sort_order, created_at);
    CREATE INDEX IF NOT EXISTS idx_saved_insights_user_source ON saved_insights(user_id, source_kind, source_id);
  `);
}

// ── Users / password auth ─────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  password_hash: string;
  created_at: string;
}

export function judgeEmailFromEnv(): string {
  const raw = (process.env.AUTH_USERNAME || "judge").trim();
  return normalizeEmail(raw.includes("@") ? raw : `${raw}@ravenstack.app`);
}

export function getUserByEmail(email: string): User | null {
  const row = appdb().prepare("SELECT * FROM users WHERE email = ? COLLATE NOCASE").get(normalizeEmail(email));
  return (row as User | undefined) ?? null;
}

export function getUserById(id: string): User | null {
  const row = appdb().prepare("SELECT * FROM users WHERE id = ?").get(id);
  return (row as User | undefined) ?? null;
}

export async function createUser(email: string, password: string): Promise<User> {
  const clean = normalizeEmail(email);
  if (!/^\S+@\S+\.\S+$/.test(clean)) throw new Error("Enter a valid email address.");
  if (password.length < 8) throw new Error("Password must be at least 8 characters.");
  const id = `usr_${crypto.randomUUID()}`;
  const created_at = now();
  const password_hash = await hashPassword(password);
  appdb()
    .prepare("INSERT INTO users (id, email, password_hash, created_at) VALUES (@id, @email, @password_hash, @created_at)")
    .run({ id, email: clean, password_hash, created_at });
  return { id, email: clean, password_hash, created_at };
}

export async function authenticateUser(email: string, password: string): Promise<User | null> {
  const user = getUserByEmail(email);
  if (!user) {
    // Equalize timing a little without revealing whether the email exists.
    await hashPassword(password, new Uint8Array(16));
    return null;
  }
  return (await verifyPassword(password, user.password_hash)) ? user : null;
}

export async function seedJudgeUser(): Promise<User | null> {
  const password = process.env.AUTH_PASSWORD;
  if (!password) return null;
  const email = judgeEmailFromEnv();
  const existing = getUserByEmail(email);
  if (!existing) return createUser(email, password);
  if (!(await verifyPassword(password, existing.password_hash))) {
    appdb().prepare("UPDATE users SET password_hash = ? WHERE id = ?").run(await hashPassword(password), existing.id);
    return getUserById(existing.id)!;
  }
  return existing;
}

// ── Generic JSON cache (kv_cache) ─────────────────────────────────────────────
export function getCache<T = unknown>(key: string): T | null {
  const row = appdb().prepare("SELECT value FROM kv_cache WHERE key = ?").get(key) as { value: string } | undefined;
  if (!row) return null;
  try { return JSON.parse(row.value) as T; } catch { return null; }
}

export function putCache(key: string, value: unknown): void {
  appdb()
    .prepare(`INSERT INTO kv_cache (key, value, created_at) VALUES (@key, @value, @created_at)
       ON CONFLICT(key) DO UPDATE SET value=@value, created_at=@created_at`)
    .run({ key, value: JSON.stringify(value), created_at: now() });
}

export function clearCache(keyOrPrefix?: string): void {
  if (!keyOrPrefix) appdb().prepare("DELETE FROM kv_cache").run();
  else appdb().prepare("DELETE FROM kv_cache WHERE key = ? OR key LIKE ?").run(keyOrPrefix, `${keyOrPrefix}%`);
}

export interface CacheRow { key: string; value: string; created_at: string }
export function listCacheByPrefix(prefix: string): CacheRow[] {
  return appdb().prepare("SELECT key, value, created_at FROM kv_cache WHERE key LIKE ? ORDER BY created_at DESC").all(`${prefix}%`) as CacheRow[];
}
export function deleteCache(key: string): boolean { return appdb().prepare("DELETE FROM kv_cache WHERE key = ?").run(key).changes > 0; }

// ── Conversations + messages ─────────────────────────────────────────────────
export interface Conversation { id: string; title: string; user_id: string | null; created_at: string; updated_at: string }
export interface StoredMessage { id: number; conversation_id: string; turn_id: string; seq: number; role: string; payload_json: string; created_at: string }

export function createConversation(opts: { title: string; userId: string }): Conversation {
  const id = crypto.randomUUID();
  const ts = now();
  const title = (opts.title || "New conversation").slice(0, 200);
  appdb().prepare(`INSERT INTO conversations (id, title, user_id, created_at, updated_at)
       VALUES (@id, @title, @user_id, @created_at, @updated_at)`).run({ id, title, user_id: opts.userId, created_at: ts, updated_at: ts });
  return { id, title, user_id: opts.userId, created_at: ts, updated_at: ts };
}

export function listConversations(userId: string): Conversation[] {
  return appdb().prepare("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC, rowid DESC").all(userId) as Conversation[];
}

export function getConversation(id: string, userId: string): Conversation | null {
  const row = appdb().prepare("SELECT * FROM conversations WHERE id = ? AND user_id = ?").get(id, userId);
  return (row as Conversation | undefined) ?? null;
}

export function renameConversation(id: string, userId: string, title: string): boolean {
  const info = appdb().prepare("UPDATE conversations SET title = @title, updated_at = @updated_at WHERE id = @id AND user_id = @user_id")
    .run({ id, user_id: userId, title: (title || "Untitled").slice(0, 200), updated_at: now() });
  return info.changes > 0;
}

export function deleteConversation(id: string, userId: string): boolean {
  return appdb().prepare("DELETE FROM conversations WHERE id = ? AND user_id = ?").run(id, userId).changes > 0;
}

export function appendMessage(opts: { conversationId: string; userId: string; turnId: string; seq: number; role: string; payload: unknown }): StoredMessage {
  const ts = now();
  const payload_json = JSON.stringify(opts.payload);
  const db = appdb();
  const tx = db.transaction(() => {
    const owner = db.prepare("SELECT 1 FROM conversations WHERE id = ? AND user_id = ?").get(opts.conversationId, opts.userId);
    if (!owner) throw new Error("Conversation not found");
    db.prepare(`INSERT INTO messages (conversation_id, turn_id, seq, role, payload_json, created_at)
       VALUES (@conversation_id, @turn_id, @seq, @role, @payload_json, @created_at)
       ON CONFLICT(conversation_id, turn_id)
         DO UPDATE SET seq = @seq, role = @role, payload_json = @payload_json`).run({
      conversation_id: opts.conversationId, turn_id: opts.turnId, seq: opts.seq, role: opts.role, payload_json, created_at: ts,
    });
    db.prepare("UPDATE conversations SET updated_at = @updated_at WHERE id = @id AND user_id = @user_id")
      .run({ id: opts.conversationId, user_id: opts.userId, updated_at: ts });
  });
  tx();
  return db.prepare("SELECT * FROM messages WHERE conversation_id = ? AND turn_id = ?").get(opts.conversationId, opts.turnId) as StoredMessage;
}

export function getMessages(conversationId: string, userId: string): StoredMessage[] {
  return appdb().prepare(`SELECT m.* FROM messages m
      JOIN conversations c ON c.id = m.conversation_id
      WHERE m.conversation_id = ? AND c.user_id = ? ORDER BY m.seq ASC`).all(conversationId, userId) as StoredMessage[];
}

// ── Saved insights ────────────────────────────────────────────────────────────
export interface SavedInsight {
  id: number; source_kind: string; source_id: string; conversation_id: string | null; user_id: string | null;
  question: string | null; answer: string | null; cited_sql_json: string | null; chart_json: string | null;
  table_json: string | null; dataset_id: string | null;
  title: string | null; note: string | null; sort_order: number; created_at: string;
}

export function createSavedInsight(opts: {
  sourceKind: PinKind; sourceId: string; conversationId?: string | null; userId: string;
  question?: string | null; answer?: string | null; citedSql?: string[]; chart?: StoredChart | ChartSpec | null;
  table?: TablePayload | null; datasetId?: string | null; title?: string | null; note?: string | null;
}): SavedInsight {
  const db = appdb();
  // Part pins (chart/table/narrative) UPSERT: re-pinning an artifact refreshes its
  // stored projection/payload (the pin identity is the object, the payload is the
  // user's latest view of it). turn/finding keep the historical DO NOTHING.
  const conflictClause = isPartKind(opts.sourceKind)
    ? `ON CONFLICT(user_id, source_kind, source_id) DO UPDATE SET
         conversation_id=@conversation_id, question=@question, answer=@answer,
         cited_sql_json=@cited_sql_json, chart_json=@chart_json, table_json=@table_json,
         dataset_id=@dataset_id, title=COALESCE(saved_insights.title, @title)`
    : "ON CONFLICT(user_id, source_kind, source_id) DO NOTHING";
  db.prepare(`INSERT INTO saved_insights
       (source_kind, source_id, conversation_id, user_id, question, answer, cited_sql_json, chart_json, table_json, dataset_id, title, note, sort_order, created_at)
     VALUES
       (@source_kind, @source_id, @conversation_id, @user_id, @question, @answer, @cited_sql_json, @chart_json, @table_json, @dataset_id, @title, @note,
        (SELECT COALESCE(MAX(sort_order), -1) + 1 FROM saved_insights WHERE user_id = @user_id), @created_at)
     ${conflictClause}`).run({
    source_kind: opts.sourceKind,
    source_id: opts.sourceId,
    conversation_id: opts.conversationId ?? null,
    user_id: opts.userId,
    question: opts.question ?? null,
    answer: opts.answer ?? null,
    cited_sql_json: JSON.stringify(opts.citedSql ?? []),
    chart_json: opts.chart ? JSON.stringify(opts.chart) : null,
    table_json: opts.table ? JSON.stringify(opts.table) : null,
    dataset_id: opts.datasetId ?? null,
    title: opts.title ?? null,
    note: opts.note ?? null,
    created_at: now(),
  });
  return db.prepare("SELECT * FROM saved_insights WHERE user_id = ? AND source_kind = ? AND source_id = ?")
    .get(opts.userId, opts.sourceKind, opts.sourceId) as SavedInsight;
}

export function listSavedInsights(userId: string): SavedInsight[] {
  return appdb().prepare("SELECT * FROM saved_insights WHERE user_id = ? ORDER BY sort_order ASC, created_at ASC").all(userId) as SavedInsight[];
}

export function renameSavedInsight(id: number, userId: string, title: string): boolean {
  return appdb().prepare("UPDATE saved_insights SET title = ? WHERE id = ? AND user_id = ?")
    .run((title || "Untitled").slice(0, 200), id, userId).changes > 0;
}

export function deleteSavedInsight(id: number, userId: string): boolean {
  return appdb().prepare("DELETE FROM saved_insights WHERE id = ? AND user_id = ?").run(id, userId).changes > 0;
}

export function deleteSavedInsightBySource(userId: string, sourceKind: string, sourceId: string): boolean {
  return appdb().prepare("DELETE FROM saved_insights WHERE user_id = ? AND source_kind = ? AND source_id = ?")
    .run(userId, sourceKind, sourceId).changes > 0;
}

export function reorderSavedInsights(userId: string, orderedIds: number[]): void {
  const db = appdb();
  const upd = db.prepare("UPDATE saved_insights SET sort_order = ? WHERE id = ? AND user_id = ?");
  db.transaction((ids: number[]) => ids.forEach((id, i) => upd.run(i, id, userId)))(orderedIds);
}
