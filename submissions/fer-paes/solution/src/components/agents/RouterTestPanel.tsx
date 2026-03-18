import { useState } from 'react';
import { Send, Loader2, CheckCircle2, Circle, ArrowDown, Zap, Brain, Shield, ChevronDown, ChevronRight, Bot, Clock } from 'lucide-react';
import { routeMessage, ruleRouterLocal, ROUTING_RULES } from '../../services/agentRouterService';
import type { RouterResult, RoutingLayer } from '../../types';

interface HistoryEntry {
  message: string;
  result: RouterResult;
  timestamp: Date;
  matchedKeyword?: string;
}

const LAYER_META: Record<RoutingLayer, { label: string; description: string; color: string; icon: React.ComponentType<{ className?: string }> }> = {
  rule: {
    label: 'Rule Router',
    description: 'Keyword matching — fast, no LLM call needed',
    color: 'emerald',
    icon: Zap,
  },
  llm: {
    label: 'LLM Router',
    description: 'AI intent classification using a lightweight model',
    color: 'blue',
    icon: Brain,
  },
  fallback: {
    label: 'Fallback Router',
    description: 'Default routing to triage agent when uncertain',
    color: 'amber',
    icon: Shield,
  },
};

const AGENT_TYPE_LABELS: Record<string, string> = {
  triage_agent: 'Triage Agent',
  support_agent: 'Support Agent',
  technical_agent: 'Technical Agent',
  billing_agent: 'Billing Agent',
  sales_agent: 'Sales Agent',
  qa_agent: 'QA Agent',
};

const AGENT_TYPE_COLORS: Record<string, string> = {
  triage_agent: 'bg-slate-500/15 text-slate-300',
  support_agent: 'bg-blue-500/15 text-blue-300',
  technical_agent: 'bg-orange-500/15 text-orange-300',
  billing_agent: 'bg-emerald-500/15 text-emerald-300',
  sales_agent: 'bg-rose-500/15 text-rose-300',
  qa_agent: 'bg-amber-500/15 text-amber-300',
};

const QUICK_TESTS = [
  { label: 'Refund request', message: 'I need a refund for my last payment' },
  { label: 'Technical issue', message: 'The app keeps crashing on login' },
  { label: 'Pricing inquiry', message: 'What are your enterprise pricing plans?' },
  { label: 'General help', message: 'I need some help with my account' },
  { label: 'Ambiguous', message: 'Hi there' },
];

