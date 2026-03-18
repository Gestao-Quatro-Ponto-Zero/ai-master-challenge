import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Loader2, ArrowDown, Zap } from 'lucide-react';
import { createRule, updateRule } from '../../services/automationService';
import { getTags } from '../../services/tagService';
import { supabase } from '../../lib/supabaseClient';
import type {
  AutomationRule,
  AutomationCondition,
  AutomationAction,
  TriggerEvent,
  ConditionField,
  ConditionOperator,
  ActionType,
  Tag,
} from '../../types';

const TRIGGER_OPTIONS: { value: TriggerEvent; label: string; desc: string }[] = [
  { value: 'ticket_created', label: 'Ticket Created', desc: 'Fires when a new ticket is opened' },
  { value: 'message_received', label: 'Message Received', desc: 'Fires when a new message arrives' },
  { value: 'ticket_updated', label: 'Ticket Updated', desc: 'Fires when ticket fields change' },
];

const FIELD_OPTIONS: { value: ConditionField; label: string }[] = [
  { value: 'priority', label: 'Priority' },
  { value: 'status', label: 'Status' },
  { value: 'channel', label: 'Channel' },
  { value: 'tag', label: 'Tag' },
  { value: 'assigned', label: 'Assigned user' },
];

const OPERATOR_OPTIONS: { value: ConditionOperator; label: string }[] = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equals', label: 'does not equal' },
  { value: 'contains', label: 'contains' },
  { value: 'is_empty', label: 'is empty' },
];

const ACTION_OPTIONS: { value: ActionType; label: string }[] = [
  { value: 'assign_user', label: 'Assign user' },
  { value: 'add_tag', label: 'Add tag' },
  { value: 'change_priority', label: 'Set priority' },
  { value: 'change_status', label: 'Set status' },
];

const PRIORITY_OPTIONS = ['low', 'medium', 'high', 'urgent'];
const STATUS_OPTIONS = ['open', 'pending', 'resolved', 'closed'];

interface RefData {
  tags: Tag[];
  users: { id: string; full_name: string | null; email: string }[];
  channels: { id: string; name: string }[];
}

function ValueSelect({
  field,
  actionType,
  value,
  onChange,
  refs,
}: {
  field?: ConditionField;
  actionType?: ActionType;
  value: string;
  onChange: (v: string) => void;
  refs: RefData;
}) {
  const cls =
    'w-full px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200';

  if (field === 'priority' || actionType === 'change_priority') {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">Select…</option>
        {PRIORITY_OPTIONS.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
    );
  }
  if (field === 'status' || actionType === 'change_status') {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">Select…</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
    );
  }
  if (field === 'tag' || actionType === 'add_tag') {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">Select tag…</option>
        {refs.tags.map((t) => (
          <option key={t.id} value={t.id}>{t.name}</option>
        ))}
      </select>
    );
  }
  if (field === 'channel') {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">Select channel…</option>
        {refs.channels.map((c) => (
          <option key={c.id} value={c.name}>{c.name}</option>
        ))}
      </select>
    );
  }
  if (field === 'assigned' || actionType === 'assign_user') {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">Select user…</option>
        {refs.users.map((u) => (
          <option key={u.id} value={u.id}>{u.full_name || u.email}</option>
        ))}
      </select>
    );
  }
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Value…"
      className={cls}
    />
  );
}

interface Props {
  rule: AutomationRule | null;
  onClose: () => void;
  onSaved: () => void;
}

const emptyCondition = (): AutomationCondition => ({ field: 'priority', operator: 'equals', value: '' });
const emptyAction = (): AutomationAction => ({ type: 'change_priority', value: '' });

