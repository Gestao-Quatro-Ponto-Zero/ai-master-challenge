"use client";

import { useId, useMemo, useState } from "react";
import { showLabelAt, xAxisLabels } from "./axis";

export interface LineSeries {
  name: string;
  /** null = no value (a gap, e.g. projected months with no actual data). */
  values: (number | null)[];
  color?: string;
}

type Point = { x: number; y: number; value: number | null };
const comValor = (points: Point[]) => points.filter((p) => p.value !== null);

export interface LineChartProps {
  categories: string[];
  series: LineSeries[];
  height?: number;
  yFormat?: (n: number) => string;
  markLastPartial?: boolean;
  /** Hero mode: drop the bordered frame + "Line chart / N points" header chrome. */
  bare?: boolean;
  /** Fixed top of a 0-based axis, for bounded scales (a 1–5 score reads 0–5). */
  yMax?: number;
  /** viewBox width: pass the container's pixel width so text draws at 1:1. */
  viewWidth?: number;
  /** Shade under the first series (default on). Always off when a series goes below zero. */
  area?: boolean;
  /** One trend line per series (same index), drawn dashed in the series colour. */
  trends?: (number | null)[][];
  /** Legend text for the dashed trend lines. */
  trendLabel?: string;
  /** Index of the first projected category: from there on the plot is shaded and labelled. */
  projectFrom?: number;
  /** A vertical marker at one category, with a short label (e.g. where two trends meet). */
  marker?: { index: number; label: string };
}

const DEFAULT_VIEW_WIDTH = 640;
const DEFAULT_ACCENT = "#e3b341";
const DEFAULT_SECONDARY = "#8a90ad";
const DEFAULT_GRID = "#23232b";
const DEFAULT_LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

