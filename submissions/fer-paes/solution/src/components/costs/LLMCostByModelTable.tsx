import { Cpu, Loader2 } from 'lucide-react';
import type { CostByModel } from '../../services/costCalculatorService';

function fmt(n: number): string {
  if (n >= 1000)   return `$${n.toFixed(2)}`;
  if (n >= 1)      return `$${n.toFixed(4)}`;
  if (n >= 0.001)  return `$${n.toFixed(6)}`;
  return `$${n.toFixed(8)}`;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  google:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  mistral:   'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

interface Props {
  rows: CostByModel[];
  loading: boolean;
}

export default function LLMCostByModelTable({ rows, loading }: Props) {
  const maxCost = rows.length > 0 ? Math.max(...rows.map((r) => Number(r.total_cost))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Cpu className="w-4 h-4 text-slate-400" />
        <h3 className="text-white font-semibold text-sm">Cost by Model</h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="py-12 text-center text-slate-600 text-sm">No cost data for selected period</div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Model</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Requests</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Input Cost</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Output Cost</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Total</th>
              <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Avg/Req</th>
              <th className="px-5 py-3 w-28" />
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((row, i) => {
              const providerCls = PROVIDER_COLORS[row.provider ?? ''] ?? 'bg-slate-700 text-slate-400 border-white/10';
              const pct = maxCost > 0 ? Math.round((Number(row.total_cost) / maxCost) * 100) : 0;
              return (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${providerCls}`}>
                        {row.provider ?? '—'}
                      </span>
                      <code className="text-slate-300 text-sm font-mono">{row.model_identifier ?? '—'}</code>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-500 text-sm">{Number(row.request_count).toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-400 text-sm">{fmt(Number(row.input_cost))}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-400 text-sm">{fmt(Number(row.output_cost))}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-white font-semibold text-sm">{fmt(Number(row.total_cost))}</td>
                  <td className="px-5 py-3.5 text-right tabular-nums text-slate-500 text-sm">{fmt(Number(row.avg_cost))}</td>
                  <td className="px-5 py-3.5">
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
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
