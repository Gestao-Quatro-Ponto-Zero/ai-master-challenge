import { useEffect, useState } from 'react';
import { ClipboardList, User, Clock, ChevronDown, ChevronUp, Search } from 'lucide-react';
import { supabase } from '../lib/supabaseClient';
import type { AuditLog } from '../types';

const ACTION_COLORS: Record<string, string> = {
  login: 'bg-green-50 text-green-700 border-green-100',
  logout: 'bg-slate-50 text-slate-600 border-slate-200',
  user_created: 'bg-blue-50 text-blue-700 border-blue-100',
  user_updated: 'bg-amber-50 text-amber-700 border-amber-100',
  user_suspended: 'bg-red-50 text-red-700 border-red-100',
  user_role_changed: 'bg-cyan-50 text-cyan-700 border-cyan-100',
  profile_updated: 'bg-teal-50 text-teal-700 border-teal-100',
  password_changed: 'bg-orange-50 text-orange-700 border-orange-100',
  avatar_updated: 'bg-pink-50 text-pink-700 border-pink-100',
};

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(iso));
}

function ActionBadge({ action }: { action: string }) {
  const classes = ACTION_COLORS[action] ?? 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${classes}`}>
      {action.replace(/_/g, ' ')}
    </span>
  );
}

function MetaExpander({ meta }: { meta: Record<string, unknown> | null }) {
  const [open, setOpen] = useState(false);
  if (!meta || Object.keys(meta).length === 0) return <span className="text-gray-300 text-xs">—</span>;
  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {open ? 'Ocultar' : 'Visualizar'}
      </button>
      {open && (
        <pre className="mt-2 p-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap max-w-xs">
          {JSON.stringify(meta, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function Audit() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    async function fetchLogs() {
      setLoading(true);
      const { data, error } = await supabase
        .from('audit_logs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(200);

      if (!error && data) {
        setLogs(data as AuditLog[]);
      }
      setLoading(false);
    }
    fetchLogs();
  }, []);

  const uniqueActions = [...new Set(logs.map((l) => l.action))].sort();

  const filtered = logs.filter((log) => {
    const matchesAction = !actionFilter || log.action === actionFilter;
    const matchesSearch =
      !search ||
      log.action.includes(search.toLowerCase()) ||
      log.resource.includes(search.toLowerCase()) ||
      (log.resource_id ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (log.user_id ?? '').toLowerCase().includes(search.toLowerCase());
    return matchesAction && matchesSearch;
  });

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="px-8 py-6 border-b border-gray-100 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Log de Auditoria</h1>
              <p className="text-sm text-gray-400">Registro imutável de toda a atividade do sistema</p>
            </div>
          </div>
          <span className="text-xs text-gray-400 bg-gray-50 border border-gray-100 px-3 py-1.5 rounded-full">
            {filtered.length} registros
          </span>
        </div>
      </div>

      <div className="px-8 py-4 border-b border-gray-100 bg-white flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar registros..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
          />
        </div>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="px-3.5 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white transition-all"
        >
          <option value="">Todas as ações</option>
          {uniqueActions.map((a) => (
            <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      <div className="flex-1 px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            Carregando registros de auditoria...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-center">
            <ClipboardList className="w-8 h-8 text-gray-200 mb-2" />
            <p className="text-sm text-gray-400">Nenhum registro de auditoria encontrado</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/70">
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide w-44">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      Data/Hora
                    </div>
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Ação</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Recurso</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5" />
                      Ator
                    </div>
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Metadados</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-5 py-3.5 text-xs text-gray-500 whitespace-nowrap font-mono">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-5 py-3.5">
                      <ActionBadge action={log.action} />
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-gray-700 font-medium">{log.resource}</span>
                      {log.resource_id && (
                        <p className="text-xs text-gray-400 font-mono mt-0.5 truncate max-w-[120px]">
                          {log.resource_id}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      {log.user_id ? (
                        <span className="text-xs font-mono text-gray-500 truncate block max-w-[120px]">
                          {log.user_id}
                        </span>
                      ) : (
                        <span className="text-gray-300 text-xs">sistema</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <MetaExpander meta={log.meta} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
