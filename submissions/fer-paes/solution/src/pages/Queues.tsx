import { useState, useEffect, useCallback } from 'react';
import {
  ListOrdered, Plus, RefreshCw, Loader2, Search, Pencil,
  Trash2, Users, Ticket as TicketIcon, Power, MoreHorizontal,
  CheckCircle, ArrowUpDown, Shuffle, TrendingDown, Brain, User as UserIcon,
} from 'lucide-react';
import {
  listQueues, toggleQueueActive, deleteQueue,
  type QueueWithStats, type Queue, type DistributionStrategy,
} from '../services/queueService';
import QueueCreateModal    from '../components/queues/QueueCreateModal';
import QueueOperatorsEditor from '../components/queues/QueueOperatorsEditor';
import QueueTicketsPanel    from '../components/queues/QueueTicketsPanel';

const STRATEGY_META: Record<DistributionStrategy, { label: string; icon: React.ComponentType<{ className?: string }>; className: string }> = {
  least_loaded: { label: 'Menos Carregado', icon: TrendingDown, className: 'bg-emerald-900/50 text-emerald-300 border-emerald-500/20' },
  round_robin:  { label: 'Round Robin',     icon: Shuffle,      className: 'bg-blue-900/50 text-blue-300 border-blue-500/20'         },
  skill_based:  { label: 'Por Habilidade',  icon: Brain,        className: 'bg-amber-900/50 text-amber-300 border-amber-500/20'       },
  manual:       { label: 'Manual',          icon: UserIcon,     className: 'bg-slate-700/60 text-slate-400 border-slate-600/30'       },
};

