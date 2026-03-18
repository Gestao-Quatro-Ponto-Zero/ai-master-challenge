import { useState, useEffect, useCallback } from 'react';
import { Database, RefreshCw, TrendingUp, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { getRequests } from '../services/llmRequestLoggerService';
import { getModels } from '../services/modelRegistryService';
import type { LLMRequest, LLMRequestFilters, LLMModel } from '../types';
import LLMRequestFiltersBar from '../components/llm/LLMRequestFilters';
import LLMRequestsTable from '../components/llm/LLMRequestsTable';
import LLMRequestDetails from '../components/llm/LLMRequestDetails';

export default function LLMRequestsLog() {
  const [requests, setRequests] = useState<LLMRequest[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<LLMRequestFilters>({});
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<LLMRequest | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [reqs, mdls] = await Promise.all([getRequests(filters, 200), getModels()]);
      setRequests(reqs);
      setModels(mdls);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar logs.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const filtered = requests.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.model_identifier?.toLowerCase().includes(q) ||
      r.provider?.toLowerCase().includes(q) ||
      r.model?.name?.toLowerCase().includes(q) ||
      r.agent?.name?.toLowerCase().includes(q) ||
      r.id.toLowerCase().includes(q)
    );
  });

  const stats = {
    total:   requests.length,
    success: requests.filter((r) => r.status === 'success').length,
    errors:  requests.filter((r) => r.status === 'error' || r.status === 'timeout').length,
    avgLatency:
      requests.filter((r) => r.latency_ms !== null).length > 0
        ? Math.round(
            requests
              .filter((r) => r.latency_ms !== null)
              .reduce((sum, r) => sum + (r.latency_ms ?? 0), 0) /
              requests.filter((r) => r.latency_ms !== null).length
          )
        : null,
    totalTokens: requests.reduce((sum, r) => sum + (r.total_tokens ?? 0), 0),
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950">
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 flex items-center justify-center">
              <Database className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Log de Requisições LLM</h1>
              <p className="text-slate-400 text-sm mt-0.5">Trilha de auditoria de todas as chamadas de API de modelos de linguagem</p>
            </div>
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

        <div className="grid grid-cols-5 gap-4 mt-6">
          <div className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
            <p className="text-xs text-slate-500 font-medium">Total de Requisições</p>
            <p className="text-2xl font-bold text-white mt-1">{stats.total.toLocaleString()}</p>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <p className="text-xs text-slate-500 font-medium">Com Sucesso</p>
            </div>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.success.toLocaleString()}</p>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
            <div className="flex items-center gap-1.5">
              <XCircle className="w-3 h-3 text-red-400" />
              <p className="text-xs text-slate-500 font-medium">Erros / Timeouts</p>
            </div>
            <p className="text-2xl font-bold text-red-400 mt-1">{stats.errors.toLocaleString()}</p>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-blue-400" />
              <p className="text-xs text-slate-500 font-medium">Latência Média</p>
            </div>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {stats.avgLatency !== null
                ? stats.avgLatency >= 1000
                  ? `${(stats.avgLatency / 1000).toFixed(1)}s`
                  : `${stats.avgLatency}ms`
                : '—'}
            </p>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-3 h-3 text-amber-400" />
              <p className="text-xs text-slate-500 font-medium">Total de Tokens</p>
            </div>
            <p className="text-2xl font-bold text-amber-400 mt-1">
              {stats.totalTokens >= 1_000_000
                ? `${(stats.totalTokens / 1_000_000).toFixed(1)}M`
                : stats.totalTokens >= 1_000
                ? `${(stats.totalTokens / 1_000).toFixed(0)}K`
                : stats.totalTokens.toString()}
            </p>
          </div>
        </div>
      </div>

      <LLMRequestFiltersBar
        filters={filters}
        search={search}
        models={models}
        onChange={(f) => { setFilters(f); setSelected(null); }}
        onSearchChange={setSearch}
      />

      {error && (
        <div className="mx-8 mt-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="flex-1 flex min-h-0">
        <div className="flex-1 overflow-auto px-8 py-4">
          <LLMRequestsTable
            requests={filtered}
            loading={loading}
            selectedId={selected?.id ?? null}
            onSelect={setSelected}
          />
        </div>

        {selected && (
          <LLMRequestDetails
            request={selected}
            onClose={() => setSelected(null)}
          />
        )}
      </div>
    </div>
  );
}
