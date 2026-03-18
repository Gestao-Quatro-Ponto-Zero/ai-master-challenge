import { useState, useEffect, useCallback } from 'react';
import {
  Search, Loader2, Inbox, ListOrdered, CheckCircle2, RefreshCw,
  AlertCircle,
} from 'lucide-react';
import {
  getAssignedTickets, getQueuedTickets, getResolvedTickets,
  type WorkspaceTicket,
} from '../../services/workspaceService';
import type { TicketPriority, TicketStatus } from '../../types';

interface Props {
  userId:           string;
  selectedId:       string | null;
  onSelect:         (ticket: WorkspaceTicket) => void;
}

type Tab = 'assigned' | 'queue' | 'resolved';

const PRIORITY_DOT: Record<TicketPriority, string> = {
  urgent: 'bg-rose-500',
  high:   'bg-amber-400',
  medium: 'bg-blue-400',
  low:    'bg-slate-500',
};

const STATUS_COLOR: Record<TicketStatus, string> = {
  open:             'text-emerald-400',
  in_progress:      'text-blue-400',
  waiting_customer: 'text-amber-400',
  resolved:         'text-slate-500',
  closed:           'text-slate-600',
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60000);
  if (mins < 1)  return 'now';
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

export default function TicketSidebar({ userId, selectedId, onSelect }: Props) {
  const [tab,      setTab]      = useState<Tab>('assigned');
  const [tickets,  setTickets]  = useState<WorkspaceTicket[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [search,   setSearch]   = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      let data: WorkspaceTicket[];
      if (tab === 'assigned') data = await getAssignedTickets(userId);
      else if (tab === 'queue') data = await getQueuedTickets();
      else data = await getResolvedTickets(userId);
      setTickets(data);
    } catch { } finally { setLoading(false); }
  }, [tab, userId]);

  useEffect(() => { load(); }, [load]);

  const filtered = tickets.filter((t) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    const name = (t.customer as { name?: string } | null)?.name?.toLowerCase() ?? '';
    const subj = (t.subject ?? '').toLowerCase();
    return name.includes(q) || subj.includes(q);
  });

  const TABS: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'assigned', label: 'My Tickets', icon: Inbox        },
    { id: 'queue',    label: 'Queue',      icon: ListOrdered  },
    { id: 'resolved', label: 'Resolved',   icon: CheckCircle2 },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-950 border-r border-white/5">
      {/* Header */}
      <div className="px-4 pt-4 pb-2 shrink-0">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Tickets</span>
          <button
            onClick={load}
            disabled={loading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            className="w-full bg-slate-800/60 border border-white/6 rounded-xl pl-8 pr-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-blue-500/40 transition-colors"
          />
        </div>

        {/* Tabs */}
        <div className="flex gap-0.5 bg-slate-900 rounded-xl p-0.5">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                tab === id
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-center">
            <AlertCircle className="w-6 h-6 text-slate-500" />
            <p className="text-xs text-slate-400">
              {search ? 'No results' : tab === 'assigned' ? 'No tickets assigned' : tab === 'queue' ? 'Queue is empty' : 'No resolved tickets'}
            </p>
          </div>
        ) : (
          filtered.map((ticket) => {
            const customer = ticket.customer as { name?: string; email?: string } | null;
            const isSelected = ticket.id === selectedId;

            return (
              <button
                key={ticket.id}
                onClick={() => onSelect(ticket)}
                className={`w-full text-left px-3 py-3 rounded-xl mb-1 transition-colors group ${
                  isSelected
                    ? 'bg-blue-600/20 border border-blue-500/30'
                    : 'hover:bg-white/4 border border-transparent'
                }`}
              >
                {/* Top row */}
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${PRIORITY_DOT[ticket.priority]}`} />
                    <span className="text-xs font-medium text-white truncate">
                      {customer?.name || customer?.email || 'Unknown'}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 shrink-0">{timeAgo(ticket.updated_at)}</span>
                </div>

                {/* Subject */}
                <p className={`text-xs truncate mb-1.5 ${isSelected ? 'text-slate-200' : 'text-slate-300'}`}>
                  {ticket.subject || 'No subject'}
                </p>

                {/* Status + channel */}
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium capitalize ${STATUS_COLOR[ticket.status]}`}>
                    {ticket.status.replace(/_/g, ' ')}
                  </span>
                  {ticket.channel && (
                    <span className="text-xs text-slate-400 capitalize">
                      · {(ticket.channel as { name?: string }).name}
                    </span>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
