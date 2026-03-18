import { useState, useEffect } from 'react';
import { X, Loader2, ArrowRightLeft, Users, ListOrdered, Bot, CheckCircle } from 'lucide-react';
import {
  transferTicket,
  getOperatorTransferTargets,
  getQueueTransferTargets,
  getAgentTransferTargets,
  type TransferType,
  type OperatorTarget,
  type QueueTarget,
  type AgentTarget,
} from '../../services/transferService';
import type { OperatorStatus } from '../../types';

interface Props {
  ticketId: string;
  userId:   string;
  onClose:  () => void;
  onDone:   () => void;
}

const PRESENCE_DOT: Record<OperatorStatus, { dot: string; text: string; label: string }> = {
  online:  { dot: 'bg-emerald-400', text: 'text-emerald-300', label: 'Online'  },
  busy:    { dot: 'bg-rose-400',    text: 'text-rose-300',    label: 'Busy'    },
  away:    { dot: 'bg-amber-400',   text: 'text-amber-300',   label: 'Away'    },
  offline: { dot: 'bg-slate-600',   text: 'text-slate-600',   label: 'Offline' },
};

const AGENT_TYPE_LABELS: Record<string, string> = {
  triage_agent:    'Triage',
  support_agent:   'Support',
  technical_agent: 'Technical',
  billing_agent:   'Billing',
  sales_agent:     'Sales',
  qa_agent:        'QA',
};

function Avatar({ name, size = 'sm' }: { name: string; size?: 'sm' | 'md' }) {
  const initials = name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const colors = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-slate-600'];
  const color  = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  const dim    = size === 'sm' ? 'w-7 h-7 text-xs' : 'w-8 h-8 text-sm';
  return (
    <div className={`${dim} rounded-full ${color} flex items-center justify-center shrink-0 font-semibold text-white`}>
      {initials}
    </div>
  );
}

function LoadBar({ active, max }: { active: number; max: number }) {
  const pct   = max > 0 ? Math.min(100, Math.round((active / max) * 100)) : 0;
  const color = pct >= 90 ? 'bg-rose-500' : pct >= 60 ? 'bg-amber-400' : 'bg-emerald-400';
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 h-1 bg-slate-700/60 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-600 tabular-nums">{active}/{max}</span>
    </div>
  );
}

const TABS: { id: TransferType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'operator', label: 'Operator', icon: Users       },
  { id: 'queue',    label: 'Queue',    icon: ListOrdered },
  { id: 'agent',    label: 'Agent',    icon: Bot         },
];

