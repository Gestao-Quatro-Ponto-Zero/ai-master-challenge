import { useState } from 'react';
import { BarChart2, Loader2 } from 'lucide-react';
import type { CostByDay } from '../../services/aiUsageAnalyticsService';
import { formatTokens } from '../../services/aiUsageAnalyticsService';

function fmtCost(n: number): string {
  if (n >= 1)     return `$${n.toFixed(2)}`;
  if (n >= 0.001) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(6)}`;
}

function shortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00Z');
  return d.toLocaleDateString('pt-BR', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

type View = 'cost' | 'tokens';

interface Props {
  daily:   CostByDay[];
  loading: boolean;
}

const CHART_H = 180;
const BAR_W   = 20;
const BAR_GAP = 5;

export default function AIUsageTimeseriesChart({ daily, loading }: Props) {
  const [view, setView] = useState<View>('cost');
  const visible = daily.slice(-30);
  const today   = new Date().toISOString().slice(0, 10);

  const maxCost   = visible.length > 0 ? Math.max(...visible.map((d) => Number(d.total_cost)),   0.000001) : 1;
  const maxTokens = visible.length > 0 ? Math.max(...visible.map((d) => Number(d.total_tokens)), 1)        : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-slate-400" />
          <h3 className="text-white font-semibold text-sm">Uso ao Longo do Tempo</h3>
          <span className="text-xs text-slate-500">— últimos 30 dias</span>
        </div>
        <div className="flex rounded-lg overflow-hidden border border-white/10 text-xs font-medium">
          {(['cost', 'tokens'] as View[]).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 transition-colors ${view === v
                ? v === 'cost' ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white'
                : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
            >
              {v === 'cost' ? 'Custo' : 'Tokens'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: CHART_H + 64 }}>
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : visible.length === 0 ? (
        <div className="flex items-center justify-center text-slate-600 text-sm" style={{ height: CHART_H + 64 }}>
          Sem dados para o período selecionado
        </div>
      ) : (
        <div className="px-5 py-4 overflow-x-auto">
          {/* bars */}
          <div className="flex items-end" style={{ gap: BAR_GAP, height: CHART_H, minWidth: visible.length * (BAR_W + BAR_GAP) }}>
            {visible.map((d, i) => {
              const isToday = d.day === today;

              if (view === 'cost') {
                const total   = Number(d.total_cost);
                const inputC  = Number(d.input_cost);
                const outputC = Number(d.output_cost);
                const barH    = Math.max(Math.round((total / maxCost) * CHART_H), total > 0 ? 4 : 0);
                const inputH  = Math.round((total > 0 ? inputC / total : 0) * barH);
                const outputH = barH - inputH;
                return (
                  <div key={i} className="group flex flex-col items-center" style={{ width: BAR_W, flexShrink: 0 }}>
                    <div className="relative">
                      {total > 0 && (
                        <div className="absolute -top-12 left-1/2 -translate-x-1/2 hidden group-hover:flex flex-col z-10 whitespace-nowrap">
                          <div className="bg-slate-800 border border-white/10 rounded px-2 py-1.5 text-xs text-white shadow-lg">
                            <div className="font-semibold">{fmtCost(total)}</div>
                            <div className="text-emerald-400">entrada {fmtCost(inputC)}</div>
                            <div className="text-blue-400">saída {fmtCost(outputC)}</div>
                          </div>
                        </div>
                      )}
                      <div
                        className={`rounded-t overflow-hidden flex flex-col-reverse ${isToday ? 'ring-1 ring-emerald-500/50' : ''}`}
                        style={{ width: BAR_W, height: barH || 2 }}
                      >
                        <div className="bg-emerald-500" style={{ height: inputH }} />
                        <div className="bg-blue-400"    style={{ height: outputH }} />
                      </div>
                    </div>
                  </div>
                );
              }

              const total = Number(d.total_tokens);
              const barH  = Math.max(Math.round((total / maxTokens) * CHART_H), total > 0 ? 4 : 0);
              return (
                <div key={i} className="group flex flex-col items-center" style={{ width: BAR_W, flexShrink: 0 }}>
                  <div className="relative">
                    {total > 0 && (
                      <div className="absolute -top-9 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 whitespace-nowrap">
                        <div className="bg-slate-800 border border-white/10 rounded px-2 py-1 text-xs text-white shadow-lg">
                          {formatTokens(total)} tokens totais
                        </div>
                      </div>
                    )}
                    <div
                      className={`rounded-t ${isToday ? 'bg-blue-400 ring-1 ring-blue-400/50' : 'bg-blue-600'}`}
                      style={{ width: BAR_W, height: barH || 2 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* x-axis */}
          <div className="flex mt-3" style={{ gap: BAR_GAP, minWidth: visible.length * (BAR_W + BAR_GAP) }}>
            {visible.map((d, i) => {
              const show = visible.length <= 14 || i % Math.ceil(visible.length / 12) === 0;
              return (
                <div key={i} className="flex items-center justify-center" style={{ width: BAR_W, flexShrink: 0 }}>
                  {show && (
                    <span className="text-slate-600 text-[10px] rotate-45 origin-left whitespace-nowrap block">
                      {shortDate(d.day)}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* legend */}
          <div className="flex items-center gap-4 mt-6">
            {view === 'cost' ? (
              <>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
                  <span className="text-xs text-slate-500">Custo de entrada</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm bg-blue-400" />
                  <span className="text-xs text-slate-500">Custo de saída</span>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-sm bg-blue-600" />
                <span className="text-xs text-slate-500">Total de tokens</span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-sm ring-1 ring-white/30 bg-white/10" />
              <span className="text-xs text-slate-500">Hoje</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
