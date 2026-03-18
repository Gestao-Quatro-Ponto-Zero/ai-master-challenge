import { useState } from 'react';
import { MoreHorizontal, Power, Wrench, Cpu, Thermometer, ChevronDown } from 'lucide-react';
import { setAgentStatus } from '../../services/agentService';
import type { AgentWithRelations, AgentStatus, AgentType, LLMProvider } from '../../types';
import { AGENT_TYPE_COLORS, PROVIDER_COLORS } from './agentConfig';
import AgentSkillsEditor from './AgentSkillsEditor';
import AgentModelEditor from './AgentModelEditor';

const STATUS_STYLES: Record<AgentStatus, string> = {
  active: 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/25',
  disabled: 'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/25',
  testing: 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/25',
};

interface Props {
  agents: AgentWithRelations[];
  onRefresh: () => void;
}

export default function AgentsTable({ agents, onRefresh }: Props) {
  const [skillsAgent, setSkillsAgent] = useState<AgentWithRelations | null>(null);
  const [modelAgent, setModelAgent] = useState<AgentWithRelations | null>(null);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  async function handleToggleStatus(agent: AgentWithRelations) {
    setOpenMenu(null);
    setTogglingId(agent.id);
    try {
      const next: AgentStatus = agent.status === 'active' ? 'disabled' : 'active';
      await setAgentStatus(agent.id, next);
      onRefresh();
    } finally {
      setTogglingId(null);
    }
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center mb-4">
          <Cpu className="w-6 h-6 text-slate-600" />
        </div>
        <p className="text-slate-400 font-medium">No agents configured</p>
        <p className="text-slate-600 text-sm mt-1">Create your first agent to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-6 py-3">Agent</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Type</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Model</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Temp</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Skills</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {agents.map((agent) => {
              const typeColor = agent.type ? AGENT_TYPE_COLORS[agent.type as AgentType] : 'bg-slate-500/15 text-slate-400';
              const providerColor = agent.default_model_provider ? PROVIDER_COLORS[agent.default_model_provider as LLMProvider] : '';
              const visibleSkills = agent.skills.slice(0, 2);
              const extraSkills = agent.skills.length - 2;

              return (
                <tr key={agent.id} className="group hover:bg-white/2 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-white font-medium">{agent.name}</p>
                      {agent.description && (
                        <p className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">{agent.description}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    {agent.type ? (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ring-1 ${typeColor}`}>
                        {agent.type.replace('_', ' ')}
                      </span>
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    {agent.default_model_provider && agent.default_model_name ? (
                      <div className="space-y-1">
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${providerColor}`}>
                          {agent.default_model_provider}
                        </span>
                        <p className="text-xs text-slate-400 font-mono">{agent.default_model_name}</p>
                      </div>
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <Thermometer className="w-3 h-3 text-slate-600" />
                      <span className="text-xs font-mono">{agent.temperature?.toFixed(1) ?? '—'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1 flex-wrap">
                      {agent.skills.length === 0 && (
                        <span className="text-xs text-slate-600">None</span>
                      )}
                      {visibleSkills.map((s) => (
                        <span key={s.id} className="inline-flex px-1.5 py-0.5 rounded bg-slate-700/60 text-slate-400 text-xs font-mono">
                          {s.skill_name.replace(/_/g, ' ')}
                        </span>
                      ))}
                      {extraSkills > 0 && (
                        <span className="inline-flex px-1.5 py-0.5 rounded bg-slate-700/60 text-slate-500 text-xs">
                          +{extraSkills}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[agent.status as AgentStatus]}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === 'active' ? 'bg-emerald-400' :
                        agent.status === 'testing' ? 'bg-amber-400' : 'bg-slate-500'
                      }`} />
                      {agent.status}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="relative">
                      <button
                        onClick={() => setOpenMenu(openMenu === agent.id ? null : agent.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/8 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                      {openMenu === agent.id && (
                        <div
                          className="absolute right-0 top-full mt-1 w-44 bg-slate-800 border border-white/10 rounded-xl shadow-xl z-20 overflow-hidden"
                          onMouseLeave={() => setOpenMenu(null)}
                        >
                          <button
                            onClick={() => { setOpenMenu(null); setSkillsAgent(agent); }}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <Wrench className="w-3.5 h-3.5" />
                            Manage Skills
                          </button>
                          <button
                            onClick={() => { setOpenMenu(null); setModelAgent(agent); }}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <Cpu className="w-3.5 h-3.5" />
                            Configure Model
                          </button>
                          <div className="border-t border-white/8 my-0.5" />
                          <button
                            onClick={() => handleToggleStatus(agent)}
                            disabled={togglingId === agent.id}
                            className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm transition-colors ${
                              agent.status === 'active'
                                ? 'text-rose-400 hover:text-rose-300 hover:bg-rose-500/8'
                                : 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/8'
                            }`}
                          >
                            <Power className="w-3.5 h-3.5" />
                            {agent.status === 'active' ? 'Disable' : 'Activate'}
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {skillsAgent && (
        <AgentSkillsEditor
          agent={skillsAgent}
          onClose={() => setSkillsAgent(null)}
          onUpdated={() => { setSkillsAgent(null); onRefresh(); }}
        />
      )}
      {modelAgent && (
        <AgentModelEditor
          agent={modelAgent}
          onClose={() => setModelAgent(null)}
          onUpdated={() => { setModelAgent(null); onRefresh(); }}
        />
      )}
    </>
  );
}
