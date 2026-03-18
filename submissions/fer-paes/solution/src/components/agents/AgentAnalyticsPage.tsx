import { useState, useEffect, useCallback } from 'react';
import {
  Activity, TrendingUp, Clock, Zap, Cpu, Wrench, CheckCircle2,
  XCircle, RefreshCw, ChevronDown, AlertTriangle, Loader2,
  BarChart3, Bot, Search,
} from 'lucide-react';
import {
  getOverview, getAgentMetrics, getExecutionLogs,
  type ExecutionOverview, type TimelinePoint, type ToolUsageStat,
  type AgentMetricsSummary, type ExecutionLog,
} from '../../services/observabilityService';

const STATUS_STYLES: Record<string, { label: string; cls: string }> = {
  success:   { label: 'Success',   cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  error:     { label: 'Error',     cls: 'text-rose-400    bg-rose-500/10    border-rose-500/20'    },
  timeout:   { label: 'Timeout',   cls: 'text-amber-400  bg-amber-500/10   border-amber-500/20'   },
  cancelled: { label: 'Cancelled', cls: 'text-slate-400  bg-slate-500/10   border-slate-500/20'   },
};

function OverviewCard({ label, value, sub, icon: Icon, color }: {
  label: string; value: string | number; sub?: string;
  icon: React.ComponentType<{ className?: string }>; color: string;
}) {
  return (
    <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-slate-400">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color.replace('text-', 'bg-').replace('-400', '-500/15').replace('-500', '-500/15')}`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
      </div>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function MiniBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  );
}

function TimelineChart({ points, days }: { points: TimelinePoint[]; days: number }) {
  if (!points.length) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
        No data for this period
      </div>
    );
  }

  const maxRuns = Math.max(...points.map((p) => p.total_runs), 1);

  return (
    <div className="flex items-end gap-1.5 h-32 px-1">
      {Array.from({ length: days }, (_, i) => {
        const d = new Date(Date.now() - (days - 1 - i) * 86400000);
        const key = d.toISOString().slice(0, 10);
        const pt = points.find((p) => p.day?.slice(0, 10) === key);
        const total   = pt?.total_runs   ?? 0;
        const success = pt?.success_runs ?? 0;
        const error   = total - success;
        const pct = (total / maxRuns) * 100;
        return (
          <div key={key} className="flex-1 flex flex-col items-center gap-1 group relative">
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {key.slice(5)}: {total} runs ({success} ok)
            </div>
            <div className="w-full flex-1 flex flex-col-reverse gap-px">
              {total > 0 ? (
                <div className="w-full rounded-t overflow-hidden" style={{ height: `${pct}%`, minHeight: 4 }}>
                  <div className="w-full bg-rose-500/60"    style={{ height: `${error > 0 ? (error / total) * 100 : 0}%` }} />
                  <div className="w-full bg-emerald-500/60" style={{ height: `${success > 0 ? (success / total) * 100 : 0}%` }} />
                </div>
              ) : (
                <div className="w-full h-1 rounded bg-slate-800" />
              )}
            </div>
            {i % Math.ceil(days / 7) === 0 && (
              <span className="text-xs text-slate-400 shrink-0">{key.slice(8)}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

type SubTab = 'overview' | 'agents' | 'executions' | 'tools';

export default function AgentAnalyticsPage() {
  const [subTab,      setSubTab]      = useState<SubTab>('overview');
  const [days,        setDays]        = useState(7);
  const [loading,     setLoading]     = useState(true);
  const [overview,    setOverview]    = useState<ExecutionOverview | null>(null);
  const [timeline,    setTimeline]    = useState<TimelinePoint[]>([]);
  const [toolUsage,   setToolUsage]   = useState<ToolUsageStat[]>([]);
  const [agentMets,   setAgentMets]   = useState<AgentMetricsSummary[]>([]);
  const [execLogs,    setExecLogs]    = useState<ExecutionLog[]>([]);
  const [execTotal,   setExecTotal]   = useState(0);
  const [execOffset,  setExecOffset]  = useState(0);
  const [statusFlt,   setStatusFlt]   = useState('');
  const [agentFlt,    setAgentFlt]    = useState('');
  const [search,      setSearch]      = useState('');
  const LIMIT = 50;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (subTab === 'overview') {
        const d = await getOverview(days);
        setOverview(d.overview);
        setTimeline(d.timeline);
        setToolUsage(d.tool_usage);
      } else if (subTab === 'agents') {
        setAgentMets(await getAgentMetrics());
      } else if (subTab === 'executions') {
        const d = await getExecutionLogs({ status: statusFlt || undefined, agent_id: agentFlt || undefined, limit: LIMIT, offset: execOffset });
        setExecLogs(d.executions);
        setExecTotal(d.total);
      } else if (subTab === 'tools') {
        const d = await getOverview(days);
        setToolUsage(d.tool_usage);
      }
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [subTab, days, statusFlt, agentFlt, execOffset]);

  useEffect(() => { load(); }, [load]);

  const fmt = (n: number) => n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K` : String(n);
  const fmtMs = (ms: number) => ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;

  const filteredLogs = search
    ? execLogs.filter((l) => (l.agents?.name ?? '').toLowerCase().includes(search.toLowerCase()) || l.model_name.toLowerCase().includes(search.toLowerCase()) || l.status.includes(search))
    : execLogs;

  const tabs: { id: SubTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'overview',   label: 'Overview',   icon: BarChart3    },
    { id: 'agents',     label: 'Per Agent',  icon: Bot          },
    { id: 'executions', label: 'Exec Logs',  icon: Activity     },
    { id: 'tools',      label: 'Tool Usage', icon: Wrench       },
  ];

  return (
    <div className="px-8 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 bg-slate-800/40 border border-white/6 rounded-xl p-1">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => { setSubTab(id); setExecOffset(0); }}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${subTab === id ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-300 hover:text-white'}`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {(subTab === 'overview' || subTab === 'tools') && (
            <div className="relative">
              <select value={days} onChange={(e) => setDays(Number(e.target.value))}
                className="appearance-none bg-slate-800 border border-white/8 rounded-xl pl-3 pr-8 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors">
                {[1, 7, 14, 30].map((d) => <option key={d} value={d}>Last {d}d</option>)}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
            </div>
          )}
          <button onClick={load} disabled={loading} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading && !overview && subTab === 'overview' ? (
        <div className="flex items-center justify-center py-16"><Loader2 className="w-5 h-5 animate-spin text-slate-400" /></div>
      ) : (
        <>
          {subTab === 'overview' && overview && (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <OverviewCard label="Total Runs"    value={fmt(overview.total_runs)}    sub={`${overview.successful_runs} succeeded`}      icon={Activity}    color="text-white" />
                <OverviewCard label="Success Rate"  value={`${overview.success_rate}%`} sub={`${overview.failed_runs} failed`}             icon={TrendingUp}  color={overview.success_rate >= 90 ? 'text-emerald-400' : overview.success_rate >= 70 ? 'text-amber-400' : 'text-rose-400'} />
                <OverviewCard label="Avg Latency"   value={fmtMs(overview.avg_latency_ms)} sub="per execution"                            icon={Clock}       color="text-blue-400" />
                <OverviewCard label="Total Tokens"  value={fmt(overview.total_tokens)}  sub={`${fmt(overview.input_tokens)} in / ${fmt(overview.output_tokens)} out`} icon={Zap} color="text-amber-400" />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 bg-slate-800/60 border border-white/6 rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white">Daily Executions</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-emerald-500/60 inline-block" />Success</span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-rose-500/60 inline-block" />Error</span>
                    </div>
                  </div>
                  <TimelineChart points={timeline} days={days} />
                </div>

                <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4">Top Tools</h3>
                  {toolUsage.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-24 text-slate-400 text-sm">No tool data</div>
                  ) : (
                    <div className="space-y-3">
                      {toolUsage.slice(0, 6).map((t) => (
                        <div key={t.tool_name}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-slate-400 truncate">{t.tool_name}</span>
                            <span className="text-xs text-slate-400 shrink-0 ml-2">{fmt(t.call_count)} calls</span>
                          </div>
                          <MiniBar pct={t.success_rate} color="bg-emerald-500" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-5 flex flex-col gap-1">
                  <span className="text-xs text-slate-400 mb-1">Tool Calls</span>
                  <p className="text-2xl font-semibold text-white">{fmt(overview.total_tool_calls)}</p>
                  <p className="text-xs text-slate-400">across all executions</p>
                </div>
                <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-5">
                  <span className="text-xs text-slate-400 block mb-3">Status Breakdown</span>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs"><span className="text-emerald-400">Success</span><span className="text-slate-400">{overview.successful_runs}</span></div>
                    <div className="flex justify-between text-xs"><span className="text-rose-400">Error</span><span className="text-slate-400">{overview.failed_runs}</span></div>
                    <div className="mt-2">
                      <MiniBar pct={overview.success_rate} color="bg-emerald-500" />
                    </div>
                  </div>
                </div>
                <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-5">
                  <span className="text-xs text-slate-400 block mb-3">Token Efficiency</span>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between"><span className="text-slate-400">Input</span><span className="text-white">{fmt(overview.input_tokens)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Output</span><span className="text-white">{fmt(overview.output_tokens)}</span></div>
                    <div className="flex justify-between pt-1 border-t border-white/6"><span className="text-slate-400">Ratio</span><span className="text-white">{overview.input_tokens > 0 ? (overview.output_tokens / overview.input_tokens).toFixed(2) : '—'}x</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {subTab === 'agents' && (
            <div className="bg-slate-900/60 border border-white/8 rounded-2xl overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center py-12"><Loader2 className="w-4 h-4 animate-spin text-slate-400" /></div>
              ) : agentMets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-14 text-center">
                  <Bot className="w-10 h-10 text-slate-500 mb-3" />
                  <p className="text-sm text-slate-300">No agent metrics yet — run an agent to see data</p>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/6">
                      {['Agent', 'Type', 'Runs', 'Success Rate', 'Avg Latency', 'P95 Latency', 'Tokens', 'Tool Calls', 'Last Run'].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-medium text-slate-400 first:pl-5 last:pr-5">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/4">
                    {agentMets.map((a) => (
                      <tr key={a.agent_id} className="hover:bg-white/2 transition-colors">
                        <td className="px-4 py-3 pl-5">
                          <p className="text-sm text-white font-medium">{a.agent_name}</p>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs text-slate-400">{a.agent_type?.replace('_', ' ')}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-300">{fmt(a.total_runs)}</td>
                        <td className="px-4 py-3">
                          <div className="w-20">
                            <div className="flex justify-between mb-0.5">
                              <span className={`text-xs font-medium ${a.success_rate >= 90 ? 'text-emerald-400' : a.success_rate >= 70 ? 'text-amber-400' : 'text-rose-400'}`}>{a.success_rate}%</span>
                            </div>
                            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${a.success_rate >= 90 ? 'bg-emerald-500' : a.success_rate >= 70 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${a.success_rate}%` }} />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-300">{fmtMs(a.avg_latency_ms)}</td>
                        <td className="px-4 py-3 text-sm text-slate-300">{fmtMs(a.p95_latency_ms)}</td>
                        <td className="px-4 py-3 text-xs text-slate-400">{fmt(a.total_input_tokens + a.total_output_tokens)}</td>
                        <td className="px-4 py-3 text-sm text-slate-300">{fmt(a.total_tool_calls)}</td>
                        <td className="px-4 py-3 pr-5 text-xs text-slate-400">
                          {a.last_run_at ? new Date(a.last_run_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {subTab === 'executions' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search agent, model…"
                    className="bg-slate-800/60 border border-white/8 rounded-xl pl-8 pr-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors w-48" />
                </div>
                <div className="flex items-center gap-1 bg-slate-800/60 border border-white/8 rounded-xl p-1">
                  {['', 'success', 'error', 'timeout'].map((s) => (
                    <button key={s} onClick={() => { setStatusFlt(s); setExecOffset(0); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${statusFlt === s ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}>
                      {s || 'All'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-slate-900/60 border border-white/8 rounded-2xl overflow-hidden">
                {loading ? (
                  <div className="flex items-center justify-center py-12"><Loader2 className="w-4 h-4 animate-spin text-slate-400" /></div>
                ) : filteredLogs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-14 text-center">
                    <Activity className="w-10 h-10 text-slate-500 mb-3" />
                    <p className="text-sm text-slate-300">No execution logs yet</p>
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/6">
                        {['Time', 'Agent', 'Model', 'Latency', 'Tokens', 'Tools', 'Iters', 'Status'].map((h) => (
                          <th key={h} className="text-left px-4 py-3 text-xs font-medium text-slate-400 first:pl-5 last:pr-5">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/4">
                      {filteredLogs.map((log) => {
                        const st = STATUS_STYLES[log.status] ?? STATUS_STYLES.error;
                        return (
                          <tr key={log.id} className="hover:bg-white/2 transition-colors group">
                            <td className="px-4 py-3 pl-5 text-xs text-slate-400 whitespace-nowrap">
                              {new Date(log.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </td>
                            <td className="px-4 py-3">
                              <p className="text-xs text-white">{log.agents?.name ?? '—'}</p>
                              <p className="text-xs text-slate-400">{log.agents?.type?.replace('_', ' ') ?? ''}</p>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-400 font-mono">{log.model_name || '—'}</td>
                            <td className="px-4 py-3 text-xs text-slate-300">{fmtMs(log.latency_ms)}</td>
                            <td className="px-4 py-3 text-xs text-slate-400">{fmt(log.input_tokens + log.output_tokens)}</td>
                            <td className="px-4 py-3 text-xs text-slate-400">{log.tool_calls_count}</td>
                            <td className="px-4 py-3 text-xs text-slate-400">{log.iterations}</td>
                            <td className="px-4 py-3 pr-5">
                              <div className="flex flex-col gap-0.5">
                                <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-lg border w-fit ${st.cls}`}>
                                  {log.status === 'success' ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                                  {st.label}
                                </span>
                                {log.error_message && (
                                  <p className="text-xs text-rose-500 truncate max-w-32" title={log.error_message}>{log.error_message}</p>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
                {execTotal > LIMIT && (
                  <div className="flex items-center justify-between px-5 py-3 border-t border-white/6">
                    <span className="text-xs text-slate-400">{execOffset + 1}–{Math.min(execOffset + LIMIT, execTotal)} of {execTotal}</span>
                    <div className="flex gap-2">
                      <button disabled={execOffset === 0} onClick={() => setExecOffset((o) => Math.max(0, o - LIMIT))}
                        className="px-3 py-1.5 rounded-lg border border-white/8 text-xs text-slate-400 hover:text-white disabled:opacity-30 transition-colors">Prev</button>
                      <button disabled={execOffset + LIMIT >= execTotal} onClick={() => setExecOffset((o) => o + LIMIT)}
                        className="px-3 py-1.5 rounded-lg border border-white/8 text-xs text-slate-400 hover:text-white disabled:opacity-30 transition-colors">Next</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {subTab === 'tools' && (
            <div className="space-y-4">
              {loading ? (
                <div className="flex items-center justify-center py-12"><Loader2 className="w-4 h-4 animate-spin text-slate-400" /></div>
              ) : toolUsage.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-14 bg-slate-800/30 border border-white/6 rounded-2xl text-center">
                  <Wrench className="w-10 h-10 text-slate-500 mb-3" />
                  <p className="text-sm text-slate-300">No tool calls recorded yet</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Tools Used</p>
                      <p className="text-2xl font-semibold text-white">{toolUsage.length}</p>
                    </div>
                    <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Calls</p>
                      <p className="text-2xl font-semibold text-white">{fmt(toolUsage.reduce((a, t) => a + t.call_count, 0))}</p>
                    </div>
                    <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Overall Success</p>
                      <p className="text-2xl font-semibold text-emerald-400">
                        {toolUsage.length > 0 ? Math.round(toolUsage.reduce((a, t) => a + t.success_rate, 0) / toolUsage.length) : 0}%
                      </p>
                    </div>
                  </div>

                  <div className="bg-slate-900/60 border border-white/8 rounded-2xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/6">
                          {['Tool', 'Calls', 'Success Rate', 'Avg Latency', 'Usage Share'].map((h) => (
                            <th key={h} className="text-left px-5 py-3 text-xs font-medium text-slate-400">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/4">
                        {toolUsage.map((t) => {
                          const maxCalls = toolUsage[0].call_count;
                          const share = Math.round((t.call_count / maxCalls) * 100);
                          return (
                            <tr key={t.tool_name} className="hover:bg-white/2 transition-colors">
                              <td className="px-5 py-3">
                                <div className="flex items-center gap-2">
                                  <div className="w-6 h-6 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center">
                                    <Wrench className="w-3 h-3 text-slate-500" />
                                  </div>
                                  <span className="text-sm text-white font-mono">{t.tool_name}</span>
                                </div>
                              </td>
                              <td className="px-5 py-3 text-sm text-slate-300">{fmt(t.call_count)}</td>
                              <td className="px-5 py-3">
                                <div className="flex items-center gap-2">
                                  <span className={`text-xs font-medium w-10 ${t.success_rate >= 90 ? 'text-emerald-400' : t.success_rate >= 70 ? 'text-amber-400' : 'text-rose-400'}`}>{t.success_rate}%</span>
                                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden w-20">
                                    <div className={`h-full rounded-full ${t.success_rate >= 90 ? 'bg-emerald-500' : t.success_rate >= 70 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${t.success_rate}%` }} />
                                  </div>
                                </div>
                              </td>
                              <td className="px-5 py-3 text-sm text-slate-400">{fmtMs(t.avg_latency)}</td>
                              <td className="px-5 py-3">
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden w-24">
                                    <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${share}%` }} />
                                  </div>
                                  <span className="text-xs text-slate-400 w-8">{share}%</span>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex items-center gap-2 px-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-slate-400" />
                    <p className="text-xs text-slate-400">
                      Tool latency and success data is collected from live agent runs. Data grows as agents execute.
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
