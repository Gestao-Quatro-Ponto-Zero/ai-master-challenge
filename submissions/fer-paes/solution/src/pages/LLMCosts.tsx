import { useState, useEffect, useCallback } from 'react';
import { DollarSign, RefreshCw, Calendar } from 'lucide-react';
import {
  getCostsByModel,
  getCostsByAgent,
  getCostsByDay,
  type CostByModel,
  type CostByAgent,
  type CostByDay,
  type CostFilters,
} from '../services/costCalculatorService';
import LLMCostOverview     from '../components/costs/LLMCostOverview';
import LLMCostByModelTable from '../components/costs/LLMCostByModelTable';
import LLMCostByAgentTable from '../components/costs/LLMCostByAgentTable';
import LLMCostChart        from '../components/costs/LLMCostChart';

const RANGE_PRESETS = [
  { label: 'Hoje',      days: 1  },
  { label: '7 Dias',   days: 7  },
  { label: '30 Dias',  days: 30 },
  { label: '90 Dias',  days: 90 },
];

function daysAgo(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString();
}

export default function LLMCosts() {
  const [byModel,  setByModel]  = useState<CostByModel[]>([]);
  const [byAgent,  setByAgent]  = useState<CostByAgent[]>([]);
  const [byDay,    setByDay]    = useState<CostByDay[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [preset,   setPreset]   = useState(30);
  const [filters,  setFilters]  = useState<CostFilters>({
    from: daysAgo(30),
    to:   new Date().toISOString(),
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [m, a, d] = await Promise.all([
        getCostsByModel(filters),
        getCostsByAgent(filters),
        getCostsByDay(filters),
      ]);
      setByModel(m);
      setByAgent(a);
      setByDay(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar dados de custo.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  function applyPreset(days: number) {
    setPreset(days);
    setFilters({ from: daysAgo(days), to: new Date().toISOString() });
  }

  const totalRequests = byModel.reduce((s, r) => s + Number(r.request_count), 0);

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Custos LLM</h1>
              <p className="text-slate-400 text-sm mt-0.5">Monitore os gastos com IA por modelos e agentes</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 bg-slate-900 border border-white/10 rounded-lg p-1">
              {RANGE_PRESETS.map((p) => (
                <button
                  key={p.days}
                  onClick={() => applyPreset(p.days)}
                  className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                    preset === p.days
                      ? 'bg-emerald-600 text-white'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 bg-slate-900 border border-white/10 rounded-lg px-3 py-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <input
                type="date"
                value={filters.from ? filters.from.slice(0, 10) : ''}
                onChange={(e) => {
                  setPreset(0);
                  setFilters((f) => ({ ...f, from: e.target.value ? `${e.target.value}T00:00:00Z` : undefined }));
                }}
                className="bg-transparent text-sm text-white focus:outline-none"
              />
              <span className="text-slate-400">—</span>
              <input
                type="date"
                value={filters.to ? filters.to.slice(0, 10) : ''}
                onChange={(e) => {
                  setPreset(0);
                  setFilters((f) => ({ ...f, to: e.target.value ? `${e.target.value}T23:59:59Z` : undefined }));
                }}
                className="bg-transparent text-sm text-white focus:outline-none"
              />
            </div>

            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 border border-white/10 text-slate-300 hover:text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-6">
        {error && (
          <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        <LLMCostOverview daily={byDay} totalRequests={totalRequests} />

        <LLMCostChart daily={byDay} loading={loading} />

        <div className="grid grid-cols-2 gap-6">
          <LLMCostByModelTable rows={byModel} loading={loading} />
          <LLMCostByAgentTable rows={byAgent} loading={loading} />
        </div>
      </div>
    </div>
  );
}
