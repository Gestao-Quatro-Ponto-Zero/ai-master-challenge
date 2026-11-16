/**
 * Pure, testable helpers for the chat Artifact Layer (Stream A). No React, no DOM —
 * these are the deterministic transforms the ArtifactFrame and the markdown-table
 * artifact lean on, so the honesty rules (grounded rows in, grounded rows out) are
 * unit-testable in isolation (see scripts/artifact-frame-test.ts).
 */
import { parseDisplayNumber } from "@/engine/parts";
import { allowedChartTypes } from "@/engine/parts";
import type { ChartSpec, ChartType } from "@/engine/tools";
import { TABLE_PIN_MAX_ROWS } from "@/engine/parts";

/** Is a single cell value a magnitude? Tolerant of numbers and display strings. */
function isNumericValue(v: unknown): boolean {
  if (typeof v === "number") return Number.isFinite(v);
  if (typeof v === "string") return parseDisplayNumber(v) !== null;
  return false;
}

/**
 * Build a grounded ChartSpec from raw query rows so an evidence table can be
 * projected as a chart WITHOUT inventing numbers — every cell it charts already
 * parses to a magnitude (the same guard the persisted-chart path uses).
 *
 * x = the first non-numeric column (the natural category), else the first column.
 * y = the numeric columns (majority-parse rule per column), never x.
 * type = allowedChartTypes for the shape, defaulting to "column" when allowed.
 */
export function chartSpecFromRows(
  columns: string[],
  rows: Record<string, unknown>[],
  title = "",
): ChartSpec {
  const cols = columns.length > 0 ? columns : rows[0] ? Object.keys(rows[0]) : [];
  const numericCols = cols.filter((c) => {
    if (rows.length === 0) return false;
    const parsed = rows.filter((r) => isNumericValue(r[c])).length;
    return parsed * 2 >= rows.length && parsed > 0; // majority of body cells parse
  });
  const x = cols.find((c) => !numericCols.includes(c)) ?? cols[0] ?? "";
  const y = numericCols.filter((c) => c !== x);
  const allowed = allowedChartTypes({ x, y, data: rows });
  const type: ChartType = allowed.includes("column") ? "column" : (allowed[0] ?? "column");
  return { type, title, x, y, data: rows };
}

/**
 * Sort markdown table BODY rows by a column, non-mutating. Numeric when both cells
 * parse as display numbers (via the one deterministic parser), else string compare —
 * so a "$21.9M" column sorts by magnitude and a name column sorts alphabetically.
 */
export function sortMarkdownBody(body: string[][], colIndex: number, dir: "asc" | "desc"): string[][] {
  const sign = dir === "asc" ? 1 : -1;
  return [...body].sort((ra, rb) => {
    const a = (ra[colIndex] ?? "").trim();
    const b = (rb[colIndex] ?? "").trim();
    const an = parseDisplayNumber(a);
    const bn = parseDisplayNumber(b);
    if (an !== null && bn !== null) return (an - bn) * sign;
    return a.localeCompare(b) * sign;
  });
}

/**
 * Convert parsed markdown table rows (head + body, cells as strings) into the
 * table-pin payload: header cells as columns, each body row as an object keyed by
 * its header. Capped at the pin row limit. Blank/duplicate headers get a stable
 * fallback key so no cell is silently dropped.
 */
export function markdownRowsToTablePayload(rows: string[][]): { columns: string[]; rows: Record<string, string>[] } {
  const head = rows[0] ?? [];
  const columns = head.map((h, i) => (h.trim() ? h.trim() : `col${i + 1}`));
  const body = rows.slice(1, 1 + TABLE_PIN_MAX_ROWS);
  const out = body.map((r) => {
    const obj: Record<string, string> = {};
    columns.forEach((c, i) => {
      obj[c] = (r[i] ?? "").trim();
    });
    return obj;
  });
  return { columns, rows: out };
}
