import { useState, useEffect, useCallback } from 'react';
import { ClipboardList, Loader2, RefreshCw, ChevronLeft, ChevronRight, AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';
import { getRouterLogs, type RouterLogEntry } from '../../services/llmRouterService';

const STATUS_MAP: Record<string, { icon: typeof CheckCircle; cls: string; label: string }> = {
  success: { icon: CheckCircle, cls: 'text-emerald-400', label: 'Success' },
  error:   { icon: XCircle,     cls: 'text-red-400',     label: 'Error'   },
  pending: { icon: Clock,       cls: 'text-amber-400',   label: 'Pending' },
  timeout: { icon: AlertCircle, cls: 'text-orange-400',  label: 'Timeout' },
};

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  google:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  mistral:   'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

const PAGE_SIZE = 20;

interface ExpandedRow {
  id: string;
}

export default function RouterLogsViewer() {
  const [logs,     setLogs]     = useState<RouterLogEntry[]>([]);
  const [total,    setTotal]    = useState(0);
  const [page,     setPage]     = useState(0);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [expanded, setExpanded] = useState<ExpandedRow | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getRouterLogs(PAGE_SIZE, page * PAGE_SIZE);
      setLogs(result.logs);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function fmtTime(iso: string): string {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  }

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-slate-400" />
          <h3 className="text-white font-semibold text-sm">Router Logs</h3>
          <span className="text-xs text-slate-600">({total.toLocaleString()} total)</span>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-white/10 text-slate-400 hover:text-white text-xs transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mx-5 mt-4 px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading && logs.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : logs.length === 0 ? (
        <div className="py-12 text-center text-slate-600 text-sm">No router requests yet</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Model</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Agent</th>
                <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Tokens</th>
                <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Latency</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map((log) => {
                const statusCfg = STATUS_MAP[log.status] ?? STATUS_MAP.pending;
                const StatusIcon = statusCfg.icon;
                const isOpen = expanded?.id === log.id;

                return (
                  <>
                    <tr
                      key={log.id}
                      onClick={() => setExpanded(isOpen ? null : { id: log.id })}
                      className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          <StatusIcon className={`w-3.5 h-3.5 ${statusCfg.cls}`} />
                          <span className={`text-xs ${statusCfg.cls}`}>{statusCfg.label}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          {log.provider && (
                            <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border capitalize ${PROVIDER_COLORS[log.provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                              {log.provider}
                            </span>
                          )}
                          <code className="text-slate-400 text-xs">{log.model_identifier ?? '—'}</code>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-slate-500 text-xs">
                          {(log.agent as { name?: string } | null)?.name ?? (log.agent_id ? log.agent_id.slice(0, 8) + '…' : '—')}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right tabular-nums text-slate-500 text-xs">
                        {log.total_tokens != null ? log.total_tokens.toLocaleString() : '—'}
                      </td>
                      <td className="px-5 py-3 text-right tabular-nums text-xs">
                        {log.latency_ms != null ? (
                          <span className={log.latency_ms > 5000 ? 'text-amber-400' : 'text-slate-500'}>
                            {log.latency_ms < 1000 ? `${log.latency_ms}ms` : `${(log.latency_ms / 1000).toFixed(1)}s`}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-5 py-3 text-slate-600 text-xs whitespace-nowrap">{fmtTime(log.created_at)}</td>
                    </tr>
                    {isOpen && (
                      <tr key={`${log.id}-detail`} className="bg-slate-800/30">
                        <td colSpan={6} className="px-5 py-3">
                          <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-xs font-mono">
                            <div className="flex gap-2"><span className="text-slate-600 w-28">Request ID</span><span className="text-slate-400">{log.id}</span></div>
                            <div className="flex gap-2"><span className="text-slate-600 w-28">Task type</span><span className="text-slate-400">{(log.metadata as Record<string, unknown> | null)?.task_type as string ?? '—'}</span></div>
                            <div className="flex gap-2"><span className="text-slate-600 w-28">Prompt tokens</span><span className="text-slate-400">{log.prompt_tokens ?? '—'}</span></div>
                            <div className="flex gap-2"><span className="text-slate-600 w-28">Completion tokens</span><span className="text-slate-400">{log.completion_tokens ?? '—'}</span></div>
                            {log.error_message && (
                              <div className="flex gap-2 col-span-2">
                                <span className="text-slate-600 w-28">Error</span>
                                <span className="text-red-400 break-all">{log.error_message}</span>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
          <span className="text-xs text-slate-600">
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded bg-slate-800 border border-white/10 text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded bg-slate-800 border border-white/10 text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
