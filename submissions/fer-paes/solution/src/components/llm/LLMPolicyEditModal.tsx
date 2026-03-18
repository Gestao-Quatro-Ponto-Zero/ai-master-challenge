import { useState } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { updatePolicy, TASK_TYPES, type LLMPolicy, type UpdatePolicyData } from '../../services/promptPolicyService';
import type { RouterModel } from '../../services/llmRouterService';

interface Props {
  policy:  LLMPolicy;
  models:  RouterModel[];
  onSaved: () => void;
  onClose: () => void;
}

export default function LLMPolicyEditModal({ policy, models, onSaved, onClose }: Props) {
  const [form,   setForm]   = useState<UpdatePolicyData>({
    policy_name: policy.policy_name,
    task_type:   policy.task_type,
    model_id:    policy.model_id,
    priority:    policy.priority,
    is_active:   policy.is_active,
  });
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState('');

  function set<K extends keyof UpdatePolicyData>(key: K, value: UpdatePolicyData[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await updatePolicy(policy.id, form);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update policy');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <Save className="w-4 h-4 text-blue-400" />
            <h2 className="text-white font-semibold">Edit Policy</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4">
          {/* Policy name */}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
              Policy Name
            </label>
            <input
              type="text"
              value={form.policy_name ?? ''}
              onChange={(e) => set('policy_name', e.target.value)}
              required
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-slate-600 focus:outline-none focus:border-white/20"
            />
          </div>

          {/* Task type */}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
              Task Type
            </label>
            <select
              value={form.task_type ?? ''}
              onChange={(e) => set('task_type', e.target.value)}
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20"
            >
              {TASK_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
              Model
            </label>
            <select
              value={form.model_id ?? ''}
              onChange={(e) => set('model_id', e.target.value)}
              required
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  [{m.provider}] {m.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
              Priority — <span className="text-white normal-case font-normal">{form.priority} {form.priority === 1 ? '(primary)' : '(fallback)'}</span>
            </label>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={form.priority ?? 1}
              onChange={(e) => set('priority', Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
              <span>1 — primary</span><span>10 — lowest fallback</span>
            </div>
          </div>

          {/* Active toggle */}
          <div className="flex items-center justify-between py-1">
            <div>
              <p className="text-sm text-white font-medium">Active</p>
              <p className="text-xs text-slate-500 mt-0.5">Inactive policies are skipped by the router</p>
            </div>
            <button
              type="button"
              onClick={() => set('is_active', !form.is_active)}
              className={`relative w-10 h-5.5 rounded-full transition-colors focus:outline-none ${form.is_active ? 'bg-emerald-600' : 'bg-slate-700'}`}
              style={{ height: '22px', minWidth: '40px' }}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.is_active ? 'translate-x-[18px]' : 'translate-x-0'}`}
              />
            </button>
          </div>

          {error && (
            <p className="text-red-400 text-sm px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
