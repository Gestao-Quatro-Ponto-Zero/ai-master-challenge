import { useState, useEffect, useCallback } from 'react';
import {
  Play, Loader2, ChevronDown, ChevronRight, Bot, User, Wrench,
  Terminal, CheckCircle2, XCircle, Clock, Cpu, Zap, RefreshCw,
  MessageSquare, Hash, Copy, Check,
} from 'lucide-react';
import { getAgents } from '../../services/agentService';
import { executeAgent, getAgentRuns, getAgentRunWithMessages } from '../../services/agentExecutorService';
import { routeMessage } from '../../services/agentRouterService';
import type { AgentWithRelations, AgentRun, AgentRunWithMessages, ExecuteAgentResult, AgentMessageRole } from '../../types';

const ROLE_META: Record<AgentMessageRole, { label: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }> = {
  system: { label: 'System', icon: Terminal, color: 'text-slate-400', bg: 'bg-slate-800/60' },
  user: { label: 'User', icon: User, color: 'text-blue-400', bg: 'bg-blue-500/8' },
  assistant: { label: 'Assistant', icon: Bot, color: 'text-emerald-400', bg: 'bg-emerald-500/8' },
  tool: { label: 'Tool', icon: Wrench, color: 'text-amber-400', bg: 'bg-amber-500/8' },
};

const STATUS_META: Record<string, { label: string; color: string; icon: React.ComponentType<{ className?: string }> }> = {
  running: { label: 'Running', color: 'text-blue-400', icon: Loader2 },
  completed: { label: 'Completed', color: 'text-emerald-400', icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'text-rose-400', icon: XCircle },
  pending: { label: 'Pending', color: 'text-slate-400', icon: Clock },
  cancelled: { label: 'Cancelled', color: 'text-slate-500', icon: XCircle },
};

const AGENT_TYPE_COLORS: Record<string, string> = {
  triage_agent: 'bg-slate-500/15 text-slate-300',
  support_agent: 'bg-blue-500/15 text-blue-300',
  technical_agent: 'bg-orange-500/15 text-orange-300',
  billing_agent: 'bg-emerald-500/15 text-emerald-300',
  sales_agent: 'bg-rose-500/15 text-rose-300',
  qa_agent: 'bg-amber-500/15 text-amber-300',
};

const QUICK_MESSAGES = [
  'I need a refund for my last invoice',
  'The app crashes when I try to log in',
  'What are your enterprise pricing plans?',
  'How do I reset my password?',
  'My subscription was charged twice',
];

