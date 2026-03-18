import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Mail, Phone, User, Ticket, MessageSquare, Calendar, AlertCircle, CreditCard as Edit2, Check, X, ExternalLink, Clock, Hash } from 'lucide-react';
import { getCustomerWithTickets, updateCustomer } from '../services/customerService';
import type { Customer, TicketWithRelations, Conversation, UpdateCustomerPayload, TicketStatus, TicketPriority } from '../types';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Sem atividade';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Agora mesmo';
  if (mins < 60) return `${mins}min atrás`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h atrás`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d atrás`;
  return new Date(dateStr).toLocaleDateString();
}

const STATUS_STYLES: Record<TicketStatus, string> = {
  open: 'bg-green-50 text-green-700 border-green-200',
  in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
  waiting_customer: 'bg-amber-50 text-amber-700 border-amber-200',
  resolved: 'bg-teal-50 text-teal-700 border-teal-200',
  closed: 'bg-gray-100 text-gray-500 border-gray-200',
};

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  urgent: 'text-red-600',
  high: 'text-orange-500',
  medium: 'text-amber-500',
  low: 'text-gray-400',
};

interface EditableFieldProps {
  label: string;
  value: string | null;
  onSave: (val: string) => Promise<void>;
  icon: React.ComponentType<{ className?: string }>;
  type?: string;
  placeholder?: string;
}

