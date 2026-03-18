import { useState, useEffect, useCallback } from 'react';
import {
  Users, Plus, RefreshCw, Loader2, Search, Layers,
  MoreHorizontal, Pencil, Trash2, CheckCircle, Power,
  Wifi, WifiOff, AlertTriangle,
} from 'lucide-react';
import {
  listOperators, updateOperatorStatus, deleteOperator,
  type OperatorRow, type OperatorStatusValue,
} from '../services/operatorService';
import OperatorCreateModal  from '../components/operators/OperatorCreateModal';
import OperatorSkillsEditor from '../components/operators/OperatorSkillsEditor';

const STATUS_CONFIG: Record<OperatorStatusValue, { label: string; dot: string; badge: string }> = {
  online:  { label: 'Online',   dot: 'bg-emerald-400', badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/20' },
  busy:    { label: 'Ocupado',  dot: 'bg-amber-400',   badge: 'bg-amber-500/15   text-amber-300   border-amber-500/20'   },
  away:    { label: 'Ausente',  dot: 'bg-yellow-400',  badge: 'bg-yellow-500/15  text-yellow-300  border-yellow-500/20'  },
  offline: { label: 'Offline',  dot: 'bg-slate-600',   badge: 'bg-slate-700/50   text-slate-500   border-slate-600/30'   },
};

const SKILL_LEVEL_COLORS: Record<number, string> = {
  1: 'bg-slate-700/80 text-slate-400',
  2: 'bg-blue-900/60  text-blue-300',
  3: 'bg-amber-900/60 text-amber-300',
};

function StatusBadge({ status }: { status: OperatorStatusValue }) {
  const c = STATUS_CONFIG[status];
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${c.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </div>
  );
}

function Avatar({ name, email }: { name: string; email: string }) {
  const initials = name
    ? name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
    : (email[0] ?? '?').toUpperCase();
  const colors = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-slate-600'];
  const color  = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-8 h-8 rounded-full ${color} flex items-center justify-center shrink-0`}>
      <span className="text-white text-xs font-semibold">{initials}</span>
    </div>
  );
}

function CapacityBar({ active, max }: { active: number; max: number }) {
  const pct  = max > 0 ? Math.min(100, Math.round((active / max) * 100)) : 0;
  const full  = active >= max;
  const color = full ? 'bg-rose-500' : pct >= 70 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-slate-400 shrink-0">{active}/{max}</span>
    </div>
  );
}

type Filter = OperatorStatusValue | 'all';

export default function Operators() {
  const [operators, setOperators] = useState<OperatorRow[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [search,    setSearch]    = useState('');
  const [filter,    setFilter]    = useState<Filter>('all');
  const [showCreate,    setShowCreate]    = useState(false);
  const [editSkillsFor, setEditSkillsFor] = useState<OperatorRow | null>(null);
  const [actionMenu,    setActionMenu]    = useState<string | null>(null);
  const [updating,      setUpdating]      = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setOperators(await listOperators()); }
    catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    function close() { setActionMenu(null); }
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const filtered = operators.filter((op) => {
    const name  = op.profile?.full_name ?? '';
    const email = op.profile?.email ?? '';
    const matchSearch = !search || [name, email].some((v) =>
      v.toLowerCase().includes(search.toLowerCase()),
    );
    const matchFilter = filter === 'all' || op.status === filter;
    return matchSearch && matchFilter;
  });

  const counts: Record<OperatorStatusValue, number> = operators.reduce(
    (acc, op) => { acc[op.status] = (acc[op.status] ?? 0) + 1; return acc; },
    { online: 0, busy: 0, away: 0, offline: 0 } as Record<OperatorStatusValue, number>,
  );

  async function handleStatusChange(op: OperatorRow, status: OperatorStatusValue) {
    setUpdating(op.id);
    try {
      await updateOperatorStatus(op.id, op.user_id, status);
      await load();
    } catch { } finally { setUpdating(null); setActionMenu(null); }
  }

  async function handleDelete(op: OperatorRow) {
    if (!confirm(`Remover operador ${op.profile?.full_name ?? op.profile?.email}?`)) return;
    setUpdating(op.id);
    try {
      await deleteOperator(op.id);
      await load();
    } catch { } finally { setUpdating(null); setActionMenu(null); }
  }

  const FILTER_OPTS: { value: Filter; label: string }[] = [
    { value: 'all',     label: 'Todos'   },
    { value: 'online',  label: 'Online'  },
    { value: 'busy',    label: 'Ocupado' },
    { value: 'away',    label: 'Ausente' },
    { value: 'offline', label: 'Offline' },
  ];

  const STATUS_ACTIONS: OperatorStatusValue[] = ['online', 'busy', 'away', 'offline'];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/5 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <Users className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Operadores</h1>
              <p className="text-xs text-slate-500">Agentes humanos para atendimento de tickets</p>
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
              Novo Operador
            </button>
          </div>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-4 gap-3">
          {([
            { label: 'Total',    value: operators.length,             icon: Users,         color: 'text-slate-300' },
            { label: 'Online',   value: counts.online,             icon: Wifi,          color: 'text-emerald-400' },
            { label: 'Ocupado',  value: counts.busy,               icon: AlertTriangle, color: 'text-amber-400' },
            { label: 'Offline',  value: counts.offline + counts.away, icon: WifiOff,    color: 'text-slate-600' },
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
            placeholder="Buscar operadores…"
            className="w-full bg-slate-900 border border-white/8 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
          />
        </div>
        <div className="flex gap-1">
          {FILTER_OPTS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                filter === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-500 hover:text-white hover:bg-white/8'
              }`}
            >
              {opt.label}
            </button>
          ))}
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
            <Users className="w-8 h-8 text-slate-700" />
            <p className="text-sm text-slate-600">
              {search || filter !== 'all' ? 'Nenhum operador encontrado.' : 'Nenhum operador ainda. Crie o primeiro.'}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-slate-950/80 backdrop-blur-sm">
              <tr className="border-b border-white/5">
                {['Operador', 'Status', 'Capacidade', 'Habilidades', ''].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium text-slate-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((op) => {
                const isUpdating = updating === op.id;
                const name  = op.profile?.full_name ?? '';
                const email = op.profile?.email ?? '';
                const load  = op.load;
                const active = load?.active_tickets ?? 0;
                const max    = load?.max_tickets ?? op.max_active_tickets;

                return (
                  <tr
                    key={op.id}
                    className="border-b border-white/4 hover:bg-white/2 transition-colors"
                  >
                    {/* Operator */}
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <Avatar name={name} email={email} />
                        <div>
                          <p className="text-sm font-medium text-white">{name || email}</p>
                          {name && <p className="text-xs text-slate-500">{email}</p>}
                        </div>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="px-6 py-3.5">
                      <StatusBadge status={op.status} />
                    </td>

                    {/* Capacity */}
                    <td className="px-6 py-3.5">
                      <CapacityBar active={active} max={max} />
                    </td>

                    {/* Skills */}
                    <td className="px-6 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {(op.skills ?? []).slice(0, 3).map((s) => (
                          <span
                            key={s.id}
                            className={`px-2 py-0.5 rounded-lg text-xs font-medium ${SKILL_LEVEL_COLORS[s.skill_level]}`}
                          >
                            {s.skill_name.replace(/_/g, ' ')}
                          </span>
                        ))}
                        {(op.skills?.length ?? 0) > 3 && (
                          <span className="px-2 py-0.5 rounded-lg text-xs text-slate-600 bg-slate-800">
                            +{(op.skills?.length ?? 0) - 3}
                          </span>
                        )}
                        {(op.skills?.length ?? 0) === 0 && (
                          <span className="text-xs text-slate-700">—</span>
                        )}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-3.5">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditSkillsFor(op)}
                          title="Editar habilidades"
                          className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
                        >
                          <Layers className="w-3.5 h-3.5" />
                        </button>

                        <div className="relative" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setActionMenu((v) => v === op.id ? null : op.id)}
                            disabled={isUpdating}
                            className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
                          >
                            {isUpdating
                              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              : <MoreHorizontal className="w-3.5 h-3.5" />
                            }
                          </button>

                          {actionMenu === op.id && (
                            <div className="absolute right-0 top-full mt-1 w-44 bg-slate-800 border border-white/10 rounded-2xl shadow-xl z-20 overflow-hidden">
                              <div className="px-3 py-2 border-b border-white/6">
                                <p className="text-xs text-slate-500 font-medium">Definir Status</p>
                              </div>
                              {STATUS_ACTIONS.map((s) => {
                                const c = STATUS_CONFIG[s];
                                return (
                                  <button
                                    key={s}
                                    onClick={() => handleStatusChange(op, s)}
                                    className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs transition-colors hover:bg-white/5 ${
                                      op.status === s ? 'text-white font-medium' : 'text-slate-400'
                                    }`}
                                  >
                                    <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
                                    {c.label}
                                    {op.status === s && <CheckCircle className="w-3 h-3 ml-auto text-emerald-400" />}
                                  </button>
                                );
                              })}
                              <div className="border-t border-white/6">
                                <button
                                  onClick={() => setEditSkillsFor(op)}
                                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
                                >
                                  <Pencil className="w-3 h-3" /> Editar Habilidades
                                </button>
                                <button
                                  onClick={() => handleDelete(op)}
                                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-rose-400 hover:bg-rose-500/10 transition-colors"
                                >
                                  <Trash2 className="w-3 h-3" /> Remover Operador
                                </button>
                              </div>
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => handleStatusChange(op, op.status === 'online' ? 'offline' : 'online')}
                          title={op.status === 'online' ? 'Definir offline' : 'Definir online'}
                          disabled={isUpdating}
                          className={`p-1.5 rounded-xl transition-colors disabled:opacity-40 ${
                            op.status === 'online'
                              ? 'text-emerald-400 hover:bg-emerald-500/10'
                              : 'text-slate-600 hover:text-emerald-400 hover:bg-white/8'
                          }`}
                        >
                          <Power className="w-3.5 h-3.5" />
                        </button>
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
        <OperatorCreateModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
        />
      )}

      {editSkillsFor && (
        <OperatorSkillsEditor
          operator={editSkillsFor}
          onClose={() => setEditSkillsFor(null)}
          onSaved={() => { setEditSkillsFor(null); load(); }}
        />
      )}
    </div>
  );
}
