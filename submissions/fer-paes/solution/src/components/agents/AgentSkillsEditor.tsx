import { useState } from 'react';
import { X, Wrench, Plus, Trash2, Loader2, CheckCircle2 } from 'lucide-react';
import { addAgentSkill, removeAgentSkill } from '../../services/agentService';
import type { AgentWithRelations } from '../../types';
import { ALL_SKILLS } from './agentConfig';

interface Props {
  agent: AgentWithRelations;
  onClose: () => void;
  onUpdated: () => void;
}

export default function AgentSkillsEditor({ agent, onClose, onUpdated }: Props) {
  const [activeSkills, setActiveSkills] = useState<string[]>(agent.skills.map((s) => s.skill_name));
  const [loadingSkill, setLoadingSkill] = useState<string | null>(null);
  const [error, setError] = useState('');

  async function toggleSkill(skillName: string) {
    setLoadingSkill(skillName);
    setError('');
    try {
      if (activeSkills.includes(skillName)) {
        await removeAgentSkill(agent.id, skillName);
        setActiveSkills((prev) => prev.filter((s) => s !== skillName));
      } else {
        await addAgentSkill(agent.id, skillName);
        setActiveSkills((prev) => [...prev, skillName]);
      }
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update skill.');
    } finally {
      setLoadingSkill(null);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center">
              <Wrench className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-base">Manage Skills</h2>
              <p className="text-xs text-slate-500 mt-0.5">{agent.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-2">
          <p className="text-xs text-slate-500 mb-3">Toggle skills to enable or disable capabilities for this agent.</p>
          {ALL_SKILLS.map((skill) => {
            const active = activeSkills.includes(skill.name);
            const loading = loadingSkill === skill.name;
            return (
              <button
                key={skill.name}
                onClick={() => !loading && toggleSkill(skill.name)}
                disabled={loading}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border transition-all text-left ${
                  active
                    ? 'border-emerald-500/30 bg-emerald-500/10'
                    : 'border-white/8 bg-slate-800/50 hover:bg-slate-800 hover:border-white/15'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                  active ? 'bg-emerald-500/20' : 'bg-slate-700/60'
                }`}>
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 text-slate-400 animate-spin" />
                  ) : active ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Plus className="w-3.5 h-3.5 text-slate-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium transition-colors ${active ? 'text-white' : 'text-slate-300'}`}>
                    {skill.label}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5 truncate">{skill.description}</p>
                </div>
                {active && !loading && (
                  <Trash2 className="w-3.5 h-3.5 text-slate-500 hover:text-rose-400 transition-colors shrink-0" />
                )}
              </button>
            );
          })}
        </div>

        {error && (
          <div className="px-6 pb-4">
            <p className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</p>
          </div>
        )}

        <div className="px-6 pb-5">
          <button
            onClick={onClose}
            className="w-full px-4 py-2.5 rounded-lg border border-white/10 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
