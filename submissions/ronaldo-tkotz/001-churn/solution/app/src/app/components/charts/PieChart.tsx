"use client";

import { useId, useMemo, useState } from "react";

export interface PieSlice {
  label: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  slices: PieSlice[];
  height?: number;
  valueFormat?: (n: number) => string;
  /** Render with a centre hole (donut) instead of a full pie. */
  donut?: boolean;
  bare?: boolean;
  /** When set, a slice is clickable — fires with the slice label to drill in. */
  onSelect?: (label: string) => void;
}

const VIEW_WIDTH = 640;
const SLICE_COLORS = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb", "#d98b6b", "#7f9cd1", "#b7c46a", "#cf7f9c"];
const LABEL = "#9a9aa6";
const DEFAULT_FORMAT = (n: number) => n.toLocaleString("en-US");

function safeNumber(value: number | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

/** A point on a circle of radius r centred at (cx,cy), angle in degrees from 12 o'clock. */
function polar(cx: number, cy: number, r: number, deg: number): { x: number; y: number } {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

/** Annular (or wedge, when innerR=0) sector path from a0 to a1 degrees. */
function sectorPath(cx: number, cy: number, outerR: number, innerR: number, a0: number, a1: number): string {
  const large = a1 - a0 > 180 ? 1 : 0;
  const o0 = polar(cx, cy, outerR, a0);
  const o1 = polar(cx, cy, outerR, a1);
  if (innerR <= 0) {
    return `M ${cx} ${cy} L ${o0.x.toFixed(2)} ${o0.y.toFixed(2)} A ${outerR} ${outerR} 0 ${large} 1 ${o1.x.toFixed(2)} ${o1.y.toFixed(2)} Z`;
  }
  const i1 = polar(cx, cy, innerR, a1);
  const i0 = polar(cx, cy, innerR, a0);
  return `M ${o0.x.toFixed(2)} ${o0.y.toFixed(2)} A ${outerR} ${outerR} 0 ${large} 1 ${o1.x.toFixed(2)} ${o1.y.toFixed(2)} L ${i1.x.toFixed(2)} ${i1.y.toFixed(2)} A ${innerR} ${innerR} 0 ${large} 0 ${i0.x.toFixed(2)} ${i0.y.toFixed(2)} Z`;
}

export function PieChart({ slices, height = 240, valueFormat = DEFAULT_FORMAT, donut = false, bare = false, onSelect }: PieChartProps) {
  const titleId = useId();
  const [hovered, setHovered] = useState<number | null>(null);
  const clickable = typeof onSelect === "function";

  const data = useMemo(
    () =>
      slices
        .map((s, i) => ({ label: s.label, value: Math.max(0, safeNumber(s.value)), color: s.color ?? SLICE_COLORS[i % SLICE_COLORS.length] }))
        .filter((s) => s.value > 0),
    [slices],
  );

  const total = data.reduce((sum, s) => sum + s.value, 0);

  if (data.length === 0 || total <= 0) {
    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        <div className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 text-[12px] text-faint" style={{ minHeight: height }}>
          No data to plot.
        </div>
      </div>
    );
  }

  const cx = 160;
  const cy = height / 2;
  const outerR = Math.min(height / 2 - 12, 116);
  const innerR = donut ? outerR * 0.58 : 0;

  // Build cumulative angles (immutable reduce — each arc starts where the last ended).
  const arcs = data.reduce<{ label: string; value: number; color: string; a0: number; a1: number; pct: number }[]>((acc, s) => {
    const a0 = acc.length > 0 ? acc[acc.length - 1].a1 : 0;
    acc.push({ ...s, a0, a1: a0 + (s.value / total) * 360, pct: (s.value / total) * 100 });
    return acc;
  }, []);

  const single = arcs.length === 1; // a single 100% slice — draw a full ring/disc, not a 360° arc.
  const legendX = 330;
  const legendStep = Math.min(26, (height - 24) / Math.max(1, arcs.length));
  const legendTop = cy - (legendStep * (arcs.length - 1)) / 2;
  const hov = hovered !== null ? arcs[hovered] : null;

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">{donut ? "Donut chart" : "Pie chart"}</span>
          <span className="font-mono text-[10px] text-faint">{arcs.length.toLocaleString("en-US")} slices</span>
        </div>
      )}

      <div className="relative veta-rise" onMouseLeave={() => setHovered(null)}>
        <svg viewBox={`0 0 ${VIEW_WIDTH} ${height}`} preserveAspectRatio="xMidYMid meet" width="100%" height="auto" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`${donut ? "Donut" : "Pie"} chart with ${arcs.length} slices`}</title>

          {single ? (
            donut ? (
              <circle
                cx={cx}
                cy={cy}
                r={(outerR + innerR) / 2}
                fill="none"
                stroke={arcs[0].color}
                strokeWidth={outerR - innerR}
                className={clickable ? "cursor-pointer" : undefined}
                onClick={clickable ? () => onSelect!(arcs[0].label) : undefined}
              />
            ) : (
              <circle
                cx={cx}
                cy={cy}
                r={outerR}
                fill={arcs[0].color}
                className={clickable ? "cursor-pointer" : undefined}
                onClick={clickable ? () => onSelect!(arcs[0].label) : undefined}
              />
            )
          ) : (
            arcs.map((a, i) => (
              <path
                key={a.label + i}
                d={sectorPath(cx, cy, outerR, innerR, a.a0, a.a1)}
                fill={a.color}
                fillOpacity={hovered === null || hovered === i ? 0.95 : 0.4}
                stroke="#0E0E10"
                strokeWidth="1.5"
                className={clickable ? "cursor-pointer" : undefined}
                onMouseEnter={() => setHovered(i)}
                onClick={clickable ? () => onSelect!(a.label) : undefined}
              />
            ))
          )}

          {/* Donut centre: total, or the hovered slice's share. */}
          {donut && (
            <g>
              <text x={cx} y={cy - 2} textAnchor="middle" fontSize="20" fontWeight="700" fill="#f5f5f7" className="font-mono">
                {hov ? `${Math.round(hov.pct)}%` : valueFormat(total)}
              </text>
              <text x={cx} y={cy + 16} textAnchor="middle" fontSize="10" fill={LABEL}>
                {hov ? hov.label.slice(0, 18) : "total"}
              </text>
            </g>
          )}

          {/* Legend — label, value, share. */}
          {arcs.map((a, i) => {
            const y = legendTop + legendStep * i;
            const strong = hovered === i;
            return (
              <g
                key={`legend-${a.label}-${i}`}
                onMouseEnter={() => setHovered(i)}
                onClick={clickable ? () => onSelect!(a.label) : undefined}
                style={{ cursor: clickable ? "pointer" : "default" }}
              >
                <rect x={legendX} y={y - 8} width={11} height={11} rx={2} fill={a.color} fillOpacity={hovered === null || strong ? 1 : 0.5} />
                <text x={legendX + 18} y={y + 1} fontSize="11.5" fill={strong ? "#f5f5f7" : "#c7c7cf"}>
                  {a.label.length > 22 ? `${a.label.slice(0, 21)}…` : a.label}
                </text>
                <text x={VIEW_WIDTH - 16} y={y + 1} textAnchor="end" fontSize="11" fill={LABEL} className="font-mono tabular-nums">
                  {valueFormat(a.value)} · {Math.round(a.pct)}%
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
