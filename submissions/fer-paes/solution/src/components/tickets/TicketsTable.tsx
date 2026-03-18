import { Ticket } from 'lucide-react';
import type { TicketWithRelations, TicketStatus, TicketSLA, Tag } from '../../types';
import TicketRow from './TicketRow';

interface Props {
  tickets: TicketWithRelations[];
  slaMap?: Record<string, TicketSLA>;
  tagMap?: Record<string, Tag[]>;
  loading: boolean;
  actionLoadingId: string | null;
  onAssign: (ticket: TicketWithRelations) => void;
  onClose: (ticket: TicketWithRelations) => void;
  onStatusChange: (ticket: TicketWithRelations, status: TicketStatus) => void;
  hasFilters: boolean;
}

export default function TicketsTable({
  tickets,
  slaMap = {},
  tagMap = {},
  loading,
  actionLoadingId,
  onAssign,
  onClose,
  onStatusChange,
  hasFilters,
}: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 rounded-xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
          <Ticket className="w-7 h-7 text-gray-300" />
        </div>
        <p className="text-gray-600 font-medium">No tickets found</p>
        <p className="text-gray-400 text-sm mt-1">
          {hasFilters ? 'Try adjusting your filters' : 'No tickets have been created yet'}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50/80 border-b border-gray-100">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Ticket
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Customer
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Channel
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Status
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Priority
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Assigned
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Last Update
              </th>
              <th className="px-5 py-3 w-28" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {tickets.map((ticket) => (
              <TicketRow
                key={ticket.id}
                ticket={ticket}
                sla={slaMap[ticket.id]}
                tags={tagMap[ticket.id]}
                actionLoading={actionLoadingId === ticket.id}
                onAssign={() => onAssign(ticket)}
                onClose={() => onClose(ticket)}
                onStatusChange={(s) => onStatusChange(ticket, s)}
              />
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-5 py-3 border-t border-gray-100 bg-gray-50/40 flex items-center justify-between">
        <p className="text-xs text-gray-400">
          {tickets.length} ticket{tickets.length !== 1 ? 's' : ''}
          {hasFilters ? ' matching filters' : ' total'}
        </p>
      </div>
    </div>
  );
}
