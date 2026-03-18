import { Bot, Loader2 } from 'lucide-react';
import type { CostByAgent } from '../../services/costCalculatorService';

function fmt(n: number): string {
  if (n >= 1000)   return `$${n.toFixed(2)}`;
  if (n >= 1)      return `$${n.toFixed(4)}`;
  if (n >= 0.001)  return `$${n.toFixed(6)}`;
  return `$${n.toFixed(8)}`;
}

interface Props {
  rows: CostByAgent[];
  loading: boolean;
}

export default function LLMCostByAgentTable({ rows, loading }: Props) {
  const maxCost = rows.length > 0 ? Math.max(...rows.map((r) => Number(r.total_cost))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Bot className="w-4 h-4 text-slate-400" />
        <h3 className="text-white font-semibold text-sm">Cost by Agent</h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="py-12 text-center text-slate-600 text-sm">No agent cost data for selected period</div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Agent</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Requests</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Tokens</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Total Cost</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Avg/Req</th>
              <th className="px-5 py-3 w-28" />
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((row, i) => {
              const pct = maxCost > 0 ? Math.round((Number(row.total_cost) / maxCost) * 100) : 0;
              return (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-3.5 h-3.5 text-slate-400" />
                      </div>
                      <span className="text-white text-sm">
                        {row.agent_name ?? <span className="text-slate-500 italic">System / No agent</span>}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-500 text-sm">{Number(row.request_count).toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-400 text-sm">
                    {Number(row.total_tokens) >= 1000
                      ? `${(Number(row.total_tokens) / 1000).toFixed(1)}K`
                      : Number(row.total_tokens).toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-white font-semibold text-sm">{fmt(Number(row.total_cost))}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-500 text-sm">{fmt(Number(row.avg_cost))}</td>
                  <td className="px-5 py-3.5">
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
