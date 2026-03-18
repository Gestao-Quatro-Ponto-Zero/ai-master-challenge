import { Bot, Loader2 } from 'lucide-react';
import type { CostByAgent } from '../../services/aiUsageAnalyticsService';
import { formatTokens, formatUSD } from '../../services/aiUsageAnalyticsService';

interface Props {
  data:    CostByAgent[];
  loading: boolean;
}

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full bg-slate-800 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 tabular-nums w-16 text-right">{formatUSD(value)}</span>
    </div>
  );
}

export default function AIUsageByAgentTable({ data, loading }: Props) {
  const maxCost = data.length > 0 ? Math.max(...data.map((d) => Number(d.total_cost))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Bot className="w-4 h-4 text-slate-400" />
        <h3 className="text-white font-semibold text-sm">Uso por Agente</h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="py-10 text-center text-slate-600 text-sm">Sem dados de uso por agente para o período selecionado</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Agente', 'Requisições', 'Tokens', 'Custo Médio/req', 'Custo Total'].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-6 h-6 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-3.5 h-3.5 text-slate-400" />
                      </div>
                      <p className="text-white text-sm font-medium">
                        {row.agent_name ?? <span className="text-slate-500 italic">Sem agente</span>}
                      </p>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-slate-400 text-sm tabular-nums">
                    {Number(row.request_count).toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-slate-400 text-sm tabular-nums">
                    {formatTokens(Number(row.total_tokens))}
                  </td>
                  <td className="px-5 py-3 text-slate-400 text-sm tabular-nums">
                    {formatUSD(Number(row.avg_cost))}
                  </td>
                  <td className="px-5 py-3 min-w-[160px]">
                    <MiniBar value={Number(row.total_cost)} max={maxCost} color="bg-blue-500" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
