import { useState, useEffect, useCallback } from 'react';
import {
  Cpu, CheckCircle2, XCircle, Send, Loader2, RefreshCw,
  BarChart2, Zap, DollarSign, AlertTriangle, Clock,
  ChevronDown, ArrowRightLeft, Activity,
} from 'lucide-react';
import {
  getProviders, getModels, getUsageStats, getUsageLogs, testModel,
  type ProviderConfig, type ModelConfig, type UsageStats, type UsageLog,
} from '../../services/llmService';

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: 'text-amber-400',
  openai:    'text-emerald-400',
  google:    'text-blue-400',
};
const PROVIDER_BG: Record<string, string> = {
  anthropic: 'bg-amber-500/10 border-amber-500/20',
  openai:    'bg-emerald-500/10 border-emerald-500/20',
  google:    'bg-blue-500/10 border-blue-500/20',
};

function ProviderCard({ provider }: { provider: ProviderConfig }) {
  const color = PROVIDER_COLORS[provider.id] ?? 'text-slate-400';
  const bg    = PROVIDER_BG[provider.id]    ?? 'bg-slate-500/10 border-slate-500/20';

  return (
    <div className={`border rounded-2xl p-5 ${bg}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className={`text-base font-semibold ${color}`}>{provider.name}</p>
          <p className="text-xs text-slate-500 mt-0.5">{provider.models.length} models available</p>
        </div>
        {provider.available ? (
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 rounded-lg">
            <CheckCircle2 className="w-3 h-3" /> Configured
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-500/10 border border-slate-500/20 px-2 py-1 rounded-lg">
            <XCircle className="w-3 h-3" /> No API Key
          </span>
        )}
      </div>
      <div className="space-y-1.5">
        {provider.models.slice(0, 3).map((m) => (
          <div key={m.id} className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono truncate">{m.id}</span>
            <span className="text-slate-600 shrink-0 ml-2">${(m.cost_per_input_token * 1_000_000).toFixed(2)}/1M in</span>
          </div>
        ))}
        {provider.models.length > 3 && (
          <p className="text-xs text-slate-600">+{provider.models.length - 3} more models</p>
        )}
      </div>
    </div>
  );
}

function UsageStat({ icon: Icon, label, value, sub, color = 'text-white' }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-slate-800/60 border border-white/6 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-slate-500" />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function TestPanel({ providers, models }: { providers: ProviderConfig[]; models: ModelConfig[] }) {
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel]       = useState('');
  const [message, setMessage]   = useState('');
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState<{ response: string; provider: string; model: string; usage: { input_tokens: number; output_tokens: number }; fallback: boolean } | null>(null);
  const [error, setError]       = useState('');

  const availableModels = models.filter((m) => m.provider === provider);

  useEffect(() => {
    const first = availableModels[0]?.id ?? '';
    setModel(first);
  }, [provider]);

  async function handleTest(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim() || !model) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await testModel(provider, model, message.trim());
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test failed');
    } finally {
      setLoading(false);
    }
  }

  const configuredProviders = providers.filter((p) => p.available);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">Provider</label>
          <div className="relative">
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full appearance-none bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
            >
              {configuredProviders.length > 0 ? (
                configuredProviders.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))
              ) : (
                providers.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))
              )}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">Model</label>
          <div className="relative">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full appearance-none bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
            >
              {availableModels.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>
        </div>
      </div>

      <form onSubmit={handleTest} className="space-y-3">
        <div className="relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a test message…"
            rows={3}
            className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !message.trim() || !model}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          {loading ? 'Calling model…' : 'Send Test'}
        </button>
      </form>

      {error && (
        <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
          {error}
        </div>
      )}

      {result && (
        <div className="border border-white/8 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800/60 border-b border-white/6">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className={PROVIDER_COLORS[result.provider] ?? 'text-slate-400'}>{result.provider}</span>
              <span className="text-slate-700">/</span>
              <span className="font-mono">{result.model}</span>
              {result.fallback && (
                <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-md">
                  <ArrowRightLeft className="w-2.5 h-2.5" /> Fallback used
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-600">
              <span>{result.usage.input_tokens} in</span>
              <span>{result.usage.output_tokens} out</span>
            </div>
          </div>
          <div className="px-4 py-4">
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{result.response}</p>
          </div>
        </div>
      )}
    </div>
  );
}

const STATUS_STYLE: Record<string, string> = {
  success:  'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  error:    'text-rose-400 bg-rose-500/10 border-rose-500/20',
  fallback: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
};

function LogsTable({ logs, loading }: { logs: UsageLog[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <Activity className="w-8 h-8 text-slate-700 mb-2" />
        <p className="text-sm text-slate-500">No usage logs yet</p>
        <p className="text-xs text-slate-600 mt-1">Logs appear after agents make LLM calls</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/6">
            {['Provider / Model', 'Tokens', 'Cost', 'Latency', 'Status', 'Time'].map((h) => (
              <th key={h} className="text-left px-3 py-2.5 text-xs font-medium text-slate-500 first:pl-0 last:pr-0">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/4">
          {logs.map((log) => (
            <tr key={log.id} className="hover:bg-white/2 transition-colors">
              <td className="px-3 py-3 first:pl-0">
                <div>
                  <span className={`text-xs font-medium ${PROVIDER_COLORS[log.provider] ?? 'text-slate-400'}`}>
                    {log.provider}
                  </span>
                  <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-[180px]">{log.model_name}</p>
                  {log.fallback_from && (
                    <p className="text-xs text-amber-500 mt-0.5 flex items-center gap-1">
                      <ArrowRightLeft className="w-2.5 h-2.5" /> from {log.fallback_from.split('/')[0]}
                    </p>
                  )}
                </div>
              </td>
              <td className="px-3 py-3">
                <div className="text-xs">
                  <span className="text-slate-400">{(log.input_tokens + log.output_tokens).toLocaleString()}</span>
                  <p className="text-slate-600">{log.input_tokens}↑ {log.output_tokens}↓</p>
                </div>
              </td>
              <td className="px-3 py-3">
                <span className="text-xs text-slate-400">${Number(log.total_cost).toFixed(6)}</span>
              </td>
              <td className="px-3 py-3">
                <span className="text-xs text-slate-500">{log.latency_ms}ms</span>
              </td>
              <td className="px-3 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-md border ${STATUS_STYLE[log.status] ?? 'text-slate-400'}`}>
                  {log.status}
                </span>
                {log.error_message && (
                  <p className="text-xs text-rose-400 mt-0.5 truncate max-w-[120px]" title={log.error_message}>{log.error_message}</p>
                )}
              </td>
              <td className="px-3 py-3 last:pr-0">
                <span className="text-xs text-slate-600">
                  {new Date(log.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type SubTab = 'overview' | 'test' | 'logs';

export default function LlmManagerPanel() {
  const [subTab,     setSubTab]     = useState<SubTab>('overview');
  const [providers,  setProviders]  = useState<ProviderConfig[]>([]);
  const [models,     setModels]     = useState<ModelConfig[]>([]);
  const [stats,      setStats]      = useState<UsageStats | null>(null);
  const [logs,       setLogs]       = useState<UsageLog[]>([]);
  const [range,      setRange]      = useState<'1d' | '7d' | '30d'>('30d');
  const [loadingP,   setLoadingP]   = useState(true);
  const [loadingS,   setLoadingS]   = useState(true);
  const [loadingL,   setLoadingL]   = useState(false);

  const loadProviders = useCallback(async () => {
    setLoadingP(true);
    try {
      const [p, m] = await Promise.all([getProviders(), getModels()]);
      setProviders(p);
      setModels(m);
    } catch { /* ignore */ } finally {
      setLoadingP(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    setLoadingS(true);
    try {
      const s = await getUsageStats(range);
      setStats(s);
    } catch { /* ignore */ } finally {
      setLoadingS(false);
    }
  }, [range]);

  const loadLogs = useCallback(async () => {
    setLoadingL(true);
    try {
      const { logs: l } = await getUsageLogs(100);
      setLogs(l);
    } catch { /* ignore */ } finally {
      setLoadingL(false);
    }
  }, []);

  useEffect(() => { loadProviders(); }, [loadProviders]);
  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { if (subTab === 'logs') loadLogs(); }, [subTab, loadLogs]);

  const configuredCount = providers.filter((p) => p.available).length;
  const totalModels     = models.length;

  const FALLBACK_CHAINS: Record<string, string[]> = {
    anthropic: ['OpenAI', 'Google'],
    openai:    ['Anthropic', 'Google'],
    google:    ['Anthropic', 'OpenAI'],
  };

  return (
    <div className="px-8 py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <UsageStat icon={Cpu}        label="Providers"       value={`${configuredCount}/${providers.length}`} sub="configured"          color="text-white" />
        <UsageStat icon={Zap}        label="Total Models"    value={totalModels}                               sub="across all providers" color="text-white" />
        <UsageStat icon={BarChart2}  label="Total Calls"     value={(stats?.totalCalls ?? 0).toLocaleString()} sub={`last ${range}`}     color={stats?.totalCalls ? 'text-blue-400' : 'text-slate-500'} />
        <UsageStat icon={DollarSign} label="Total Cost"      value={`$${(stats?.totalCost ?? 0).toFixed(4)}`} sub={`last ${range}`}     color={stats?.totalCost ? 'text-emerald-400' : 'text-slate-500'} />
      </div>

      <div className="flex items-center gap-1 bg-slate-800/40 border border-white/6 rounded-xl p-1 w-fit">
        {(['overview', 'test', 'logs'] as SubTab[]).map((t) => (
          <button
            key={t}
            onClick={() => setSubTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              subTab === t ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            {t === 'overview' ? 'Providers' : t === 'test' ? 'Test Model' : 'Usage Logs'}
          </button>
        ))}
      </div>

      {subTab === 'overview' && (
        <div className="space-y-6">
          {loadingP ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4">
                {providers.map((p) => <ProviderCard key={p.id} provider={p} />)}
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <ArrowRightLeft className="w-4 h-4 text-slate-500" />
                  Automatic Fallback Chains
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(FALLBACK_CHAINS).map(([primary, chain]) => (
                    <div key={primary} className="bg-slate-800/40 border border-white/6 rounded-xl p-4">
                      <p className={`text-xs font-semibold uppercase tracking-wider mb-3 ${PROVIDER_COLORS[primary] ?? 'text-slate-400'}`}>
                        {primary}
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
                            <span className="text-emerald-400 text-xs font-bold">1</span>
                          </div>
                          <span className="text-xs text-slate-300 font-medium capitalize">{primary}</span>
                          <span className="text-xs text-slate-600">(primary)</span>
                        </div>
                        {chain.map((fb, i) => (
                          <div key={fb} className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded-full bg-slate-700 border border-white/8 flex items-center justify-center shrink-0">
                              <span className="text-slate-400 text-xs font-bold">{i + 2}</span>
                            </div>
                            <span className="text-xs text-slate-400">{fb}</span>
                            <span className="text-xs text-slate-600">(fallback {i + 1})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-slate-500" />
                    Usage by Provider
                  </h3>
                  <div className="flex items-center gap-1 bg-slate-800 border border-white/6 rounded-lg p-1">
                    {(['1d', '7d', '30d'] as const).map((r) => (
                      <button
                        key={r}
                        onClick={() => setRange(r)}
                        className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${range === r ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                      >
                        {r}
                      </button>
                    ))}
                    <button onClick={loadStats} disabled={loadingS} className="p-1 rounded-md text-slate-600 hover:text-white transition-colors">
                      <RefreshCw className={`w-3 h-3 ${loadingS ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>

                {stats && Object.keys(stats.summary).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(stats.summary).map(([prov, s]) => {
                      const pct = stats.totalCalls > 0 ? Math.round((s.calls / stats.totalCalls) * 100) : 0;
                      return (
                        <div key={prov} className="bg-slate-800/40 border border-white/6 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className={`text-sm font-medium capitalize ${PROVIDER_COLORS[prov] ?? 'text-slate-400'}`}>{prov}</span>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span>{s.calls} calls ({pct}%)</span>
                              <span>{(s.input_tokens + s.output_tokens).toLocaleString()} tokens</span>
                              <span className="text-emerald-400">${s.total_cost.toFixed(6)}</span>
                              {s.errors > 0 && (
                                <span className="text-rose-400 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" /> {s.errors} errors
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                prov === 'anthropic' ? 'bg-amber-500' :
                                prov === 'openai'    ? 'bg-emerald-500' : 'bg-blue-500'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 bg-slate-800/30 border border-white/6 rounded-2xl text-center">
                    <BarChart2 className="w-8 h-8 text-slate-700 mb-2" />
                    <p className="text-sm text-slate-500">No usage data for this period</p>
                    <p className="text-xs text-slate-600 mt-1">Usage logs appear after agents make LLM calls</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {subTab === 'test' && (
        <div className="max-w-2xl">
          <div className="bg-slate-800/40 border border-white/8 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                <Send className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Test a Model</h3>
                <p className="text-xs text-slate-500">Send a test message to verify provider connectivity and fallback behavior</p>
              </div>
            </div>
            <TestPanel providers={providers} models={models} />
          </div>
        </div>
      )}

      {subTab === 'logs' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-white">Usage Logs</h3>
              <span className="text-xs text-slate-600">({logs.length} records)</span>
            </div>
            <button onClick={loadLogs} disabled={loadingL} className="p-1.5 rounded-lg hover:bg-white/6 text-slate-500 hover:text-white transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingL ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
            <LogsTable logs={logs} loading={loadingL} />
          </div>
        </div>
      )}
    </div>
  );
}