/** Pads to the category count; an explicit null stays null (a gap), anything else non-finite is 0. */
function alignValues(values: (number | null)[], length: number): (number | null)[] {
  return Array.from({ length }, (_, index) => (values[index] === null ? null : safeNumber(values[index] as number | undefined)));
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

/**
 * A 0-based axis that hugs the data (D42): the smallest round step (1, 2, 2.5, 3 or 5 × 10ⁿ) that
 * covers the maximum in at most four intervals. 11.2 → 0–12 in steps of 3, not 0–20; a 0.85 mi
 * maximum still reads 0–1 mi in steps of 250 mil.
 */
/** A 0-based axis with a fixed top: whole steps up to 6, else four intervals. */
function fixedScale(max: number): { max: number; ticks: number[] } {
  const n = Number.isInteger(max) && max <= 6 ? max : 4;
  return { max, ticks: Array.from({ length: n + 1 }, (_, i) => Math.round(((n - i) * max * 1e6) / n) / 1e6) };
}

function tightScale(values: number[]): { max: number; ticks: number[] } {
  const hi = Math.max(0, ...values);
  if (!(hi > 0)) return { max: 1, ticks: [1, 0.75, 0.5, 0.25, 0] };
  const mag = 10 ** Math.floor(Math.log10(hi / 4));
  for (const m of [1, 2, 2.5, 3, 5, 10, 20]) {
    const step = m * mag;
    const n = Math.ceil(hi / step - 1e-9);
    if (n <= 4) {
      const ticks = Array.from({ length: n + 1 }, (_, i) => Math.round((n - i) * step * 1e6) / 1e6);
      return { max: n * step, ticks };
    }
  }
  return { max: safeNiceMax(values), ticks: [safeNiceMax(values), 0] };
}

function xAt(index: number, count: number, left: number, width: number): number {
  if (count <= 1) return left + width / 2;
  return left + (index / (count - 1)) * width;
}

function yAt(value: number, max: number, top: number, height: number, min = 0): number {
  const span = max - min > 0 ? max - min : 1;
  const clamped = Math.max(min, Math.min(value, max));
  return top + height - ((clamped - min) / span) * height;
}

/** Axis range for series that go below zero: one nice step, max and min snapped to it. */
function signedScale(values: number[]): { max: number; min: number; ticks: number[] } {
  const hi = Math.max(0, ...values);
  const lo = Math.min(0, ...values);
  const step = niceCeil((hi - lo) / 4);
  const max = Math.ceil(hi / step) * step;
  const min = Math.floor(lo / step) * step;
  const ticks: number[] = [];
  for (let t = max; t >= min - step / 2; t -= step) ticks.push(Math.round(t * 1e6) / 1e6);
  return { max, min, ticks };
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

function formatRowLabel(values: { name: string; value: number | null; color: string }[], yFormat: (n: number) => string): string {
  return values.map((entry) => `${entry.name}: ${entry.value === null ? "—" : yFormat(entry.value)}`).join(" • ");
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
  yMax,
  area = true,
  trends = [],
  trendLabel = "tendência",
  projectFrom,
  marker,
  viewWidth,
}: LineChartProps) {
  const VIEW_WIDTH = viewWidth ?? DEFAULT_VIEW_WIDTH;
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

  // Bare charts sit inside a panel that already has a title: trim the outer margins (D41).
  const top = bare ? 12 : 20;
  const right = 18;
  const bottom = bare ? 24 : 40;
  const plotHeight = Math.max(1, height - top - bottom);
  const baseY = top + plotHeight;

  const trendValues = trends.slice(0, visibleSeries.length).map((t) => alignValues(t, categories.length));
  const flattenedValues = [...visibleSeries.flatMap((entry) => entry.values), ...trendValues.flat()].filter(
    (v): v is number => v !== null,
  );
  const negativo = flattenedValues.some((v) => v < 0);
  const signed = negativo ? signedScale(flattenedValues) : null;
  const positive = signed ? null : yMax ? fixedScale(yMax) : tightScale(flattenedValues);
  const niceMax = signed ? signed.max : positive!.max;
  const niceMin = signed ? signed.min : 0;
  const ticks = signed ? signed.ticks : positive!.ticks;
  // The y gutter fits the longest tick label (10px mono ≈ 6.2 units a character), never under 52.
  const left = Math.max(52, Math.ceil(Math.max(...ticks.map((t) => yFormat(t).length)) * 6.2) + 12);
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const zeroY = yAt(0, niceMax, top, plotHeight, niceMin);
  // Keep the time-series density (≤9 ticks) but size the font to the point spacing and
  // edge-anchor the ends so the first/last label never spills past the plot.
  const pointSpacing = categories.length <= 1 ? plotWidth : plotWidth / (categories.length - 1);
  // At most one label per ~70px of plot, so narrow charts never collide (edge labels are anchored inward).
  const xLabels = xAxisLabels(categories.length, pointSpacing, { maxVisible: Math.max(2, Math.min(9, Math.floor(plotWidth / 70))) });

  const toPoints = (values: (number | null)[]): Point[] =>
    values.map((value, index) => ({
      x: xAt(index, categories.length, left, plotWidth),
      y: yAt(value ?? 0, niceMax, top, plotHeight, niceMin),
      value,
    }));
  const pointsBySeries = visibleSeries.map((entry) => toPoints(entry.values));
  const trendPoints = trendValues.map((values) => comValor(toPoints(values)));

  const hoverIndex = hoveredIndex !== null && hoveredIndex >= 0 && hoveredIndex < categories.length ? hoveredIndex : null;
  const hoverX = hoverIndex === null ? null : xAt(hoverIndex, categories.length, left, plotWidth);
  const hoveredValues =
    hoverIndex === null
      ? []
      : visibleSeries.map((entry, index) => ({
          name: entry.name,
          value: entry.values[hoverIndex] ?? null,
          color: entry.color,
          y: pointsBySeries[index]?.[hoverIndex]?.y ?? baseY,
        }));
  // Projected months have no actual value: the tooltip shows the trends there instead.
  const hoveredTrends =
    hoverIndex === null || trendValues.length === 0
      ? []
      : visibleSeries.map((entry, index) => ({ name: entry.name, value: trendValues[index]?.[hoverIndex] ?? null, color: entry.color }));
  const showTrendsInTooltip = hoveredValues.every((entry) => entry.value === null) && hoveredTrends.some((t) => t.value !== null);
  const comY = hoveredValues.filter((entry) => entry.value !== null);
  const tooltipY = hoverIndex === null ? null : comY.length ? Math.min(...comY.map((entry) => entry.y)) : top + plotHeight / 2;
  const tooltipLeft = hoverX === null ? null : clampPercent((hoverX / VIEW_WIDTH) * 100, 10, 90);
  const tooltipTop = tooltipY === null ? null : clampPercent((tooltipY / height) * 100, 20, 90);

  const hasDashedTail = markLastPartial && categories.length > 1;
  const firstAreaPath = area && !negativo ? buildAreaPath(comValor(pointsBySeries[0] ?? []), baseY) : "";
  const projX = projectFrom !== undefined && projectFrom > 0 && projectFrom < categories.length ? xAt(projectFrom - 1, categories.length, left, plotWidth) : null;
  const markerX = marker && marker.index >= 0 && marker.index < categories.length ? xAt(marker.index, categories.length, left, plotWidth) : null;

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
          {trendPoints.length > 0 && (
            <div className="flex items-center gap-1.5 text-[10px] text-muted">
              <svg width="16" height="4" aria-hidden="true">
                <line x1="0" x2="16" y1="2" y2="2" stroke={DEFAULT_LABEL} strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
              <span className="font-mono">{trendLabel}</span>
            </div>
          )}
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHoveredIndex(null)}>
        <svg
          viewBox={`0 0 ${VIEW_WIDTH} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          width="100%"
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
            const y = yAt(tick, niceMax, top, plotHeight, niceMin);
            return (
              <g key={tick}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={DEFAULT_GRID} strokeWidth="1" strokeOpacity="0.5" />
                <text x={left - 8} y={y + 4} textAnchor="end" fontSize="10" fill={DEFAULT_LABEL} className="font-mono">
                  {yFormat(tick)}
                </text>
              </g>
            );
          })}

          {projX !== null && (
            <g>
              <rect x={projX} y={top} width={VIEW_WIDTH - right - projX} height={plotHeight} fill="#ffffff" fillOpacity="0.035" />
              <text x={projX + 6} y={top + 11} fontSize="10" fill={DEFAULT_LABEL}>
                projeção
              </text>
            </g>
          )}

          {firstAreaPath && <path d={firstAreaPath} fill={`url(#${gradientId})`} />}

          {pointsBySeries.map((points, seriesIndex) => {
            const color = visibleSeries[seriesIndex]?.color ?? DEFAULT_ACCENT;
            const reais = comValor(points);
            const solidPoints = hasDashedTail ? reais.slice(0, -1) : reais;
            const dashedPoints = hasDashedTail ? reais.slice(-2) : [];
            const solidPath = buildLinePath(solidPoints.length > 0 ? solidPoints : reais);
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

          {trendPoints.map((points, seriesIndex) =>
            points.length > 1 ? (
              <path
                key={`trend-${seriesIndex}`}
                d={buildLinePath(points)}
                fill="none"
                stroke={visibleSeries[seriesIndex]?.color ?? DEFAULT_ACCENT}
                strokeWidth="1.5"
                strokeOpacity="0.9"
                vectorEffect="non-scaling-stroke"
                strokeDasharray="4 4"
              />
            ) : null,
          )}

          {markerX !== null && marker && (
            <g>
              <line x1={markerX} x2={markerX} y1={top} y2={baseY} stroke="#e6e6ea" strokeOpacity="0.7" strokeWidth="1" />
              <text
                x={markerX > VIEW_WIDTH - right - 120 ? markerX - 6 : markerX + 6}
                y={top + 26}
                textAnchor={markerX > VIEW_WIDTH - right - 120 ? "end" : "start"}
                fontSize="11"
                fontWeight="600"
                fill="#e6e6ea"
              >
                {marker.label}
              </text>
            </g>
          )}

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
              if (!point || point.value === null) return null;
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
          {negativo && <line x1={left} x2={VIEW_WIDTH - right} y1={zeroY} y2={zeroY} stroke={DEFAULT_LABEL} strokeOpacity="0.45" strokeWidth="1" />}

          {categories.map((category, index) => {
            if (!showLabelAt(index, categories.length, xLabels.step)) return null;
            const x = xAt(index, categories.length, left, plotWidth);
            // Points sit on the plot edges, so a middle-anchored end label spills out — anchor the ends inward.
            const anchor = index === 0 ? "start" : index === categories.length - 1 ? "end" : "middle";
            return (
              <text key={`${category}-${index}-label`} x={x} y={height - (bare ? 6 : 14)} textAnchor={anchor} fontSize={xLabels.fontSize} fill={DEFAULT_LABEL}>
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
              {(showTrendsInTooltip ? hoveredTrends : hoveredValues).map((entry) => (
                <div key={entry.name} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 text-muted">
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span>{entry.name}</span>
                  </span>
                  <span className="font-mono tabular-nums text-foreground">{entry.value === null ? "—" : yFormat(entry.value)}</span>
                </div>
              ))}
              {showTrendsInTooltip && <div className="text-[10px] text-faint">{trendLabel}, projetada</div>}
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