function durationMs(run: AgentRun): string {
  if (!run.finished_at) return '—';
  const ms = new Date(run.finished_at).getTime() - new Date(run.started_at).getTime();
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      className="p-1 rounded hover:bg-white/8 text-slate-600 hover:text-slate-400 transition-colors"
    >
      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

function RunMessages({ run }: { run: AgentRunWithMessages }) {
  const [showSystem, setShowSystem] = useState(false);
  const visible = run.messages.filter((m) => showSystem || m.role !== 'system');

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-slate-500">{run.messages.length} messages</p>
        <button
          onClick={() => setShowSystem((s) => !s)}
          className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
        >
          {showSystem ? 'Hide' : 'Show'} system prompt
        </button>
      </div>

      {visible.map((msg) => {
        const meta = ROLE_META[msg.role];
        const Icon = meta.icon;
        const toolName = msg.metadata?.tool_name;

        return (
          <div key={msg.id} className={`rounded-xl border border-white/6 ${meta.bg} overflow-hidden`}>
            <div className="flex items-center gap-2 px-3 py-2 border-b border-white/6">
              <Icon className={`w-3.5 h-3.5 ${meta.color} shrink-0`} />
              <span className={`text-xs font-medium ${meta.color}`}>{meta.label}</span>
              {toolName && (
                <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 text-xs font-mono">
                  {toolName}
                </span>
              )}
              <div className="ml-auto">
                <CopyButton text={msg.content ?? ''} />
              </div>
            </div>
            <div className="px-3 py-2.5">
              {msg.role === 'tool' && msg.metadata?.tool_input ? (
                <div className="space-y-1.5">
                  <p className="text-xs text-slate-600 font-medium">Input</p>
                  <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-all">{JSON.stringify(msg.metadata.tool_input, null, 2)}</pre>
                  {msg.metadata?.tool_result !== undefined && (
                    <>
                      <p className="text-xs text-slate-600 font-medium mt-2">Result</p>
                      <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-all">{JSON.stringify(msg.metadata.tool_result, null, 2)}</pre>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {msg.content ?? <span className="italic text-slate-600">empty</span>}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RunRow({ run, agents }: { run: AgentRun; agents: AgentWithRelations[] }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<AgentRunWithMessages | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const statusMeta = STATUS_META[run.status] ?? STATUS_META.pending;
  const StatusIcon = statusMeta.icon;
  const agent = agents.find((a) => a.id === run.agent_id);

  async function handleExpand() {
    if (expanded) { setExpanded(false); return; }
    setExpanded(true);
    if (!detail) {
      setLoadingDetail(true);
      try { setDetail(await getAgentRunWithMessages(run.id)); } finally { setLoadingDetail(false); }
    }
  }

  return (
    <div className="border border-white/8 rounded-xl overflow-hidden">
      <button onClick={handleExpand} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/3 transition-colors">
        <StatusIcon className={`w-3.5 h-3.5 shrink-0 ${statusMeta.color} ${run.status === 'running' ? 'animate-spin' : ''}`} />
        <div className="flex-1 min-w-0 text-left">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-300 truncate">
              {agent?.name ?? 'Unknown agent'}
            </span>
            {agent?.type && (
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs ${AGENT_TYPE_COLORS[agent.type] ?? 'bg-slate-500/15 text-slate-400'}`}>
                {agent.type}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="text-xs text-slate-600 font-mono">{run.model_name}</span>
            {(run.input_tokens ?? 0) > 0 && (
              <span className="text-xs text-slate-600">{((run.input_tokens ?? 0) + (run.output_tokens ?? 0)).toLocaleString()} tokens</span>
            )}
            <span className="text-xs text-slate-600">{durationMs(run)}</span>
          </div>
        </div>
        <span className="text-xs text-slate-600 shrink-0">
          {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        {expanded ? <ChevronDown className="w-3.5 h-3.5 text-slate-600 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-white/6">
          {run.error_message && (
            <div className="mt-3 px-3 py-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 font-mono">
              {run.error_message}
            </div>
          )}
          <div className="mt-3">
            {loadingDetail ? (
              <div className="flex items-center gap-2 text-slate-500 text-xs py-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Loading messages...
              </div>
            ) : detail ? (
              <RunMessages run={detail} />
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ExecutorTestPanel() {
  const [agents, setAgents] = useState<AgentWithRelations[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [message, setMessage] = useState('');
  const [ticketId, setTicketId] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<ExecuteAgentResult | null>(null);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'direct' | 'route'>('direct');
  const [loadingRuns, setLoadingRuns] = useState(false);

  const loadAgents = useCallback(async () => {
    try {
      const data = await getAgents();
      setAgents(data);
      const firstActive = data.find((a) => a.status === 'active');
      if (firstActive) setSelectedAgentId(firstActive.id);
    } catch { }
  }, []);

  const loadRuns = useCallback(async () => {
    setLoadingRuns(true);
    try { setRuns(await getAgentRuns(15)); } finally { setLoadingRuns(false); }
  }, []);

  useEffect(() => { loadAgents(); loadRuns(); }, [loadAgents, loadRuns]);

  async function handleExecute(msg?: string) {
    const text = msg ?? message;
    if (!text.trim()) return;
    if (mode === 'direct' && !selectedAgentId) return;
    if (msg) setMessage(msg);
    setExecuting(true);
    setResult(null);
    setError('');

    try {
      let agentId = selectedAgentId;

      if (mode === 'route') {
        const routed = await routeMessage({ message: text, ticket_id: ticketId || undefined });
        if (!routed.agent_id) throw new Error('Router could not select an agent');
        agentId = routed.agent_id;
      }

      const res = await executeAgent({
        agent_id: agentId,
        message: text,
        ticket_id: ticketId || undefined,
      });
      setResult(res);
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setExecuting(false);
    }
  }

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <div className="flex gap-6 p-6 h-full overflow-auto">
      <div className="flex-1 min-w-0 space-y-5">
        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Execute Agent</h3>
              <p className="text-xs text-slate-500 mt-0.5">Run an agent against a message and see the full execution trace.</p>
            </div>
            <div className="flex items-center gap-1 bg-slate-800/60 border border-white/8 rounded-lg p-1">
              {(['direct', 'route'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${mode === m ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >
                  {m === 'direct' ? 'Direct' : 'Route + Execute'}
                </button>
              ))}
            </div>
          </div>

          {mode === 'direct' && (
            <div className="mb-3">
              <label className="block text-xs text-slate-500 mb-1.5">Agent</label>
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
              >
                <option value="">Select an agent…</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name} ({a.type ?? 'no type'})</option>
                ))}
              </select>
            </div>
          )}

          {mode === 'route' && (
            <div className="mb-3 flex items-center gap-2 px-3 py-2.5 rounded-xl bg-blue-500/8 border border-blue-500/15">
              <Zap className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <p className="text-xs text-blue-300">The router will automatically select the best agent for your message.</p>
            </div>
          )}

          <div className="relative mb-2">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleExecute(); } }}
              placeholder="Type a customer message to execute…"
              rows={3}
              className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-3 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors resize-none"
            />
            <button
              onClick={() => handleExecute()}
              disabled={executing || !message.trim() || (mode === 'direct' && !selectedAgentId)}
              className="absolute bottom-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs font-medium text-white"
            >
              {executing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              {executing ? 'Running' : 'Run'}
            </button>
          </div>

          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={() => setShowContext((s) => !s)}
              className="text-xs text-slate-600 hover:text-slate-400 transition-colors flex items-center gap-1"
            >
              {showContext ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              Context (optional)
            </button>
          </div>

          {showContext && (
            <div className="mb-3">
              <label className="block text-xs text-slate-500 mb-1.5">
                <Hash className="w-3 h-3 inline mr-1" />
                Ticket ID
              </label>
              <input
                type="text"
                value={ticketId}
                onChange={(e) => setTicketId(e.target.value)}
                placeholder="Optional ticket UUID for context loading"
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
              />
            </div>
          )}

          <div className="flex flex-wrap gap-1.5">
            {QUICK_MESSAGES.map((qm, i) => (
              <button
                key={i}
                onClick={() => handleExecute(qm)}
                disabled={executing || (mode === 'direct' && !selectedAgentId)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 border border-white/8 text-xs text-slate-400 hover:text-white hover:bg-slate-700 transition-colors disabled:opacity-40"
              >
                {qm.length > 40 ? qm.slice(0, 38) + '…' : qm}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
            {error}
          </div>
        )}

        {executing && (
          <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/15 flex items-center justify-center">
                <Cpu className="w-4 h-4 text-blue-400 animate-pulse" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Executing agent…</p>
                <p className="text-xs text-slate-500 mt-0.5">Loading context → Building prompt → Calling LLM</p>
              </div>
            </div>
            <div className="mt-4 space-y-2">
              {['Loading context', 'Building prompt', 'Calling LLM', 'Finalizing response'].map((step, i) => (
                <div key={step} className="flex items-center gap-2.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${i === 0 ? 'bg-blue-400 animate-pulse' : 'bg-slate-700'}`} />
                  <span className={`text-xs ${i === 0 ? 'text-slate-300' : 'text-slate-600'}`}>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {result && !executing && (
          <div className="bg-slate-900/60 border border-white/8 rounded-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Agent Response</p>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-slate-500">{result.agent_name}</span>
                    <span className="text-xs text-slate-600 font-mono">{result.model_name}</span>
                    <span className="text-xs text-slate-600">{((result.input_tokens ?? 0) + (result.output_tokens ?? 0)).toLocaleString()} tokens</span>
                  </div>
                </div>
              </div>
              <CopyButton text={result.response} />
            </div>

            <div className="px-5 py-4">
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{result.response}</p>
            </div>

            <div className="px-5 py-3 border-t border-white/6 flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <MessageSquare className="w-3 h-3 text-slate-600" />
                <span className="text-xs text-slate-600">Run ID: <span className="font-mono text-slate-500">{result.agent_run_id.slice(0, 8)}…</span></span>
              </div>
              <div className="flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-slate-600" />
                <span className="text-xs text-slate-600">{result.input_tokens} in / {result.output_tokens} out tokens</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="w-80 shrink-0 space-y-4">
        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Recent Runs</h3>
            <button onClick={loadRuns} disabled={loadingRuns} className="p-1.5 rounded-lg hover:bg-white/6 transition-colors text-slate-500 hover:text-white">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingRuns ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {loadingRuns && !runs.length ? (
            <div className="flex items-center gap-2 text-slate-600 text-xs py-4">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Loading runs…
            </div>
          ) : runs.length === 0 ? (
            <p className="text-xs text-slate-600 py-4">No runs yet. Execute an agent to see history.</p>
          ) : (
            <div className="space-y-2">
              {runs.map((run) => (
                <RunRow key={run.id} run={run} agents={agents} />
              ))}
            </div>
          )}
        </div>

        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Available Tools</h3>
          <div className="space-y-2">
            {[
              { name: 'lookup_customer', desc: 'Find customer by ID or email' },
              { name: 'get_ticket_info', desc: 'Fetch ticket details' },
              { name: 'update_ticket_status', desc: 'Change ticket status' },
              { name: 'add_ticket_note', desc: 'Add internal note to ticket' },
              { name: 'search_knowledge_base', desc: 'Search help articles' },
            ].map((tool) => (
              <div key={tool.name} className="flex items-start gap-2.5">
                <Wrench className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-mono text-slate-300">{tool.name}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{tool.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {selectedAgent && mode === 'direct' && (
          <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Selected Agent</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Name</span>
                <span className="text-xs text-slate-300">{selectedAgent.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Type</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${AGENT_TYPE_COLORS[selectedAgent.type ?? ''] ?? 'bg-slate-500/15 text-slate-400'}`}>
                  {selectedAgent.type ?? '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Model</span>
                <span className="text-xs text-slate-400 font-mono">{selectedAgent.default_model_name ?? 'default'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Status</span>
                <span className={`text-xs font-medium ${selectedAgent.status === 'active' ? 'text-emerald-400' : selectedAgent.status === 'testing' ? 'text-amber-400' : 'text-slate-500'}`}>
                  {selectedAgent.status}
                </span>
              </div>
              {selectedAgent.skills.length > 0 && (
                <div>
                  <span className="text-xs text-slate-500 block mb-1.5">Skills</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedAgent.skills.map((sk) => (
                      <span key={sk.id} className="px-1.5 py-0.5 rounded bg-slate-700/60 border border-white/6 text-xs text-slate-400 font-mono">
                        {sk.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
