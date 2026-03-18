import { useState } from 'react';
import {
  CheckCircle, XCircle, Pencil, Trash2, ToggleLeft, ToggleRight,
  ChevronUp, ChevronDown, ArrowUpDown,
} from 'lucide-react';
import type { LLMPolicy } from '../../services/promptPolicyService';

const TASK_COLORS: Record<string, string> = {
  chat:           'bg-blue-500/10   text-blue-400   border-blue-500/20',
  classification: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  summarization:  'bg-amber-500/10  text-amber-400  border-amber-500/20',
  reasoning:      'bg-rose-500/10   text-rose-400   border-rose-500/20',
  extraction:     'bg-cyan-500/10   text-cyan-400   border-cyan-500/20',
  translation:    'bg-teal-500/10   text-teal-400   border-teal-500/20',
  embedding:      'bg-slate-500/10  text-slate-400  border-slate-500/20',
  test:           'bg-slate-500/10  text-slate-400  border-slate-500/20',
};

const PROVIDER_COLORS: Record<string, string> = {
  openai:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  anthropic: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  google:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  mistral:   'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

type SortField = 'task_type' | 'priority' | 'policy_name';
type SortDir   = 'asc' | 'desc';

interface Props {
  policies:  LLMPolicy[];
  onEdit:    (policy: LLMPolicy)  => void;
  onToggle:  (policy: LLMPolicy)  => void;
  onDelete:  (policy: LLMPolicy)  => void;
  loading?:  boolean;
}

export default function LLMPoliciesTable({ policies, onEdit, onToggle, onDelete, loading }: Props) {
  const [sortField, setSortField] = useState<SortField>('task_type');
  const [sortDir,   setSortDir]   = useState<SortDir>('asc');

  function toggleSort(field: SortField) {
    if (sortField === field) setSortDir((d) => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('asc'); }
  }

  const sorted = [...policies].sort((a, b) => {
    let va: string | number = a[sortField];
    let vb: string | number = b[sortField];
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    if (va < vb) return sortDir === 'asc' ? -1 :  1;
    if (va > vb) return sortDir === 'asc' ?  1 : -1;
    return 0;
  });

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <ArrowUpDown className="w-3 h-3 text-slate-600" />;
    return sortDir === 'asc'
      ? <ChevronUp   className="w-3 h-3 text-white" />
      : <ChevronDown className="w-3 h-3 text-white" />;
  }

  if (!loading && policies.length === 0) {
    return (
      <div className="py-16 text-center text-slate-600 text-sm">
        No policies configured yet. Create your first policy to start routing prompts.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            {([
              ['policy_name', 'Policy Name'],
              ['task_type',   'Task Type'],
            ] as [SortField, string][]).map(([f, label]) => (
              <th key={f} className="text-left px-5 py-3">
                <button
                  onClick={() => toggleSort(f)}
                  className="flex items-center gap-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider hover:text-slate-300 transition-colors"
                >
                  {label} <SortIcon field={f} />
                </button>
              </th>
            ))}
            <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Model</th>
            <th className="text-left px-5 py-3">
              <button
                onClick={() => toggleSort('priority')}
                className="flex items-center gap-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider hover:text-slate-300 transition-colors"
              >
                Priority <SortIcon field="priority" />
              </button>
            </th>
            <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
            <th className="px-5 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {sorted.map((policy) => {
            const model = policy.model as { name: string; provider: string; model_identifier: string } | null;
            return (
              <tr
                key={policy.id}
                className={`transition-colors hover:bg-white/[0.02] ${!policy.is_active ? 'opacity-50' : ''}`}
              >
                <td className="px-5 py-3.5">
                  <span className="text-white text-sm font-medium">{policy.policy_name}</span>
                </td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${TASK_COLORS[policy.task_type] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                    {policy.task_type}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    {model?.provider && (
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border capitalize ${PROVIDER_COLORS[model.provider] ?? 'bg-slate-700 text-slate-400 border-white/10'}`}>
                        {model.provider}
                      </span>
                    )}
                    <div>
                      <p className="text-slate-300 text-sm">{model?.name ?? '—'}</p>
                      <code className="text-slate-600 text-[10px]">{model?.model_identifier}</code>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold tabular-nums
                    ${policy.priority === 1 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>
                    {policy.priority}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-1.5">
                    {policy.is_active ? (
                      <>
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-xs text-emerald-400">Active</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5 text-slate-600" />
                        <span className="text-xs text-slate-600">Inactive</span>
                      </>
                    )}
                  </div>
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onEdit(policy)}
                      title="Edit"
                      className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onToggle(policy)}
                      title={policy.is_active ? 'Deactivate' : 'Activate'}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-amber-400 hover:bg-white/5 transition-colors"
                    >
                      {policy.is_active
                        ? <ToggleRight className="w-3.5 h-3.5" />
                        : <ToggleLeft  className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => onDelete(policy)}
                      title="Delete"
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-white/5 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
