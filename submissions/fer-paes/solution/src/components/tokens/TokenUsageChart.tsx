import { BarChart2, Loader2 } from 'lucide-react';
import type { TokenUsageByDay } from '../../services/tokenUsageTrackerService';

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function shortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00Z');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

interface Props {
  daily: TokenUsageByDay[];
  loading: boolean;
}

const CHART_H = 160;
const BAR_GAP = 4;

export default function TokenUsageChart({ daily, loading }: Props) {
  const visible = daily.slice(-30);
  const maxTotal = visible.length > 0 ? Math.max(...visible.map((d) => Number(d.total_tokens))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-slate-400" />
          <h3 className="text-white font-semibold text-sm">Daily Token Consumption</h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-blue-500" />
            <span className="text-xs text-slate-500">Input</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-cyan-400" />
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
          No data available
        </div>
      ) : (
        <div className="px-5 py-4 overflow-x-auto">
          <div className="flex items-end gap-1" style={{ height: CHART_H, minWidth: visible.length * (24 + BAR_GAP) }}>
            {visible.map((d, i) => {
              const total     = Number(d.total_tokens);
              const input     = Number(d.input_tokens);
              const output    = Number(d.output_tokens);
              const totalPct  = maxTotal > 0 ? total / maxTotal : 0;
              const inputPct  = total > 0 ? input / total : 0;
              const outputPct = total > 0 ? output / total : 0;
              const barH      = Math.max(Math.round(totalPct * CHART_H), total > 0 ? 4 : 0);
              const inputH    = Math.round(inputPct * barH);
              const outputH   = barH - inputH;
              const today     = new Date().toISOString().slice(0, 10);
              const isToday   = d.day === today;

              return (
                <div key={i} className="group flex flex-col items-center" style={{ width: 24, flexShrink: 0 }}>
                  <div className="relative">
                    {total > 0 && (
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 whitespace-nowrap">
                        <div className="bg-slate-800 border border-white/10 rounded px-2 py-1 text-xs text-white shadow-lg">
                          {formatTokens(total)}
                          <br />
                          <span className="text-blue-400">{formatTokens(input)}</span>
                          {' / '}
                          <span className="text-cyan-400">{formatTokens(output)}</span>
                        </div>
                      </div>
                    )}
                    <div
                      className={`w-5 rounded-t overflow-hidden flex flex-col-reverse ${isToday ? 'ring-1 ring-white/20' : ''}`}
                      style={{ height: barH || 2 }}
                    >
                      <div className="bg-blue-500" style={{ height: inputH }} />
                      <div className="bg-cyan-400" style={{ height: outputH }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex gap-1 mt-2" style={{ minWidth: visible.length * (24 + BAR_GAP) }}>
            {visible.map((d, i) => {
              const showLabel = visible.length <= 14 || i % Math.ceil(visible.length / 14) === 0;
              return (
                <div key={i} className="flex items-center justify-center" style={{ width: 24, flexShrink: 0 }}>
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
