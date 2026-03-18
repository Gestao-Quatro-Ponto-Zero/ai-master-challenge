import { useState, useEffect } from 'react';
import { X, Loader2, Users, Search } from 'lucide-react';
import {
  getQueueOperators, replaceQueueOperators, listOperatorsForQueue,
  type Queue,
} from '../../services/queueService';

interface OperatorOption {
  id:      string;
  status:  string;
  profile: { full_name: string; email: string } | null;
}

interface Props {
  queue:   Queue;
  onClose: () => void;
  onSaved: () => void;
}

const STATUS_DOT: Record<string, string> = {
  online:  'bg-emerald-400',
  busy:    'bg-amber-400',
  away:    'bg-yellow-400',
  offline: 'bg-slate-600',
};

function Avatar({ name, email }: { name: string; email: string }) {
  const initials = name
    ? name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
    : (email[0] ?? '?').toUpperCase();
  const colors = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-slate-600'];
  const color  = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-7 h-7 rounded-full ${color} flex items-center justify-center shrink-0`}>
      <span className="text-white text-xs font-semibold">{initials}</span>
    </div>
  );
}

export default function QueueOperatorsEditor({ queue, onClose, onSaved }: Props) {
  const [allOps,   setAllOps]   = useState<OperatorOption[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search,   setSearch]   = useState('');
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [error,    setError]    = useState('');

  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const [ops, assigned] = await Promise.all([
          listOperatorsForQueue(),
          getQueueOperators(queue.id),
        ]);
        setAllOps(ops);
        setSelected(new Set(assigned.map((a) => a.operator_id)));
      } catch { } finally { setLoading(false); }
    }
    init();
  }, [queue.id]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleSave() {
    setSaving(true);
    setError('');
    try {
      await replaceQueueOperators(queue.id, Array.from(selected));
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save operators.');
    } finally {
      setSaving(false);
    }
  }

  const filtered = allOps.filter((op) => {
    const name  = op.profile?.full_name ?? '';
    const email = op.profile?.email     ?? '';
    return !search || [name, email].some((v) => v.toLowerCase().includes(search.toLowerCase()));
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md shadow-2xl flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-600/15 flex items-center justify-center">
              <Users className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Manage Operators</h2>
              <p className="text-xs text-slate-500">{queue.name.replace(/_/g, ' ')}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-4 py-3 border-b border-white/6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600 pointer-events-none" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter operators…"
              className="w-full bg-slate-800 border border-white/8 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-xs text-slate-600 text-center py-10">
              {allOps.length === 0 ? 'No operators available.' : 'No operators match your search.'}
            </p>
          ) : (
            filtered.map((op) => {
              const name    = op.profile?.full_name ?? '';
              const email   = op.profile?.email     ?? '';
              const checked = selected.has(op.id);
              return (
                <label
                  key={op.id}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                    checked ? 'bg-blue-600/12' : 'hover:bg-white/4'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(op.id)}
                    className="sr-only"
                  />
                  <div className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                    checked ? 'bg-blue-600 border-blue-600' : 'border-slate-600'
                  }`}>
                    {checked && (
                      <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 10 10">
                        <path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>
                  <Avatar name={name} email={email} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{name || email}</p>
                    {name && <p className="text-xs text-slate-600 truncate">{email}</p>}
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[op.status] ?? 'bg-slate-600'}`} />
                    <span className="text-xs text-slate-600 capitalize">{op.status}</span>
                  </div>
                </label>
              );
            })
          )}
        </div>

        <div className="px-6 py-4 border-t border-white/8">
          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 mb-3">
              {error}
            </p>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-600">{selected.size} operator{selected.size !== 1 ? 's' : ''} selected</span>
            <div className="flex items-center gap-2">
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500 disabled:opacity-50 transition-colors"
              >
                {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
