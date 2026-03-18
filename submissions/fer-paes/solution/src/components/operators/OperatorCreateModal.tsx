import { useState, useEffect } from 'react';
import { X, Loader2, UserPlus, Plus, Trash2 } from 'lucide-react';
import {
  createOperator, listUsersWithoutOperator,
  PRESET_SKILLS, SKILL_LEVELS,
} from '../../services/operatorService';

interface SkillEntry { skill_name: string; skill_level: 1 | 2 | 3 }

interface Props {
  onClose:   () => void;
  onCreated: () => void;
}

export default function OperatorCreateModal({ onClose, onCreated }: Props) {
  const [users,        setUsers]        = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [userId,       setUserId]       = useState('');
  const [maxTickets,   setMaxTickets]   = useState(5);
  const [skills,       setSkills]       = useState<SkillEntry[]>([]);
  const [customSkill,  setCustomSkill]  = useState('');
  const [loading,      setLoading]      = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [error,        setError]        = useState('');

  useEffect(() => {
    listUsersWithoutOperator()
      .then(setUsers)
      .finally(() => setLoadingUsers(false));
  }, []);

  function addSkill(name: string) {
    const trimmed = name.trim().toLowerCase().replace(/\s+/g, '_');
    if (!trimmed || skills.some((s) => s.skill_name === trimmed)) return;
    setSkills((prev) => [...prev, { skill_name: trimmed, skill_level: 1 }]);
  }

  function removeSkill(name: string) {
    setSkills((prev) => prev.filter((s) => s.skill_name !== name));
  }

  function setLevel(name: string, level: 1 | 2 | 3) {
    setSkills((prev) =>
      prev.map((s) => (s.skill_name === name ? { ...s, skill_level: level } : s)),
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userId) { setError('Select a user.'); return; }
    setError('');
    setLoading(true);
    try {
      await createOperator({ user_id: userId, max_active_tickets: maxTickets, skills });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create operator.');
    } finally {
      setLoading(false);
    }
  }

  const LEVEL_COLORS: Record<number, string> = {
    1: 'bg-slate-700 text-slate-300',
    2: 'bg-blue-900/60 text-blue-300',
    3: 'bg-amber-900/60 text-amber-300',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <UserPlus className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="text-sm font-semibold text-white">New Operator</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col overflow-hidden">
          <div className="px-6 py-5 space-y-5 overflow-y-auto flex-1">
            {/* User select */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">User</label>
              {loadingUsers ? (
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading users…
                </div>
              ) : users.length === 0 ? (
                <p className="text-xs text-slate-600">All active users are already operators.</p>
              ) : (
                <select
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full bg-slate-800 border border-white/8 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                >
                  <option value="">Select a user…</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name || u.email} {u.full_name ? `(${u.email})` : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Max tickets */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Max active tickets
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range" min={1} max={20} value={maxTickets}
                  onChange={(e) => setMaxTickets(Number(e.target.value))}
                  className="flex-1 accent-blue-500"
                />
                <span className="text-sm font-semibold text-white w-6 text-right tabular-nums">{maxTickets}</span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Operator is marked <span className="text-amber-400">busy</span> when this limit is reached.
              </p>
            </div>

            {/* Skills */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2">Skills</label>

              <div className="flex flex-wrap gap-1.5 mb-3">
                {PRESET_SKILLS.map((s) => {
                  const added = skills.some((sk) => sk.skill_name === s);
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => added ? removeSkill(s) : addSkill(s)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                        added
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                      }`}
                    >
                      {s.replace(/_/g, ' ')}
                    </button>
                  );
                })}
              </div>

              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={customSkill}
                  onChange={(e) => setCustomSkill(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') { e.preventDefault(); addSkill(customSkill); setCustomSkill(''); }
                  }}
                  placeholder="Custom skill…"
                  className="flex-1 bg-slate-800 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
                />
                <button
                  type="button"
                  onClick={() => { addSkill(customSkill); setCustomSkill(''); }}
                  className="p-2 rounded-xl bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              {skills.length > 0 && (
                <div className="space-y-2">
                  {skills.map((s) => (
                    <div key={s.skill_name} className="flex items-center gap-2 bg-slate-800/60 border border-white/6 rounded-xl px-3 py-2">
                      <span className="flex-1 text-xs text-slate-300">{s.skill_name.replace(/_/g, ' ')}</span>
                      <div className="flex gap-1">
                        {SKILL_LEVELS.map((lv) => (
                          <button
                            key={lv.value}
                            type="button"
                            onClick={() => setLevel(s.skill_name, lv.value as 1|2|3)}
                            className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-colors ${
                              s.skill_level === lv.value
                                ? LEVEL_COLORS[lv.value]
                                : 'bg-slate-700/50 text-slate-600 hover:text-slate-400'
                            }`}
                          >
                            {lv.label}
                          </button>
                        ))}
                      </div>
                      <button type="button" onClick={() => removeSkill(s.skill_name)} className="text-slate-600 hover:text-rose-400 transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {error && (
              <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">
                {error}
              </p>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-white/8">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !userId}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Create Operator
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
