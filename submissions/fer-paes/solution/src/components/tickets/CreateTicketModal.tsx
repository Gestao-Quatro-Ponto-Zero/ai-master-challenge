import { useState, useEffect } from 'react';
import { X, Plus, Search, User, Loader2 } from 'lucide-react';
import { createTicket } from '../../services/ticketService';
import { getCustomers } from '../../services/customerService';
import type { Channel, Customer, CreateTicketPayload, TicketPriority } from '../../types';

interface Props {
  channels: Channel[];
  onCreated: () => void;
  onClose: () => void;
}

const PRIORITIES: { value: TicketPriority; label: string }[] = [
  { value: 'low',    label: 'Baixa' },
  { value: 'medium', label: 'Média' },
  { value: 'high',   label: 'Alta' },
  { value: 'urgent', label: 'Urgente' },
];

export default function CreateTicketModal({ channels, onCreated, onClose }: Props) {
  const [customerSearch, setCustomerSearch] = useState('');
  const [customers, setCustomers]           = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerLoading, setCustomerLoading]   = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [subject,        setSubject]        = useState('');
  const [channelId,      setChannelId]      = useState(channels[0]?.id ?? '');
  const [priority,       setPriority]       = useState<TicketPriority>('medium');
  const [initialMessage, setInitialMessage] = useState('');
  const [submitting,     setSubmitting]     = useState(false);
  const [error,          setError]          = useState('');

  useEffect(() => {
    if (channels.length > 0 && !channelId) setChannelId(channels[0].id);
  }, [channels, channelId]);

  useEffect(() => {
    if (!customerSearch.trim()) { setCustomers([]); setShowDropdown(false); return; }
    const timer = setTimeout(async () => {
      setCustomerLoading(true);
      try {
        const results = await getCustomers({ search: customerSearch });
        setCustomers(results.map((r) => r as unknown as Customer));
        setShowDropdown(true);
      } finally {
        setCustomerLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [customerSearch]);

  function selectCustomer(c: Customer) {
    setSelectedCustomer(c);
    setCustomerSearch(c.name ?? c.email ?? c.id);
    setShowDropdown(false);
  }

  function clearCustomer() {
    setSelectedCustomer(null);
    setCustomerSearch('');
    setCustomers([]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCustomer) { setError('Selecione um cliente.'); return; }
    if (!initialMessage.trim()) { setError('A mensagem inicial é obrigatória.'); return; }
    if (!channelId) { setError('Selecione um canal.'); return; }

    setSubmitting(true);
    setError('');
    try {
      const payload: CreateTicketPayload = {
        customer_id:     selectedCustomer.id,
        channel_id:      channelId,
        subject:         subject.trim() || undefined,
        initial_message: initialMessage.trim(),
        priority,
      };
      await createTicket(payload);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar ticket.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
              <Plus className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Novo Ticket</h2>
              <p className="text-xs text-gray-400">Criar solicitação manualmente</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-auto">
          <div className="px-6 py-5 space-y-4">
            {error && (
              <div className="px-3 py-2.5 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="relative">
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Cliente <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input
                  type="text"
                  value={customerSearch}
                  onChange={(e) => { setCustomerSearch(e.target.value); if (selectedCustomer) setSelectedCustomer(null); }}
                  placeholder="Buscar por nome ou e-mail..."
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                />
                {customerLoading && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
                )}
              </div>

              {selectedCustomer && (
                <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-xl">
                  <div className="w-6 h-6 rounded-full bg-blue-200 flex items-center justify-center flex-shrink-0">
                    <User className="w-3 h-3 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-blue-900 truncate">{selectedCustomer.name ?? 'Sem nome'}</p>
                    {selectedCustomer.email && <p className="text-xs text-blue-500 truncate">{selectedCustomer.email}</p>}
                  </div>
                  <button type="button" onClick={clearCustomer} className="text-blue-400 hover:text-blue-600 transition-colors">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {showDropdown && customers.length > 0 && !selectedCustomer && (
                <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                  {customers.slice(0, 8).map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => selectCustomer(c)}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-gray-50 transition-colors text-left"
                    >
                      <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                        <User className="w-3.5 h-3.5 text-gray-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{c.name ?? 'Sem nome'}</p>
                        {c.email && <p className="text-xs text-gray-400 truncate">{c.email}</p>}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {showDropdown && customers.length === 0 && !customerLoading && customerSearch.trim() && (
                <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg px-4 py-3 text-sm text-gray-400">
                  Nenhum cliente encontrado
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Assunto</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Descreva brevemente o assunto..."
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  Canal <span className="text-red-500">*</span>
                </label>
                <select
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                >
                  {channels.map((ch) => (
                    <option key={ch.id} value={ch.id}>{ch.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Prioridade</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as TicketPriority)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                >
                  {PRIORITIES.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Mensagem inicial <span className="text-red-500">*</span>
              </label>
              <textarea
                value={initialMessage}
                onChange={(e) => setInitialMessage(e.target.value)}
                rows={4}
                placeholder="Descreva o problema ou solicitação do cliente..."
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all resize-none"
              />
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-100 flex gap-3 shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !selectedCustomer || !initialMessage.trim()}
              className="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              {submitting ? 'Criando...' : 'Criar Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
