"use client";

import { useId, useMemo, useState } from "react";
import { showLabelAt, xAxisLabels } from "./axis";

export interface LineSeries {
  name: string;
  values: number[];
  color?: string;
}

export interface LineChartProps {
  categories: string[];
  series: LineSeries[];
  height?: number;
  yFormat?: (n: number) => string;
  markLastPartial?: boolean;
  /** Hero mode: drop the bordered frame + "Line chart / N points" header chrome. */
  bare?: boolean;
}

const VIEW_WIDTH = 640;
const DEFAULT_ACCENT = "#e3b341";
const DEFAULT_SECONDARY = "#8a90ad";
const DEFAULT_GRID = "#23232b";
const DEFAULT_LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function alignValues(values: number[], length: number): number[] {
  return Array.from({ length }, (_, index) => safeNumber(values[index]));
}

function niceCeil(value: number): number {
  if (!(value > 0)) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;

  if (normalized <= 1) return magnitude;
  if (normalized <= 2) return 2 * magnitude;
  if (normalized <= 5) return 5 * magnitude;
  return 10 * magnitude;
}

function safeNiceMax(values: number[]): number {
  let max = 0;
  for (const value of values) {
    if (value > max) max = value;
  }
  const next = niceCeil(max);
  return next > 0 ? next : 1;
}

function yTicks(max: number, count = 5): number[] {
  const safeCount = Math.max(2, count);
  const step = max / (safeCount - 1);
  return Array.from({ length: safeCount }, (_, index) => max - step * index);
}

function xAt(index: number, count: number, left: number, width: number): number {
  if (count <= 1) return left + width / 2;
  return left + (index / (count - 1)) * width;
}

function yAt(value: number, max: number, top: number, height: number): number {
  const safeMax = max > 0 ? max : 1;
  const clamped = Math.max(0, Math.min(value, safeMax));
  return top + height - (clamped / safeMax) * height;
}

function buildLinePath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
}

function buildAreaPath(points: { x: number; y: number }[], baseY: number): string {
  if (points.length === 0) return "";
  const line = buildLinePath(points);
  const last = points[points.length - 1];
  const first = points[0];
  return `${line} L ${last.x.toFixed(2)} ${baseY.toFixed(2)} L ${first.x.toFixed(2)} ${baseY.toFixed(2)} Z`;
}

