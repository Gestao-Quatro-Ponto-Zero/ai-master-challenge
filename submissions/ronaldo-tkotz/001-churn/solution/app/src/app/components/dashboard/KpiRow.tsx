import type { Kpi } from "@/engine/dashboard";
import { Sparkline } from "./Sparkline";

const TONE: Record<Kpi["status"]["tone"], string> = {
  good: "text-emerald-300 border-emerald-400/25 bg-emerald-400/10",
  warn: "text-amber-300 border-amber-400/25 bg-amber-400/10",
  bad: "text-red-300 border-red-400/25 bg-red-400/10",
  neutral: "text-muted border-edge bg-surface",
};

// Sparkline colour ties to the card's accent so the trend reads as part of the metric.
const SPARK: Record<Kpi["accent"], string> = {
  neutral: "#8a90ad",
  critical: "#f87171",
  warning: "#e3b341",
  opportunity: "#34d399",
};

function fmt(kpi: Kpi): string {
  const n = kpi.value;
  switch (kpi.format) {
    case "usd":
      if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
      if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
      return `$${n.toLocaleString("en-US")}`;
    case "pct":
      return `${n}%`;
    case "int":
      return n.toLocaleString("en-US");
    default:
      return String(n);
  }
}

export function KpiRow({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {kpis.map((kpi) => {
        const d = kpi.delta;
        const arrow = d ? (d.direction === "up" ? "▲" : d.direction === "down" ? "▼" : "→") : "";
        const dirColor = d ? (d.direction === "up" ? "text-emerald-400" : d.direction === "down" ? "text-red-400" : "text-faint") : "";
        return (
          <div key={kpi.id} className="flex flex-col rounded-xl border border-edge bg-panel p-3.5">
            <div className="flex items-center gap-2">
              <span className="text-[10.5px] font-medium uppercase tracking-wider text-faint">{kpi.label}</span>
              <span className={`ml-auto rounded-full border px-1.5 py-[1px] text-[9.5px] font-semibold uppercase tracking-wide ${TONE[kpi.status.tone]}`}>
                {kpi.status.label}
              </span>
            </div>

            <div className="mt-2 font-mono text-[24px] font-semibold leading-none tracking-tight text-foreground tabular-nums">
              {fmt(kpi)}
            </div>

            <div className="mt-2.5 flex items-end gap-3">
              {d ? (
                <div className="flex shrink-0 items-center gap-1.5 text-[11px]">
                  <span className={`font-mono font-medium ${dirColor}`}>
                    {arrow} {Math.abs(d.pct)}%
                  </span>
                </div>
              ) : null}
              <div className="min-w-0 flex-1">
                <Sparkline values={kpi.spark} color={SPARK[kpi.accent]} mode={kpi.id === "at_risk" ? "bar" : "line"} />
              </div>
            </div>

            <div className="mt-1.5 truncate text-[10.5px] leading-snug text-faint">{d ? d.label : kpi.sub}</div>
          </div>
        );
      })}
    </div>
  );
}