export default function RuleEditorModal({ rule, onClose, onSaved }: Props) {
  const [name, setName] = useState(rule?.name ?? '');
  const [trigger, setTrigger] = useState<TriggerEvent>(rule?.trigger_event ?? 'ticket_created');
  const [conditions, setConditions] = useState<AutomationCondition[]>(
    rule?.conditions?.length ? rule.conditions : []
  );
  const [actions, setActions] = useState<AutomationAction[]>(
    rule?.actions?.length ? rule.actions : [emptyAction()]
  );
  const [saving, setSaving] = useState(false);
  const [refs, setRefs] = useState<RefData>({ tags: [], users: [], channels: [] });

  useEffect(() => {
    async function load() {
      const [tagsData, usersData, channelsData] = await Promise.all([
        getTags().catch(() => []),
        supabase.from('profiles').select('id, full_name, email').then(({ data }) => data ?? []),
        supabase.from('channels').select('id, name').eq('is_active', true).then(({ data }) => data ?? []),
      ]);
      setRefs({
        tags: tagsData as Tag[],
        users: usersData as RefData['users'],
        channels: channelsData as RefData['channels'],
      });
    }
    load();
  }, []);

  function updateCondition(i: number, patch: Partial<AutomationCondition>) {
    setConditions((prev) => prev.map((c, idx) => (idx === i ? { ...c, ...patch } : c)));
  }

  function removeCondition(i: number) {
    setConditions((prev) => prev.filter((_, idx) => idx !== i));
  }

  function updateAction(i: number, patch: Partial<AutomationAction>) {
    setActions((prev) => prev.map((a, idx) => (idx === i ? { ...a, ...patch } : a)));
  }

  function removeAction(i: number) {
    setActions((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        trigger_event: trigger,
        conditions,
        actions,
        is_active: rule?.is_active ?? true,
      };
      if (rule) {
        await updateRule(rule.id, payload);
      } else {
        await createRule(payload);
      }
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-100 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <h2 className="text-sm font-semibold text-gray-900">
              {rule ? 'Edit Rule' : 'New Automation Rule'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-5 space-y-6">
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1.5">Rule Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Escalate urgent billing tickets"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-4 h-4 rounded bg-blue-100 flex items-center justify-center text-[9px] font-bold text-blue-600">W</span>
                Trigger — When this happens
              </span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {TRIGGER_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTrigger(t.value)}
                  className={`rounded-xl border p-3 text-left transition-all ${
                    trigger === t.value
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <p className={`text-xs font-semibold mb-0.5 ${trigger === t.value ? 'text-blue-700' : 'text-gray-700'}`}>
                    {t.label}
                  </p>
                  <p className="text-[10px] text-gray-400 leading-snug">{t.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-center">
            <ArrowDown className="w-4 h-4 text-gray-300" />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-gray-500">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded bg-slate-100 flex items-center justify-center text-[9px] font-bold text-slate-500">IF</span>
                  Conditions — All must match
                </span>
              </label>
              <button
                onClick={() => setConditions((prev) => [...prev, emptyCondition()])}
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                <Plus className="w-3 h-3" />
                Add
              </button>
            </div>

            {conditions.length === 0 && (
              <p className="text-xs text-gray-400 italic py-2 px-3 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                No conditions — rule will always run
              </p>
            )}

            <div className="space-y-2">
              {conditions.map((c, i) => (
                <div key={i} className="flex items-center gap-2 bg-slate-50 rounded-xl p-3 border border-slate-200">
                  {i > 0 && (
                    <span className="text-[9px] font-bold text-gray-400 uppercase shrink-0">AND</span>
                  )}
                  <select
                    value={c.field}
                    onChange={(e) => updateCondition(i, { field: e.target.value as ConditionField, value: '' })}
                    className="px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 bg-white"
                  >
                    {FIELD_OPTIONS.map((f) => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                  <select
                    value={c.operator}
                    onChange={(e) => updateCondition(i, { operator: e.target.value as ConditionOperator })}
                    className="px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 bg-white"
                  >
                    {OPERATOR_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  {c.operator !== 'is_empty' && (
                    <div className="flex-1 min-w-0">
                      <ValueSelect
                        field={c.field}
                        value={c.value}
                        onChange={(v) => updateCondition(i, { value: v })}
                        refs={refs}
                      />
                    </div>
                  )}
                  <button
                    onClick={() => removeCondition(i)}
                    className="text-gray-300 hover:text-red-400 transition-colors shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center">
            <ArrowDown className="w-4 h-4 text-gray-300" />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-gray-500">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded bg-blue-100 flex items-center justify-center text-[9px] font-bold text-blue-600">DO</span>
                  Actions — What to do
                </span>
              </label>
              <button
                onClick={() => setActions((prev) => [...prev, emptyAction()])}
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                <Plus className="w-3 h-3" />
                Add
              </button>
            </div>

            <div className="space-y-2">
              {actions.map((a, i) => (
                <div key={i} className="flex items-center gap-2 bg-blue-50 rounded-xl p-3 border border-blue-200">
                  {i > 0 && (
                    <span className="text-[9px] font-bold text-gray-400 uppercase shrink-0">AND</span>
                  )}
                  <select
                    value={a.type}
                    onChange={(e) => updateAction(i, { type: e.target.value as ActionType, value: '' })}
                    className="px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 bg-white"
                  >
                    {ACTION_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  <div className="flex-1 min-w-0">
                    <ValueSelect
                      actionType={a.type}
                      value={a.value}
                      onChange={(v) => updateAction(i, { value: v })}
                      refs={refs}
                    />
                  </div>
                  <button
                    onClick={() => removeAction(i)}
                    className="text-blue-300 hover:text-red-400 transition-colors shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            disabled={!name.trim() || saving}
            onClick={handleSave}
            className="px-4 py-2 text-sm rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            {rule ? 'Save Changes' : 'Create Rule'}
          </button>
        </div>
      </div>
    </div>
  );
}
