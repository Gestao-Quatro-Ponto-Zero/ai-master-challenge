import { useState, useEffect, useCallback } from 'react';
import { Ticket as TicketIcon, RefreshCw, Plus, AlertCircle, XCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import {
  getTickets,
  assignTicket,
  closeTicket,
  changeStatus,
  getChannels,
} from '../services/ticketService';
import { getTicketSLA } from '../services/slaService';
import { getTagsForTickets } from '../services/tagService';
import type { TicketWithRelations, TicketStatus, Channel, TicketFilters, TicketSLA, Tag } from '../types';
import TicketFiltersBar from '../components/tickets/TicketFilters';
import TicketsTable from '../components/tickets/TicketsTable';
import AssignTicketModal from '../components/tickets/AssignTicketModal';
import CreateTicketModal from '../components/tickets/CreateTicketModal';

interface CloseModalProps {
  ticket: TicketWithRelations;
  onConfirm: () => void;
  onClose: () => void;
  loading?: boolean;
}

function CloseTicketModal({ ticket, onConfirm, onClose, loading }: CloseModalProps) {
  const id = ticket.id.slice(0, 8).toUpperCase();
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <AlertCircle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Fechar Ticket</h2>
            <p className="text-xs text-gray-400">#{id}</p>
          </div>
        </div>
        <p className="text-sm text-gray-600 mb-6 leading-relaxed">
          Tem certeza que deseja fechar este ticket? Ele será marcado como fechado e o horário será registrado.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            ) : (
              <XCircle className="w-4 h-4" />
            )}
            Fechar Ticket
          </button>
        </div>
      </div>
    </div>
  );
}

type ModalState =
  | { type: 'none' }
  | { type: 'create' }
  | { type: 'assign'; ticket: TicketWithRelations }
  | { type: 'close'; ticket: TicketWithRelations };

export default function Tickets() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<TicketWithRelations[]>([]);
  const [slaMap, setSlaMap] = useState<Record<string, TicketSLA>>({});
  const [tagMap, setTagMap] = useState<Record<string, Tag[]>>({});
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>({ type: 'none' });
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<TicketFilters>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ticketsData, channelsData] = await Promise.all([getTickets(filters), getChannels()]);
      setTickets(ticketsData);
      setChannels(channelsData);

      const openTicketIds = ticketsData.filter((t) => t.status !== 'closed').map((t) => t.id);
      const allTicketIds = ticketsData.map((t) => t.id);

      const [slaEntries, fetchedTagMap] = await Promise.all([
        Promise.all(
          openTicketIds.map((id) =>
            getTicketSLA(id).then((sla) => ({ id, sla })).catch(() => ({ id, sla: null }))
          )
        ),
        getTagsForTickets(allTicketIds).catch(() => ({})),
      ]);

      const map: Record<string, TicketSLA> = {};
      for (const { id, sla } of slaEntries) {
        if (sla) map[id] = sla;
      }
      setSlaMap(map);
      setTagMap(fetchedTagMap);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleAssign(ticket: TicketWithRelations, userId: string) {
    setActionLoading(ticket.id);
    try {
      await assignTicket(ticket.id, userId, user!.id);
      setModal({ type: 'none' });
      await loadData();
    } finally {
      setActionLoading(null);
    }
  }

  async function handleClose(ticket: TicketWithRelations) {
    setActionLoading(ticket.id);
    try {
      await closeTicket(ticket.id, user!.id);
      setModal({ type: 'none' });
      await loadData();
    } finally {
      setActionLoading(null);
    }
  }

  async function handleStatusChange(ticket: TicketWithRelations, newStatus: TicketStatus) {
    setActionLoading(ticket.id);
    try {
      await changeStatus(ticket.id, newStatus, user!.id);
      await loadData();
    } finally {
      setActionLoading(null);
    }
  }

  const filtered = tickets.filter((t) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      t.id.toLowerCase().includes(q) ||
      (t.subject || '').toLowerCase().includes(q) ||
      (t.customer?.name || '').toLowerCase().includes(q) ||
      (t.customer?.email || '').toLowerCase().includes(q)
    );
  });

  const statusCounts = tickets.reduce<Record<string, number>>((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1;
    return acc;
  }, {});

  const openCount = statusCounts['open'] || 0;
  const hasFilters = search.length > 0 || Object.values(filters).some(Boolean);

  return (
    <div className="flex flex-col h-full">
      <div className="px-8 py-5 border-b border-gray-100 bg-white shrink-0">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <TicketIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold text-gray-900">Tickets</h1>
                {openCount > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-blue-600 text-white text-xs font-bold">
                    {openCount}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-400">Gerencie todas as solicitações de suporte</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              disabled={loading}
              className="w-9 h-9 flex items-center justify-center rounded-xl border border-gray-200 text-gray-400 hover:text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              title="Atualizar"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setModal({ type: 'create' })}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-95 transition-all shadow-sm shadow-blue-200"
            >
              <Plus className="w-4 h-4" />
              Novo Ticket
            </button>
          </div>
        </div>

        <TicketFiltersBar
          filters={filters}
          search={search}
          channels={channels}
          ticketCounts={statusCounts}
          totalCount={tickets.length}
          onFilterChange={setFilters}
          onSearchChange={setSearch}
        />
      </div>

      <div className="flex-1 overflow-auto px-8 py-6">
        <TicketsTable
          tickets={filtered}
          slaMap={slaMap}
          tagMap={tagMap}
          loading={loading}
          actionLoadingId={actionLoading}
          onAssign={(ticket) => setModal({ type: 'assign', ticket })}
          onClose={(ticket) => setModal({ type: 'close', ticket })}
          onStatusChange={handleStatusChange}
          hasFilters={hasFilters}
        />
      </div>

      {modal.type === 'create' && (
        <CreateTicketModal
          channels={channels}
          onCreated={() => { setModal({ type: 'none' }); loadData(); }}
          onClose={() => setModal({ type: 'none' })}
        />
      )}

      {modal.type === 'assign' && (
        <AssignTicketModal
          ticket={modal.ticket}
          currentUserId={user!.id}
          onConfirm={(userId) => handleAssign(modal.ticket, userId)}
          onClose={() => setModal({ type: 'none' })}
          loading={actionLoading === modal.ticket.id}
        />
      )}

      {modal.type === 'close' && (
        <CloseTicketModal
          ticket={modal.ticket}
          onConfirm={() => handleClose(modal.ticket)}
          onClose={() => setModal({ type: 'none' })}
          loading={actionLoading === modal.ticket.id}
        />
      )}
    </div>
  );
}
