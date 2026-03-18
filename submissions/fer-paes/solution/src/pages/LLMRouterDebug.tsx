import { useState, useEffect, useCallback } from 'react';
import { Route, RefreshCw } from 'lucide-react';
import {
  getRouterStatus,
  getActiveModels,
  type RouterStatus,
  type RouterModel,
  type ExecuteResponse,
} from '../services/llmRouterService';
import RouterStatusPanel  from '../components/router/RouterStatusPanel';
import RouterRequestTester from '../components/router/RouterRequestTester';
import RouterLogsViewer   from '../components/router/RouterLogsViewer';

export default function LLMRouterDebug() {
  const [status,   setStatus]   = useState<RouterStatus | null>(null);
  const [models,   setModels]   = useState<RouterModel[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [lastExec, setLastExec] = useState<ExecuteResponse | null>(null);
  const [logKey,   setLogKey]   = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [s, m] = await Promise.all([getRouterStatus(), getActiveModels()]);
      setStatus(s);
      setModels(m);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao acessar o Roteador LLM');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function handleExecuted(result: ExecuteResponse) {
    setLastExec(result);
    setLogKey((k) => k + 1);
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <Route className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Roteador LLM</h1>
              <p className="text-slate-400 text-sm mt-0.5">Seleção de modelo, execução de requisições e pipeline de métricas</p>
            </div>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 border border-white/10 text-slate-300 hover:text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>

        {/* Last execution summary bar */}
        {lastExec && (
          <div className="mt-4 flex items-center gap-6 px-4 py-2.5 bg-slate-900 border border-white/5 rounded-lg text-xs">
            <span className="text-slate-500">Última resposta:</span>
            <span className="text-white font-medium truncate max-w-xs">{lastExec.response.slice(0, 80)}{lastExec.response.length > 80 ? '…' : ''}</span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-400">{lastExec.model}</span>
            <span className="text-slate-600">·</span>
            <span className="text-emerald-400">{lastExec.latency_ms}ms</span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-400">{lastExec.usage.total_tokens} tokens</span>
            {lastExec.fallback && (
              <span className="px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">fallback usado</span>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 px-8 py-6">
        {error && (
          <div className="mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-[320px_1fr] gap-6 h-full">
          {/* Left column — status + tester */}
          <div className="space-y-5">
            <RouterStatusPanel status={status} models={models} loading={loading} />
            <RouterRequestTester models={models} onExecuted={handleExecuted} />
          </div>

          {/* Right column — logs */}
          <RouterLogsViewer key={logKey} />
        </div>
      </div>
    </div>
  );
}
