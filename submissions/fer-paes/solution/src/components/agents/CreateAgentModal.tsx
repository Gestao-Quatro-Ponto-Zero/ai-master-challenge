import { useState, useEffect } from 'react';
import { X, Bot, Loader2 } from 'lucide-react';
import { createAgent } from '../../services/agentService';
import type { CreateAgentPayload } from '../../services/agentService';
import type { AgentType, LLMProvider } from '../../types';
import { AGENT_TYPES, LLM_PROVIDERS, MODELS_BY_PROVIDER } from './agentConfig';

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

const DEFAULT_FORM: CreateAgentPayload = {
  name: '',
  description: '',
  type: undefined,
  default_model_provider: 'anthropic',
  default_model_name: 'claude-sonnet-4-6',
  temperature: 0.2,
  max_tokens: 2000,
};

export default function CreateAgentModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState<CreateAgentPayload>(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const provider = form.default_model_provider as LLMProvider | undefined;
    if (provider && MODELS_BY_PROVIDER[provider]) {
      setForm((f) => ({ ...f, default_model_name: MODELS_BY_PROVIDER[provider][0] }));
    }
  }, [form.default_model_provider]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) { setError('Agent name is required.'); return; }
    setSaving(true);
    setError('');
    try {
      await createAgent(form);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-white font-semibold text-base">Create Agent</h2>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Name <span className="text-rose-400">*</span></label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Support Agent"
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="What does this agent do?"
              rows={2}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Type</label>
            <select
              value={form.type ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, type: (e.target.value as AgentType) || undefined }))}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
            >
              <option value="">Select type...</option>
              {AGENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Model Provider</label>
              <select
                value={form.default_model_provider ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, default_model_provider: e.target.value as LLMProvider || undefined }))}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
              >
                <option value="">None</option>
                {LLM_PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Model</label>
              <select
                value={form.default_model_name ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, default_model_name: e.target.value || undefined }))}
                disabled={!form.default_model_provider}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors disabled:opacity-40"
              >
                <option value="">Select model...</option>
                {form.default_model_provider &&
                  MODELS_BY_PROVIDER[form.default_model_provider as LLMProvider]?.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Temperature <span className="text-slate-500 font-normal">(0.0 – 1.0)</span>
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={form.temperature}
                onChange={(e) => setForm((f) => ({ ...f, temperature: parseFloat(e.target.value) }))}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Max Tokens</label>
              <input
                type="number"
                step="100"
                min="100"
                max="32000"
                value={form.max_tokens}
                onChange={(e) => setForm((f) => ({ ...f, max_tokens: parseInt(e.target.value) }))}
                className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-lg border border-white/10 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium text-white transition-colors"
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
