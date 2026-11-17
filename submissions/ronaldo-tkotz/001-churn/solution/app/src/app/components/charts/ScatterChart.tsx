"use client";

import { useId, useMemo, useState } from "react";

export interface ScatterPoint {
  x: number;
  y: number;
  label?: string;
}

export interface ScatterSeries {
  name: string;
  points: ScatterPoint[];
  color?: string;
}

export interface ScatterChartProps {
  series: ScatterSeries[];
  xLabel?: string;
  yLabel?: string;
  height?: number;
  xFormat?: (n: number) => string;
  yFormat?: (n: number) => string;
  bare?: boolean;
  /** viewBox width: pass the container's pixel width so text draws at 1:1. */
  viewWidth?: number;
  /** When set, a point is clickable — fires with the point's label (entity) to drill in. */
  onSelect?: (label: string) => void;
}

const DEFAULT_VIEW_WIDTH = 640;
const SERIES_COLORS = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb"];
const GRID = "#23232b";
const LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => (Number.isInteger(n) ? n.toLocaleString("en-US") : n.toFixed(2));

function isNum(v: number): boolean {
  return typeof v === "number" && Number.isFinite(v);
}

/** A padded [min,max] domain for an axis; widens a degenerate range so points aren't stacked on an edge. */
function bounds(values: number[]): [number, number] {
  const v = values.filter(isNum);
  if (v.length === 0) return [0, 1];
  let min = Math.min(...v);
  const max = Math.max(...v);
  if (min === max) {
    const d = Math.abs(min) || 1;
    return [min - d * 0.5, max + d * 0.5];
  }
  const pad = (max - min) * 0.08;
  // Anchor at zero when the data sits comfortably above it (cleaner axis).
  if (min > 0 && min < (max - min) * 0.4) min = 0;
  else min -= pad;
  return [min, max + pad];
}

function ticks(min: number, max: number, count = 4): number[] {
  return Array.from({ length: count + 1 }, (_, i) => min + ((max - min) * i) / count);
}

function clampPercent(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function ScatterChart({ series, xLabel, yLabel, height = 240, xFormat = DEFAULT_FORMAT, yFormat = DEFAULT_FORMAT, bare = false, onSelect, viewWidth }: ScatterChartProps) {
  const VIEW_WIDTH = viewWidth ?? DEFAULT_VIEW_WIDTH;
  const titleId = useId();
  const [hovered, setHovered] = useState<{ s: number; p: number } | null>(null);
  const clickable = typeof onSelect === "function";

  const cleanSeries = useMemo(
    () =>
      series.slice(0, 4).map((s, i) => ({
        name: s.name,
        color: s.color ?? SERIES_COLORS[i % SERIES_COLORS.length],
        points: s.points.filter((p) => isNum(p.x) && isNum(p.y)),
      })),
    [series],
  );

  const allPoints = cleanSeries.flatMap((s) => s.points);

  if (allPoints.length === 0) {
    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        <div className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 text-[12px] text-faint" style={{ minHeight: height }}>
          No points to plot.
        </div>
      </div>
    );
  }

  const top = 16;
  const right = 30;
  const bottom = 38;
  const left = 54;
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const plotHeight = Math.max(1, height - top - bottom);

  const [xMin, xMax] = bounds(allPoints.map((p) => p.x));
  const [yMin, yMax] = bounds(allPoints.map((p) => p.y));
  const sx = (x: number) => left + ((x - xMin) / (xMax - xMin || 1)) * plotWidth;
  const sy = (y: number) => top + plotHeight - ((y - yMin) / (yMax - yMin || 1)) * plotHeight;

  const hov = hovered ? cleanSeries[hovered.s]?.points[hovered.p] : null;
  const hovColor = hovered ? cleanSeries[hovered.s]?.color : undefined;
  const tipLeft = hov ? clampPercent((sx(hov.x) / VIEW_WIDTH) * 100, 12, 88) : null;
  const tipTop = hov ? clampPercent((sy(hov.y) / height) * 100, 14, 86) : null;

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Scatter plot</span>
          <span className="font-mono text-[10px] text-faint">{allPoints.length.toLocaleString("en-US")} points</span>
        </div>
      )}

      {cleanSeries.length > 1 && (
        <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1">
          {cleanSeries.map((s) => (
            <div key={s.name} className="flex items-center gap-1.5 text-[10px] text-muted">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="font-mono tabular-nums">{s.name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHovered(null)}>
        <svg viewBox={`0 0 ${VIEW_WIDTH} ${height}`} preserveAspectRatio="xMidYMid meet" width="100%" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`Scatter plot of ${allPoints.length} points`}</title>

          {ticks(yMin, yMax, 4).map((t) => {
            const y = sy(t);
            return (
              <g key={`y-${t}`}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={GRID} strokeWidth="1" strokeOpacity="0.6" />
                <text x={left - 7} y={y + 4} textAnchor="end" fontSize="10" fill={LABEL} className="font-mono">
                  {yFormat(t)}
                </text>
              </g>
            );
          })}

          {ticks(xMin, xMax, 4).map((t) => {
            const x = sx(t);
            return (
              <text key={`x-${t}`} x={x} y={height - 18} textAnchor="middle" fontSize="10" fill={LABEL} className="font-mono">
                {xFormat(t)}
              </text>
            );
          })}

          {cleanSeries.map((s, si) =>
            s.points.map((p, pi) => {
              const on = hovered?.s === si && hovered?.p === pi;
              return (
                <circle
                  key={`${si}-${pi}`}
                  cx={sx(p.x)}
                  cy={sy(p.y)}
                  r={on ? 6 : 4.2}
                  fill={s.color}
                  fillOpacity={hovered === null || on ? 0.85 : 0.45}
                  stroke={on ? "#f5f5f7" : "#0E0E10"}
                  strokeWidth={on ? 1.4 : 0.8}
                  className={clickable && p.label ? "cursor-pointer" : undefined}
                  onMouseEnter={() => setHovered({ s: si, p: pi })}
                  onClick={clickable && p.label ? () => onSelect!(p.label!) : undefined}
                />
              );
            }),
          )}

          <line x1={left} x2={VIEW_WIDTH - right} y1={top + plotHeight} y2={top + plotHeight} stroke={GRID} strokeWidth="1" />
          {xLabel && (
            <text x={left + plotWidth / 2} y={height - 3} textAnchor="middle" fontSize="10" fill={LABEL} className="uppercase tracking-wider">
              {xLabel}
            </text>
          )}
          {yLabel && (
            <text x={12} y={top + plotHeight / 2} textAnchor="middle" fontSize="10" fill={LABEL} className="uppercase tracking-wider" transform={`rotate(-90 12 ${top + plotHeight / 2})`}>
              {yLabel}
            </text>
          )}
        </svg>

        {hov && tipLeft !== null && tipTop !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-28 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
            style={{ left: `${tipLeft}%`, top: `${tipTop}%` }}
          >
            {hov.label && <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{hov.label}</div>}
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-muted">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: hovColor }} />
                <span>{xLabel ?? "x"}</span>
              </span>
              <span className="font-mono tabular-nums text-foreground">{xFormat(hov.x)}</span>
            </div>
            <div className="mt-0.5 flex items-center justify-between gap-3">
              <span className="text-muted">{yLabel ?? "y"}</span>
              <span className="font-mono tabular-nums text-foreground">{yFormat(hov.y)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
