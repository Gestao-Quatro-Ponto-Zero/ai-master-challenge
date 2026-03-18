import { useState, useEffect, useCallback, useRef } from 'react';
import { Activity, RefreshCw, Loader2 } from 'lucide-react';
import {
  getAIUsageOverview, getUsageByModel, getUsageByAgent, getUsageTimeseries, getActiveBudgetForDashboard,
  defaultFilters, PERIOD_PRESETS,
  type AIUsageOverview, type CostByModel, type CostByAgent, type CostByDay, type AIUsageFilters,
} from '../services/aiUsageAnalyticsService';
import type { LLMBudget } from '../services/budgetManagerService';
import AIUsageOverviewCards    from '../components/ai-usage/AIUsageOverviewCards';
import AIUsageTimeseriesChart  from '../components/ai-usage/AIUsageTimeseriesChart';
import AIUsageByModelTable     from '../components/ai-usage/AIUsageByModelTable';
import AIUsageByAgentTable     from '../components/ai-usage/AIUsageByAgentTable';
import AIUsageBudgetStatus     from '../components/ai-usage/AIUsageBudgetStatus';

const AUTO_REFRESH_MS = 30_000;

export default function AIUsageDashboard() {
  const [preset,   setPreset]   = useState(30);
  const [filters,  setFilters]  = useState<AIUsageFilters>(defaultFilters(30));
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [overview, setOverview] = useState<AIUsageOverview | null>(null);
  const [models,   setModels]   = useState<CostByModel[]>([]);
  const [agents,   setAgents]   = useState<CostByAgent[]>([]);
  const [daily,    setDaily]    = useState<CostByDay[]>([]);
  const [budget,   setBudget]   = useState<LLMBudget | null>(null);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async (f: AIUsageFilters) => {
    setLoading(true);
    setError('');
    try {
      const [ov, mo, ag, dy, bud] = await Promise.all([
        getAIUsageOverview(f),
        getUsageByModel(f),
        getUsageByAgent(f),
        getUsageTimeseries(f),
        getActiveBudgetForDashboard(),
      ]);
      setOverview(ov);
      setModels(mo);
      setAgents(ag);
      setDaily(dy);
      setBudget(bud);
      setLastSynced(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar dados do painel.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(filters);
    timerRef.current = setInterval(() => load(filters), AUTO_REFRESH_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [filters, load]);

  function changePreset(days: number) {
    setPreset(days);
    const f = defaultFilters(days);
    setFilters(f);
  }

  function manualRefresh() {
    load(filters);
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Activity className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Painel de Uso de IA</h1>
              <p className="text-slate-400 text-sm mt-0.5">
                Tokens, custo, latência e uso por modelo — tudo em um painel
                {lastSynced && (
                  <span className="text-slate-600 ml-2">
                    · Atualizado às {lastSynced.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Period presets */}
            <div className="flex rounded-lg overflow-hidden border border-white/10 text-xs font-medium">
              {PERIOD_PRESETS.map((p) => (
                <button
                  key={p.days}
                  onClick={() => changePreset(p.days)}
                  className={`px-3 py-1.5 transition-colors ${preset === p.days ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Refresh */}
            <button
              onClick={manualRefresh}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 text-slate-500 hover:text-white hover:border-white/20 transition-colors text-xs font-medium disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Atualizar
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-6">
        {error && (
          <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
        )}

        {/* Budget status */}
        <AIUsageBudgetStatus budget={budget} />

        {/* Overview cards */}
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Visão Geral</p>
          <AIUsageOverviewCards overview={overview} loading={loading} />
        </div>

        {/* Timeseries */}
        <AIUsageTimeseriesChart daily={daily} loading={loading} />

        {/* Model + Agent tables side by side on wide screens */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <AIUsageByModelTable data={models} loading={loading} />
          <AIUsageByAgentTable data={agents} loading={loading} />
        </div>
      </div>
    </div>
  );
}
