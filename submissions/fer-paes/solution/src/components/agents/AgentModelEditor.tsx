import { useState, useEffect } from 'react';
import { X, Cpu, Loader2 } from 'lucide-react';
import { setAgentModel, updateAgent } from '../../services/agentService';
import type { AgentWithRelations, LLMProvider } from '../../types';
import { LLM_PROVIDERS, MODELS_BY_PROVIDER } from './agentConfig';

interface Props {
  agent: AgentWithRelations;
  onClose: () => void;
  onUpdated: () => void;
}

export default function AgentModelEditor({ agent, onClose, onUpdated }: Props) {
  const [provider, setProvider] = useState<LLMProvider>(
    (agent.default_model_provider as LLMProvider) || 'anthropic'
  );
  const [modelName, setModelName] = useState(agent.default_model_name || '');
  const [temperature, setTemperature] = useState(agent.temperature ?? 0.2);
  const [maxTokens, setMaxTokens] = useState(agent.max_tokens ?? 2000);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (provider && MODELS_BY_PROVIDER[provider]) {
      setModelName(MODELS_BY_PROVIDER[provider][0]);
    }
  }, [provider]);

  async function handleSave() {
    if (!modelName) { setError('Select a model.'); return; }
    setSaving(true);
    setError('');
    try {
      await setAgentModel(agent.id, { provider, model_name: modelName, temperature, max_tokens: maxTokens });
      await updateAgent(agent.id, { temperature, max_tokens: maxTokens });
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save model config.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-sm shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-600/20 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-base">Configure Model</h2>
              <p className="text-xs text-slate-500 mt-0.5">{agent.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as LLMProvider)}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
            >
              {LLM_PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Model</label>
            <select
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
            >
              {MODELS_BY_PROVIDER[provider]?.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Max Tokens</label>
              <input
                type="number"
                step="100"
                min="100"
                max="32000"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-lg border border-white/10 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium text-white transition-colors"
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
