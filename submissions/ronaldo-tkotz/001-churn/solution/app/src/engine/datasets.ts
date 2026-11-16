/** Per-user dataset registry. The built-in RavenStack database is shared; uploads and active pointer are user-owned. */
import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { appdb } from "./appdb";
import { warehousePath, datasetsDir } from "./seed";

export const DEFAULT_DATASET_ID = "ravenstack";
export const DEFAULT_DATASET_LABEL = "RavenStack";
export const MAX_UPLOAD_BYTES = 200 * 1024 * 1024;

export interface DatasetRow {
  id: string;
  label: string;
  filename: string | null;
  rel_path: string | null;
  user_id: string | null;
  is_default: number;
  is_active: number; // computed per caller, not a global switch
  table_count: number | null;
  size_bytes: number | null;
  created_at: string;
}

const now = () => new Date().toISOString();
let _migrated = false;

function ensureDatasets(db: Database.Database): void {
  if (_migrated) return;
  db.exec(`
    CREATE TABLE IF NOT EXISTS datasets (
      id          TEXT PRIMARY KEY,
      label       TEXT    NOT NULL,
      filename    TEXT,
      rel_path    TEXT,
      user_id     TEXT,
      is_default  INTEGER NOT NULL DEFAULT 0,
      is_active   INTEGER NOT NULL DEFAULT 0,
      table_count INTEGER,
      size_bytes  INTEGER,
      created_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_dataset_state (
      user_id           TEXT PRIMARY KEY,
      active_dataset_id TEXT NOT NULL DEFAULT '${DEFAULT_DATASET_ID}',
      updated_at        TEXT NOT NULL
    );
  `);
  const cols = db.prepare("PRAGMA table_info(datasets)").all() as { name: string }[];
  if (!cols.some((c) => c.name === "user_id")) db.exec("ALTER TABLE datasets ADD COLUMN user_id TEXT");
  db.prepare(`INSERT OR IGNORE INTO datasets (id, label, filename, rel_path, user_id, is_default, is_active, created_at)
     VALUES (@id, @label, NULL, NULL, NULL, 1, 0, @created_at)`).run({ id: DEFAULT_DATASET_ID, label: DEFAULT_DATASET_LABEL, created_at: now() });
  db.exec("CREATE INDEX IF NOT EXISTS idx_datasets_user_created ON datasets(user_id, created_at DESC)");
  _migrated = true;
}

function db(): Database.Database { const d = appdb(); ensureDatasets(d); return d; }

function activeIdRaw(userId: string): string {
  const row = db().prepare("SELECT active_dataset_id FROM user_dataset_state WHERE user_id = ?").get(userId) as { active_dataset_id: string } | undefined;
  return row?.active_dataset_id ?? DEFAULT_DATASET_ID;
}

export function listDatasets(userId: string): DatasetRow[] {
  const activeId = activeIdRaw(userId);
  const rows = db().prepare(`SELECT * FROM datasets WHERE is_default = 1 OR user_id = ? ORDER BY is_default DESC, created_at DESC`).all(userId) as DatasetRow[];
  return rows.map((r) => ({ ...r, is_active: r.id === activeId ? 1 : 0 }));
}

export function getDataset(id: string, userId: string): DatasetRow | null {
  const row = db().prepare("SELECT * FROM datasets WHERE id = ? AND (is_default = 1 OR user_id = ?)").get(id, userId) as DatasetRow | undefined;
  if (!row) return null;
  return { ...row, is_active: row.id === activeIdRaw(userId) ? 1 : 0 };
}

export function activeDataset(userId: string): DatasetRow {
  return getDataset(activeIdRaw(userId), userId) ?? getDataset(DEFAULT_DATASET_ID, userId)!;
}

export function activeDatasetId(userId: string): string { return activeDataset(userId).id; }

