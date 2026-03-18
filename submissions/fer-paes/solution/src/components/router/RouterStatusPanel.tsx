import { CheckCircle, XCircle, Cpu, Activity } from 'lucide-react';
import type { RouterStatus, RouterModel } from '../../services/llmRouterService';

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  google:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  mistral:   'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

interface Props {
  status: RouterStatus | null;
  models: RouterModel[];
  loading: boolean;
}

export default function RouterStatusPanel({ status, models, loading }: Props) {
  const providerEntries = status ? Object.entries(status.providers) : [];
  const availableCount  = providerEntries.filter(([, v]) => v).length;
  const activeModels    = models.length;

  const stats = [
    { label: 'Providers Available', value: loading ? '—' : `${availableCount} / ${providerEntries.length}`, icon: Activity, ok: availableCount > 0 },
    { label: 'Active Models',       value: loading ? '—' : String(activeModels), icon: Cpu, ok: activeModels > 0 },
  ];

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-white/5">
        <h3 className="text-white font-semibold text-sm">Router Status</h3>
      </div>

      <div className="p-5 space-y-5">
        {/* Stat cards */}
        <div className="grid grid-cols-2 gap-3">
          {stats.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.label} className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1.5">
                  <Icon className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xs text-slate-500">{s.label}</span>
                </div>
                <p className={`text-xl font-bold tabular-nums ${s.ok ? 'text-white' : 'text-red-400'}`}>{s.value}</p>
              </div>
            );
          })}
        </div>

        {/* Provider grid */}
        {providerEntries.length > 0 && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Providers</p>
            <div className="space-y-2">
              {providerEntries.map(([provider, available]) => (
                <div key={provider} className="flex items-center justify-between py-1.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${PROVIDER_COLORS[provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                    {provider}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {available ? (
                      <>
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-xs text-emerald-400">Configured</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5 text-slate-600" />
                        <span className="text-xs text-slate-600">No API key</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active models list */}
        {models.length > 0 && (
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Active Models</p>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {models.map((m) => (
                <div key={m.id} className="flex items-center gap-2 py-1">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border capitalize flex-shrink-0 ${PROVIDER_COLORS[m.provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                    {m.provider}
                  </span>
                  <code className="text-slate-400 text-xs flex-1 truncate">{m.model_identifier}</code>
                  {m.input_cost_per_1k_tokens != null && (
                    <span className="text-slate-600 text-[10px] tabular-nums flex-shrink-0">
                      ${m.input_cost_per_1k_tokens}/1k
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
