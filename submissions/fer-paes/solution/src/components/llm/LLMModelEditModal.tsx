import { useState } from 'react';
import { X, Pencil } from 'lucide-react';
import { updateModel } from '../../services/modelRegistryService';
import type { LLMModel, UpdateLLMModelPayload } from '../../types';

interface Props {
  model: LLMModel;
  onClose: () => void;
  onUpdated: () => void;
}

export default function LLMModelEditModal({ model, onClose, onUpdated }: Props) {
  const [form, setForm] = useState<UpdateLLMModelPayload>({
    name: model.name,
    description: model.description ?? '',
    input_cost_per_1k_tokens: model.input_cost_per_1k_tokens ?? undefined,
    output_cost_per_1k_tokens: model.output_cost_per_1k_tokens ?? undefined,
    max_tokens: model.max_tokens ?? undefined,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function set<K extends keyof UpdateLLMModelPayload>(key: K, value: UpdateLLMModelPayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name?.trim()) return;
    setSaving(true);
    setError('');
    try {
      await updateModel(model.id, {
        ...form,
        description: form.description || undefined,
      });
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update model.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <Pencil className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold">Edit Model</h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">{model.model_identifier}</p>
            </div>
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

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Model Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              required
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="Optional notes"
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
              disabled={saving || !form.name?.trim()}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
