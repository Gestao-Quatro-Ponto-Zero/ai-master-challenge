import { TrendingUp, Loader2 } from 'lucide-react';
import type { CostByDay } from '../../services/costCalculatorService';

function fmtShort(n: number): string {
  if (n >= 1)     return `$${n.toFixed(2)}`;
  if (n >= 0.001) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(6)}`;
}

function shortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00Z');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

interface Props {
  daily: CostByDay[];
  loading: boolean;
}

const CHART_H = 160;
const BAR_W   = 24;
const BAR_GAP = 4;

export default function LLMCostChart({ daily, loading }: Props) {
  const visible  = daily.slice(-30);
  const maxCost  = visible.length > 0 ? Math.max(...visible.map((d) => Number(d.total_cost))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-slate-400" />
          <h3 className="text-white font-semibold text-sm">Daily Cost</h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
            <span className="text-xs text-slate-500">Input</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-blue-400" />
            <span className="text-xs text-slate-500">Output</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: CHART_H + 60 }}>
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : visible.length === 0 ? (
        <div className="flex items-center justify-center text-slate-600 text-sm" style={{ height: CHART_H + 60 }}>
          No cost data available
        </div>
      ) : (
        <div className="px-5 py-4 overflow-x-auto">
          <div
            className="flex items-end"
            style={{ gap: BAR_GAP, height: CHART_H, minWidth: visible.length * (BAR_W + BAR_GAP) }}
          >
            {visible.map((d, i) => {
              const total      = Number(d.total_cost);
              const inputCost  = Number(d.input_cost);
              const outputCost = Number(d.output_cost);
              const totalPct   = maxCost > 0 ? total / maxCost : 0;
              const inputPct   = total > 0 ? inputCost / total : 0;
              const barH       = Math.max(Math.round(totalPct * CHART_H), total > 0 ? 4 : 0);
              const inputH     = Math.round(inputPct * barH);
              const outputH    = barH - inputH;
              const today      = new Date().toISOString().slice(0, 10);
              const isToday    = d.day === today;

              return (
                <div key={i} className="group flex flex-col items-center" style={{ width: BAR_W, flexShrink: 0 }}>
                  <div className="relative">
                    {total > 0 && (
                      <div className="absolute -top-9 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 whitespace-nowrap">
                        <div className="bg-slate-800 border border-white/10 rounded px-2 py-1 text-xs text-white shadow-lg">
                          <span className="font-medium">{fmtShort(total)}</span>
                          <br />
                          <span className="text-emerald-400">{fmtShort(inputCost)}</span>
                          {' / '}
                          <span className="text-blue-400">{fmtShort(outputCost)}</span>
                        </div>
                      </div>
                    )}
                    <div
                      className={`w-5 rounded-t overflow-hidden flex flex-col-reverse ${isToday ? 'ring-1 ring-white/20' : ''}`}
                      style={{ height: barH || 2 }}
                    >
                      <div className="bg-emerald-500" style={{ height: inputH }} />
                      <div className="bg-blue-400"    style={{ height: outputH }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div
            className="flex mt-2"
            style={{ gap: BAR_GAP, minWidth: visible.length * (BAR_W + BAR_GAP) }}
          >
            {visible.map((d, i) => {
              const showLabel = visible.length <= 14 || i % Math.ceil(visible.length / 14) === 0;
              return (
                <div key={i} className="flex items-center justify-center" style={{ width: BAR_W, flexShrink: 0 }}>
                  {showLabel && (
                    <span className="text-slate-600 text-[10px] rotate-45 origin-left whitespace-nowrap">
                      {shortDate(d.day)}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
