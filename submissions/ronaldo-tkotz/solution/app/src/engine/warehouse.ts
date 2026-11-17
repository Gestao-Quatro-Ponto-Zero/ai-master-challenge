/** Read-only warehouse access with a connection cache keyed by absolute path. */
import Database from "better-sqlite3";
import { activeWarehousePath, defaultWarehousePath } from "./datasets";

export interface WarehouseContext { userId?: string; warehousePath?: string }

const handles = new Map<string, Database.Database>();

export function resolveWarehousePath(ctx: WarehouseContext = {}): string {
  if (ctx.warehousePath) return ctx.warehousePath;
  if (ctx.userId) return activeWarehousePath(ctx.userId);
  return defaultWarehousePath();
}

export function warehouseForPath(target: string): Database.Database {
  const existing = handles.get(target);
  if (existing) return existing;
  const db = new Database(target, { readonly: true, fileMustExist: true });
  db.pragma("query_only = TRUE");
  db.pragma("trusted_schema = OFF");
  handles.set(target, db);
  return db;
}

export function warehouse(ctx: WarehouseContext = {}): Database.Database {
  return warehouseForPath(resolveWarehousePath(ctx));
}

export interface QueryResult {
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  truncated: boolean;
  ms: number;
}

const FORBIDDEN = /\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|TRIGGER|GRANT|REVOKE)\b/i;

export function runQuery(sql: string, maxRowsOrCtx: number | WarehouseContext = 5000, maybeCtx: WarehouseContext = {}): QueryResult {
  const maxRows = typeof maxRowsOrCtx === "number" ? maxRowsOrCtx : 5000;
  const ctx = typeof maxRowsOrCtx === "number" ? maybeCtx : maxRowsOrCtx;
  const trimmed = sql.trim().replace(/;\s*$/, "");

  if (!/^\s*(SELECT|WITH)\b/i.test(trimmed)) throw new Error("Only read-only SELECT/WITH queries are permitted.");
  if (trimmed.includes(";")) throw new Error("Multiple statements are not permitted; submit one query.");
  if (FORBIDDEN.test(trimmed)) throw new Error("Query contains a forbidden write or DDL keyword.");

  const t0 = performance.now();
  const stmt = warehouse(ctx).prepare(trimmed);
  stmt.raw(false);
  const allRows = stmt.all() as Record<string, unknown>[];
  const ms = Math.round((performance.now() - t0) * 100) / 100;
  const truncated = allRows.length > maxRows;
  const rows = truncated ? allRows.slice(0, maxRows) : allRows;
  const columns = rows.length > 0 ? Object.keys(rows[0]) : stmt.columns().map((c) => c.name);
  return { sql: trimmed, columns, rows, rowCount: allRows.length, truncated, ms };
}

/**
 * Tables AND views (the RavenStack analytical layer lives in views). The raw_* tables are
 * byte-exact text copies of the CSVs kept for load reconciliation; they are left out so the
 * agent always reads the typed tables and views.
 */
export function schemaSnapshot(ctx: WarehouseContext = {}): { table: string; kind: "table" | "view"; columns: { name: string; type: string }[] }[] {
  const db = warehouse(ctx);
  const objects = db
    .prepare("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'raw\\_%' ESCAPE '\\' ORDER BY type, name")
    .all() as { name: string; type: "table" | "view" }[];
  return objects.map(({ name, type }) => ({
    table: name,
    kind: type,
    columns: (db.prepare(`PRAGMA table_info(${name})`).all() as { name: string; type: string }[]).map((c) => ({ name: c.name, type: c.type })),
  }));
}
