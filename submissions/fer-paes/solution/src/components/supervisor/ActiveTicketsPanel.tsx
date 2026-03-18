import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, UserPlus, Loader2, AlertCircle, X, Clock } from 'lucide-react';
import { manualAssign } from '../../services/ticketAssignmentService';
import type { ActiveTicketRow, OperatorMetric } from '../../services/monitoringService';

interface Props {
  tickets:           ActiveTicketRow[];
  operators:         OperatorMetric[];
  supervisorUserId:  string;
  onRefresh:         () => void;
}

const PRIORITY_CFG: Record<string, { label: string; color: string; dot: string }> = {
  urgent:   { label: 'Urgent',   color: 'text-rose-400',   dot: 'bg-rose-400'   },
  high:     { label: 'High',     color: 'text-amber-400',  dot: 'bg-amber-400'  },
  medium:   { label: 'Medium',   color: 'text-blue-400',   dot: 'bg-blue-400'   },
  low:      { label: 'Low',      color: 'text-slate-500',  dot: 'bg-slate-600'  },
  normal:   { label: 'Normal',   color: 'text-slate-400',  dot: 'bg-slate-500'  },
};

const STATUS_CFG: Record<string, { label: string; color: string }> = {
  open:        { label: 'Open',        color: 'text-blue-400'    },
  in_progress: { label: 'In Progress', color: 'text-emerald-400' },
};

function timeWaiting(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

interface AssignModalProps {
  ticket:           ActiveTicketRow;
  operators:        OperatorMetric[];
  supervisorUserId: string;
  onClose:          () => void;
  onAssigned:       () => void;
}

function AssignModal({ ticket, operators, supervisorUserId, onClose, onAssigned }: AssignModalProps) {
  const [selectedId, setSelectedId] = useState('');
  const [saving,     setSaving]     = useState(false);
  const [error,      setError]      = useState('');

  const available = operators.filter((op) => op.status === 'online' || op.status === 'busy');

  async function handleAssign() {
    if (!selectedId) return;
    setSaving(true);
    setError('');
    try {
      await manualAssign(ticket.id, selectedId, supervisorUserId);
      onAssigned();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Assignment failed');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <div>
            <h3 className="text-sm font-semibold text-white">Assign Ticket</h3>
            <p className="text-xs text-slate-600 mt-0.5 truncate max-w-xs">{ticket.subject || 'No subject'}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {available.length === 0 ? (
            <div className="flex items-center gap-2 text-xs text-slate-600 py-2">
              <AlertCircle className="w-4 h-4 text-slate-700 shrink-0" />
              No online operators available to assign.
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs text-slate-500 mb-2">Select operator</label>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {available.map((op) => (
                    <button
                      key={op.id}
                      onClick={() => setSelectedId(op.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-colors text-left ${
                        selectedId === op.id
                          ? 'border-blue-500/40 bg-blue-500/10'
                          : 'border-white/6 bg-slate-800/60 hover:bg-white/5'
                      }`}
                    >
                      <div className={`w-2 h-2 rounded-full shrink-0 ${op.status === 'online' ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-white truncate">{op.full_name || op.email}</p>
                        <p className="text-xs text-slate-600">{op.active_tickets}/{op.max_tickets} tickets</p>
                      </div>
                      {selectedId === op.id && (
                        <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center shrink-0">
                          <div className="w-1.5 h-1.5 rounded-full bg-white" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <p className="text-xs text-rose-400 flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  {error}
                </p>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleAssign}
                  disabled={!selectedId || saving}
                  className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UserPlus className="w-3.5 h-3.5" />}
                  {saving ? 'Assigning…' : 'Assign'}
                </button>
                <button onClick={onClose} className="px-4 py-2.5 rounded-xl text-slate-500 text-xs hover:text-white hover:bg-white/8 transition-colors">
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ActiveTicketsPanel({ tickets, operators, supervisorUserId, onRefresh }: Props) {
  const navigate                        = useNavigate();
  const [assignTarget, setAssignTarget] = useState<ActiveTicketRow | null>(null);

  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <AlertCircle className="w-10 h-10 text-slate-800" />
        <div>
          <p className="text-sm font-medium text-slate-500">No active tickets</p>
          <p className="text-xs text-slate-700 mt-1">All tickets have been resolved or are in queue.</p>
        </div>
      </div>
    );
  }

  const urgentCount = tickets.filter((t) => t.priority === 'urgent' || t.priority === 'high').length;
  const unassigned  = tickets.filter((t) => !t.operator_id).length;

  return (
    <>
      {assignTarget && (
        <AssignModal
          ticket={assignTarget}
          operators={operators}
          supervisorUserId={supervisorUserId}
          onClose={() => setAssignTarget(null)}
          onAssigned={() => { setAssignTarget(null); onRefresh(); }}
        />
      )}

      {/* Summary row */}
      <div className="flex items-center gap-5 px-1 mb-3">
        <span className="text-xs text-slate-600">{tickets.length} active</span>
        {unassigned > 0 && (
          <span className="text-xs text-amber-400">{unassigned} unassigned</span>
        )}
        {urgentCount > 0 && (
          <span className="text-xs text-rose-400">{urgentCount} urgent/high priority</span>
        )}
      </div>

      <div className="bg-slate-900/60 border border-white/6 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Ticket</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Customer</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Operator</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-600">
                <div className="flex items-center gap-1"><Clock className="w-3 h-3" />Wait</div>
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => {
              const prioConfig   = PRIORITY_CFG[t.priority]   ?? PRIORITY_CFG.normal;
              const statusConfig = STATUS_CFG[t.status] ?? { label: t.status, color: 'text-slate-400' };
              return (
                <tr key={t.id} className="border-b border-white/4 last:border-0 hover:bg-white/2 transition-colors">
                  <td className="px-4 py-3 max-w-[200px]">
                    <p className="text-xs font-medium text-white truncate">
                      {t.subject || 'No subject'}
                    </p>
                    {t.queue_name && (
                      <p className="text-xs text-slate-700 mt-0.5 capitalize truncate">
                        {t.queue_name.replace(/_/g, ' ')}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-xs text-slate-400 truncate max-w-[120px]">
                      {t.customer_name || t.customer_email || '—'}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    {t.operator_name ? (
                      <p className="text-xs text-slate-400 truncate max-w-[100px]">{t.operator_name}</p>
                    ) : (
                      <span className="text-xs text-amber-500/80 font-medium">Unassigned</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`flex items-center gap-1.5 text-xs font-medium ${prioConfig.color}`}>
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${prioConfig.dot}`} />
                      {prioConfig.label}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${statusConfig.color}`}>{statusConfig.label}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-slate-600 tabular-nums">{timeWaiting(t.created_at)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setAssignTarget(t)}
                        className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-slate-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                        title="Assign to operator"
                      >
                        <UserPlus className="w-3 h-3" />
                        Assign
                      </button>
                      <button
                        onClick={() => navigate(`/tickets/${t.id}`)}
                        className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-slate-500 hover:text-white hover:bg-white/8 transition-colors"
                        title="View ticket"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
