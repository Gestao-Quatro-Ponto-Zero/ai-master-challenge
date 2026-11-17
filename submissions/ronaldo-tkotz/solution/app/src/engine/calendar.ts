/**
 * The data clock — the analysis window, read from the database's own `parametros` table
 * (data_inicio, data_corte; decisions D17 and D21). Nothing is hardcoded here: change the
 * parameters in solution/sql/01_schema.sql, rebuild, and every window re-anchors.
 *
 * "Today" is the cutoff date (31/12/2024). The cutoff day is whole, so the last month is
 * complete. A database without `parametros` (e.g. an uploaded file) degrades to an empty clock.
 */
import { resolveWarehousePath, runQuery, type WarehouseContext } from "./warehouse";

export interface DataClock {
  /** YYYY-MM-DD — the cutoff date ("as of"). */
  today: string;
  /** First day of the analysis window (YYYY-MM-DD). */
  firstDate: string;
  /** Last day of the analysis window (YYYY-MM-DD) — the cutoff date. */
  lastDate: string;
  /** YYYY-MM if the latest month is incomplete, else null. */
  partialMonth: string | null;
  /** YYYY-MM — the last complete month. */
  lastFullMonth: string;
  /** Trailing-12-full-months window, lower bound (YYYY-MM-01, inclusive). */
  windowStart: string;
  /** Trailing-12-full-months window, upper bound (YYYY-MM-01, exclusive). */
  windowEnd: string;
  /** YYYY-MM-01 — the first complete month (for long-run trend charts). */
  adoptionStart: string;
}

const EMPTY_CLOCK: DataClock = {
  today: "",
  firstDate: "",
  lastDate: "",
  partialMonth: null,
  lastFullMonth: "",
  windowStart: "",
  windowEnd: "",
  adoptionStart: "",
};

/** True when the clock could be derived — i.e. the dataset has a usable time frame. */
export function hasClock(clock: DataClock): boolean {
  return clock.today !== "";
}

const cache = new Map<string, DataClock>();

export function dataClock(ctx: WarehouseContext = {}): DataClock {
  const key = resolveWarehousePath(ctx);
  const hit = cache.get(key);
  if (hit) return hit;

  let r;
  try {
    r = runQuery(
      `WITH p AS (
         SELECT date((SELECT valor FROM parametros WHERE nome = 'data_inicio')) AS ini,
                date((SELECT valor FROM parametros WHERE nome = 'data_corte'))  AS corte
       )
       SELECT ini AS first_date,
              corte AS last_date,
              corte AS today,
              date(corte, 'start of month', '+1 month')               AS window_end,
              date(corte, 'start of month', '+1 month', '-12 months') AS window_start,
              strftime('%Y-%m', corte)                                AS last_full_month,
              date(ini, 'start of month')                             AS adoption_start
       FROM p
       WHERE ini IS NOT NULL AND corte IS NOT NULL`,
      ctx,
    );
  } catch {
    cache.set(key, EMPTY_CLOCK);
    return EMPTY_CLOCK;
  }

  const row = r.rows[0] as Record<string, string | null> | undefined;
  if (!row) {
    cache.set(key, EMPTY_CLOCK);
    return EMPTY_CLOCK;
  }
  const clock: DataClock = {
    today: String(row.today ?? ""),
    firstDate: String(row.first_date ?? ""),
    lastDate: String(row.last_date ?? ""),
    partialMonth: null,
    lastFullMonth: String(row.last_full_month ?? ""),
    windowStart: String(row.window_start ?? ""),
    windowEnd: String(row.window_end ?? ""),
    adoptionStart: String(row.adoption_start ?? ""),
  };
  cache.set(key, clock);
  return clock;
}
