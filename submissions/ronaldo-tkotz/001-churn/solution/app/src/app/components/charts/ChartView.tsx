"use client";

import { useMemo } from "react";
import type { ChartSpec } from "@/engine/tools";
import { BarChart, type BarDatum } from "./BarChart";
import { LineChart, type LineSeries } from "./LineChart";
import { ColumnChart } from "./ColumnChart";
import { PieChart } from "./PieChart";
import { ScatterChart } from "./ScatterChart";
import { RadarChart } from "./RadarChart";
import { ComboChart } from "./ComboChart";

const SERIES_COLORS = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb"];

/** Coerce a cell to a finite number — tolerant of "$1,200" / "84%" string values. */
function num(v: unknown): number {
  if (typeof v === "number") return Number.isFinite(v) ? v : 0;
  if (typeof v === "string") {
    const n = Number(v.replace(/[$,%\s]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}

/**
 * Order two x-axis keys along a timeline: numeric first, then parseable dates
 * (YYYY-MM / YYYY-MM-DD / ISO), then plain string. Used only for line/area, whose
 * x-axis is inherently ordered — a line drawn through unsorted months zig-zags.
 */
function byXAxis(a: unknown, b: unknown): number {
  const sa = String(a ?? "").trim();
  const sb = String(b ?? "").trim();
  const na = Number(sa);
  const nb = Number(sb);
  if (sa !== "" && sb !== "" && Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
  const da = Date.parse(sa);
  const db = Date.parse(sb);
  if (Number.isFinite(da) && Number.isFinite(db)) return da - db;
  return sa < sb ? -1 : sa > sb ? 1 : 0;
}

function compactUsd(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 1_000) return `$${(n / 1_000).toFixed(abs >= 10_000 ? 0 : 1)}K`;
  return `$${Math.round(n).toLocaleString("en-US")}`;
}

/** Compact a plain (non-currency) magnitude so axis labels never overflow — 200000000 → "200M". */
function compactNum(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`;
  if (abs >= 10_000) return `${Math.round(n / 1_000)}K`;
  return Number.isInteger(n) ? n.toLocaleString("en-US") : n.toFixed(1);
}

/** Infer a value formatter from the plotted column names — currency vs. percent vs. plain count. */
function makeFormatter(fields: string[]): (n: number) => string {
  if (fields.some((f) => /usd|arr|mrr|revenue|amount|spend|cost|price|\$/i.test(f))) return compactUsd;
  if (fields.some((f) => /pct|percent|rate|ratio|share|score/i.test(f))) {
    return (n) => (Number.isInteger(n) ? `${n}` : n.toFixed(1));
  }
  // Plain counts/values — compact large magnitudes so vertical-axis labels don't clip.
  return compactNum;
}

const label = (f: string): string => f.replace(/_/g, " ");

/**
 * Renders a grounded make_chart spec inline. The spec's `data` is a snapshot of
 * rows the agent already queried this turn, so the chart never invents numbers —
 * it only re-draws grounded rows. Routes every chart type onto a real renderer
 * (the same components the deck SlideView uses), so chat and deck draw identically.
 * `bare` drops the framed chrome (and the figure title) when the caller supplies its
 * own — e.g. inside a deck's dark panel.
 */
export function ChartView({
  spec,
  height,
  bare = false,
  onDrill,
}: {
  spec: ChartSpec;
  height?: number;
  bare?: boolean;
  /** When set (chat only — never on a deck slide), clicking a chart element drills into it. */
  onDrill?: (label: string) => void;
}) {
  const yFields = useMemo(() => (spec.y ?? []).filter(Boolean), [spec.y]);
  const data = useMemo(() => (Array.isArray(spec.data) ? spec.data : []), [spec.data]);
  // line/area plot an ordered x-axis; if the query returned its rows unsorted, the
  // line zig-zags across time. Sort those two types by x — grounded (the same rows,
  // reordered), never fabricated — and leave categorical charts (bar/column/pie/…)
  // in the agent's intentional order (it may have sorted by value on purpose).
  const plotData = useMemo(() => {
    if (spec.type !== "line" && spec.type !== "area") return data;
    return [...data].sort((r1, r2) => byXAxis(r1[spec.x], r2[spec.x]));
  }, [data, spec.type, spec.x]);
  const fmt = useMemo(() => makeFormatter(yFields), [yFields]);
  const h = height ? { height } : {};

  // For scatter, the click handle should be the entity, not the numeric x-value:
  // prefer the first string column that is neither x nor a plotted y (e.g. account_name).
  const scatterLabelKey = useMemo(() => {
    const row = data[0];
    if (!row) return spec.x;
    const named = Object.keys(row).find((k) => k !== spec.x && !yFields.includes(k) && typeof row[k] === "string");
    return named ?? spec.x;
  }, [data, spec.x, yFields]);

  const categories = useMemo(() => plotData.map((r) => String(r[spec.x] ?? "")), [plotData, spec.x]);
  const numericSeries = useMemo(
    () =>
      yFields.map((f, i) => ({
        name: label(f),
        values: plotData.map((r) => num(r[f])),
        color: SERIES_COLORS[i % SERIES_COLORS.length],
      })),
    [yFields, plotData],
  );

  let chart: React.ReactNode;

  if (data.length === 0 || yFields.length === 0) {
    chart = (
      <div className="rounded-md border border-dashed border-edge bg-panel/40 px-3 py-5 text-center text-[11.5px] text-faint">
        No rows to plot.
      </div>
    );
  } else if (spec.type === "pie" || spec.type === "donut") {
    const slices = data.map((r) => ({ label: String(r[spec.x] ?? ""), value: num(r[yFields[0]]) }));
    chart = <PieChart slices={slices} donut={spec.type === "donut"} valueFormat={fmt} bare={bare} onSelect={onDrill} {...h} />;
  } else if (spec.type === "scatter") {
    const xFmt = makeFormatter([spec.x]);
    const series = yFields.map((f, i) => ({
      name: label(f),
      color: SERIES_COLORS[i % SERIES_COLORS.length],
      points: data.map((r) => ({ x: num(r[spec.x]), y: num(r[f]), label: String(r[scatterLabelKey] ?? r[spec.x] ?? "") })),
    }));
    chart = <ScatterChart series={series} xLabel={label(spec.x)} yLabel={label(yFields[0])} xFormat={xFmt} yFormat={fmt} bare={bare} onSelect={onDrill} {...h} />;
  } else if (spec.type === "radar") {
    chart = <RadarChart axes={categories} series={numericSeries} valueFormat={fmt} bare={bare} onSelect={onDrill} {...h} />;
  } else if (spec.type === "combo") {
    chart = (
      <ComboChart
        categories={categories}
        bar={numericSeries[0]}
        line={numericSeries[1]}
        barFormat={makeFormatter([yFields[0]])}
        lineFormat={makeFormatter([yFields[1] ?? yFields[0]])}
        bare={bare}
        onSelect={onDrill}
        {...h}
      />
    );
  } else if (spec.type === "column" || spec.type === "stacked") {
    chart = <ColumnChart categories={categories} series={numericSeries} stacked={spec.type === "stacked"} valueFormat={fmt} bare={bare} onSelect={onDrill} {...h} />;
  } else if (spec.type === "line" || spec.type === "area") {
    const series: LineSeries[] = yFields.slice(0, 2).map((f, i) => ({
      name: label(f),
      values: plotData.map((r) => num(r[f])),
      color: SERIES_COLORS[i % SERIES_COLORS.length],
    }));
    // line/area chart trends by an ordered x — drilling a single time point reads oddly, so it stays non-interactive.
    chart = <LineChart categories={categories} series={series} yFormat={fmt} bare={bare} {...h} />;
  } else {
    // bar (default) — a single value series, horizontal.
    const barData: BarDatum[] = data.map((r) => ({ label: String(r[spec.x] ?? ""), value: num(r[yFields[0]]) }));
    chart = <BarChart data={barData} valueFormat={fmt} bare={bare} onSelect={onDrill} {...h} />;
  }

  // A drilled chart re-charts a finer cut; the hint shows only in chat (never on a deck slide),
  // and only when there's something to click.
  const drillable = typeof onDrill === "function" && !bare && spec.type !== "line" && spec.type !== "area" && data.length > 0 && yFields.length > 0;

  return (
    <figure className="space-y-1.5">
      {!bare && spec.title && (
        <figcaption className="text-[12px] font-medium tracking-tight text-foreground">{spec.title}</figcaption>
      )}
      {chart}
      {drillable && (
        <figcaption className="flex items-center gap-1 text-[10.5px] text-faint">
          <span aria-hidden>↳</span> Click an element to drill into it.
        </figcaption>
      )}
    </figure>
  );
}
