"use client";

import { useId, useMemo, useState } from "react";
import { axisTicks, niceCeil, niceDomain, showLabelAt } from "./axis";

export interface ColumnSeries {
  name: string;
  values: number[];
  color?: string;
}

export interface ColumnChartProps {
  categories: string[];
  series: ColumnSeries[];
  height?: number;
  valueFormat?: (n: number) => string;
  /** Stack the series into one bar per category (composition) instead of grouping them side by side. */
  stacked?: boolean;
  /** Drop the bordered frame + header chrome (e.g. inside a deck panel). */
  bare?: boolean;
  /** viewBox width: pass the container's pixel width so text draws at 1:1. */
  viewWidth?: number;
  /** When set, a category is clickable — fires with the category label to drill in. */
  onSelect?: (label: string) => void;
}

const DEFAULT_VIEW_WIDTH = 640;
const SERIES_COLORS = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb"];
const NEG_COLOR = "#d9737a"; // negative values render as a muted rose so decline reads at a glance
const GRID = "#23232b";
const ZERO_GRID = "#33333d";
const LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function clampPercent(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function ColumnChart({
  categories,
  series,
  height = 240,
  valueFormat = DEFAULT_FORMAT,
  stacked = false,
  bare = false,
  onSelect,
  viewWidth,
}: ColumnChartProps) {
  const VIEW_WIDTH = viewWidth ?? DEFAULT_VIEW_WIDTH;
  const titleId = useId();
  const [hovered, setHovered] = useState<number | null>(null);
  const clickable = typeof onSelect === "function";

  const cleanSeries = useMemo(
    () =>
      series.slice(0, 4).map((s, i) => ({
        name: s.name,
        color: s.color ?? SERIES_COLORS[i % SERIES_COLORS.length],
        values: categories.map((_, ci) => safeNumber(s.values[ci])),
      })),
    [series, categories],
  );

  const ticks = useMemo(() => axisTicks(categories, Math.max(1, (VIEW_WIDTH - 66) / Math.max(1, categories.length))), [categories, VIEW_WIDTH]);

  if (categories.length === 0 || cleanSeries.length === 0) {
    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        <div className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 text-[12px] text-faint" style={{ minHeight: height }}>
          No column data available yet.
        </div>
      </div>
    );
  }

  const top = 16;
  const right = 16;
  const bottom = 36;
  const left = 50;
  const labelPad = ticks.rotate ? ticks.bottomPad : 0;
  const svgHeight = height + labelPad;
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const plotHeight = Math.max(1, height - top - bottom);
  const bandWidth = plotWidth / categories.length;
  // A rotated first label extends left of its bar center — widen the viewBox left so it never clips.
  const leftPad = ticks.rotate ? Math.max(0, Math.ceil(ticks.labelSpanX - (left + bandWidth / 2) + 4)) : 0;

  // Signed value domain: stacked composes non-negative parts (clamped); grouped/single
  // spans [lo ≤ 0 ≤ hi] so negative bars draw DOWN from the zero baseline (not vanish).
  const flatValues = cleanSeries.flatMap((s) => s.values);
  const stackedMax = Math.max(
    1,
    ...categories.map((_, ci) => cleanSeries.reduce((sum, s) => sum + Math.max(0, s.values[ci]), 0)),
  );
  const domain = stacked ? { lo: 0, hi: niceCeil(stackedMax), span: niceCeil(stackedMax) || 1 } : niceDomain(flatValues);
  const { lo, hi } = domain;
  const span = hi - lo || 1;
  const yOf = (v: number) => top + plotHeight - ((v - lo) / span) * plotHeight;
  const yZero = yOf(0);
  const gridTicks = lo < 0 ? [hi, 0, lo] : [hi, (hi + lo) / 2, lo];

  const groupInner = Math.min(bandWidth * 0.72, 44);
  const subWidth = stacked ? Math.min(bandWidth * 0.6, 46) : groupInner / cleanSeries.length;

  const hoverX = hovered === null ? null : left + bandWidth * hovered + bandWidth / 2;
  const tooltipLeft = hoverX === null ? null : clampPercent((hoverX / VIEW_WIDTH) * 100, 12, 88);

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">{stacked ? "Stacked bar chart" : "Column chart"}</span>
          <span className="font-mono text-[10px] text-faint">{categories.length.toLocaleString("en-US")} categories</span>
        </div>
      )}

      {cleanSeries.length > 1 && (
        <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1">
          {cleanSeries.map((s) => (
            <div key={s.name} className="flex items-center gap-1.5 text-[10px] text-muted">
              <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: s.color }} />
              <span className="font-mono tabular-nums">{s.name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHovered(null)}>
        <svg viewBox={`${-leftPad} 0 ${VIEW_WIDTH + leftPad} ${svgHeight}`} preserveAspectRatio="xMidYMid meet" width="100%" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`${stacked ? "Stacked" : "Grouped"} column chart, ${categories.length} categories`}</title>

          {gridTicks.map((tick, ti) => {
            const y = yOf(tick);
            const isZero = tick === 0;
            return (
              <g key={`${tick}-${ti}`}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={isZero ? ZERO_GRID : GRID} strokeWidth="1" />
                <text x={left - 6} y={y + 4} textAnchor="end" fontSize="10" fill={LABEL} className="font-mono">
                  {valueFormat(tick)}
                </text>
              </g>
            );
          })}

          {categories.map((cat, ci) => {
            const bandLeft = left + bandWidth * ci;
            const highlighted = hovered === ci;
            let stackTop = yZero;
            return (
              <g key={`${cat}-${ci}`}>
                {cleanSeries.map((s, si) => {
                  const v = s.values[ci];
                  let x: number;
                  let y: number;
                  let barH: number;
                  if (stacked) {
                    const h = (Math.max(0, v) / span) * plotHeight;
                    x = bandLeft + bandWidth / 2 - subWidth / 2;
                    stackTop -= h;
                    y = stackTop;
                    barH = h;
                  } else {
                    const groupLeft = bandLeft + (bandWidth - groupInner) / 2;
                    x = groupLeft + subWidth * si + subWidth * 0.1;
                    const yv = yOf(v);
                    y = Math.min(yv, yZero);
                    barH = Math.abs(yv - yZero);
                  }
                  const w = stacked ? subWidth : subWidth * 0.8;
                  const fill = !stacked && v < 0 ? NEG_COLOR : s.color;
                  return (
                    <rect
                      key={s.name}
                      x={x}
                      y={y}
                      width={Math.max(1, w)}
                      height={Math.max(0, barH)}
                      rx={stacked ? 0 : 3}
                      fill={fill}
                      fillOpacity={hovered === null || highlighted ? 0.92 : 0.45}
                    />
                  );
                })}
                <rect
                  x={bandLeft}
                  y={top}
                  width={bandWidth}
                  height={plotHeight}
                  fill="transparent"
                  className={clickable ? "cursor-pointer" : undefined}
                  onMouseEnter={() => setHovered(ci)}
                  onClick={clickable ? () => onSelect!(cat) : undefined}
                />
                {showLabelAt(ci, categories.length, ticks.step) && (() => {
                  const lx = bandLeft + bandWidth / 2;
                  const ly = top + plotHeight + (ticks.rotate ? 12 : 14);
                  return (
                    <text
                      x={lx}
                      y={ly}
                      textAnchor={ticks.rotate ? "end" : "middle"}
                      fontSize={ticks.fontSize}
                      fill={LABEL}
                      transform={ticks.rotate ? `rotate(${ticks.angle} ${lx} ${ly})` : undefined}
                    >
                      {cat}
                    </text>
                  );
                })()}
              </g>
            );
          })}

          <line x1={left} x2={VIEW_WIDTH - right} y1={top + plotHeight} y2={top + plotHeight} stroke={GRID} strokeWidth="1" />
        </svg>

        {hovered !== null && tooltipLeft !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-32 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
            style={{ left: `${tooltipLeft}%`, top: "12%" }}
          >
            <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{categories[hovered]}</div>
            <div className="space-y-1">
              {cleanSeries.map((s) => (
                <div key={s.name} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 text-muted">
                    <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: s.color }} />
                    <span>{s.name}</span>
                  </span>
                  <span className="font-mono tabular-nums text-foreground">{valueFormat(s.values[hovered])}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