export default function TransferModal({ ticketId, userId, onClose, onDone }: Props) {
  const [type,       setType]      = useState<TransferType>('operator');
  const [operators,  setOperators] = useState<OperatorTarget[]>([]);
  const [queues,     setQueues]    = useState<QueueTarget[]>([]);
  const [agents,     setAgents]    = useState<AgentTarget[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [reason,     setReason]    = useState('');
  const [loading,    setLoading]   = useState(true);
  const [saving,     setSaving]    = useState(false);
  const [error,      setError]     = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [ops, qs, ags] = await Promise.all([
          getOperatorTransferTargets(),
          getQueueTransferTargets(),
          getAgentTransferTargets(),
        ]);
        setOperators(ops);
        setQueues(qs);
        setAgents(ags);
      } catch { } finally { setLoading(false); }
    })();
  }, []);

  async function handleTransfer() {
    if (!selectedId) { setError('Please select a destination.'); return; }
    setSaving(true);
    setError('');
    try {
      await transferTicket({
        ticket_id:     ticketId,
        transfer_type: type,
        target_id:     selectedId,
        reason:        reason.trim() || undefined,
        from_user_id:  userId,
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transfer failed.');
    } finally { setSaving(false); }
  }

  function changeTab(t: TransferType) {
    setType(t);
    setSelectedId('');
    setError('');
  }

  const emptyMsg = type === 'operator'
    ? 'No operators found.'
    : type === 'queue'
      ? 'No active queues found.'
      : 'No active agents found.';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <ArrowRightLeft className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Transfer Ticket</h2>
              <p className="text-xs text-slate-600">Select a destination for this ticket</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-col flex-1 overflow-hidden p-5 gap-4">
          {/* Type tabs */}
          <div className="flex gap-0.5 bg-slate-800 rounded-xl p-0.5 shrink-0">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => changeTab(id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                  type === id
                    ? 'bg-slate-700 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Options list */}
          <div className="flex-1 overflow-y-auto space-y-1 min-h-0">
            {loading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
              </div>
            ) : type === 'operator' && operators.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-8">{emptyMsg}</p>
            ) : type === 'queue' && queues.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-8">{emptyMsg}</p>
            ) : type === 'agent' && agents.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-8">{emptyMsg}</p>
            ) : type === 'operator' ? (
              operators.map((op) => {
                const pres    = PRESENCE_DOT[op.presence_status] ?? PRESENCE_DOT.offline;
                const isActive = selectedId === op.id;
                return (
                  <button
                    key={op.id}
                    onClick={() => setSelectedId(op.id)}
                    className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-colors ${
                      isActive
                        ? 'bg-blue-600/15 border-blue-500/30'
                        : 'border-transparent hover:bg-white/4'
                    }`}
                  >
                    <div className="relative shrink-0">
                      <Avatar name={op.full_name || op.email} />
                      <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-slate-900 ${pres.dot}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-xs font-medium truncate ${isActive ? 'text-white' : 'text-slate-300'}`}>
                          {op.full_name || op.email}
                        </p>
                        <span className={`text-xs shrink-0 ${pres.text}`}>{pres.label}</span>
                      </div>
                      <div className="flex items-center justify-between gap-2 mt-0.5">
                        <p className="text-xs text-slate-600 truncate">{op.email}</p>
                        <LoadBar active={op.active_tickets} max={op.max_tickets} />
                      </div>
                    </div>
                    {isActive && <CheckCircle className="w-4 h-4 text-blue-400 shrink-0" />}
                  </button>
                );
              })
            ) : type === 'queue' ? (
              queues.map((q) => {
                const isActive = selectedId === q.id;
                return (
                  <button
                    key={q.id}
                    onClick={() => setSelectedId(q.id)}
                    className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-colors ${
                      isActive
                        ? 'bg-blue-600/15 border-blue-500/30'
                        : 'border-transparent hover:bg-white/4'
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 ${
                      isActive ? 'bg-blue-600/20' : 'bg-slate-800'
                    }`}>
                      <ListOrdered className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-medium capitalize truncate ${isActive ? 'text-white' : 'text-slate-300'}`}>
                        {q.name.replace(/_/g, ' ')}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-xs ${q.tickets_waiting > 0 ? 'text-amber-400' : 'text-slate-600'}`}>
                          {q.tickets_waiting} waiting
                        </span>
                        <span className="text-slate-700">·</span>
                        <span className="text-xs text-slate-600">{q.operators_count} operators</span>
                      </div>
                    </div>
                    {isActive && <CheckCircle className="w-4 h-4 text-blue-400 shrink-0" />}
                  </button>
                );
              })
            ) : (
              agents.map((ag) => {
                const isActive = selectedId === ag.id;
                const typeLabel = AGENT_TYPE_LABELS[ag.type ?? ''] ?? ag.type ?? 'Agent';
                return (
                  <button
                    key={ag.id}
                    onClick={() => setSelectedId(ag.id)}
                    className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-colors ${
                      isActive
                        ? 'bg-blue-600/15 border-blue-500/30'
                        : 'border-transparent hover:bg-white/4'
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 ${
                      isActive ? 'bg-blue-600/20' : 'bg-slate-800'
                    }`}>
                      <Bot className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-medium truncate ${isActive ? 'text-white' : 'text-slate-300'}`}>
                        {ag.name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-slate-600">{typeLabel}</span>
                        <span className="text-slate-700">·</span>
                        <span className="text-xs text-emerald-400 capitalize">{ag.status}</span>
                      </div>
                    </div>
                    {isActive && <CheckCircle className="w-4 h-4 text-blue-400 shrink-0" />}
                  </button>
                );
              })
            )}
          </div>

          {/* Reason */}
          <div className="shrink-0 space-y-1.5">
            <label className="text-xs font-medium text-slate-500">Reason (optional)</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why is this ticket being transferred?"
              rows={2}
              className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/40 resize-none transition-colors"
            />
          </div>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 shrink-0">
              {error}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 shrink-0">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleTransfer}
              disabled={!selectedId || saving}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {saving ? 'Transferring…' : 'Transfer'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
