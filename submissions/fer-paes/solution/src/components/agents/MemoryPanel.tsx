import { useState, useEffect, useCallback } from 'react';
import {
  Brain, RefreshCw, Trash2, Plus, ChevronDown, Search,
  MessageSquare, Ticket, User, Loader2, X, AlertTriangle,
  Cpu, Wrench, Eye, CheckCircle2, Clock,
} from 'lucide-react';
import {
  getMemoryStats, listMemories, deleteMemory, createMemory, getScratchpads,
  type AgentMemory, type MemoryStats, type ScratchpadStep,
} from '../../services/memoryService';

const TYPE_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }> = {
  conversation: { label: 'Conversation', icon: MessageSquare, color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/20' },
  ticket:       { label: 'Ticket',       icon: Ticket,        color: 'text-amber-400',  bg: 'bg-amber-500/10 border-amber-500/20' },
  customer:     { label: 'Customer',     icon: User,          color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
};

const STEP_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  memory_load: { label: 'Memory Load', icon: Brain,          color: 'text-blue-400' },
  thought:     { label: 'Thought',     icon: Brain,          color: 'text-slate-400' },
  tool_call:   { label: 'Tool Call',   icon: Wrench,         color: 'text-amber-400' },
  tool_result: { label: 'Tool Result', icon: CheckCircle2,   color: 'text-emerald-400' },
  observation: { label: 'Observation', icon: Eye,            color: 'text-cyan-400' },
};

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number; icon: React.ComponentType<{ className?: string }>; color: string;
}) {
  return (
    <div className="bg-slate-800/60 border border-white/6 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${color}`}>{value.toLocaleString()}</p>
    </div>
  );
}

