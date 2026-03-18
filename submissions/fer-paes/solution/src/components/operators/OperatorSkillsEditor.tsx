import { useState } from 'react';
import { X, Loader2, Layers, Plus, Trash2 } from 'lucide-react';
import {
  replaceOperatorSkills, PRESET_SKILLS, SKILL_LEVELS,
  type OperatorRow, type OperatorSkill,
} from '../../services/operatorService';

interface Props {
  operator: OperatorRow;
  onClose:  () => void;
  onSaved:  () => void;
}

type SkillEntry = { skill_name: string; skill_level: 1 | 2 | 3 };

const LEVEL_BADGE: Record<number, { bg: string; label: string }> = {
  1: { bg: 'bg-slate-700 text-slate-300',       label: 'Basic'        },
  2: { bg: 'bg-blue-900/60 text-blue-300',       label: 'Intermediate' },
  3: { bg: 'bg-amber-900/60 text-amber-300',     label: 'Specialist'   },
};

export default function OperatorSkillsEditor({ operator, onClose, onSaved }: Props) {
  const initialSkills: SkillEntry[] = (operator.skills ?? []).map((s: OperatorSkill) => ({
    skill_name:  s.skill_name,
    skill_level: s.skill_level as 1 | 2 | 3,
  }));

  const [skills,      setSkills]      = useState<SkillEntry[]>(initialSkills);
  const [customSkill, setCustomSkill] = useState('');
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState('');

  const name = operator.profile?.full_name || operator.profile?.email || operator.user_id.slice(0, 8);

  function addSkill(raw: string) {
    const trimmed = raw.trim().toLowerCase().replace(/\s+/g, '_');
    if (!trimmed || skills.some((s) => s.skill_name === trimmed)) return;
    setSkills((prev) => [...prev, { skill_name: trimmed, skill_level: 1 }]);
  }

  function removeSkill(name: string) {
    setSkills((prev) => prev.filter((s) => s.skill_name !== name));
  }

  function setLevel(skillName: string, level: 1 | 2 | 3) {
    setSkills((prev) =>
      prev.map((s) => (s.skill_name === skillName ? { ...s, skill_level: level } : s)),
    );
  }

  async function handleSave() {
    setError('');
    setLoading(true);
    try {
      await replaceOperatorSkills(operator.id, skills);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save skills.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md shadow-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-600/15 flex items-center justify-center">
              <Layers className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Edit Skills</h2>
              <p className="text-xs text-slate-500">{name}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5 overflow-y-auto flex-1">
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2">Quick add</p>
            <div className="flex flex-wrap gap-1.5">
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
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={customSkill}
              onChange={(e) => setCustomSkill(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') { e.preventDefault(); addSkill(customSkill); setCustomSkill(''); }
              }}
              placeholder="Add custom skill…"
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

          {skills.length === 0 ? (
            <p className="text-xs text-slate-600 text-center py-4">No skills assigned. Add skills above.</p>
          ) : (
            <div className="space-y-2">
              {skills.map((s) => (
                <div key={s.skill_name} className="flex items-center gap-2 bg-slate-800/60 border border-white/6 rounded-xl px-3 py-2.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-200">{s.skill_name.replace(/_/g, ' ')}</p>
                  </div>
                  <div className="flex gap-1">
                    {SKILL_LEVELS.map((lv) => (
                      <button
                        key={lv.value}
                        type="button"
                        onClick={() => setLevel(s.skill_name, lv.value as 1 | 2 | 3)}
                        className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-colors ${
                          s.skill_level === lv.value
                            ? LEVEL_BADGE[lv.value].bg
                            : 'bg-slate-700/40 text-slate-600 hover:text-slate-300'
                        }`}
                      >
                        {lv.label}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => removeSkill(s.skill_name)}
                    className="text-slate-600 hover:text-rose-400 transition-colors ml-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

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
            type="button"
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500 disabled:opacity-50 transition-colors"
          >
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            Save Skills
          </button>
        </div>
      </div>
    </div>
  );
}