export function datasetWarehousePath(dataset: DatasetRow): string {
  if (dataset.is_default || !dataset.rel_path) return warehousePath();
  return path.join(datasetsDir(), dataset.rel_path);
}

export function activeWarehousePath(userId: string): string { return datasetWarehousePath(activeDataset(userId)); }
export function defaultWarehousePath(): string { return warehousePath(); }

export function setActiveDataset(userId: string, id: string): DatasetRow {
  const target = getDataset(id, userId);
  if (!target) throw new Error(`No dataset ${id}`);
  db().prepare(`INSERT INTO user_dataset_state (user_id, active_dataset_id, updated_at)
      VALUES (@user_id, @active_dataset_id, @updated_at)
      ON CONFLICT(user_id) DO UPDATE SET active_dataset_id=@active_dataset_id, updated_at=@updated_at`)
    .run({ user_id: userId, active_dataset_id: id, updated_at: now() });
  return getDataset(id, userId)!;
}

export interface SqliteProbe { ok: boolean; tableCount: number; error?: string }
export function probeSqlite(absPath: string): SqliteProbe {
  let conn: Database.Database | null = null;
  try {
    conn = new Database(absPath, { readonly: true, fileMustExist: true });
    conn.pragma("query_only = TRUE");
    const row = conn.prepare("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").get() as { n: number };
    if (row.n < 1) return { ok: false, tableCount: 0, error: "The file has no tables." };
    return { ok: true, tableCount: row.n };
  } catch (e) {
    return { ok: false, tableCount: 0, error: e instanceof Error ? e.message : "Not a valid SQLite database." };
  } finally { conn?.close(); }
}

export interface RegisterResult { ok: boolean; dataset?: DatasetRow; error?: string }
export function registerUpload(userId: string, originalName: string, bytes: Buffer): RegisterResult {
  if (bytes.length === 0) return { ok: false, error: "The file is empty." };
  if (bytes.length > MAX_UPLOAD_BYTES) return { ok: false, error: `Too large — the limit is ${Math.round(MAX_UPLOAD_BYTES / 1024 / 1024)} MB.` };

  const id = `ds_${crypto.randomUUID().slice(0, 8)}`;
  const relPath = `${id}.sqlite`;
  fs.mkdirSync(datasetsDir(), { recursive: true });
  const abs = path.join(datasetsDir(), relPath);
  fs.writeFileSync(abs, bytes);
  const probe = probeSqlite(abs);
  if (!probe.ok) {
    try { fs.rmSync(abs, { force: true }); } catch {}
    return { ok: false, error: probe.error ?? "Not a valid SQLite database." };
  }

  db().prepare(`INSERT INTO datasets (id, label, filename, rel_path, user_id, is_default, is_active, table_count, size_bytes, created_at)
       VALUES (@id, @label, @filename, @rel_path, @user_id, 0, 0, @table_count, @size_bytes, @created_at)`).run({
    id, label: cleanLabel(originalName), filename: originalName, rel_path: relPath, user_id: userId,
    table_count: probe.tableCount, size_bytes: bytes.length, created_at: now(),
  });
  return { ok: true, dataset: getDataset(id, userId)! };
}

export function removeDataset(userId: string, id: string): { ok: boolean; error?: string } {
  const d = getDataset(id, userId);
  if (!d) return { ok: false, error: "No such dataset." };
  if (d.is_default) return { ok: false, error: "The built-in dataset can't be removed." };
  if (activeDatasetId(userId) === id) setActiveDataset(userId, DEFAULT_DATASET_ID);
  if (d.rel_path) {
    try { fs.rmSync(path.join(datasetsDir(), d.rel_path), { force: true }); } catch {}
  }
  db().prepare("DELETE FROM datasets WHERE id = ? AND user_id = ?").run(id, userId);
  return { ok: true };
}

function cleanLabel(filename: string): string {
  const base = filename.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim();
  return base.length > 0 ? base.slice(0, 60) : "Uploaded dataset";
}
