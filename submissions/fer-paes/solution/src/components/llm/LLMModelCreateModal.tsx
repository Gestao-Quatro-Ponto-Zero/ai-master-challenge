import { useState } from 'react';
import { X, Cpu } from 'lucide-react';
import { createModel } from '../../services/modelRegistryService';
import type { CreateLLMModelPayload, LLMModelProvider } from '../../types';

const PROVIDERS: { value: LLMModelProvider; label: string }[] = [
  { value: 'openai',    label: 'OpenAI'    },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google',    label: 'Google'    },
  { value: 'mistral',   label: 'Mistral'   },
];

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function LLMModelCreateModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState<CreateLLMModelPayload>({
    name: '',
    provider: 'openai',
    model_identifier: '',
    description: '',
    input_cost_per_1k_tokens: undefined,
    output_cost_per_1k_tokens: undefined,
    max_tokens: undefined,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function set<K extends keyof CreateLLMModelPayload>(key: K, value: CreateLLMModelPayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || !form.model_identifier.trim()) return;
    setSaving(true);
    setError('');
    try {
      await createModel({
        ...form,
        description: form.description || undefined,
      });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-white font-semibold">Register LLM Model</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Model Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => set('name', e.target.value)}
                placeholder="GPT-4o"
                required
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Provider *</label>
              <select
                value={form.provider}
                onChange={(e) => set('provider', e.target.value as LLMModelProvider)}
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              >
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">API Model Identifier *</label>
            <input
              type="text"
              value={form.model_identifier}
              onChange={(e) => set('model_identifier', e.target.value)}
              placeholder="gpt-5.4"
              required
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 font-mono focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="Optional notes about this model"
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Input $/1K tokens</label>
              <input
                type="number"
                step="0.00001"
                min="0"
                value={form.input_cost_per_1k_tokens ?? ''}
                onChange={(e) => set('input_cost_per_1k_tokens', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="0.005"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Output $/1K tokens</label>
              <input
                type="number"
                step="0.00001"
                min="0"
                value={form.output_cost_per_1k_tokens ?? ''}
                onChange={(e) => set('output_cost_per_1k_tokens', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="0.015"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Max Tokens</label>
              <input
                type="number"
                min="1"
                value={form.max_tokens ?? ''}
                onChange={(e) => set('max_tokens', e.target.value ? parseInt(e.target.value, 10) : undefined)}
                placeholder="128000"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !form.name.trim() || !form.model_identifier.trim()}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {saving ? 'Registering...' : 'Register Model'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
