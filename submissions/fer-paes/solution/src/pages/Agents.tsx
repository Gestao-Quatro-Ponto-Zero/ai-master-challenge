import { useState, useEffect, useCallback } from 'react';
import { Bot, Plus, RefreshCw, Search, Network, Play, Wrench, Cpu, Brain, BarChart3, CheckCircle2, AlertCircle } from 'lucide-react';
import { getAgents } from '../services/agentService';
import type { AgentWithRelations, AgentStatus } from '../types';
import AgentsTable from '../components/agents/AgentsTable';
import CreateAgentModal from '../components/agents/CreateAgentModal';
import RouterTestPanel from '../components/agents/RouterTestPanel';
import ExecutorTestPanel from '../components/agents/ExecutorTestPanel';
import ToolsPanel from '../components/agents/ToolsPanel';
import LlmManagerPanel from '../components/agents/LlmManagerPanel';
import MemoryPanel from '../components/agents/MemoryPanel';
import AgentAnalyticsPage from '../components/agents/AgentAnalyticsPage';

type Tab = 'registry' | 'router' | 'executor' | 'tools' | 'llm' | 'memory' | 'analytics';

const STATUS_FILTERS: { value: AgentStatus | 'all'; label: string }[] = [
  { value: 'all',      label: 'Todos' },
  { value: 'active',   label: 'Ativo' },
  { value: 'testing',  label: 'Testando' },
  { value: 'disabled', label: 'Desabilitado' },
];

const TABS: { value: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: 'registry',  label: 'Registro',        icon: Bot       },
  { value: 'router',    label: 'Roteador',         icon: Network   },
  { value: 'executor',  label: 'Executor',         icon: Play      },
  { value: 'tools',     label: 'Ferramentas',      icon: Wrench    },
  { value: 'llm',       label: 'Gerenciador LLM',  icon: Cpu       },
  { value: 'memory',    label: 'Memória',           icon: Brain     },
  { value: 'analytics', label: 'Análises',          icon: BarChart3 },
];

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-4 h-4 text-current" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xl font-bold text-gray-900 tabular-nums">{value}</p>
      </div>
    </div>
  );
}

export default function Agents() {
  const [tab,          setTab]          = useState<Tab>('registry');
  const [agents,       setAgents]       = useState<AgentWithRelations[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState('');
  const [showCreate,   setShowCreate]   = useState(false);
  const [search,       setSearch]       = useState('');
  const [statusFilter, setStatusFilter] = useState<AgentStatus | 'all'>('all');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAgents();
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar agentes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = agents.filter((a) => {
    const matchSearch =
      !search ||
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.description?.toLowerCase().includes(search.toLowerCase()) ||
      a.type?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const counts = {
    total:    agents.length,
    active:   agents.filter((a) => a.status === 'active').length,
    testing:  agents.filter((a) => a.status === 'testing').length,
    disabled: agents.filter((a) => a.status === 'disabled').length,
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Bot className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Agentes</h1>
              <p className="text-sm text-gray-400">Configure e gerencie seus agentes de IA</p>
            </div>
          </div>
          {tab === 'registry' && (
            <div className="flex items-center gap-2">
              <button
                onClick={load}
                disabled={loading}
                className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-50 border border-gray-100 transition-colors disabled:opacity-40"
                title="Atualizar"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Criar Agente
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-5 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total de agentes" value={counts.total}    icon={Bot}          color="bg-blue-50 text-blue-600"     />
          <StatCard label="Ativos"            value={counts.active}   icon={CheckCircle2} color="bg-emerald-50 text-emerald-600" />
          <StatCard label="Testando"          value={counts.testing}  icon={Play}         color="bg-amber-50 text-amber-600"    />
          <StatCard label="Desabilitados"     value={counts.disabled} icon={AlertCircle}  color="bg-gray-100 text-gray-500"     />
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-white rounded-xl border border-gray-100 p-1 w-fit flex-wrap">
          {TABS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setTab(value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === value
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* Registry filters */}
        {tab === 'registry' && (
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar agentes..."
                className="w-full bg-white border border-gray-100 rounded-xl pl-9 pr-3 py-2 text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 transition-colors"
              />
            </div>
            <div className="flex items-center gap-1 bg-white rounded-xl border border-gray-100 p-1">
              {STATUS_FILTERS.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setStatusFilter(f.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === f.value
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="flex-1 min-h-0">
          {tab === 'registry' && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-700">Agentes</h2>
                {loading && <RefreshCw className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />}
                <span className="text-xs text-gray-400 ml-1">{filtered.length} resultado{filtered.length !== 1 ? 's' : ''}</span>
              </div>
              <AgentsTable agents={filtered} onRefresh={load} />
            </div>
          )}
          {tab === 'router'    && <RouterTestPanel />}
          {tab === 'executor'  && <ExecutorTestPanel />}
          {tab === 'tools'     && <ToolsPanel />}
          {tab === 'llm'       && <LlmManagerPanel />}
          {tab === 'memory'    && <MemoryPanel />}
          {tab === 'analytics' && <AgentAnalyticsPage />}
        </div>
      </div>

      {showCreate && (
        <CreateAgentModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
        />
      )}
    </div>
  );
}
