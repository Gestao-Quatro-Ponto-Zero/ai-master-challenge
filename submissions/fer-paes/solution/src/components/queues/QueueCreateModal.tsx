import { useState } from 'react';
import { X, Loader2, ListOrdered, Shuffle, TrendingDown, Brain, User } from 'lucide-react';
import {
  createQueue, updateQueue,
  type Queue, type DistributionStrategy,
} from '../../services/queueService';

interface Props {
  existing?: Queue;
  onClose:   () => void;
  onSaved:   () => void;
}

const STRATEGY_OPTS: {
  value:   DistributionStrategy;
  label:   string;
  desc:    string;
  icon:    React.ComponentType<{ className?: string }>;
  color:   string;
  active:  string;
}[] = [
  {
    value:  'least_loaded',
    label:  'Least Loaded',
    desc:   'Operator with fewest active tickets',
    icon:   TrendingDown,
    color:  'text-emerald-400',
    active: 'border-emerald-500/60 bg-emerald-600/12',
  },
  {
    value:  'round_robin',
    label:  'Round Robin',
    desc:   'Sequential rotation across operators',
    icon:   Shuffle,
    color:  'text-blue-400',
    active: 'border-blue-500/60 bg-blue-600/12',
  },
  {
    value:  'skill_based',
    label:  'Skill Based',
    desc:   'Match ticket topic to operator skills',
    icon:   Brain,
    color:  'text-amber-400',
    active: 'border-amber-500/60 bg-amber-600/12',
  },
  {
    value:  'manual',
    label:  'Manual',
    desc:   'Supervisor assigns each ticket',
    icon:   User,
    color:  'text-slate-400',
    active: 'border-slate-500/60 bg-slate-700/40',
  },
];

const PRIORITY_OPTS = [
  { value: 1, label: 'Standard', desc: 'Normal flow' },
  { value: 2, label: 'High',     desc: 'Prioritised' },
  { value: 3, label: 'Critical', desc: 'Processed first' },
];

export default function QueueCreateModal({ existing, onClose, onSaved }: Props) {
  const [name,     setName]     = useState(existing?.name.replace(/_/g, ' ') ?? '');
  const [desc,     setDesc]     = useState(existing?.description ?? '');
  const [priority, setPriority] = useState(existing?.priority ?? 1);
  const [strategy, setStrategy] = useState<DistributionStrategy>(
    existing?.distribution_strategy ?? 'least_loaded',
  );
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  const isEdit = !!existing;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError('Name is required.'); return; }
    setError('');
    setLoading(true);
    try {
      if (isEdit) {
        await updateQueue(existing.id, { name, description: desc, priority, distribution_strategy: strategy });
      } else {
        await createQueue({ name, description: desc, priority, distribution_strategy: strategy });
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save queue.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-y-auto max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <ListOrdered className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-sm font-semibold text-white">{isEdit ? 'Edit Queue' : 'New Queue'}</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Queue name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Technical Support"
              className="w-full bg-slate-800 border border-white/8 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
            <p className="text-xs text-slate-700 mt-1">
              Stored as: <span className="text-slate-500">{name.trim().toLowerCase().replace(/\s+/g, '_') || '…'}</span>
            </p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={2}
              placeholder="Brief description of this queue's purpose…"
              className="w-full bg-slate-800 border border-white/8 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors resize-none"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Priority</label>
            <div className="grid grid-cols-3 gap-2">
              {PRIORITY_OPTS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setPriority(opt.value)}
                  className={`flex flex-col items-center gap-1 px-3 py-3 rounded-xl border text-center transition-colors ${
                    priority === opt.value
                      ? 'border-blue-500/60 bg-blue-600/15 text-white'
                      : 'border-white/8 bg-slate-800 text-slate-500 hover:border-white/15 hover:text-slate-300'
                  }`}
                >
                  <span className="text-xs font-semibold">{opt.label}</span>
                  <span className={`text-xs ${priority === opt.value ? 'text-slate-400' : 'text-slate-700'}`}>{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Distribution Strategy */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Distribution strategy</label>
            <div className="grid grid-cols-2 gap-2">
              {STRATEGY_OPTS.map((opt) => {
                const Icon    = opt.icon;
                const isSelected = strategy === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setStrategy(opt.value)}
                    className={`flex items-start gap-3 px-3.5 py-3 rounded-xl border text-left transition-colors ${
                      isSelected
                        ? opt.active + ' text-white'
                        : 'border-white/8 bg-slate-800 text-slate-500 hover:border-white/15 hover:text-slate-300'
                    }`}
                  >
                    <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${isSelected ? opt.color : 'text-slate-600'}`} />
                    <div>
                      <p className={`text-xs font-semibold ${isSelected ? 'text-white' : ''}`}>{opt.label}</p>
                      <p className={`text-xs mt-0.5 ${isSelected ? 'text-slate-400' : 'text-slate-700'}`}>{opt.desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex items-center justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-50 transition-colors"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {isEdit ? 'Save Changes' : 'Create Queue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