interface CreateModalProps {
  onClose: () => void;
  onCreated: () => void;
}
function CreateModal({ onClose, onCreated }: CreateModalProps) {
  const [type,    setType]    = useState<'conversation' | 'ticket' | 'customer'>('customer');
  const [content, setContent] = useState('');
  const [custId,  setCustId]  = useState('');
  const [tickId,  setTickId]  = useState('');
  const [convId,  setConvId]  = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  async function handle(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true); setError('');
    try {
      await createMemory({
        memory_type:     type,
        content:         content.trim(),
        customer_id:     custId.trim() || undefined,
        ticket_id:       tickId.trim() || undefined,
        conversation_id: convId.trim() || undefined,
      });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed');
    } finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center">
              <Plus className="w-4 h-4 text-emerald-400" />
            </div>
            <h2 className="text-sm font-semibold text-white">New Memory</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={handle} className="p-6 space-y-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">Memory Type</label>
            <div className="relative">
              <select value={type} onChange={(e) => setType(e.target.value as typeof type)}
                className="w-full appearance-none bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors">
                {Object.entries(TYPE_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">Content</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={4} placeholder="Memory content…"
              className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Customer ID', val: custId, set: setCustId, placeholder: 'uuid…' },
              { label: 'Ticket ID',   val: tickId, set: setTickId, placeholder: 'uuid…' },
              { label: 'Conv. ID',    val: convId, set: setConvId, placeholder: 'uuid…' },
            ].map(({ label, val, set, placeholder }) => (
              <div key={label}>
                <label className="block text-xs text-slate-500 mb-1.5">{label}</label>
                <input value={val} onChange={(e) => set(e.target.value)} placeholder={placeholder}
                  className="w-full bg-slate-800 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors font-mono" />
              </div>
            ))}
          </div>
          {error && <p className="text-xs text-rose-400">{error}</p>}
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 rounded-xl border border-white/8 text-slate-400 hover:text-white text-sm transition-colors">Cancel</button>
            <button type="submit" disabled={loading || !content.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-sm font-medium transition-colors">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              Save Memory
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ScratchpadViewer() {
  const [runId,   setRunId]   = useState('');
  const [steps,   setSteps]   = useState<ScratchpadStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  async function load() {
    if (!runId.trim()) return;
    setLoading(true); setError('');
    try {
      const { scratchpads } = await getScratchpads(runId.trim());
      setSteps(scratchpads);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed');
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <input value={runId} onChange={(e) => setRunId(e.target.value)} placeholder="Enter agent run ID (UUID)…"
          className="flex-1 bg-slate-800 border border-white/8 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors font-mono"
          onKeyDown={(e) => e.key === 'Enter' && load()} />
        <button onClick={load} disabled={loading || !runId.trim()}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium transition-colors flex items-center gap-2">
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
          Load
        </button>
      </div>

      {error && <p className="text-xs text-rose-400 px-1">{error}</p>}

      {steps.length > 0 && (
        <div className="space-y-2">
          {steps.map((step) => {
            const cfg = STEP_CONFIG[step.step_type] ?? STEP_CONFIG.thought;
            const Icon = cfg.icon;
            return (
              <div key={step.id} className="flex gap-3 group">
                <div className="flex flex-col items-center">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-slate-800 border border-white/8`}>
                    <Icon className={`w-3.5 h-3.5 ${cfg.color}`} />
                  </div>
                  <div className="w-px flex-1 bg-white/6 mt-1" />
                </div>
                <div className="flex-1 pb-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-xs text-slate-600">Step {step.step}</span>
                    <span className="text-xs text-slate-700 ml-auto">
                      {new Date(step.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="bg-slate-800/60 border border-white/6 rounded-xl px-4 py-3">
                    <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap">{step.content}</p>
                    {Object.keys(step.metadata ?? {}).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-slate-600 cursor-pointer hover:text-slate-400">metadata</summary>
                        <pre className="text-xs text-slate-600 mt-1 overflow-x-auto">{JSON.stringify(step.metadata, null, 2)}</pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {steps.length === 0 && !loading && runId && (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Cpu className="w-8 h-8 text-slate-700 mb-2" />
          <p className="text-sm text-slate-500">No scratchpad steps found for this run</p>
        </div>
      )}

      {!runId && (
        <div className="flex flex-col items-center justify-center py-10 text-center bg-slate-800/30 border border-white/6 rounded-2xl">
          <Brain className="w-8 h-8 text-slate-700 mb-2" />
          <p className="text-sm text-slate-500">Enter a run ID to inspect the agent scratchpad</p>
          <p className="text-xs text-slate-600 mt-1">Find run IDs in the Executor tab after running an agent</p>
        </div>
      )}
    </div>
  );
}

type SubTab = 'memories' | 'scratchpad';

export default function MemoryPanel() {
  const [subTab,      setSubTab]      = useState<SubTab>('memories');
  const [stats,       setStats]       = useState<MemoryStats | null>(null);
  const [memories,    setMemories]    = useState<AgentMemory[]>([]);
  const [total,       setTotal]       = useState(0);
  const [loading,     setLoading]     = useState(true);
  const [typeFilter,  setTypeFilter]  = useState('');
  const [search,      setSearch]      = useState('');
  const [showCreate,  setShowCreate]  = useState(false);
  const [deleting,    setDeleting]    = useState<string | null>(null);
  const [offset,      setOffset]      = useState(0);
  const LIMIT = 50;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, m] = await Promise.all([
        getMemoryStats(),
        listMemories({ memory_type: typeFilter || undefined, limit: LIMIT, offset }),
      ]);
      setStats(s);
      setMemories(m.memories);
      setTotal(m.total);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [typeFilter, offset]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(id: string) {
    setDeleting(id);
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      setTotal((t) => t - 1);
      setStats((s) => s ? { ...s, stats: { ...s.stats } } : s);
    } catch { /* ignore */ } finally { setDeleting(null); }
  }

  const filtered = search
    ? memories.filter((m) => m.content.toLowerCase().includes(search.toLowerCase()) || (m.customers?.name ?? '').toLowerCase().includes(search.toLowerCase()))
    : memories;

  return (
    <div className="px-8 py-6 space-y-6">
      <div className="grid grid-cols-5 gap-4">
        <StatCard label="Conversation"   value={stats?.stats.conversation   ?? 0} icon={MessageSquare} color="text-blue-400" />
        <StatCard label="Ticket"         value={stats?.stats.ticket         ?? 0} icon={Ticket}        color="text-amber-400" />
        <StatCard label="Customer"       value={stats?.stats.customer       ?? 0} icon={User}          color="text-emerald-400" />
        <StatCard label="Total Memories" value={Object.values(stats?.stats ?? {}).reduce((a, b) => a + b, 0)} icon={Brain} color="text-white" />
        <StatCard label="Scratchpad Steps" value={stats?.scratchpad_steps ?? 0} icon={Cpu} color="text-slate-400" />
      </div>

      <div className="flex items-center gap-1 bg-slate-800/40 border border-white/6 rounded-xl p-1 w-fit">
        {(['memories', 'scratchpad'] as SubTab[]).map((t) => (
          <button key={t} onClick={() => setSubTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${subTab === t ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}>
            {t === 'memories' ? 'Memory Store' : 'Scratchpad Viewer'}
          </button>
        ))}
      </div>

      {subTab === 'memories' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search memories…"
                className="w-full bg-slate-800/60 border border-white/8 rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors" />
            </div>
            <div className="flex items-center gap-1 bg-slate-800/60 border border-white/8 rounded-xl p-1">
              <button onClick={() => { setTypeFilter(''); setOffset(0); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${!typeFilter ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}>All</button>
              {Object.entries(TYPE_CONFIG).map(([k, v]) => {
                const Icon = v.icon;
                return (
                  <button key={k} onClick={() => { setTypeFilter(k); setOffset(0); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${typeFilter === k ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}>
                    <Icon className="w-3 h-3" />{v.label}
                  </button>
                );
              })}
            </div>
            <button onClick={load} disabled={loading} className="p-2 rounded-xl text-slate-500 hover:text-white hover:bg-white/8 transition-colors">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors">
              <Plus className="w-3.5 h-3.5" /> Add Memory
            </button>
          </div>

          {loading && !memories.length ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-14 bg-slate-800/30 border border-white/6 rounded-2xl text-center">
              <Brain className="w-10 h-10 text-slate-700 mb-3" />
              <p className="text-sm text-slate-500">No memories stored yet</p>
              <p className="text-xs text-slate-600 mt-1">Memories are created automatically when agents complete runs</p>
            </div>
          ) : (
            <div className="bg-slate-900/60 border border-white/8 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/6">
                    {['Type', 'Content', 'Customer', 'Context', 'Updated', ''].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-slate-500 first:pl-5 last:pr-5">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/4">
                  {filtered.map((mem) => {
                    const cfg = TYPE_CONFIG[mem.memory_type];
                    const Icon = cfg?.icon ?? Brain;
                    return (
                      <tr key={mem.id} className="hover:bg-white/2 transition-colors group">
                        <td className="px-4 py-3 pl-5">
                          <span className={`flex items-center gap-1.5 text-xs font-medium ${cfg?.color ?? 'text-slate-400'} ${cfg?.bg ?? ''} border px-2 py-0.5 rounded-lg w-fit`}>
                            <Icon className="w-3 h-3" />{cfg?.label ?? mem.memory_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 max-w-xs">
                          <p className="text-xs text-slate-300 line-clamp-2">{mem.content}</p>
                        </td>
                        <td className="px-4 py-3">
                          {mem.customers ? (
                            <div>
                              <p className="text-xs text-slate-300">{mem.customers.name}</p>
                              <p className="text-xs text-slate-600">{mem.customers.email}</p>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-700">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="space-y-0.5 text-xs text-slate-600 font-mono">
                            {mem.ticket_id       && <p>ticket: {mem.ticket_id.substring(0, 8)}…</p>}
                            {mem.conversation_id && <p>conv: {mem.conversation_id.substring(0, 8)}…</p>}
                            {mem.agents?.name    && <p className="text-slate-500">by {mem.agents.name}</p>}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs text-slate-600">
                            {new Date(mem.updated_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </td>
                        <td className="px-4 py-3 pr-5">
                          <button onClick={() => handleDelete(mem.id)} disabled={deleting === mem.id}
                            className="p-1.5 rounded-lg text-slate-700 hover:text-rose-400 hover:bg-rose-500/10 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-40">
                            {deleting === mem.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {total > LIMIT && (
                <div className="flex items-center justify-between px-5 py-3 border-t border-white/6">
                  <span className="text-xs text-slate-600">{offset + 1}–{Math.min(offset + LIMIT, total)} of {total}</span>
                  <div className="flex gap-2">
                    <button disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
                      className="px-3 py-1.5 rounded-lg border border-white/8 text-xs text-slate-400 hover:text-white disabled:opacity-30 transition-colors">Prev</button>
                    <button disabled={offset + LIMIT >= total} onClick={() => setOffset((o) => o + LIMIT)}
                      className="px-3 py-1.5 rounded-lg border border-white/8 text-xs text-slate-400 hover:text-white disabled:opacity-30 transition-colors">Next</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {total > 0 && (
            <div className="flex items-center gap-2 px-1">
              <AlertTriangle className="w-3.5 h-3.5 text-slate-600" />
              <p className="text-xs text-slate-600">
                Memories grow with each agent run. Future versions will add summarization and pruning to manage size.
              </p>
            </div>
          )}
        </div>
      )}

      {subTab === 'scratchpad' && (
        <div className="max-w-2xl">
          <div className="bg-slate-800/40 border border-white/8 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-8 h-8 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center">
                <Clock className="w-4 h-4 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Scratchpad Viewer</h3>
                <p className="text-xs text-slate-500">Inspect step-by-step reasoning and tool calls for a specific agent run</p>
              </div>
            </div>
            <ScratchpadViewer />
          </div>
        </div>
      )}

      {showCreate && (
        <CreateModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); load(); }} />
      )}
    </div>
  );
}
