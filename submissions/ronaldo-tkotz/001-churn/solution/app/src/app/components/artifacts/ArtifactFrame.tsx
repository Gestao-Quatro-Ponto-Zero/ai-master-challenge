"use client";

import { useEffect, useMemo, useState } from "react";
import { ChartView } from "../charts/ChartView";
import { EvidenceTable } from "../EvidenceTable";
import { allowedChartTypes, applyTransform, type ArtifactTransform } from "@/engine/parts";
import type { ChartSpec, ChartType } from "@/engine/tools";

/**
 * The uniform quick-transform frame around any grounded chart/table artifact in a
 * chat answer. It owns ONLY projection state (type · sort · chart⇄table view) plus
 * the per-artifact pin — the toolbar changes the PROJECTION, never the data. The
 * numbers on screen stay exactly the grounded rows: every branch renders
 * applyTransform(spec, transform), which is pure and never mutates the base spec.
 *
 * ChartView is left untouched (pure) — this frame is the only owner of the state.
 * It renders in chat only; deck slides import ChartView directly, so wrapping at the
 * Chat call sites keeps the toolbar out of decks by construction.
 */

const TYPE_LABEL: Record<ChartType, string> = {
  bar: "Bar",
  column: "Column",
  stacked: "Stacked",
  line: "Line",
  area: "Area",
  pie: "Pie",
  donut: "Donut",
  scatter: "Scatter",
  radar: "Radar",
  combo: "Combo",
};

/** The sort choices, flattened for a compact single dropdown. */
type SortChoice = "none" | "value-desc" | "value-asc" | "label-asc" | "label-desc";
const SORT_LABEL: Record<SortChoice, string> = {
  none: "Sort: default",
  "value-desc": "Value ↓",
  "value-asc": "Value ↑",
  "label-asc": "Label A–Z",
  "label-desc": "Label Z–A",
};
function sortToTransform(choice: SortChoice): Pick<ArtifactTransform, "sortBy" | "sortDir"> {
  switch (choice) {
    case "value-desc": return { sortBy: "value", sortDir: "desc" };
    case "value-asc": return { sortBy: "value", sortDir: "asc" };
    case "label-asc": return { sortBy: "label", sortDir: "asc" };
    case "label-desc": return { sortBy: "label", sortDir: "desc" };
    default: return {};
  }
}

const selectCls =
  "rounded border border-edge bg-surface px-1.5 py-0.5 text-[10.5px] text-muted transition-colors hover:border-edge-strong hover:text-foreground focus:outline-none focus:border-edge-strong";

