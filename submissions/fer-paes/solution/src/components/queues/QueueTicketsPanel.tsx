import { useState, useEffect } from 'react';
import { X, Loader2, Ticket as TicketIcon, Trash2, ChevronUp } from 'lucide-react';
import {
  getQueueTickets, removeTicketFromQueue, type Queue, type QueueTicket,
} from '../../services/queueService';

interface Props {
  queue:   Queue;
  onClose: () => void;
  onChanged?: () => void;
}

const TICKET_STATUS_BADGE: Record<string, string> = {
  open:        'bg-blue-500/15 text-blue-300 border-blue-500/20',
  in_progress: 'bg-amber-500/15 text-amber-300 border-amber-500/20',
  resolved:    'bg-emerald-500/15 text-emerald-300 border-emerald-500/20',
  closed:      'bg-slate-700/50 text-slate-500 border-slate-600/30',
};

const TICKET_PRIORITY_BADGE: Record<string, string> = {
  low:      'bg-slate-700/50 text-slate-500',
  normal:   'bg-blue-900/60 text-blue-300',
  high:     'bg-amber-900/60 text-amber-300',
  urgent:   'bg-rose-900/60 text-rose-300',
  critical: 'bg-rose-600/80 text-white',
};

export default function QueueTicketsPanel({ queue, onClose, onChanged }: Props) {
  const [tickets, setTickets] = useState<QueueTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try { setTickets(await getQueueTickets(queue.id)); }
    catch { } finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [queue.id]);

  async function handleRemove(qt: QueueTicket) {
    setRemoving(qt.id);
    try {
      await removeTicketFromQueue(qt.id);
      setTickets((prev) => prev.filter((t) => t.id !== qt.id));
      onChanged?.();
    } catch { } finally { setRemoving(null); }
  }

  const name = queue.name.replace(/_/g, ' ');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <TicketIcon className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white capitalize">{name}</h2>
              <p className="text-xs text-slate-500">Waiting tickets · ordered by priority</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
            </div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-2">
              <TicketIcon className="w-7 h-7 text-slate-700" />
              <p className="text-xs text-slate-600">No tickets in this queue.</p>
            </div>
          ) : (
            <div className="divide-y divide-white/4">
              {tickets.map((qt, idx) => {
                const t      = qt.ticket;
                const status   = t?.status   ?? 'open';
                const priority = t?.priority ?? 'normal';
                const customer = t?.customer;
                return (
                  <div key={qt.id} className="flex items-start gap-3 px-6 py-3.5 hover:bg-white/2 transition-colors">
                    <div className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-xs text-slate-500 tabular-nums font-medium">{idx + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{t?.subject ?? qt.ticket_id.slice(0, 8)}</p>
                      {customer && (
                        <p className="text-xs text-slate-600 truncate">{customer.name || customer.email}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className={`inline-flex px-2 py-0.5 rounded-full border text-xs font-medium ${TICKET_STATUS_BADGE[status] ?? TICKET_STATUS_BADGE.open}`}>
                          {status.replace(/_/g, ' ')}
                        </span>
                        <span className={`inline-flex px-2 py-0.5 rounded-lg text-xs font-medium ${TICKET_PRIORITY_BADGE[priority] ?? TICKET_PRIORITY_BADGE.normal}`}>
                          {priority}
                        </span>
                        {qt.priority > 1 && (
                          <span className="inline-flex items-center gap-0.5 text-xs text-amber-400">
                            <ChevronUp className="w-3 h-3" />boosted
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemove(qt)}
                      disabled={removing === qt.id}
                      title="Remove from queue"
                      className="p-1.5 rounded-xl text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 disabled:opacity-40 transition-colors shrink-0"
                    >
                      {removing === qt.id
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        : <Trash2 className="w-3.5 h-3.5" />
                      }
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-6 py-3 border-t border-white/8 flex items-center justify-between">
          <span className="text-xs text-slate-600">{tickets.length} ticket{tickets.length !== 1 ? 's' : ''} waiting</span>
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
