import { useState, useEffect, useCallback } from 'react';
import { Cpu, Plus, RefreshCw, Search, CheckCircle2, XCircle, ToggleLeft, ToggleRight, Pencil } from 'lucide-react';
import { getModels, activateModel, deactivateModel } from '../services/modelRegistryService';
import type { LLMModel, LLMModelProvider } from '../types';
import LLMModelCreateModal from '../components/llm/LLMModelCreateModal';
import LLMModelEditModal from '../components/llm/LLMModelEditModal';

const PROVIDER_COLORS: Record<LLMModelProvider, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  google:    'bg-blue-500/10 text-blue-400 border-blue-500/20',
  mistral:   'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

const PROVIDER_LABELS: Record<LLMModelProvider, string> = {
  openai:    'OpenAI',
  anthropic: 'Anthropic',
  google:    'Google',
  mistral:   'Mistral',
};

function formatCost(value: number | null): string {
  if (value === null || value === undefined) return '—';
  if (value === 0) return '$0.00';
  if (value < 0.001) return `$${value.toFixed(5)}`;
  return `$${value.toFixed(4)}`;
}

function formatTokens(value: number | null): string {
  if (!value) return '—';
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return String(value);
}

export default function LLMModels() {
  const [models, setModels] = useState<LLMModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [providerFilter, setProviderFilter] = useState<LLMModelProvider | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [editTarget, setEditTarget] = useState<LLMModel | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setModels(await getModels());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar modelos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleToggle(model: LLMModel) {
    setTogglingId(model.id);
    try {
      if (model.is_active) {
        await deactivateModel(model.id);
      } else {
        await activateModel(model.id);
      }
      await load();
    } finally {
      setTogglingId(null);
    }
  }

  const providers = [...new Set(models.map((m) => m.provider))] as LLMModelProvider[];

  const filtered = models.filter((m) => {
    const matchSearch =
      !search ||
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.model_identifier.toLowerCase().includes(search.toLowerCase()) ||
      m.description?.toLowerCase().includes(search.toLowerCase());
    const matchProvider = providerFilter === 'all' || m.provider === providerFilter;
    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && m.is_active) ||
      (statusFilter === 'inactive' && !m.is_active);
    return matchSearch && matchProvider && matchStatus;
  });

  const counts = {
    total: models.length,
    active: models.filter((m) => m.is_active).length,
    inactive: models.filter((m) => !m.is_active).length,
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950">
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Registro de Modelos</h1>
              <p className="text-slate-400 text-sm mt-0.5">Catálogo central de modelos de linguagem disponíveis no sistema</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Registrar Modelo
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          {[
            { label: 'Total de Modelos', value: counts.total, color: 'text-white' },
            { label: 'Ativo',            value: counts.active,   color: 'text-emerald-400' },
            { label: 'Inativo',          value: counts.inactive, color: 'text-slate-400' },
          ].map((stat) => (
            <div key={stat.label} className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
              <p className="text-xs text-slate-400 font-medium">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="px-8 py-4 border-b border-white/5 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar modelos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-white/10 rounded-lg text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          {(['all', ...providers] as const).map((p) => (
            <button
              key={p}
              onClick={() => setProviderFilter(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                providerFilter === p
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-900 border border-white/10 text-slate-300 hover:text-white'
              }`}
            >
              {p === 'all' ? 'Todos os Provedores' : PROVIDER_LABELS[p]}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {(['all', 'active', 'inactive'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                statusFilter === s
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-900 border border-white/10 text-slate-300 hover:text-white'
              }`}
            >
              {s === 'all' ? 'Todos os Status' : s === 'active' ? 'Ativo' : 'Inativo'}
            </button>
          ))}
        </div>

        <button
          onClick={load}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-900 border border-white/10 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex-1 overflow-auto px-8 py-4">
        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <RefreshCw className="w-6 h-6 text-slate-400 animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-3">
              <Cpu className="w-6 h-6 text-slate-500" />
            </div>
            <p className="text-slate-400 font-medium">Nenhum modelo encontrado</p>
            <p className="text-slate-400 text-sm mt-1">
              {search || providerFilter !== 'all' || statusFilter !== 'all'
                ? 'Tente ajustar seus filtros'
                : 'Registre seu primeiro modelo LLM para começar'}
            </p>
          </div>
        ) : (
          <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Modelo</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Provedor</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Identificador da API</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Máx. Tokens</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Entrada $/1K</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Saída $/1K</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.map((model) => (
                  <tr key={model.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-4 py-3.5">
                      <div>
                        <p className="text-white text-sm font-medium">{model.name}</p>
                        {model.description && (
                          <p className="text-slate-400 text-xs mt-0.5 truncate max-w-48">{model.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${PROVIDER_COLORS[model.provider] || 'bg-slate-700 text-slate-300 border-white/10'}`}>
                        {PROVIDER_LABELS[model.provider] ?? model.provider}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <code className="text-slate-300 text-xs font-mono bg-slate-800 px-2 py-1 rounded">
                        {model.model_identifier}
                      </code>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <span className="text-slate-300 text-sm tabular-nums">{formatTokens(model.max_tokens)}</span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <span className="text-slate-300 text-sm tabular-nums">{formatCost(model.input_cost_per_1k_tokens)}</span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <span className="text-slate-300 text-sm tabular-nums">{formatCost(model.output_cost_per_1k_tokens)}</span>
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {model.is_active ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          Ativo
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-700 text-slate-400 border border-white/10">
                          <XCircle className="w-3 h-3" />
                          Inativo
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => setEditTarget(model)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                          title="Editar"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleToggle(model)}
                          disabled={togglingId === model.id}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors disabled:opacity-50"
                          title={model.is_active ? 'Desativar' : 'Ativar'}
                        >
                          {model.is_active ? (
                            <ToggleRight className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <ToggleLeft className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showCreate && (
        <LLMModelCreateModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
        />
      )}

      {editTarget && (
        <LLMModelEditModal
          model={editTarget}
          onClose={() => setEditTarget(null)}
          onUpdated={() => { setEditTarget(null); load(); }}
        />
      )}
    </div>
  );
}