function StrategyBadge({ strategy }: { strategy: DistributionStrategy }) {
  const meta = STRATEGY_META[strategy] ?? STRATEGY_META.manual;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${meta.className}`}>
      <Icon className="w-3 h-3" />
      {meta.label}
    </span>
  );
}

const PRIORITY_BADGE: Record<number, { label: string; className: string }> = {
  1: { label: 'Padrão',   className: 'bg-slate-700/60 text-slate-400'       },
  2: { label: 'Alta',     className: 'bg-blue-900/60 text-blue-300'          },
  3: { label: 'Crítica',  className: 'bg-rose-900/60 text-rose-300'          },
};

function PriorityBadge({ priority }: { priority: number }) {
  const cfg = PRIORITY_BADGE[priority] ?? PRIORITY_BADGE[1];
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

export default function Queues() {
  const [queues,       setQueues]       = useState<QueueWithStats[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [search,       setSearch]       = useState('');
  const [showCreate,   setShowCreate]   = useState(false);
  const [editQueue,    setEditQueue]    = useState<Queue | null>(null);
  const [opsQueue,     setOpsQueue]     = useState<Queue | null>(null);
  const [ticketsQueue, setTicketsQueue] = useState<Queue | null>(null);
  const [actionMenu,   setActionMenu]   = useState<string | null>(null);
  const [updating,     setUpdating]     = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setQueues(await listQueues()); }
    catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    function close() { setActionMenu(null); }
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const filtered = queues.filter((q) => {
    if (!search) return true;
    return [q.name, q.description].some((v) =>
      v.toLowerCase().includes(search.toLowerCase()),
    );
  });

  const totalActive   = queues.filter((q) => q.is_active).length;
  const totalWaiting  = queues.reduce((s, q) => s + q.tickets_waiting, 0);
  const totalOps      = queues.reduce((s, q) => s + q.operators_count, 0);

  async function handleToggle(q: QueueWithStats) {
    setUpdating(q.id);
    try { await toggleQueueActive(q.id, !q.is_active); await load(); }
    catch { } finally { setUpdating(null); setActionMenu(null); }
  }

  async function handleDelete(q: QueueWithStats) {
    if (!confirm(`Excluir fila "${q.name.replace(/_/g, ' ')}"? Esta ação não pode ser desfeita.`)) return;
    setUpdating(q.id);
    try { await deleteQueue(q.id); await load(); }
    catch { } finally { setUpdating(null); setActionMenu(null); }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/5 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <ListOrdered className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Filas</h1>
              <p className="text-xs text-slate-500">Organize tickets antes da distribuição</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              disabled={loading}
              className="p-2 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Nova Fila
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3">
          {([
            { label: 'Total de Filas',      value: queues.length,  icon: ListOrdered,  color: 'text-slate-300'   },
            { label: 'Ativas',              value: totalActive,    icon: CheckCircle,  color: 'text-emerald-400' },
            { label: 'Tickets Aguardando',  value: totalWaiting,   icon: TicketIcon,   color: 'text-amber-400'   },
            { label: 'Operadores Vinculados',value: totalOps,      icon: Users,        color: 'text-blue-400'    },
          ] as const).map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-slate-900/60 border border-white/6 rounded-2xl px-4 py-3 flex items-center gap-3">
              <Icon className={`w-4 h-4 shrink-0 ${color}`} />
              <div>
                <p className={`text-xl font-semibold tabular-nums ${color}`}>{value}</p>
                <p className="text-xs text-slate-600">{label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Toolbar */}
      <div className="px-6 py-3 border-b border-white/5 flex items-center gap-3 shrink-0">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600 pointer-events-none" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar filas…"
            className="w-full bg-slate-900 border border-white/8 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
          />
        </div>
        <div className="ml-auto flex items-center gap-1.5 text-xs text-slate-600">
          <ArrowUpDown className="w-3 h-3" />
          Ordenado por prioridade
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <ListOrdered className="w-8 h-8 text-slate-700" />
            <p className="text-sm text-slate-600">
              {search ? 'Nenhuma fila encontrada.' : 'Nenhuma fila ainda. Crie a primeira.'}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-slate-950/80 backdrop-blur-sm">
              <tr className="border-b border-white/5">
                {['Fila', 'Estratégia', 'Prioridade', 'Operadores', 'Aguardando', 'Status', ''].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium text-slate-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((q) => {
                const isUpdating = updating === q.id;
                return (
                  <tr key={q.id} className="border-b border-white/4 hover:bg-white/2 transition-colors">
                    {/* Queue */}
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-white capitalize">
                          {q.name.replace(/_/g, ' ')}
                        </p>
                        {q.description && (
                          <p className="text-xs text-slate-500 mt-0.5 truncate max-w-[220px]">{q.description}</p>
                        )}
                      </div>
                    </td>

                    {/* Strategy */}
                    <td className="px-6 py-4">
                      <StrategyBadge strategy={q.distribution_strategy ?? 'least_loaded'} />
                    </td>

                    {/* Priority */}
                    <td className="px-6 py-4">
                      <PriorityBadge priority={q.priority} />
                    </td>

                    {/* Operators */}
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setOpsQueue(q)}
                        className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors group"
                      >
                        <Users className="w-3.5 h-3.5" />
                        <span className="text-sm tabular-nums">{q.operators_count}</span>
                        <span className="text-xs text-slate-600 group-hover:text-slate-400 transition-colors">
                          {q.operators_count === 1 ? 'operador' : 'operadores'}
                        </span>
                      </button>
                    </td>

                    {/* Waiting */}
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setTicketsQueue(q)}
                        className="flex items-center gap-1.5 transition-colors group"
                      >
                        <TicketIcon className={`w-3.5 h-3.5 ${q.tickets_waiting > 0 ? 'text-amber-400' : 'text-slate-600'}`} />
                        <span className={`text-sm tabular-nums ${q.tickets_waiting > 0 ? 'text-amber-300' : 'text-slate-500'}`}>
                          {q.tickets_waiting}
                        </span>
                        <span className="text-xs text-slate-600 group-hover:text-slate-400 transition-colors">aguardando</span>
                      </button>
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${
                        q.is_active
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/20'
                          : 'bg-slate-700/50 text-slate-500 border-slate-600/30'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${q.is_active ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                        {q.is_active ? 'Ativo' : 'Inativo'}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditQueue(q)}
                          title="Editar fila"
                          className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setOpsQueue(q)}
                          title="Gerenciar operadores"
                          className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
                        >
                          <Users className="w-3.5 h-3.5" />
                        </button>

                        <div className="relative" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setActionMenu((v) => v === q.id ? null : q.id)}
                            disabled={isUpdating}
                            className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
                          >
                            {isUpdating
                              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              : <MoreHorizontal className="w-3.5 h-3.5" />
                            }
                          </button>

                          {actionMenu === q.id && (
                            <div className="absolute right-0 top-full mt-1 w-44 bg-slate-800 border border-white/10 rounded-2xl shadow-xl z-20 overflow-hidden">
                              <button
                                onClick={() => setTicketsQueue(q)}
                                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
                              >
                                <TicketIcon className="w-3.5 h-3.5" /> Ver tickets
                              </button>
                              <button
                                onClick={() => handleToggle(q)}
                                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
                              >
                                <Power className="w-3.5 h-3.5" />
                                {q.is_active ? 'Desativar' : 'Ativar'}
                              </button>
                              <div className="border-t border-white/6">
                                <button
                                  onClick={() => handleDelete(q)}
                                  className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-rose-400 hover:bg-rose-500/10 transition-colors"
                                >
                                  <Trash2 className="w-3.5 h-3.5" /> Excluir fila
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals */}
      {showCreate && (
        <QueueCreateModal
          onClose={() => setShowCreate(false)}
          onSaved={() => { setShowCreate(false); load(); }}
        />
      )}

      {editQueue && (
        <QueueCreateModal
          existing={editQueue}
          onClose={() => setEditQueue(null)}
          onSaved={() => { setEditQueue(null); load(); }}
        />
      )}

      {opsQueue && (
        <QueueOperatorsEditor
          queue={opsQueue}
          onClose={() => setOpsQueue(null)}
          onSaved={() => { setOpsQueue(null); load(); }}
        />
      )}

      {ticketsQueue && (
        <QueueTicketsPanel
          queue={ticketsQueue}
          onClose={() => setTicketsQueue(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}
