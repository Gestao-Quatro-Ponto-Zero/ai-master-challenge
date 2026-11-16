/**
 * Data paths and first-boot directory setup.
 *
 * The RavenStack database is built by solution/sql/build_db.py and opened read-only.
 * Locally WAREHOUSE_PATH points at it; on a deploy the file ships at data/ravenstack.db.
 */
import fs from "node:fs";
import path from "node:path";

export function warehousePath(): string {
  return process.env.WAREHOUSE_PATH || path.join(process.cwd(), "data", "ravenstack.db");
}

export function appDbPath(): string {
  return process.env.APP_DB_PATH || path.join(process.cwd(), "data", "app.sqlite");
}

export function datasetsDir(): string {
  return process.env.DATASETS_DIR || path.join(path.dirname(appDbPath()), "datasets");
}

/** Ensure the app's writable data dirs exist and warn if the RavenStack database is missing. */
export function ensureDataDirs(): void {
  fs.mkdirSync(path.dirname(appDbPath()), { recursive: true });
  fs.mkdirSync(datasetsDir(), { recursive: true });
  if (!fs.existsSync(warehousePath())) {
    console.warn(`[data] RavenStack database not found at ${warehousePath()} — run solution/sql/build_db.py`);
  }
}
