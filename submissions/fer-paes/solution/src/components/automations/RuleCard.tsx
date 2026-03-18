import { useState } from 'react';
import { Pencil, Trash2, Zap, ArrowDown, ChevronRight } from 'lucide-react';
import { toggleRule, deleteRule } from '../../services/automationService';
import type { AutomationRule, AutomationCondition, AutomationAction } from '../../types';

const TRIGGER_LABELS: Record<string, string> = {
  ticket_created: 'Ticket Created',
  message_received: 'Message Received',
  ticket_updated: 'Ticket Updated',
};

const TRIGGER_COLORS: Record<string, string> = {
  ticket_created: 'bg-blue-50 text-blue-700 border-blue-200',
  message_received: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  ticket_updated: 'bg-amber-50 text-amber-700 border-amber-200',
};

const FIELD_LABELS: Record<string, string> = {
  priority: 'Priority',
  tag: 'Tag',
  channel: 'Channel',
  status: 'Status',
  assigned: 'Assigned',
};

const OPERATOR_LABELS: Record<string, string> = {
  equals: '=',
  not_equals: '≠',
  contains: 'contains',
  is_empty: 'is empty',
};

const ACTION_LABELS: Record<string, string> = {
  assign_user: 'Assign user',
  add_tag: 'Add tag',
  change_priority: 'Set priority',
  change_status: 'Set status',
};

function ConditionChip({ condition, index }: { condition: AutomationCondition; index: number }) {
  return (
    <div className="flex items-center gap-2">
      {index > 0 && (
        <span className="text-[10px] font-bold text-gray-400 uppercase shrink-0">AND</span>
      )}
      <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700">
        <span className="font-semibold">{FIELD_LABELS[condition.field] ?? condition.field}</span>
        <span className="text-slate-400">{OPERATOR_LABELS[condition.operator] ?? condition.operator}</span>
        {condition.operator !== 'is_empty' && (
          <span className="font-medium text-slate-600">{condition.value}</span>
        )}
      </span>
    </div>
  );
}

function ActionChip({ action, index }: { action: AutomationAction; index: number }) {
  return (
    <div className="flex items-center gap-2">
      {index > 0 && (
        <span className="text-[10px] font-bold text-gray-400 uppercase shrink-0">AND</span>
      )}
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700">
        <span className="font-semibold">{ACTION_LABELS[action.type] ?? action.type}</span>
        {action.value && (
          <>
            <ChevronRight className="w-2.5 h-2.5 text-blue-400" />
            <span className="font-medium">{action.value}</span>
          </>
        )}
      </span>
    </div>
  );
}

interface Props {
  rule: AutomationRule;
  onChange: () => void;
  onEdit: (rule: AutomationRule) => void;
}

export default function RuleCard({ rule, onChange, onEdit }: Props) {
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleToggle() {
    setToggling(true);
    try {
      await toggleRule(rule.id, !rule.is_active);
      onChange();
    } finally {
      setToggling(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete automation rule "${rule.name}"?`)) return;
    setDeleting(true);
    try {
      await deleteRule(rule.id);
      onChange();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className={`bg-white rounded-2xl border shadow-sm transition-all ${rule.is_active ? 'border-gray-100' : 'border-dashed border-gray-200 opacity-60'}`}>
      <div className="px-5 py-4 flex items-start gap-4">
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${rule.is_active ? 'bg-blue-100' : 'bg-gray-100'}`}>
          <Zap className={`w-4 h-4 ${rule.is_active ? 'text-blue-600' : 'text-gray-400'}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{rule.name}</h3>
            {!rule.is_active && (
              <span className="text-[10px] font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full uppercase">
                Disabled
              </span>
            )}
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-gray-400 uppercase w-8 shrink-0">WHEN</span>
              <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ${TRIGGER_COLORS[rule.trigger_event] ?? 'bg-gray-50 text-gray-700 border-gray-200'}`}>
                {TRIGGER_LABELS[rule.trigger_event] ?? rule.trigger_event}
              </span>
            </div>

            {rule.conditions.length > 0 && (
              <div className="flex items-start gap-2">
                <span className="text-[10px] font-bold text-gray-400 uppercase w-8 shrink-0 pt-1">IF</span>
                <div className="flex flex-col gap-1.5">
                  {rule.conditions.map((c, i) => (
                    <ConditionChip key={i} condition={c} index={i} />
                  ))}
                </div>
              </div>
            )}

            {rule.conditions.length === 0 && (
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-gray-400 uppercase w-8 shrink-0">IF</span>
                <span className="text-xs text-gray-400 italic">No conditions — always runs</span>
              </div>
            )}

            <div className="ml-10">
              <ArrowDown className="w-3.5 h-3.5 text-gray-300" />
            </div>

            <div className="flex items-start gap-2">
              <span className="text-[10px] font-bold text-gray-400 uppercase w-8 shrink-0 pt-1">DO</span>
              {rule.actions.length > 0 ? (
                <div className="flex flex-col gap-1.5">
                  {rule.actions.map((a, i) => (
                    <ActionChip key={i} action={a} index={i} />
                  ))}
                </div>
              ) : (
                <span className="text-xs text-gray-400 italic">No actions configured</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 pt-0.5">
          <button
            onClick={handleToggle}
            disabled={toggling}
            title={rule.is_active ? 'Disable rule' : 'Enable rule'}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 ${rule.is_active ? 'bg-blue-600' : 'bg-gray-200'}`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform ${rule.is_active ? 'translate-x-4' : 'translate-x-1'}`}
            />
          </button>

          <button
            onClick={() => onEdit(rule)}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Edit rule"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleDelete}
            disabled={deleting}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-40"
            title="Delete rule"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
