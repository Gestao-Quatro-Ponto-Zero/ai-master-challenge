"use client";

import { useEffect, useRef, useState } from "react";
import { Modal } from "./Modal";

/**
 * Renders the rows behind a number — grounding made visible. A compact, bounded
 * preview (no hostile horizontal scroll) with a fade hint when there's more, and
 * an "Expand" to inspect the full result set in a modal.
 */

function formatCell(value: unknown, truncate = true): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString("en-US") : value.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }
  const s = String(value);
  return truncate && s.length > 48 ? `${s.slice(0, 46)}…` : s;
}

const isNumeric = (v: unknown): boolean => typeof v === "number";

function Table({
  cols,
  rows,
  truncate = true,
}: {
  cols: string[];
  rows: Record<string, unknown>[];
  truncate?: boolean;
}) {
  // Align each column by its DATA — a numeric column right-aligns its header AND its
  // cells so the heading sits directly over its values (never drifting to the left).
  const numericCol: Record<string, boolean> = {};
  for (const c of cols) {
    let numeric = 0;
    let filled = 0;
    for (const row of rows) {
      const v = row[c];
      if (v === null || v === undefined) continue;
      filled += 1;
      if (isNumeric(v)) numeric += 1;
    }
    numericCol[c] = filled > 0 && numeric / filled >= 0.6;
  }
  return (
    <table className="w-full border-collapse text-[12px]">
      <thead>
        <tr className="border-b border-edge">
          {cols.map((c) => (
            <th
              key={c}
              className={`whitespace-nowrap bg-surface px-2.5 py-1.5 font-mono font-medium text-faint ${numericCol[c] ? "text-right" : "text-left"}`}
            >
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-edge/50 last:border-0 hover:bg-panel/60">
            {cols.map((c) => (
              <td
                key={c}
                className={`whitespace-nowrap px-2.5 py-1.5 ${
                  numericCol[c] ? "text-right font-mono tabular-nums text-foreground" : "text-muted"
                }`}
              >
                {formatCell(row[c], truncate)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function EvidenceTable({
  columns,
  rows,
  maxRows = 6,
  title = "Result set",
}: {
  columns?: string[];
  rows?: Record<string, unknown>[];
  maxRows?: number;
  title?: string;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [faded, setFaded] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const update = () => setFaded(el.scrollWidth - el.clientWidth - el.scrollLeft > 4);
    update();
    el.addEventListener("scroll", update);
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [rows, columns]);

  if (!rows || rows.length === 0) return null;
  const cols = columns && columns.length > 0 ? columns : Object.keys(rows[0]);
  const preview = rows.slice(0, maxRows);
  const more = rows.length - preview.length;

  return (
    <div className="rounded-md border border-edge bg-background/60">
      <div className="relative">
        <div ref={scrollRef} className="overflow-x-auto">
          <Table cols={cols} rows={preview} />
        </div>
        {faded && (
          <div className="pointer-events-none absolute inset-y-0 right-0 w-10 bg-gradient-to-l from-background/90 to-transparent" />
        )}
      </div>
      {(more > 0 || cols.length > 4) && (
        <div className="flex items-center justify-between border-t border-edge px-2.5 py-1.5">
          <span className="text-[11px] text-faint">
            {more > 0 ? `+ ${more.toLocaleString("en-US")} more row${more === 1 ? "" : "s"}` : `${rows.length.toLocaleString("en-US")} rows`}
          </span>
          <button
            onClick={() => setExpanded(true)}
            className="text-[11px] font-medium text-accent transition-opacity hover:opacity-80"
          >
            Expand ⤢
          </button>
        </div>
      )}

      {expanded && (
        <Modal title={`${title} · ${rows.length.toLocaleString("en-US")} rows`} onClose={() => setExpanded(false)}>
          <Table cols={cols} rows={rows} truncate={false} />
        </Modal>
      )}
    </div>
  );
}
