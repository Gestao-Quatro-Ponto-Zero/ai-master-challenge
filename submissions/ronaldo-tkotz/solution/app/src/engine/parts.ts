/**
 * The Artifact Layer contract — shared by the chat ArtifactFrame (client), the
 * saved-insights API, and the deck builder. One invariant, three surfaces:
 * every renderable object in an answer is a grounded artifact = rows +
 * projection + citations. The user owns the PROJECTION (chart type, sort,
 * chart⇄table view) and the PROSE; the warehouse owns the DATA.
 *
 * Design consequences encoded here (see ISA Decisions 2026-07-04):
 * - A projection is stored as a TRANSFORM beside the original grounded spec,
 *   never baked into rows — the deck builder re-grounds rows fresh and then
 *   re-applies the transform, so freshness can't erase the user's view.
 * - Numeric parsing of display strings ("$21.9M", "84%", "1,234") lives here,
 *   in ONE deterministic parser, so the chart-this guard and any charting of
 *   display tables share exactly the same notion of "parseable number".
 */
// ── The chart vocabulary (canonical home) ────────────────────────────────────
// parts.ts is imported by CLIENT components (the ArtifactFrame), so it must
// stay dependency-free: importing these from tools.ts would drag the whole
// server engine (warehouse, better-sqlite3) into the browser bundle. tools.ts
// re-exports this vocabulary, so server-side importers are unchanged.

/**
 * Every type the UI has a real renderer for. Single source of truth: the
 * make_chart enum, the saved-insight validator, the toolbar's switcher, and
 * the deck re-grounder all derive their allowed set from here.
 */
export const CHART_TYPES = [
  "bar",
  "column",
  "stacked",
  "line",
  "area",
  "pie",
  "donut",
  "scatter",
  "radar",
  "combo",
] as const;

export type ChartType = (typeof CHART_TYPES)[number];

/** Runtime guard — is an untrusted value one of the renderable chart types? */
export function isChartType(v: unknown): v is ChartType {
  return typeof v === "string" && (CHART_TYPES as readonly string[]).includes(v);
}

/**
 * A grounded chart the UI renders inline (chat) and can carry into a deck slide.
 * `data` is a snapshot of rows the agent already queried this turn — the chart
 * only re-draws grounded rows, it never sources its own numbers.
 */
export interface ChartSpec {
  type: ChartType;
  title: string;
  x: string;
  y: string[];
  data: Record<string, unknown>[];
}

// ── Pin kinds ────────────────────────────────────────────────────────────────

/** What a saved insight points at. turn/finding predate the artifact layer. */
export const PIN_KINDS = ["turn", "finding", "chart", "table", "narrative"] as const;
export type PinKind = (typeof PIN_KINDS)[number];

/** The per-object pin kinds introduced by the artifact layer. */
export const PART_KINDS = ["chart", "table", "narrative"] as const;
export type PartKind = (typeof PART_KINDS)[number];

export function isPinKind(v: unknown): v is PinKind {
  return typeof v === "string" && (PIN_KINDS as readonly string[]).includes(v);
}
export function isPartKind(v: unknown): v is PartKind {
  return typeof v === "string" && (PART_KINDS as readonly string[]).includes(v);
}

// ── The projection transform ─────────────────────────────────────────────────

export interface ArtifactTransform {
  /** Displayed chart type when the user switched it (else the spec's own type). */
  type?: ChartType;
  /** Sort key for categorical projections. Line/area stay x-ordered upstream. */
  sortBy?: "value" | "label";
  sortDir?: "asc" | "desc";
  /** Whether the artifact was being viewed as a chart or as its data table. */
  view?: "chart" | "table";
}

/** A chart payload as persisted on a pin: the ORIGINAL grounded spec plus the
 *  user's displayed transform. Backward compatible — old pins have no transform. */
export type StoredChart = ChartSpec & { transform?: ArtifactTransform };

export function coerceTransform(v: unknown): ArtifactTransform | undefined {
  if (!v || typeof v !== "object") return undefined;
  const t = v as Record<string, unknown>;
  const out: ArtifactTransform = {};
  if (isChartType(t.type)) out.type = t.type;
  if (t.sortBy === "value" || t.sortBy === "label") out.sortBy = t.sortBy;
  if (t.sortDir === "asc" || t.sortDir === "desc") out.sortDir = t.sortDir;
  if (t.view === "chart" || t.view === "table") out.view = t.view;
  return Object.keys(out).length > 0 ? out : undefined;
}

/**
 * Re-apply a displayed transform to grounded rows. Called AFTER re-grounding at
 * deck time (fresh rows first, then the user's sort, then their displayed type)
 * and by the chat frame for live sorting. Pure — never mutates the input.
 */