export function ArtifactFrame({
  spec,
  initialView = "chart",
  tableColumns,
  pinned,
  onTogglePin,
  onTransform,
  onAskDeeper,
}: {
  /** The grounded base spec — the ORIGINAL chart, or one built from evidence rows. */
  spec: ChartSpec;
  initialView?: "chart" | "table";
  /** Explicit column order for the table view (evidence keeps its full row shape). */
  tableColumns?: string[];
  pinned: boolean;
  /** Toggle the pin; receives the CURRENTLY displayed projection so the pin captures this card's state. */
  onTogglePin: (transform: ArtifactTransform) => void;
  /** Register the live projection so a whole-turn pin can capture the displayed chart. */
  onTransform?: (transform: ArtifactTransform) => void;
  /** Escalation only: run a fresh grounded model turn one level finer (chat only, never a deck). */
  onAskDeeper?: (spec: ChartSpec, label: string) => void;
}) {
  const allowed = useMemo(() => allowedChartTypes(spec), [spec]);
  const canChart = allowed.length > 0;
  const [type, setType] = useState<ChartType>(() => (canChart && allowed.includes(spec.type) ? spec.type : allowed[0] ?? spec.type));
  const [sort, setSort] = useState<SortChoice>("none");
  const [view, setView] = useState<"chart" | "table">(canChart ? initialView : "table");
  // Deterministic drill: clicking a chart element reveals the cached rows behind it —
  // no model call, no round-trip. The reasoning model is only re-engaged when the user
  // EXPLICITLY asks to go a level finer (the "break down further" escalation below).
  const [drill, setDrill] = useState<string | null>(null);

  const sortable = type !== "line" && type !== "area";

  // The one code path: build the displayed transform, apply it purely to the base spec.
  const transform = useMemo<ArtifactTransform>(() => {
    const s = sortable ? sortToTransform(sort) : {};
    return { type, view, ...s };
  }, [type, view, sort, sortable]);

  const rendered = useMemo(() => applyTransform(spec, transform), [spec, transform]);

  // Register the live projection for the whole-turn pin's chart capture (fires on
  // every projection change — a ref-map write on the parent, cheap).
  useEffect(() => {
    onTransform?.(transform);
  }, [onTransform, transform]);

  const cols = tableColumns && tableColumns.length > 0 ? tableColumns : [spec.x, ...spec.y];

  return (
    <div className="space-y-2">
      {/* Slim single-row toolbar — projection controls + this card's own pin. */}
      <div className="flex flex-wrap items-center gap-1.5">
        {canChart && (
          <div className="inline-flex overflow-hidden rounded border border-edge">
            {(["chart", "table"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setView(v)}
                aria-pressed={view === v}
                className={`px-2 py-0.5 text-[10.5px] font-medium transition-colors ${
                  view === v ? "bg-accent-soft/60 text-accent" : "bg-surface text-muted hover:text-foreground"
                }`}
              >
                {v === "chart" ? "Chart" : "Table"}
              </button>
            ))}
          </div>
        )}

        {canChart && view === "chart" && (
          <select
            aria-label="Chart type"
            value={type}
            onChange={(e) => setType(e.target.value as ChartType)}
            className={selectCls}
          >
            {allowed.map((t) => (
              <option key={t} value={t}>
                {TYPE_LABEL[t]}
              </option>
            ))}
          </select>
        )}

        {canChart && view === "chart" && sortable && (
          <select
            aria-label="Sort"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortChoice)}
            className={selectCls}
          >
            {(Object.keys(SORT_LABEL) as SortChoice[]).map((c) => (
              <option key={c} value={c}>
                {SORT_LABEL[c]}
              </option>
            ))}
          </select>
        )}

        <button
          type="button"
          onClick={() => onTogglePin(transform)}
          title={pinned ? "Pinned to your deck draft — click to remove" : "Pin this artifact to the deck draft"}
          aria-pressed={pinned}
          className={`group ml-auto inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10.5px] font-medium transition-colors ${
            pinned
              ? "border-accent/30 bg-accent-soft/50 text-accent hover:border-red-400/40 hover:bg-red-400/5 hover:text-red-300"
              : "border-edge text-muted hover:border-edge-strong hover:text-foreground"
          }`}
        >
          <svg viewBox="0 0 24 24" fill={pinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-2.5 w-2.5">
            <path d="M12 17v5M9 10.76V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4.76a2 2 0 0 0 .59 1.42l1.41 1.41A2 2 0 0 1 18 15.83V17H6v-1.17a2 2 0 0 1 .59-1.42L8 13a2 2 0 0 0 .59-1.42Z" />
          </svg>
          {pinned ? (
            <>
              <span className="group-hover:hidden">Pinned</span>
              <span className="hidden group-hover:inline">Remove</span>
            </>
          ) : (
            "Pin"
          )}
        </button>
      </div>

      {view === "chart" && canChart ? (
        <ChartView spec={rendered} onDrill={(label) => setDrill(label)} />
      ) : (
        <EvidenceTable columns={cols} rows={rendered.data} maxRows={8} title={spec.title || "Result set"} />
      )}

      {drill !== null && (() => {
        // Filter the ALREADY-FETCHED rows to the clicked category — first on the grouping
        // column, else any cell that equals the clicked label (covers scatter/entity picks).
        const byGroup = rendered.data.filter((r) => String(r[rendered.x] ?? "") === drill);
        const matched = byGroup.length > 0 ? byGroup : rendered.data.filter((r) => Object.values(r).some((v) => String(v) === drill));
        const detailCols = matched.length > 0 ? Object.keys(matched[0]) : cols;
        return (
          <div className="space-y-2 rounded-md border border-edge bg-surface/70 p-2.5">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Detail</span>
              <span className="text-[12px] font-medium text-foreground">{drill}</span>
              <span className="font-mono text-[10px] text-faint">
                {matched.length.toLocaleString("en-US")} row{matched.length === 1 ? "" : "s"} · instant, from this result
              </span>
              <button
                type="button"
                onClick={() => setDrill(null)}
                className="ml-auto rounded border border-edge px-1.5 py-0.5 text-[10.5px] text-muted transition-colors hover:border-edge-strong hover:text-foreground"
              >
                Close
              </button>
            </div>
            {matched.length > 0 ? (
              <EvidenceTable columns={detailCols} rows={matched} maxRows={8} title={`${drill} · detail`} />
            ) : (
              <div className="rounded border border-dashed border-edge bg-panel/40 px-3 py-3 text-center text-[11.5px] text-faint">
                No matching rows in this result.
              </div>
            )}
            {onAskDeeper && (
              <button
                type="button"
                onClick={() => {
                  onAskDeeper(rendered, drill);
                  setDrill(null);
                }}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-accent transition-opacity hover:opacity-80"
              >
                Break this down further with Veta <span aria-hidden>→</span>
              </button>
            )}
          </div>
        );
      })()}
    </div>
  );
}
