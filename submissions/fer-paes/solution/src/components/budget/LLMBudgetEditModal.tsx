import { useState } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { updateBudget, type LLMBudget, type UpdateBudgetData } from '../../services/budgetManagerService';

interface Props {
  budget:  LLMBudget;
  onSaved: () => void;
  onClose: () => void;
}

export default function LLMBudgetEditModal({ budget, onSaved, onClose }: Props) {
  const [form,    setForm]    = useState<UpdateBudgetData>({
    name:            budget.name,
    monthly_budget:  budget.monthly_budget,
    token_limit:     budget.token_limit,
    period_start:    budget.period_start.slice(0, 10),
    period_end:      budget.period_end.slice(0, 10),
    alert_threshold: budget.alert_threshold,
    is_active:       budget.is_active,
  });
  const [noLimit, setNoLimit] = useState({
    cost:   budget.monthly_budget == null,
    tokens: budget.token_limit    == null,
  });
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState('');

  function set<K extends keyof UpdateBudgetData>(key: K, value: UpdateBudgetData[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await updateBudget(budget.id, {
        ...form,
        monthly_budget: noLimit.cost   ? null : form.monthly_budget,
        token_limit:    noLimit.tokens ? null : form.token_limit,
      });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update budget');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <Save className="w-4 h-4 text-blue-400" />
            <h2 className="text-white font-semibold">Edit Budget</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Budget Name</label>
            <input
              type="text"
              value={form.name ?? ''}
              onChange={(e) => set('name', e.target.value)}
              required
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-slate-600 focus:outline-none focus:border-white/20"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Period Start</label>
              <input
                type="date"
                value={(form.period_start ?? '').slice(0, 10)}
                onChange={(e) => set('period_start', e.target.value)}
                required
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Period End</label>
              <input
                type="date"
                value={(form.period_end ?? '').slice(0, 10)}
                onChange={(e) => set('period_end', e.target.value)}
                required
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Monthly Cost Cap (USD)</label>
              <label className="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer select-none">
                <input type="checkbox" checked={noLimit.cost} onChange={(e) => setNoLimit((s) => ({ ...s, cost: e.target.checked }))} className="rounded accent-emerald-500" />
                Unlimited
              </label>
            </div>
            <input
              type="number" min={0} step={0.01}
              disabled={noLimit.cost}
              value={noLimit.cost ? '' : (form.monthly_budget ?? '')}
              onChange={(e) => set('monthly_budget', e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20 disabled:opacity-40 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Token Limit</label>
              <label className="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer select-none">
                <input type="checkbox" checked={noLimit.tokens} onChange={(e) => setNoLimit((s) => ({ ...s, tokens: e.target.checked }))} className="rounded accent-emerald-500" />
                Unlimited
              </label>
            </div>
            <input
              type="number" min={0} step={1000}
              disabled={noLimit.tokens}
              value={noLimit.tokens ? '' : (form.token_limit ?? '')}
              onChange={(e) => set('token_limit', e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/20 disabled:opacity-40 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">
              Alert Threshold — <span className="text-white normal-case font-normal">{Math.round((form.alert_threshold ?? 0.8) * 100)}%</span>
            </label>
            <input
              type="range" min={10} max={100} step={5}
              value={Math.round((form.alert_threshold ?? 0.8) * 100)}
              onChange={(e) => set('alert_threshold', Number(e.target.value) / 100)}
              className="w-full accent-amber-500"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
              <span>10%</span><span>Alert fires here</span><span>100%</span>
            </div>
          </div>

          <div className="flex items-center justify-between py-1">
            <div>
              <p className="text-sm text-white font-medium">Active</p>
              <p className="text-xs text-slate-500 mt-0.5">Inactive budgets are ignored by the router</p>
            </div>
            <button
              type="button"
              onClick={() => set('is_active', !form.is_active)}
              className={`relative rounded-full transition-colors focus:outline-none ${form.is_active ? 'bg-emerald-600' : 'bg-slate-700'}`}
              style={{ width: '40px', height: '22px' }}
            >
              <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.is_active ? 'translate-x-[18px]' : 'translate-x-0'}`} />
            </button>
          </div>

          {error && (
            <p className="text-red-400 text-sm px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors">Cancel</button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
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
