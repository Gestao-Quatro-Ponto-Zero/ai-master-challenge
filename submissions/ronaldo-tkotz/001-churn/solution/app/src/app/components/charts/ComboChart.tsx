"use client";

import { useId, useMemo, useState } from "react";
import { axisTicks, showLabelAt } from "./axis";

export interface ComboSeries {
  name: string;
  values: number[];
  color?: string;
}

export interface ComboChartProps {
  categories: string[];
  /** y[0] — drawn as bars on the left axis. */
  bar: ComboSeries;
  /** y[1] — drawn as a line on the right axis. Omit/empty to draw bars only. */
  line?: ComboSeries;
  height?: number;
  barFormat?: (n: number) => string;
  lineFormat?: (n: number) => string;
  bare?: boolean;
  /** When set, a category is clickable — fires with the category label to drill in. */
  onSelect?: (label: string) => void;
}

const VIEW_WIDTH = 640;
const BAR_COLOR = "#e3b341";
const LINE_COLOR = "#8a90ad";
const GRID = "#23232b";
const LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
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

function clampPercent(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function ComboChart({ categories, bar, line, height = 250, barFormat = DEFAULT_FORMAT, lineFormat = DEFAULT_FORMAT, bare = false, onSelect }: ComboChartProps) {
  const titleId = useId();
  const [hovered, setHovered] = useState<number | null>(null);
  const clickable = typeof onSelect === "function";

  const barColor = bar.color ?? BAR_COLOR;
  const lineColor = line?.color ?? LINE_COLOR;
  const barVals = useMemo(() => categories.map((_, i) => safeNumber(bar.values[i])), [categories, bar.values]);
  const lineVals = useMemo(() => (line ? categories.map((_, i) => safeNumber(line.values[i])) : []), [categories, line]);
  const hasLine = lineVals.length > 0;

  if (categories.length === 0) {
    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        <div className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 text-[12px] text-faint" style={{ minHeight: height }}>
          No data available yet.
        </div>
      </div>
    );
  }

  const top = 16;
  const left = 52;
  const right = hasLine ? 52 : 18;
  const bottom = 36;
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const plotHeight = Math.max(1, height - top - bottom);
  const bandWidth = plotWidth / categories.length;
  const barWidth = Math.min(bandWidth * 0.56, 40);
  const ticks = axisTicks(categories, bandWidth);
  const labelPad = ticks.rotate ? ticks.bottomPad : 0;
  const svgHeight = height + labelPad;
  const leftPad = ticks.rotate ? Math.max(0, Math.ceil(ticks.labelSpanX - (left + bandWidth / 2) + 4)) : 0;

  const barMax = niceCeil(Math.max(...barVals, 1));
  const lineMax = niceCeil(Math.max(...(hasLine ? lineVals : [1]), 1));
  const barY = (v: number) => top + plotHeight - (Math.max(0, v) / barMax) * plotHeight;
  const lineY = (v: number) => top + plotHeight - (Math.max(0, v) / lineMax) * plotHeight;
  const cx = (i: number) => left + bandWidth * i + bandWidth / 2;

  const linePath = hasLine ? lineVals.map((v, i) => `${i === 0 ? "M" : "L"} ${cx(i).toFixed(2)} ${lineY(v).toFixed(2)}`).join(" ") : "";
  const hoverX = hovered === null ? null : cx(hovered);
  const tooltipLeft = hoverX === null ? null : clampPercent((hoverX / VIEW_WIDTH) * 100, 12, 88);

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Combo chart</span>
          <span className="font-mono text-[10px] text-faint">{categories.length.toLocaleString("en-US")} categories</span>
        </div>
      )}

      <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1">
        <div className="flex items-center gap-1.5 text-[10px] text-muted">
          <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: barColor }} />
          <span className="font-mono tabular-nums">{bar.name}</span>
        </div>
        {hasLine && line && (
          <div className="flex items-center gap-1.5 text-[10px] text-muted">
            <span className="h-2 w-3.5 rounded-full" style={{ backgroundColor: lineColor }} />
            <span className="font-mono tabular-nums">{line.name}</span>
          </div>
        )}
      </div>

      <div className="relative veta-rise" onMouseLeave={() => setHovered(null)}>
        <svg viewBox={`${-leftPad} 0 ${VIEW_WIDTH + leftPad} ${svgHeight}`} preserveAspectRatio="xMidYMid meet" width="100%" height="auto" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`Combo chart: ${bar.name} as bars${hasLine && line ? ` with ${line.name} as a line` : ""}`}</title>

          {[0, 0.5, 1].map((t) => {
            const y = top + plotHeight - t * plotHeight;
            return (
              <g key={t}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={GRID} strokeWidth="1" />
                <text x={left - 6} y={y + 4} textAnchor="end" fontSize="10" fill={barColor} className="font-mono">
                  {barFormat(barMax * t)}
                </text>
                {hasLine && (
                  <text x={VIEW_WIDTH - right + 6} y={y + 4} textAnchor="start" fontSize="10" fill={lineColor} className="font-mono">
                    {lineFormat(lineMax * t)}
                  </text>
                )}
              </g>
            );
          })}

          {categories.map((cat, i) => {
            const h = (Math.max(0, barVals[i]) / barMax) * plotHeight;
            const highlighted = hovered === i;
            return (
              <g key={`${cat}-${i}`}>
                <rect x={cx(i) - barWidth / 2} y={barY(barVals[i])} width={barWidth} height={Math.max(0, h)} rx={3} fill={barColor} fillOpacity={hovered === null || highlighted ? 0.9 : 0.45} />
                <rect
                  x={left + bandWidth * i}
                  y={top}
                  width={bandWidth}
                  height={plotHeight}
                  fill="transparent"
                  className={clickable ? "cursor-pointer" : undefined}
                  onMouseEnter={() => setHovered(i)}
                  onClick={clickable ? () => onSelect!(cat) : undefined}
                />
                {showLabelAt(i, categories.length, ticks.step) && (() => {
                  const ly = top + plotHeight + (ticks.rotate ? 12 : 14);
                  return (
                    <text
                      x={cx(i)}
                      y={ly}
                      textAnchor={ticks.rotate ? "end" : "middle"}
                      fontSize={ticks.fontSize}
                      fill={LABEL}
                      transform={ticks.rotate ? `rotate(${ticks.angle} ${cx(i)} ${ly})` : undefined}
                    >
                      {cat}
                    </text>
                  );
                })()}
              </g>
            );
          })}

          {hasLine && linePath && <path d={linePath} fill="none" stroke={lineColor} strokeWidth="1.75" vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />}
          {hasLine && lineVals.map((v, i) => <circle key={i} cx={cx(i)} cy={lineY(v)} r={hovered === i ? 4 : 2.8} fill={lineColor} stroke="#0E0E10" strokeWidth="1" />)}

          <line x1={left} x2={VIEW_WIDTH - right} y1={top + plotHeight} y2={top + plotHeight} stroke={GRID} strokeWidth="1" />
        </svg>

        {hovered !== null && tooltipLeft !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-32 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
            style={{ left: `${tooltipLeft}%`, top: "12%" }}
          >
            <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{categories[hovered]}</div>
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-muted">
                <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: barColor }} />
                <span>{bar.name}</span>
              </span>
              <span className="font-mono tabular-nums text-foreground">{barFormat(barVals[hovered])}</span>
            </div>
            {hasLine && line && (
              <div className="mt-0.5 flex items-center justify-between gap-3">
                <span className="flex items-center gap-1.5 text-muted">
                  <span className="h-2 w-3.5 rounded-full" style={{ backgroundColor: lineColor }} />
                  <span>{line.name}</span>
                </span>
                <span className="font-mono tabular-nums text-foreground">{lineFormat(lineVals[hovered])}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