export default function RouterTestPanel() {
  const [message, setMessage] = useState('');
  const [routing, setRouting] = useState(false);
  const [result, setResult] = useState<RouterResult | null>(null);
  const [matchedKeyword, setMatchedKeyword] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [rulesExpanded, setRulesExpanded] = useState<string | null>('billing_agent');

  async function handleRoute(msg?: string) {
    const text = msg ?? message;
    if (!text.trim()) return;
    setRouting(true);
    setResult(null);
    setError('');
    setMatchedKeyword(null);
    if (msg) setMessage(msg);

    const localCheck = ruleRouterLocal(text);
    if (localCheck) setMatchedKeyword(localCheck.matchedKeyword);

    try {
      const res = await routeMessage({ message: text });
      setResult(res);
      setHistory((h) => [
        { message: text, result: res, timestamp: new Date(), matchedKeyword: localCheck?.matchedKeyword },
        ...h.slice(0, 9),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Routing failed.');
    } finally {
      setRouting(false);
    }
  }

  const layers: RoutingLayer[] = ['rule', 'llm', 'fallback'];
  const activeLayer = result?.routing_layer ?? null;

  return (
    <div className="flex gap-6 p-6 h-full overflow-auto">
      <div className="flex-1 min-w-0 space-y-5">
        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-1">Test Routing</h3>
          <p className="text-xs text-slate-500 mb-4">Send a message to see which agent the router selects.</p>

          <div className="relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleRoute(); } }}
              placeholder="Type a customer message..."
              rows={3}
              className="w-full bg-slate-800 border border-white/8 rounded-xl px-4 py-3 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors resize-none"
            />
            <button
              onClick={() => handleRoute()}
              disabled={routing || !message.trim()}
              className="absolute bottom-3 right-3 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {routing ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" /> : <Send className="w-3.5 h-3.5 text-white" />}
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5 mt-3">
            {QUICK_TESTS.map((qt) => (
              <button
                key={qt.label}
                onClick={() => handleRoute(qt.message)}
                disabled={routing}
                className="px-2.5 py-1 rounded-lg bg-slate-800 border border-white/8 text-xs text-slate-400 hover:text-white hover:bg-slate-700 transition-colors disabled:opacity-40"
              >
                {qt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Routing Pipeline</h3>

          <div className="space-y-2">
            {layers.map((layer, i) => {
              const meta = LAYER_META[layer];
              const Icon = meta.icon;
              const isActive = activeLayer === layer;
              const isPassed = activeLayer !== null && layers.indexOf(activeLayer) > i;
              const isPending = activeLayer === null && !routing;

              return (
                <div key={layer}>
                  <div className={`flex items-center gap-3 p-3.5 rounded-xl border transition-all ${
                    isActive
                      ? `border-${meta.color}-500/30 bg-${meta.color}-500/8`
                      : isPassed
                      ? 'border-white/6 bg-slate-800/30 opacity-50'
                      : 'border-white/6 bg-slate-800/30'
                  }`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                      isActive ? `bg-${meta.color}-500/20` : isPassed ? 'bg-slate-700/40' : 'bg-slate-700/60'
                    }`}>
                      {isPassed ? (
                        <CheckCircle2 className="w-4 h-4 text-slate-500" />
                      ) : routing && !isActive && !isPassed ? (
                        <Circle className="w-4 h-4 text-slate-600" />
                      ) : isActive ? (
                        <Icon className={`w-4 h-4 text-${meta.color}-400`} />
                      ) : (
                        <Icon className="w-4 h-4 text-slate-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={`text-sm font-medium transition-colors ${isActive ? 'text-white' : 'text-slate-400'}`}>
                          {meta.label}
                        </p>
                        {isPassed && (
                          <span className="text-xs text-slate-600 font-mono">skipped</span>
                        )}
                        {isActive && (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-${meta.color}-500/15 text-${meta.color}-400`}>
                            matched
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 mt-0.5">{meta.description}</p>
                    </div>
                  </div>

                  {isActive && result && (
                    <div className={`mx-2 px-4 py-3 rounded-b-xl border-x border-b border-${meta.color}-500/20 bg-${meta.color}-500/5`}>
                      <div className="flex items-center gap-2.5">
                        <Bot className={`w-4 h-4 text-${meta.color}-400 shrink-0`} />
                        <div>
                          <p className="text-xs text-slate-400">Selected agent</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${AGENT_TYPE_COLORS[result.agent_type] ?? 'bg-slate-500/15 text-slate-300'}`}>
                              {AGENT_TYPE_LABELS[result.agent_type] ?? result.agent_type}
                            </span>
                            {result.agent_name && (
                              <span className="text-xs text-slate-500">{result.agent_name}</span>
                            )}
                            {layer === 'rule' && matchedKeyword && (
                              <span className="text-xs text-slate-600">
                                keyword: <span className="text-slate-400 font-mono">"{matchedKeyword}"</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {i < layers.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="w-3 h-3 text-slate-700" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {error && (
            <div className="mt-4 px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
              {error}
            </div>
          )}
        </div>

        {history.length > 0 && (
          <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Recent Routing History</h3>
            <div className="space-y-2">
              {history.map((entry, i) => {
                const layerMeta = LAYER_META[entry.result.routing_layer];
                return (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-800/40 border border-white/6">
                    <div className="shrink-0 mt-0.5">
                      <layerMeta.icon className={`w-3.5 h-3.5 text-${layerMeta.color}-400`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-300 truncate">{entry.message}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`inline-flex px-1.5 py-0.5 rounded text-xs ${AGENT_TYPE_COLORS[entry.result.agent_type] ?? 'bg-slate-500/15 text-slate-300'}`}>
                          {AGENT_TYPE_LABELS[entry.result.agent_type] ?? entry.result.agent_type}
                        </span>
                        <span className="text-xs text-slate-600">via {layerMeta.label}</span>
                        {entry.matchedKeyword && (
                          <span className="text-xs text-slate-600 font-mono">"{entry.matchedKeyword}"</span>
                        )}
                      </div>
                    </div>
                    <div className="shrink-0 flex items-center gap-1 text-xs text-slate-600">
                      <Clock className="w-3 h-3" />
                      {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="w-72 shrink-0 space-y-4">
        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-1">Routing Rules</h3>
          <p className="text-xs text-slate-500 mb-4">Layer 1 keyword rules by agent type.</p>

          <div className="space-y-2">
            {ROUTING_RULES.map((rule) => {
              const expanded = rulesExpanded === rule.agentType;
              return (
                <div key={rule.agentType} className="border border-white/8 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setRulesExpanded(expanded ? null : rule.agentType)}
                    className="w-full flex items-center justify-between px-3.5 py-2.5 hover:bg-white/3 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${AGENT_TYPE_COLORS[rule.agentType] ?? 'bg-slate-500/15 text-slate-300'}`}>
                        {AGENT_TYPE_LABELS[rule.agentType] ?? rule.agentType}
                      </span>
                      <span className="text-xs text-slate-600">{rule.keywords.length} rules</span>
                    </div>
                    {expanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    )}
                  </button>
                  {expanded && (
                    <div className="px-3.5 pb-3 border-t border-white/6 pt-2.5">
                      <div className="flex flex-wrap gap-1">
                        {rule.keywords.map((kw) => (
                          <span key={kw} className="inline-flex px-1.5 py-0.5 rounded bg-slate-800 border border-white/6 text-xs text-slate-400 font-mono">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Pipeline Layers</h3>
          <div className="space-y-3">
            {layers.map((layer) => {
              const meta = LAYER_META[layer];
              const Icon = meta.icon;
              return (
                <div key={layer} className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 mt-0.5 bg-${meta.color}-500/15`}>
                    <Icon className={`w-3 h-3 text-${meta.color}-400`} />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-300">{meta.label}</p>
                    <p className="text-xs text-slate-600 mt-0.5">{meta.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