function EditableField({ label, value, onSave, icon: Icon, type = 'text', placeholder }: EditableFieldProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? '');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(draft);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setDraft(value ?? '');
    setEditing(false);
  }

  return (
    <div className="group">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">{label}</p>
      {editing ? (
        <div className="flex items-center gap-2">
          <input
            type={type}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            autoFocus
            placeholder={placeholder}
            className="flex-1 px-3 py-2 rounded-lg border border-blue-300 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-50 transition-all"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') handleCancel();
            }}
          />
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-7 h-7 flex items-center justify-center rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? <div className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : <Check className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleCancel}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-gray-400 shrink-0" />
          <span className={`text-sm flex-1 ${value ? 'text-gray-800' : 'text-gray-400 italic'}`}>
            {value || placeholder || 'Não definido'}
          </span>
          <button
            onClick={() => setEditing(true)}
            className="w-6 h-6 flex items-center justify-center rounded-md text-gray-300 hover:text-gray-500 hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-all"
          >
            <Edit2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [tickets, setTickets] = useState<TicketWithRelations[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getCustomerWithTickets(id);
      if (!result) {
        setError('Cliente não encontrado');
        return;
      }
      setCustomer(result.customer);
      setTickets(result.tickets);
      setConversations(result.recent_conversations);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar cliente');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleFieldSave(field: keyof UpdateCustomerPayload, value: string) {
    if (!customer) return;
    const updated = await updateCustomer(customer.id, { [field]: value || null });
    setCustomer(updated);
  }

  const displayName = customer
    ? customer.name || customer.email || customer.phone || `Cliente ${customer.id.slice(0, 8)}`
    : '';

  const initials = customer
    ? (customer.name || customer.email || '??').slice(0, 2).toUpperCase()
    : '??';

  if (loading) {
    return (
      <div className="flex flex-col h-full bg-gray-50">
        <div className="bg-white border-b border-gray-100 px-6 py-4">
          <div className="h-5 w-48 bg-gray-100 rounded-lg animate-pulse" />
        </div>
        <div className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4 animate-pulse">
            <div className="w-16 h-16 rounded-full bg-gray-100 mx-auto" />
            <div className="h-4 w-32 bg-gray-100 rounded mx-auto" />
            <div className="space-y-3">
              {[1, 2, 3].map((i) => <div key={i} className="h-4 bg-gray-100 rounded" />)}
            </div>
          </div>
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-3 animate-pulse">
              {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-gray-100 rounded-xl" />)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-20">
        <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
          <AlertCircle className="w-7 h-7 text-red-400" />
        </div>
        <p className="text-gray-700 font-medium">{error || 'Cliente não encontrado'}</p>
        <button
          onClick={() => navigate('/customers')}
          className="mt-4 px-4 py-2 rounded-xl bg-gray-100 text-sm text-gray-600 hover:bg-gray-200 transition-colors"
        >
          Voltar para clientes
        </button>
      </div>
    );
  }

  const openTickets = tickets.filter((t) => t.status !== 'closed' && t.status !== 'resolved');

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-6 py-4 shrink-0 flex items-center gap-4">
        <button
          onClick={() => navigate('/customers')}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-sm font-bold text-slate-600 shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <h1 className="text-base font-semibold text-gray-900 truncate">{displayName}</h1>
            <p className="text-xs text-gray-400">Cliente desde {formatDate(customer.created_at)}</p>
          </div>
        </div>
        {openTickets.length > 0 && (
          <span className="ml-auto px-2.5 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold border border-green-200">
            {openTickets.length} ticket{openTickets.length !== 1 ? 's' : ''} aberto{openTickets.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-6xl">
          <div className="space-y-5">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <div className="flex flex-col items-center text-center mb-6">
                <div className="w-16 h-16 rounded-2xl bg-slate-200 flex items-center justify-center text-xl font-bold text-slate-600 mb-3">
                  {initials}
                </div>
                <h2 className="text-base font-semibold text-gray-900">{displayName}</h2>
                {customer.external_source && (
                  <span className="text-xs text-gray-400 mt-1 capitalize">via {customer.external_source}</span>
                )}
              </div>

              <div className="space-y-4">
                <EditableField
                  label="Nome"
                  value={customer.name}
                  onSave={(v) => handleFieldSave('name', v)}
                  icon={User}
                  placeholder="Nome completo"
                />
                <EditableField
                  label="E-mail"
                  value={customer.email}
                  onSave={(v) => handleFieldSave('email', v)}
                  icon={Mail}
                  type="email"
                  placeholder="Endereço de e-mail"
                />
                <EditableField
                  label="Telefone"
                  value={customer.phone}
                  onSave={(v) => handleFieldSave('phone', v)}
                  icon={Phone}
                  type="tel"
                  placeholder="Número de telefone"
                />
              </div>

              <div className="mt-5 pt-5 border-t border-gray-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">ID do Cliente</span>
                  <span className="text-xs font-mono text-gray-400">{customer.id.slice(0, 8)}...</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Criado</span>
                  <span className="text-xs text-gray-700">{formatDate(customer.created_at)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Total de tickets</span>
                  <span className="text-xs font-semibold text-gray-800">{tickets.length}</span>
                </div>
              </div>
            </div>

            {conversations.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-gray-400" />
                  Conversas Recentes
                </h3>
                <div className="space-y-3">
                  {conversations.map((conv) => (
                    <div key={conv.id} className="flex items-center gap-3 py-2">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                        <MessageSquare className="w-3.5 h-3.5 text-blue-500" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-mono text-gray-500 truncate">{conv.id.slice(0, 12)}...</p>
                        <div className="flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3 text-gray-400" />
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(conv.last_message_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Ticket className="w-4 h-4 text-gray-400" />
                  Tickets
                  <span className="text-xs font-normal text-gray-400">({tickets.length})</span>
                </h3>
              </div>

              {tickets.length === 0 ? (
                <div className="py-12 text-center">
                  <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
                    <Ticket className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-sm text-gray-500">Nenhum ticket ainda</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-50">
                  {tickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      className="px-5 py-4 hover:bg-gray-50/80 transition-colors group"
                    >
                      <div className="flex items-start gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-1.5">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium border ${STATUS_STYLES[ticket.status]}`}
                            >
                              {ticket.status.replace('_', ' ')}
                            </span>
                            <span className={`text-xs font-semibold capitalize ${PRIORITY_STYLES[ticket.priority]}`}>
                              {ticket.priority}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-gray-800 truncate">
                            {ticket.subject || `Ticket #${ticket.id.slice(0, 8)}`}
                          </p>
                          <div className="flex items-center gap-4 mt-1.5">
                            <div className="flex items-center gap-1">
                              <Hash className="w-3 h-3 text-gray-300" />
                              <span className="text-xs font-mono text-gray-400">{ticket.id.slice(0, 8)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-400">{formatDate(ticket.created_at)}</span>
                            </div>
                            {ticket.channel && (
                              <span className="text-xs text-gray-400 capitalize">{ticket.channel.name}</span>
                            )}
                          </div>
                        </div>
                        <Link
                          to={`/tickets/${ticket.id}`}
                          className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-300 hover:text-blue-600 hover:bg-blue-50 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                          onClick={(e) => e.stopPropagation()}
                          title="Abrir ticket"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
