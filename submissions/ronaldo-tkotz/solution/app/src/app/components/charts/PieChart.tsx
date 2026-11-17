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
  /** viewBox width: pass the container's pixel width so text draws at 1:1. */
  viewWidth?: number;
  /** When set, a slice is clickable — fires with the slice label to drill in. */
  onSelect?: (label: string) => void;
}

const DEFAULT_VIEW_WIDTH = 640;
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

export function PieChart({ slices, height = 240, valueFormat = DEFAULT_FORMAT, donut = false, bare = false, onSelect, viewWidth }: PieChartProps) {
  const VIEW_WIDTH = viewWidth ?? DEFAULT_VIEW_WIDTH;
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

  // Build cumulative angles (immutable reduce — each arc starts where the last ended).
  const arcs = data.reduce<{ label: string; value: number; color: string; a0: number; a1: number; pct: number }[]>((acc, s) => {
    const a0 = acc.length > 0 ? acc[acc.length - 1].a1 : 0;
    acc.push({ ...s, a0, a1: a0 + (s.value / total) * 360, pct: (s.value / total) * 100 });
    return acc;
  }, []);

  // Layout from measured text (D39): the legend's name and figure columns are sized from their
  // longest entries, so they can never overlap. The count is dropped (share only) before the
  // donut gets too small, and the legend shrinks only as a last resort.
  const PAD = 4;
  const GAP = 16;
  const maxR = Math.max(18, Math.min(height / 2 - 8, 116));
  const nome = (l: string) => (l.length > 22 ? `${l.slice(0, 21)}…` : l);
  const figura = (a: (typeof arcs)[number], comValor: boolean) => (comValor ? `${valueFormat(a.value)} · ${Math.round(a.pct)}%` : `${Math.round(a.pct)}%`);
  const nomeW = Math.max(...arcs.map((a) => nome(a.label).length)) * 11.5 * 0.62;
  const legendaW = (comValor: boolean) => 18 + nomeW + 14 + Math.max(...arcs.map((a) => figura(a, comValor).length)) * 11 * 0.62;
  const raioCom = (comValor: boolean) => (VIEW_WIDTH - 2 * PAD - GAP - legendaW(comValor)) / 2;
  const comValor = raioCom(true) >= Math.min(maxR, 48);
  const outerR = Math.max(18, Math.min(maxR, raioCom(comValor)));
  const escala = Math.min(1, (VIEW_WIDTH - 2 * PAD - GAP - 2 * outerR) / legendaW(comValor));
  const larguraLegenda = legendaW(comValor) * escala;
  const inicio = Math.max(PAD, (VIEW_WIDTH - (2 * outerR + GAP + larguraLegenda)) / 2);
  const cx = inicio + outerR;
  const cy = height / 2;
  const innerR = donut ? outerR * 0.58 : 0;

  const single = arcs.length === 1; // a single 100% slice — draw a full ring/disc, not a 360° arc.
  const legendX = cx + outerR + GAP;
  const figuraX = legendX + larguraLegenda;
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
        <svg viewBox={`0 0 ${VIEW_WIDTH} ${height}`} preserveAspectRatio="xMidYMid meet" width="100%" role="img" aria-labelledby={titleId} className="block w-full">
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
              {(() => {
                // Fit the centre text inside the hole: mono glyphs are ~0.6 em wide.
                const centre = hov ? `${Math.round(hov.pct)}%` : valueFormat(total);
                const fit = Math.min(20, (2 * innerR * 0.82) / (Math.max(1, centre.length) * 0.6));
                return (
                  <text x={cx} y={cy - 2} textAnchor="middle" fontSize={fit} fontWeight="700" fill="#f5f5f7" className="font-mono">
                    {centre}
                  </text>
                );
              })()}
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
                <rect x={legendX} y={y - 8 * escala} width={11 * escala} height={11 * escala} rx={2} fill={a.color} fillOpacity={hovered === null || strong ? 1 : 0.5} />
                <text x={legendX + 18 * escala} y={y + 1} fontSize={11.5 * escala} fill={strong ? "#f5f5f7" : "#c7c7cf"}>
                  {nome(a.label)}
                </text>
                <text x={figuraX} y={y + 1} textAnchor="end" fontSize={11 * escala} fill={LABEL} className="font-mono tabular-nums">
                  {figura(a, comValor)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
