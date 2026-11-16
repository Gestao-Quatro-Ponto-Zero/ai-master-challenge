"use client";

import { useId, useMemo } from "react";

export interface RadarSeries {
  name: string;
  values: number[];
  color?: string;
}

export interface RadarChartProps {
  /** The axes (spokes) — one per dimension being compared. */
  axes: string[];
  series: RadarSeries[];
  height?: number;
  valueFormat?: (n: number) => string;
  bare?: boolean;
  /** When set, an axis label is clickable — fires with the axis name to drill in. */
  onSelect?: (label: string) => void;
}

const VIEW_WIDTH = 640;
const SERIES_COLORS = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb"];
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

/** Point on the radar: axis k of n at fractional radius t (0..1). */
function spoke(cx: number, cy: number, R: number, k: number, n: number, t: number): { x: number; y: number } {
  const rad = ((k / n) * 360 - 90) * (Math.PI / 180);
  return { x: cx + R * t * Math.cos(rad), y: cy + R * t * Math.sin(rad) };
}

export function RadarChart({ axes, series, height = 260, valueFormat = DEFAULT_FORMAT, bare = false, onSelect }: RadarChartProps) {
  const titleId = useId();
  const clickable = typeof onSelect === "function";

  const cleanSeries = useMemo(
    () =>
      series.slice(0, 4).map((s, i) => ({
        name: s.name,
        color: s.color ?? SERIES_COLORS[i % SERIES_COLORS.length],
        values: axes.map((_, ai) => safeNumber(s.values[ai])),
      })),
    [series, axes],
  );

  const n = axes.length;
  if (n < 3 || cleanSeries.length === 0) {
    return (
      <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
        <div className="flex items-center justify-center rounded-md border border-dashed border-edge bg-panel/60 px-3 text-center text-[12px] text-faint" style={{ minHeight: height }}>
          {n < 3 ? "A radar chart needs at least 3 axes." : "No data to plot."}
        </div>
      </div>
    );
  }

  const cx = VIEW_WIDTH / 2;
  const cy = height / 2 + 4;
  const R = Math.min(height / 2 - 30, 116);
  const max = niceCeil(Math.max(...cleanSeries.flatMap((s) => s.values), 1));
  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <div className={bare ? "" : "rounded-md border border-edge bg-background/60 p-3"}>
      {!bare && (
        <div className="mb-3 flex items-center justify-between border-b border-edge pb-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-faint">Radar chart</span>
          <span className="font-mono text-[10px] text-faint">{n.toLocaleString("en-US")} axes</span>
        </div>
      )}

      {cleanSeries.length > 1 && (
        <div className="mb-2 flex flex-wrap justify-center gap-x-3 gap-y-1">
          {cleanSeries.map((s) => (
            <div key={s.name} className="flex items-center gap-1.5 text-[10px] text-muted">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="font-mono tabular-nums">{s.name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="relative veta-rise">
        <svg viewBox={`0 0 ${VIEW_WIDTH} ${height}`} preserveAspectRatio="xMidYMid meet" width="100%" height="auto" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`Radar chart comparing ${cleanSeries.length} series across ${n} axes`}</title>

          {/* Concentric rings + the max-ring value label. */}
          {rings.map((t) => (
            <polygon
              key={t}
              points={axes.map((_, k) => { const p = spoke(cx, cy, R, k, n, t); return `${p.x.toFixed(1)},${p.y.toFixed(1)}`; }).join(" ")}
              fill="none"
              stroke={GRID}
              strokeWidth="1"
            />
          ))}

          {/* Spokes + axis labels. */}
          {axes.map((axis, k) => {
            const end = spoke(cx, cy, R, k, n, 1);
            const lbl = spoke(cx, cy, R + 16, k, n, 1);
            const anchor = Math.abs(lbl.x - cx) < 8 ? "middle" : lbl.x > cx ? "start" : "end";
            return (
              <g key={`axis-${k}`}>
                <line x1={cx} y1={cy} x2={end.x} y2={end.y} stroke={GRID} strokeWidth="1" />
                <text
                  x={lbl.x}
                  y={lbl.y + 3}
                  textAnchor={anchor}
                  fontSize="10"
                  fill={LABEL}
                  className={clickable ? "cursor-pointer" : undefined}
                  onClick={clickable ? () => onSelect!(axis) : undefined}
                >
                  {axis.length > 14 ? `${axis.slice(0, 13)}…` : axis}
                </text>
              </g>
            );
          })}

          {/* Series polygons. */}
          {cleanSeries.map((s) => {
            const pts = s.values.map((v, k) => spoke(cx, cy, R, k, n, Math.max(0, Math.min(1, v / max))));
            const d = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ") + " Z";
            return (
              <g key={s.name}>
                <path d={d} fill={s.color} fillOpacity={0.16} stroke={s.color} strokeWidth="2" strokeLinejoin="round" />
                {pts.map((p, i) => (
                  <circle key={i} cx={p.x} cy={p.y} r="2.6" fill={s.color} />
                ))}
              </g>
            );
          })}

          <text x={cx + 4} y={cy - R * 0.5} fontSize="9" fill={LABEL} className="font-mono">
            {valueFormat(max)}
          </text>
        </svg>
      </div>
    </div>
  );
}
