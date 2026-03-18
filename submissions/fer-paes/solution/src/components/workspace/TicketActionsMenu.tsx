import { useState } from 'react';
import {
  CheckCircle2, ArrowRightLeft, RefreshCw, ChevronDown,
  MoreHorizontal, Loader2,
} from 'lucide-react';
import type { TicketStatus, TicketPriority } from '../../types';
import { resolveTicket, reopenTicket } from '../../services/workspaceService';
import TransferModal from './TransferModal';
import { supabase } from '../../lib/supabaseClient';

interface Props {
  ticketId:  string;
  status:    TicketStatus;
  priority:  TicketPriority;
  userId:    string;
  onUpdated: () => void;
}

const PRIORITY_OPTS: { value: TicketPriority; label: string; dot: string }[] = [
  { value: 'urgent', label: 'Urgent', dot: 'bg-rose-500'  },
  { value: 'high',   label: 'High',   dot: 'bg-amber-400' },
  { value: 'medium', label: 'Medium', dot: 'bg-blue-400'  },
  { value: 'low',    label: 'Low',    dot: 'bg-slate-500' },
];

export default function TicketActionsMenu({ ticketId, status, priority, userId, onUpdated }: Props) {
  const [showTransfer,  setShowTransfer]  = useState(false);
  const [showPriority,  setShowPriority]  = useState(false);
  const [resolving,     setResolving]     = useState(false);
  const [reopening,     setReopening]     = useState(false);

  const isResolved = status === 'resolved' || status === 'closed';

  async function handleResolve() {
    setResolving(true);
    try { await resolveTicket(ticketId, userId); onUpdated(); }
    catch { } finally { setResolving(false); }
  }

  async function handleReopen() {
    setReopening(true);
    try { await reopenTicket(ticketId, userId); onUpdated(); }
    catch { } finally { setReopening(false); }
  }

  async function handlePriority(p: TicketPriority) {
    setShowPriority(false);
    await supabase.from('tickets').update({ priority: p, updated_at: new Date().toISOString() }).eq('id', ticketId);
    onUpdated();
  }

  return (
    <>
      <div className="flex items-center gap-2">
        {/* Priority selector */}
        <div className="relative">
          <button
            onClick={() => setShowPriority((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 border border-white/8 text-xs text-slate-300 hover:text-white hover:border-white/15 transition-colors"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${PRIORITY_OPTS.find((p) => p.value === priority)?.dot ?? 'bg-slate-500'}`} />
            {PRIORITY_OPTS.find((p) => p.value === priority)?.label ?? 'Medium'}
            <ChevronDown className="w-3 h-3 ml-0.5" />
          </button>

          {showPriority && (
            <div className="absolute top-full right-0 mt-1 bg-slate-800 border border-white/10 rounded-xl overflow-hidden shadow-xl z-20 min-w-[120px]">
              {PRIORITY_OPTS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handlePriority(opt.value)}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 text-xs text-left hover:bg-white/5 transition-colors ${
                    priority === opt.value ? 'text-white bg-white/5' : 'text-slate-400'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${opt.dot}`} />
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Transfer */}
        <button
          onClick={() => setShowTransfer(true)}
          disabled={isResolved}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 border border-white/8 text-xs text-slate-300 hover:text-white hover:border-white/15 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ArrowRightLeft className="w-3.5 h-3.5" />
          Transfer
        </button>

        {/* Resolve / Reopen */}
        {isResolved ? (
          <button
            onClick={handleReopen}
            disabled={reopening}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-700 border border-white/8 text-xs text-slate-300 hover:text-white transition-colors"
          >
            {reopening ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Reopen
          </button>
        ) : (
          <button
            onClick={handleResolve}
            disabled={resolving}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-500 disabled:opacity-40 transition-colors"
          >
            {resolving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            Resolve
          </button>
        )}
      </div>

      {showTransfer && (
        <TransferModal
          ticketId={ticketId}
          userId={userId}
          onClose={() => setShowTransfer(false)}
          onDone={() => { setShowTransfer(false); onUpdated(); }}
        />
      )}
    </>
  );
}