function clampPercent(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function formatRowLabel(values: { name: string; value: number; color: string }[], yFormat: (n: number) => string): string {
  return values.map((entry) => `${entry.name}: ${yFormat(entry.value)}`).join(" • ");
}

function EmptyState({ height, title }: { height: number; title: string }) {
  return (
    <div className="rounded-md border border-edge bg-background/60 p-3">
      <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
        <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Line chart</span>
        <span className="font-mono text-[10px] text-faint">0 rows</span>
      </div>
      <div
        className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 text-[12px] text-faint"
        style={{ minHeight: height }}
      >
        {title}
      </div>
    </div>
  );
}

export function LineChart({
  categories,
  series,
  height = 240,
  yFormat = DEFAULT_FORMAT,
  markLastPartial = false,
  bare = false,
}: LineChartProps) {
  const titleId = useId();
  const gradientId = useId();
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const visibleSeries = useMemo(
    () =>
      series.slice(0, 2).map((entry, index) => ({
        name: entry.name,
        color: entry.color ?? (index === 0 ? DEFAULT_ACCENT : DEFAULT_SECONDARY),
        values: alignValues(entry.values, categories.length),
      })),
    [categories.length, series],
  );

  if (categories.length === 0 || visibleSeries.length === 0) {
    return <EmptyState height={height} title="No series data available yet." />;
  }

  const top = 20;
  const right = 18;
  const bottom = 40;
  const left = 52;
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const plotHeight = Math.max(1, height - top - bottom);
  const baseY = top + plotHeight;

  const flattenedValues = visibleSeries.flatMap((entry) => entry.values);
  const niceMax = safeNiceMax(flattenedValues);
  const ticks = yTicks(niceMax, 5);
  // Keep the time-series density (≤9 ticks) but size the font to the point spacing and
  // edge-anchor the ends so the first/last label never spills past the plot.
  const pointSpacing = categories.length <= 1 ? plotWidth : plotWidth / (categories.length - 1);
  const xLabels = xAxisLabels(categories.length, pointSpacing, { maxVisible: 9 });

  const pointsBySeries = visibleSeries.map((entry) =>
    entry.values.map((value, index) => ({
      x: xAt(index, categories.length, left, plotWidth),
      y: yAt(value, niceMax, top, plotHeight),
      value,
    })),
  );

  const hoverIndex = hoveredIndex !== null && hoveredIndex >= 0 && hoveredIndex < categories.length ? hoveredIndex : null;
  const hoverX = hoverIndex === null ? null : xAt(hoverIndex, categories.length, left, plotWidth);
  const hoveredValues =
    hoverIndex === null
      ? []
      : visibleSeries.map((entry, index) => ({
          name: entry.name,
          value: entry.values[hoverIndex] ?? 0,
          color: entry.color,
          y: pointsBySeries[index]?.[hoverIndex]?.y ?? baseY,
        }));
  const tooltipY = hoverIndex === null ? null : Math.min(...hoveredValues.map((entry) => entry.y));
  const tooltipLeft = hoverX === null ? null : clampPercent((hoverX / VIEW_WIDTH) * 100, 10, 90);
  const tooltipTop = tooltipY === null ? null : clampPercent((tooltipY / height) * 100, 20, 90);

  const hasDashedTail = markLastPartial && categories.length > 1;
  const firstAreaPath = buildAreaPath(pointsBySeries[0] ?? [], baseY);

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Line chart</span>
          <span className="font-mono text-[10px] text-faint">{categories.length.toLocaleString("en-US")} points</span>
        </div>
      )}

      {visibleSeries.length > 1 && (
        <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1">
          {visibleSeries.map((entry) => (
            <div key={entry.name} className="flex items-center gap-1.5 text-[10px] text-muted">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="font-mono tabular-nums">{entry.name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHoveredIndex(null)}>
        <svg
          viewBox={`0 0 ${VIEW_WIDTH} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          width="100%"
          height="auto"
          role="img"
          aria-labelledby={titleId}
          className="block w-full"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <title id={titleId}>{`Line chart showing ${visibleSeries.length} series across ${categories.length} categories`}</title>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={visibleSeries[0]?.color ?? DEFAULT_ACCENT} stopOpacity="0.24" />
              <stop offset="100%" stopColor={visibleSeries[0]?.color ?? DEFAULT_ACCENT} stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {ticks.map((tick) => {
            const y = yAt(tick, niceMax, top, plotHeight);
            return (
              <g key={tick}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={DEFAULT_GRID} strokeWidth="1" strokeOpacity="0.5" />
                <text x={left - 8} y={y + 4} textAnchor="end" fontSize="10" fill={DEFAULT_LABEL} className="font-mono">
                  {yFormat(tick)}
                </text>
              </g>
            );
          })}

          {firstAreaPath && <path d={firstAreaPath} fill={`url(#${gradientId})`} />}

          {pointsBySeries.map((points, seriesIndex) => {
            const color = visibleSeries[seriesIndex]?.color ?? DEFAULT_ACCENT;
            const solidPoints = hasDashedTail ? points.slice(0, -1) : points;
            const dashedPoints = hasDashedTail ? points.slice(-2) : [];
            const solidPath = buildLinePath(solidPoints.length > 0 ? solidPoints : points);
            const dashedPath = hasDashedTail ? buildLinePath(dashedPoints) : "";

            return (
              <g key={visibleSeries[seriesIndex]?.name ?? seriesIndex}>
                {solidPath && <path d={solidPath} fill="none" stroke={color} strokeWidth="1.75" vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />}
                {dashedPath && (
                  <path
                    d={dashedPath}
                    fill="none"
                    stroke={color}
                    strokeWidth="1.75"
                    vectorEffect="non-scaling-stroke"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    strokeDasharray="5 5"
                  />
                )}
              </g>
            );
          })}

          {categories.map((category, index) => {
            const x = xAt(index, categories.length, left, plotWidth);
            const bandWidth = categories.length <= 1 ? plotWidth : plotWidth / Math.max(1, categories.length - 1);
            const hoverLeft = Math.max(left, x - bandWidth / 2);
            const maxRight = VIEW_WIDTH - right;
            const width = Math.min(bandWidth, maxRight - hoverLeft);
            return (
              <rect
                key={`${category}-${index}`}
                x={hoverLeft}
                y={top}
                width={Math.max(10, width)}
                height={plotHeight}
                fill="transparent"
                onMouseEnter={() => setHoveredIndex(index)}
              />
            );
          })}

          {hoverIndex !== null && hoverX !== null && (
            <line x1={hoverX} x2={hoverX} y1={top} y2={baseY} stroke={DEFAULT_LABEL} strokeOpacity="0.35" strokeDasharray="3 4" />
          )}

          {hoverIndex !== null &&
            pointsBySeries.map((points, seriesIndex) => {
              const point = points[hoverIndex];
              if (!point) return null;
              const color = visibleSeries[seriesIndex]?.color ?? DEFAULT_ACCENT;
              return (
                <g key={`hover-dot-${seriesIndex}`}>
                  <circle cx={point.x} cy={point.y} r="5.5" fill={color} fillOpacity="0.15" />
                  <circle cx={point.x} cy={point.y} r="3.2" fill={color} stroke="#111115" strokeWidth="1.2" />
                </g>
              );
            })}

          {hasDashedTail && !bare && (() => {
            const points = pointsBySeries[0] ?? [];
            const lastPoint = points[points.length - 1];
            if (!lastPoint) return null;
            return (
              <g>
                <text x={lastPoint.x + 8} y={Math.max(12, lastPoint.y - 10)} fontSize="10" fill={DEFAULT_LABEL} className="font-mono uppercase tracking-wider">
                  partial
                </text>
              </g>
            );
          })()}

          <line x1={left} x2={VIEW_WIDTH - right} y1={baseY} y2={baseY} stroke={DEFAULT_GRID} strokeWidth="1" />

          {categories.map((category, index) => {
            if (!showLabelAt(index, categories.length, xLabels.step)) return null;
            const x = xAt(index, categories.length, left, plotWidth);
            // Points sit on the plot edges, so a middle-anchored end label spills out — anchor the ends inward.
            const anchor = index === 0 ? "start" : index === categories.length - 1 ? "end" : "middle";
            return (
              <text key={`${category}-${index}-label`} x={x} y={height - 14} textAnchor={anchor} fontSize={xLabels.fontSize} fill={DEFAULT_LABEL}>
                {xLabels.fit(category)}
              </text>
            );
          })}
        </svg>

        {hoverIndex !== null && tooltipLeft !== null && tooltipTop !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-36 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
            style={{ left: `${tooltipLeft}%`, top: `${tooltipTop}%` }}
          >
            <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{categories[hoverIndex]}</div>
            <div className="space-y-1">
              {hoveredValues.map((entry) => (
                <div key={entry.name} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 text-muted">
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span>{entry.name}</span>
                  </span>
                  <span className="font-mono tabular-nums text-foreground">{yFormat(entry.value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {!bare && (
        <div className="mt-2 text-[10px] text-faint">{formatRowLabel(hoveredValues, yFormat) || "Hover a point to inspect the exact value."}</div>
      )}
    </div>
  );
}
