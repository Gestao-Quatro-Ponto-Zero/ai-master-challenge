"use client";

import { useId, useMemo, useState } from "react";
import { axisTicks, niceDomain, showLabelAt } from "./axis";

export interface BarDatum {
  label: string;
  value: number;
  color?: string;
}

export interface BarChartProps {
  data: BarDatum[];
  height?: number;
  valueFormat?: (n: number) => string;
  horizontal?: boolean;
  /** Drop the bordered frame + "Bar chart / N bars" header chrome (e.g. inside a deck panel). */
  bare?: boolean;
  /** When set, a bar is clickable — fires with the bar's full (untruncated) label to drill in. */
  onSelect?: (label: string) => void;
}

const VIEW_WIDTH = 640;
const CHAR_W = 0.58;
const DEFAULT_ACCENT = "#e3b341";
const NEG_COLOR = "#d9737a"; // negative bars render as a muted rose so decline reads at a glance
const DEFAULT_GRID = "#23232b";
const ZERO_GRID = "#33333d";
const DEFAULT_LABEL = "#9a9aa6";
const DEFAULT_TRACK = "#15151b";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");
const LABEL_BUDGET = 200; // max viewBox units reserved for horizontal-bar category labels

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function clampPercent(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/** Split a label into at most two lines (no ellipsis) — prefers a word break near the middle. */
function wrapTwo(label: string, maxChars: number): string[] {
  if (label.length <= maxChars) return [label];
  const slice = label.slice(0, maxChars);
  const sp = slice.lastIndexOf(" ");
  const cut = sp > maxChars * 0.4 ? sp : maxChars;
  return [label.slice(0, cut).trim(), label.slice(cut).trim()];
}

function EmptyState({ height, title }: { height: number; title: string }) {
  return (
    <div className="rounded-md border border-edge bg-background/60 p-3">
      <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
        <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Bar chart</span>
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

export function BarChart({ data, height = 220, valueFormat = DEFAULT_FORMAT, horizontal = true, bare = false, onSelect }: BarChartProps) {
  const titleId = useId();
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const clickable = typeof onSelect === "function";

  const items = useMemo(
    () =>
      data.map((entry) => ({
        label: entry.label,
        value: safeNumber(entry.value),
        color: entry.color ?? DEFAULT_ACCENT,
      })),
    [data],
  );

  if (items.length === 0) {
    return <EmptyState height={height} title="No bar data available yet." />;
  }

  const values = items.map((entry) => entry.value);
  const { lo, hi, span } = niceDomain(values);
  const hoverIndex = hoveredIndex !== null && hoveredIndex >= 0 && hoveredIndex < items.length ? hoveredIndex : null;

  if (horizontal) {
    const top = 18;
    const right = 66;
    const bottom = 22;

    // Fit the category labels into the left gutter WITHOUT truncating: size the font to
    // the longest name, widen the gutter to fit, and only wrap to two lines when even the
    // smallest readable font won't fit one line (Ronaldo's rule: never end a label in "…").
    const longest = items.reduce((m, it) => Math.max(m, it.label.length), 0);
    const labelFont = Math.max(7, Math.min(10, LABEL_BUDGET / (Math.max(8, longest) * CHAR_W)));
    const fitsOneLine = longest * labelFont * CHAR_W <= LABEL_BUDGET;
    const left = fitsOneLine ? Math.min(212, Math.max(120, longest * labelFont * CHAR_W + 16)) : 214;
    const maxCharsPerLine = Math.max(6, Math.floor(LABEL_BUDGET / (labelFont * CHAR_W)));

    const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
    const plotHeight = Math.max(1, height - top - bottom);
    const bandHeight = plotHeight / Math.max(1, items.length);
    const barHeight = Math.min(24, Math.max(8, bandHeight * 0.6));
    const xOf = (v: number) => left + ((v - lo) / span) * plotWidth;
    const xZero = xOf(0);

    const hovered = hoverIndex === null ? null : items[hoverIndex];
    const hoverRow = hoverIndex === null ? null : hoverIndex;
    const hoverBarEnd = hovered ? xOf(hovered.value) : 0;
    const tooltipLeft = hovered ? clampPercent(((Math.max(left + 12, hoverBarEnd) / VIEW_WIDTH) * 100), 16, 92) : null;
    const tooltipTop = hovered && hoverRow !== null ? clampPercent((((top + bandHeight * hoverRow + bandHeight / 2) / height) * 100), 14, 92) : null;

    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        {!bare && (
          <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
            <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Bar chart</span>
            <span className="font-mono text-[10px] text-faint">{items.length.toLocaleString("en-US")} bars</span>
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
            <title id={titleId}>{`Horizontal bar chart showing ${items.length} categories`}</title>

            {/* zero baseline — bars diverge from here so negatives read as their own magnitude */}
            <line x1={xZero} x2={xZero} y1={top - 2} y2={height - bottom} stroke={ZERO_GRID} strokeWidth="1" />

            {items.map((entry, index) => {
              const yCenter = top + bandHeight * index + bandHeight / 2;
              const y = yCenter - barHeight / 2;
              const xv = xOf(entry.value);
              const barX = Math.min(xZero, xv);
              const barW = Math.abs(xv - xZero);
              const highlighted = hoverIndex === index;
              const negative = entry.value < 0;
              const fill = negative ? NEG_COLOR : entry.color;
              const valueX = negative ? xv - 6 : xv + 6;
              const lines = wrapTwo(entry.label, maxCharsPerLine);

              return (
                <g key={`${entry.label}-${index}`}>
                  <text x={left - 10} y={yCenter + (lines.length > 1 ? 0 : 4)} textAnchor="end" fontSize={labelFont} fill={DEFAULT_LABEL}>
                    {lines.length === 1 ? (
                      lines[0]
                    ) : (
                      <>
                        <tspan x={left - 10} dy={-1}>{lines[0]}</tspan>
                        <tspan x={left - 10} dy={labelFont + 1}>{lines[1]}</tspan>
                      </>
                    )}
                  </text>
                  <rect x={left} y={y} width={plotWidth} height={barHeight} rx={barHeight / 2} fill={DEFAULT_TRACK} />
                  <rect
                    x={barX}
                    y={y}
                    width={Math.max(0, barW)}
                    height={barHeight}
                    rx={Math.min(barHeight / 2, barW / 2)}
                    fill={fill}
                    fillOpacity={highlighted ? 1 : 0.9}
                    stroke={highlighted ? "#f4d06a" : "none"}
                    strokeWidth={highlighted ? 1 : 0}
                    onMouseEnter={() => setHoveredIndex(index)}
                  />
                  <rect
                    x={left}
                    y={y - 4}
                    width={plotWidth}
                    height={barHeight + 8}
                    fill="transparent"
                    className={clickable ? "cursor-pointer" : undefined}
                    onMouseEnter={() => setHoveredIndex(index)}
                    onClick={clickable ? () => onSelect!(entry.label) : undefined}
                  />
                  <text
                    x={valueX}
                    y={yCenter + 4}
                    textAnchor={negative ? "end" : "start"}
                    fontSize="10"
                    fill={highlighted ? "#f5f5f7" : DEFAULT_LABEL}
                    className="font-mono"
                  >
                    {valueFormat(entry.value)}
                  </text>
                </g>
              );
            })}
          </svg>

          {hoverIndex !== null && tooltipLeft !== null && tooltipTop !== null && (
            <div
              className="pointer-events-none absolute z-10 min-w-32 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
              style={{ left: `${tooltipLeft}%`, top: `${tooltipTop}%` }}
            >
              <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{items[hoverIndex].label}</div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted">Value</span>
                <span className="font-mono tabular-nums text-foreground">{valueFormat(items[hoverIndex].value)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Vertical bars (single series) — diverging domain + diagonal labels ──
  const top = 18;
  const right = 18;
  const bottom = 42;
  const left = 40;
  const ticks = axisTicks(items.map((i) => i.label), Math.max(1, (VIEW_WIDTH - left - right) / Math.max(1, items.length)));
  const labelPad = ticks.rotate ? ticks.bottomPad : 0;
  const svgHeight = height + labelPad;
  const plotWidth = Math.max(1, VIEW_WIDTH - left - right);
  const plotHeight = Math.max(1, height - top - bottom);
  const bandSpace = plotWidth / items.length;
  const leftPad = ticks.rotate ? Math.max(0, Math.ceil(ticks.labelSpanX - (left + bandSpace / 2) + 4)) : 0;
  const barWidth = Math.min(42, Math.max(10, bandSpace * 0.62));
  const yOf = (v: number) => top + plotHeight - ((v - lo) / span) * plotHeight;
  const yZero = yOf(0);
  const gridTicks = lo < 0 ? [hi, 0, lo] : [hi, (hi + lo) / 2, lo];

  const hovered = hoverIndex === null ? null : items[hoverIndex];
  const hoverX = hovered !== null && hoverIndex !== null ? left + bandSpace * hoverIndex + bandSpace / 2 : null;
  const hoverY = hovered ? yOf(hovered.value) : null;
  const tooltipLeft = hoverX === null ? null : clampPercent((hoverX / VIEW_WIDTH) * 100, 10, 90);
  const tooltipTop = hoverY === null ? null : clampPercent((hoverY / height) * 100, 18, 92);

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Bar chart</span>
          <span className="font-mono text-[10px] text-faint">{items.length.toLocaleString("en-US")} bars</span>
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHoveredIndex(null)}>
        <svg
          viewBox={`${-leftPad} 0 ${VIEW_WIDTH + leftPad} ${svgHeight}`}
          preserveAspectRatio="xMidYMid meet"
          width="100%"
          height="auto"
          role="img"
          aria-labelledby={titleId}
          className="block w-full"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <title id={titleId}>{`Vertical bar chart showing ${items.length} categories`}</title>

          {gridTicks.map((tick, ti) => {
            const y = yOf(tick);
            const isZero = tick === 0;
            return (
              <g key={`${tick}-${ti}`}>
                <line x1={left} x2={VIEW_WIDTH - right} y1={y} y2={y} stroke={isZero ? ZERO_GRID : DEFAULT_GRID} strokeWidth="1" />
                <text x={left - 6} y={y + 4} textAnchor="end" fontSize="10" fill={DEFAULT_LABEL} className="font-mono">
                  {valueFormat(tick)}
                </text>
              </g>
            );
          })}

          {items.map((entry, index) => {
            const x = left + bandSpace * index + bandSpace / 2;
            const yv = yOf(entry.value);
            const y = Math.min(yv, yZero);
            const barH = Math.abs(yv - yZero);
            const highlighted = hoverIndex === index;
            const fill = entry.value < 0 ? NEG_COLOR : entry.color;
            return (
              <g key={`${entry.label}-${index}`}>
                <rect
                  x={x - barWidth / 2}
                  y={y}
                  width={barWidth}
                  height={Math.max(0, barH)}
                  rx={3}
                  fill={fill}
                  fillOpacity={highlighted ? 1 : 0.9}
                  stroke={highlighted ? "#f4d06a" : "none"}
                  strokeWidth={highlighted ? 1 : 0}
                  onMouseEnter={() => setHoveredIndex(index)}
                />
                <rect
                  x={x - Math.max(18, bandSpace / 2)}
                  y={top}
                  width={Math.max(36, bandSpace)}
                  height={plotHeight}
                  fill="transparent"
                  className={clickable ? "cursor-pointer" : undefined}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onClick={clickable ? () => onSelect!(entry.label) : undefined}
                />
                {showLabelAt(index, items.length, ticks.step) && (() => {
                  const ly = top + plotHeight + (ticks.rotate ? 12 : 14);
                  return (
                    <text
                      x={x}
                      y={ly}
                      textAnchor={ticks.rotate ? "end" : "middle"}
                      fontSize={ticks.fontSize}
                      fill={DEFAULT_LABEL}
                      transform={ticks.rotate ? `rotate(${ticks.angle} ${x} ${ly})` : undefined}
                    >
                      {entry.label}
                    </text>
                  );
                })()}
              </g>
            );
          })}

          <line x1={left} x2={VIEW_WIDTH - right} y1={top + plotHeight} y2={top + plotHeight} stroke={DEFAULT_GRID} strokeWidth="1" />
        </svg>

        {hoverIndex !== null && tooltipLeft !== null && tooltipTop !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-32 -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm"
            style={{ left: `${tooltipLeft}%`, top: `${tooltipTop}%` }}
          >
            <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{items[hoverIndex].label}</div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted">Value</span>
              <span className="font-mono tabular-nums text-foreground">{valueFormat(items[hoverIndex].value)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