export function applyTransform(spec: ChartSpec, transform?: ArtifactTransform): ChartSpec {
  if (!transform) return spec;
  const type = transform.type ?? spec.type;
  let data = spec.data;
  // line/area are inherently x-ordered (ChartView sorts them); a value-sort would fight it.
  const sortable = type !== "line" && type !== "area";
  if (sortable && transform.sortBy && spec.y[0]) {
    const key = transform.sortBy === "value" ? spec.y[0] : spec.x;
    const dir = transform.sortDir === "asc" ? 1 : -1;
    data = [...data].sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      const an = typeof av === "number" ? av : parseDisplayNumber(String(av ?? ""));
      const bn = typeof bv === "number" ? bv : parseDisplayNumber(String(bv ?? ""));
      if (transform.sortBy === "value" && an !== null && bn !== null) return (an - bn) * dir;
      return String(av ?? "").localeCompare(String(bv ?? "")) * dir;
    });
  }
  return { ...spec, type, data };
}

// ── Table pins ───────────────────────────────────────────────────────────────

export interface TablePayload {
  columns: string[];
  /** Row snapshot, capped — the pin's cited SQL re-grounds the real thing at deck time. */
  rows: Record<string, unknown>[];
}

export const TABLE_PIN_MAX_ROWS = 50;

export function coerceTablePayload(v: unknown): TablePayload | null {
  if (!v || typeof v !== "object") return null;
  const t = v as Record<string, unknown>;
  if (!Array.isArray(t.columns) || !Array.isArray(t.rows)) return null;
  const columns = t.columns.filter((c): c is string => typeof c === "string").slice(0, 12);
  const rows = t.rows
    .filter((r): r is Record<string, unknown> => !!r && typeof r === "object" && !Array.isArray(r))
    .slice(0, TABLE_PIN_MAX_ROWS);
  if (columns.length === 0 || rows.length === 0) return null;
  return { columns, rows };
}

// ── Deterministic display-number parsing (the chart-this honesty guard) ──────

const DISPLAY_NUM = /^\s*[$€£]?\s*(-?[\d,]+(?:\.\d+)?)\s*([%MKB])?\s*$/i;

/**
 * Parse a display-formatted cell to its number, or null when not deterministic.
 * "$21.9M" → 21_900_000 · "84%" → 84 · "1,234" → 1234 · "2026-01" → null (a date,
 * not a magnitude) · "n/a" → null. A column charts ONLY if every body cell parses.
 */
export function parseDisplayNumber(s: string): number | null {
  if (/^\d{4}-\d{2}(-\d{2})?$/.test(s.trim())) return null; // dates align right but aren't magnitudes
  const m = DISPLAY_NUM.exec(s);
  if (!m) return null;
  const base = Number(m[1].replace(/,/g, ""));
  if (!Number.isFinite(base)) return null;
  const mult = m[2] ? { "%": 1, K: 1e3, M: 1e6, B: 1e9 }[m[2].toUpperCase() as "%" | "K" | "M" | "B"] : 1;
  return base * (mult ?? 1);
}

// ── Shape gating: which chart types honestly fit a data shape ────────────────

/**
 * The single source of truth for the toolbar's type switcher AND any table→chart
 * offer: a projection is offered only when the data shape supports it honestly.
 */
export function allowedChartTypes(spec: Pick<ChartSpec, "x" | "y" | "data">): ChartType[] {
  const rows = spec.data.length;
  const ys = spec.y.length;
  if (rows === 0 || ys === 0) return [];
  const xNumeric = rows > 0 && spec.data.every((r) => {
    const v = r[spec.x];
    return typeof v === "number" || (typeof v === "string" && parseDisplayNumber(v) !== null);
  });
  const firstYNonNegative = spec.data.every((r) => {
    const v = Number(r[spec.y[0]]);
    return Number.isFinite(v) ? v >= 0 : true;
  });
  return CHART_TYPES.filter((t) => {
    switch (t) {
      case "bar":
      case "column":
        return rows <= 50;
      case "stacked":
        return ys >= 2 && rows <= 50;
      case "line":
      case "area":
        return rows >= 2;
      case "pie":
      case "donut":
        return ys === 1 && rows <= 10 && firstYNonNegative;
      case "scatter":
        return xNumeric;
      case "radar":
        return rows >= 3 && rows <= 12;
      case "combo":
        return ys === 2;
    }
  });
}

// ── Deck lineage (per-slide trace back to the producing chat) ────────────────

export interface SlideLineage {
  conversationId?: string | null;
  question?: string | null;
  citedSql?: string[];
}
