import { Cpu, Loader2 } from 'lucide-react';
import type { CostByModel } from '../../services/aiUsageAnalyticsService';
import { formatTokens, formatUSD } from '../../services/aiUsageAnalyticsService';

interface Props {
  data:    CostByModel[];
  loading: boolean;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/20 text-emerald-400',
  anthropic: 'bg-amber-500/20  text-amber-400',
  google:    'bg-blue-500/20   text-blue-400',
  mistral:   'bg-orange-500/20 text-orange-400',
};

function providerBadge(provider: string | null) {
  const cls = PROVIDER_COLORS[provider ?? ''] ?? 'bg-slate-700 text-slate-400';
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize border border-white/5 ${cls}`}>
      {provider ?? 'desconhecido'}
    </span>
  );
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

export default function AIUsageByModelTable({ data, loading }: Props) {
  const maxCost = data.length > 0 ? Math.max(...data.map((d) => Number(d.total_cost))) : 1;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Cpu className="w-4 h-4 text-slate-400" />
        <h3 className="text-white font-semibold text-sm">Uso por Modelo</h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="py-10 text-center text-slate-600 text-sm">Sem dados de uso por modelo para o período selecionado</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Modelo', 'Provedor', 'Requisições', 'Tokens', 'Custo'].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3">
                    <p className="text-white text-sm font-medium">{row.model_identifier ?? '—'}</p>
                  </td>
                  <td className="px-5 py-3">{providerBadge(row.provider)}</td>
                  <td className="px-5 py-3 text-slate-400 text-sm tabular-nums">
                    {Number(row.request_count).toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-slate-400 text-sm tabular-nums">
                    {formatTokens(Number(row.total_tokens))}
                    <span className="text-slate-600 text-xs ml-1">
                      ({formatTokens(Number(row.input_tokens))} ent / {formatTokens(Number(row.output_tokens))} saí)
                    </span>
                  </td>
                  <td className="px-5 py-3 min-w-[160px]">
                    <MiniBar value={Number(row.total_cost)} max={maxCost} color="bg-emerald-500" />
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
