import { useState } from 'react';
import { Send, Loader2, CheckCircle, AlertCircle, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { testRouter, type RouterModel, type ExecuteResponse } from '../../services/llmRouterService';

function fmtCost(n: number): string {
  if (n >= 0.01)   return `$${n.toFixed(4)}`;
  if (n >= 0.0001) return `$${n.toFixed(6)}`;
  return `$${n.toFixed(8)}`;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  google:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  mistral:   'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

interface Props {
  models: RouterModel[];
  onExecuted?: (result: ExecuteResponse) => void;
}

export default function RouterRequestTester({ models, onExecuted }: Props) {
  const [prompt,    setPrompt]    = useState('');
  const [modelId,   setModelId]   = useState('');
  const [maxTokens, setMaxTokens] = useState(512);
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<ExecuteResponse | null>(null);
  const [error,     setError]     = useState('');
  const [showMeta,  setShowMeta]  = useState(false);

  async function run() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await testRouter(prompt.trim(), modelId || undefined);
      setResult(res);
      onExecuted?.(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) run();
  }

  const selectedModel = models.find((m) => m.id === modelId) ?? null;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Zap className="w-4 h-4 text-amber-400" />
        <h3 className="text-white font-semibold text-sm">Request Tester</h3>
        <span className="ml-auto text-xs text-slate-600">Ctrl+Enter to run</span>
      </div>

      <div className="p-5 space-y-4">
        {/* Model selector */}
        <div>
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Model</label>
          <select
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20"
          >
            <option value="">Auto-select (lowest cost)</option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                [{m.provider}] {m.name}
                {m.input_cost_per_1k_tokens != null
                  ? ` — $${m.input_cost_per_1k_tokens}/1k in`
                  : ''}
              </option>
            ))}
          </select>
          {selectedModel && (
            <p className="text-xs text-slate-600 mt-1">
              <code className="text-slate-400">{selectedModel.model_identifier}</code>
              {' · '}
              <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border capitalize ${PROVIDER_COLORS[selectedModel.provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                {selectedModel.provider}
              </span>
              {selectedModel.max_tokens && ` · ${selectedModel.max_tokens.toLocaleString()} ctx`}
            </p>
          )}
        </div>

        {/* Max tokens */}
        <div>
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
            Max Tokens — <span className="text-white normal-case font-normal">{maxTokens}</span>
          </label>
          <input
            type="range"
            min={64}
            max={4096}
            step={64}
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            className="w-full accent-emerald-500"
          />
          <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
            <span>64</span><span>4096</span>
          </div>
        </div>

        {/* Prompt */}
        <div>
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Enter your prompt here..."
            rows={5}
            className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm placeholder-slate-600 resize-none focus:outline-none focus:border-white/20 font-mono"
          />
        </div>

        <button
          onClick={run}
          disabled={loading || !prompt.trim()}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {loading ? 'Executing…' : 'Execute Prompt'}
        </button>

        {error && (
          <div className="flex items-start gap-2.5 px-3 py-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-red-400 text-sm font-mono break-all">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-3 pt-1">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 text-sm font-medium">Response received</span>
              {result.fallback && (
                <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Fallback used
                </span>
              )}
            </div>

            {/* Response text */}
            <div className="bg-slate-800/60 border border-white/5 rounded-lg p-4">
              <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-mono">{result.response}</p>
            </div>

            {/* Meta row */}
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${PROVIDER_COLORS[result.provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                {result.provider}
              </span>
              <code className="text-xs text-slate-400">{result.model}</code>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-slate-500">{result.latency_ms}ms</span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-slate-500">{result.usage.total_tokens.toLocaleString()} tokens</span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-emerald-400 font-medium">{fmtCost(result.cost.total_cost)}</span>
              <button
                onClick={() => setShowMeta((v) => !v)}
                className="ml-auto flex items-center gap-1 text-xs text-slate-600 hover:text-slate-400 transition-colors"
              >
                {showMeta ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                Details
              </button>
            </div>

            {showMeta && (
              <div className="bg-slate-800/40 border border-white/5 rounded-lg p-3 space-y-2 text-xs text-slate-500 font-mono">
                <div className="grid grid-cols-2 gap-2">
                  <span>Request ID</span><span className="text-slate-400 break-all">{result.request_id}</span>
                  <span>Input tokens</span><span className="text-slate-400">{result.usage.input_tokens}</span>
                  <span>Output tokens</span><span className="text-slate-400">{result.usage.output_tokens}</span>
                  <span>Input cost</span><span className="text-slate-400">{fmtCost(result.cost.input_cost)}</span>
                  <span>Output cost</span><span className="text-slate-400">{fmtCost(result.cost.output_cost)}</span>
                  <span>Stop reason</span><span className="text-slate-400">{result.stop_reason}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
