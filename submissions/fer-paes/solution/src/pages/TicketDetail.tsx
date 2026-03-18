import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, Lock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useAuthorization } from '../hooks/useAuthorization';
import { getTicketById, assignTicket, closeTicket, changeStatus } from '../services/ticketService';
import { markFirstResponse, getTicketSLA } from '../services/slaService';
import {
  getConversationByTicket,
  getConversationMessages,
  countConversationMessages,
} from '../services/conversationService';
import { createMessage, type CreateMessageData, type MessageWithAttachments } from '../services/messageService';
import TicketHeader from '../components/tickets/TicketHeader';
import MessageList from '../components/tickets/MessageList';
import MessageComposer from '../components/tickets/MessageComposer';
import EmailThreadView from '../components/tickets/EmailThreadView';
import EmailComposer from '../components/tickets/EmailComposer';
import PhoneCallView from '../components/tickets/PhoneCallView';
import ResolutionPanel from '../components/tickets/ResolutionPanel';
import AssignTicketModal from '../components/tickets/AssignTicketModal';
import SLAPanel from '../components/tickets/SLAPanel';
import TagSelector from '../components/tickets/TagSelector';
import AnswerFeedback from '../components/tickets/AnswerFeedback';
import type { TicketWithRelations, TicketStatus, Conversation, TicketSLA, MacroContext } from '../types';

const PAGE_SIZE = 20;

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const { hasPermission } = useAuthorization();
  const canReply = hasPermission('tickets.reply');

  const [ticket, setTicket] = useState<TicketWithRelations | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<MessageWithAttachments[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scrollToBottom, setScrollToBottom] = useState(false);
  const [ticketSLA, setTicketSLA] = useState<TicketSLA | null>(null);
  const offsetRef = useRef(0);

  const loadTicket = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const t = await getTicketById(id);
      if (!t) {
        setError('Ticket não encontrado');
        return;
      }
      setTicket(t);

      const result = await getConversationByTicket(id);
      if (result) {
        setConversation(result.conversation);
        const total = await countConversationMessages(result.conversation.id);
        setTotalMessages(total);

        const offset = Math.max(0, total - PAGE_SIZE);
        offsetRef.current = offset;
        const msgs = await getConversationMessages(result.conversation.id, PAGE_SIZE, offset);
        setMessages(msgs);
        setScrollToBottom(true);
      }

      const sla = await getTicketSLA(id);
      setTicketSLA(sla);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar o ticket');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadTicket();
  }, [loadTicket]);

  const hasMore = messages.length < totalMessages;

  async function handleLoadMore() {
    if (!conversation || loadingMore) return;
    setLoadingMore(true);
    try {
      const newOffset = Math.max(0, offsetRef.current - PAGE_SIZE);
      const older = await getConversationMessages(conversation.id, PAGE_SIZE, newOffset);
      offsetRef.current = newOffset;
      setMessages((prev) => [...older, ...prev]);
    } finally {
      setLoadingMore(false);
    }
  }

  async function handleSend(data: Pick<CreateMessageData, 'message' | 'attachments'>) {
    if (!conversation || !user) return;

    const msg = await createMessage({
      conversation_id: conversation.id,
      sender_type: 'operator',
      sender_id: user.id,
      message: data.message,
      message_type: 'text',
      attachments: data.attachments,
    });

    setMessages((prev) => [...prev, msg]);
    setTotalMessages((n) => n + 1);
    setScrollToBottom(true);

    if (ticket) {
      markFirstResponse(ticket.id).then(async () => {
        const sla = await getTicketSLA(ticket.id);
        setTicketSLA(sla);
      }).catch(() => {});
      const updated = await getTicketById(ticket.id);
      if (updated) setTicket(updated);
    }
  }

  async function handleAddNote(text: string) {
    await handleSend({ message: text, attachments: [] });
  }

  async function handleStatusChange(newStatus: TicketStatus) {
    if (!ticket || !user) return;
    setActionLoading(true);
    try {
      await changeStatus(ticket.id, newStatus, user.id);
      const updated = await getTicketById(ticket.id);
      if (updated) setTicket(updated);
    } finally {
      setActionLoading(false);
    }
  }

  function handleAssign() {
    setShowAssignModal(true);
  }

  async function handleAssignConfirm(userId: string) {
    if (!ticket || !user) return;
    setActionLoading(true);
    try {
      await assignTicket(ticket.id, userId, user.id);
      const updated = await getTicketById(ticket.id);
      if (updated) setTicket(updated);
      setShowAssignModal(false);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleClose() {
    if (!ticket || !user) return;
    setActionLoading(true);
    try {
      await closeTicket(ticket.id, user.id);
      navigate('/tickets');
    } finally {
      setActionLoading(false);
    }
  }

  function handleResolutionSaved(notes: string) {
    if (ticket) setTicket({ ...ticket, resolution_notes: notes });
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="bg-white border-b border-gray-100 px-6 py-4">
          <div className="h-5 w-48 bg-gray-100 rounded-lg animate-pulse mb-3" />
          <div className="flex gap-3">
            <div className="h-7 w-20 bg-gray-100 rounded-lg animate-pulse" />
            <div className="h-7 w-16 bg-gray-100 rounded-lg animate-pulse" />
            <div className="h-7 w-28 bg-gray-100 rounded-lg animate-pulse" />
          </div>
        </div>
        <div className="flex-1 px-6 py-6 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
              <div className="h-12 w-64 bg-gray-100 rounded-2xl animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-20">
        <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
          <AlertCircle className="w-7 h-7 text-red-400" />
        </div>
        <p className="text-gray-700 font-medium">{error || 'Ticket não encontrado'}</p>
        <button
          onClick={() => navigate('/tickets')}
          className="mt-4 px-4 py-2 rounded-xl bg-gray-100 text-sm text-gray-600 hover:bg-gray-200 transition-colors"
        >
          Voltar para tickets
        </button>
      </div>
    );
  }

  const isClosed = ticket.status === 'closed';
  const channelType = ticket.channel?.type ?? 'chat';
  const isPhone = channelType === 'phone';
  const isEmail = channelType === 'email' || channelType === 'social';
  const isChat = !isPhone && !isEmail;

  const macroCtx: MacroContext = {
    customer_name: ticket?.customer?.name ?? ticket?.customer?.email ?? 'Cliente',
    ticket_id: ticket?.id,
    agent_name: profile?.full_name ?? user?.email ?? 'Agente',
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <TicketHeader
        ticket={ticket}
        onStatusChange={handleStatusChange}
        onAssign={handleAssign}
        onClose={handleClose}
        loading={actionLoading}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex flex-col flex-1 overflow-hidden">
          {isPhone ? (
            <PhoneCallView
              ticket={ticket}
              messages={messages}
              hasMore={hasMore}
              onLoadMore={handleLoadMore}
              loadingMore={loadingMore}
              onAddNote={handleAddNote}
              readonly={isClosed || !canReply}
              onResolutionSaved={handleResolutionSaved}
            />
          ) : isEmail ? (
            <>
              <EmailThreadView
                messages={messages}
                hasMore={hasMore}
                onLoadMore={handleLoadMore}
                loadingMore={loadingMore}
                scrollToBottom={scrollToBottom}
                customerName={ticket.customer?.name || undefined}
                customerEmail={ticket.customer?.email || undefined}
                operatorName={ticket.assigned_user?.full_name || ticket.assigned_user?.email || undefined}
                ticketSubject={ticket.subject}
                ticketDescription={ticket.description}
              />

              {isClosed ? (
                <div className="bg-white border-t border-gray-100 px-6 py-4 text-center">
                  <p className="text-sm text-gray-400">Este ticket está fechado. Reabra-o para responder.</p>
                </div>
              ) : !canReply ? (
                <div className="bg-white border-t border-gray-100 px-6 py-4 flex items-center justify-center gap-2 text-gray-400">
                  <Lock className="w-3.5 h-3.5" />
                  <p className="text-sm">Você não tem permissão para responder tickets.</p>
                </div>
              ) : (
                <EmailComposer
                  onSend={handleSend}
                  toName={ticket.customer?.name || undefined}
                  toEmail={ticket.customer?.email || undefined}
                  subject={ticket.subject}
                  macroContext={macroCtx}
                />
              )}
            </>
          ) : (
            <>
              <MessageList
                messages={messages}
                hasMore={hasMore}
                onLoadMore={handleLoadMore}
                loadingMore={loadingMore}
                scrollToBottom={scrollToBottom}
                customerName={ticket.customer?.name || ticket.customer?.email}
                operatorName={ticket.assigned_user?.full_name || ticket.assigned_user?.email}
              />

              {isClosed ? (
                <div className="bg-white border-t border-gray-100 px-6 py-4 text-center">
                  <p className="text-sm text-gray-400">Este ticket está fechado. Reabra-o para responder.</p>
                </div>
              ) : !canReply ? (
                <div className="bg-white border-t border-gray-100 px-6 py-4 flex items-center justify-center gap-2 text-gray-400">
                  <Lock className="w-3.5 h-3.5" />
                  <p className="text-sm">Você não tem permissão para responder tickets.</p>
                </div>
              ) : (
                <MessageComposer
                  onSend={handleSend}
                  placeholder="Responder ao cliente... (/ para macros)"
                  macroContext={macroCtx}
                />
              )}
            </>
          )}
        </div>

        <aside className="w-72 bg-white border-l border-gray-100 overflow-y-auto flex-shrink-0">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Detalhes</h2>
          </div>

          <div className="px-5 py-4 space-y-5">
            {ticketSLA && !isClosed && (
              <>
                <SLAPanel sla={ticketSLA} />
                <div className="h-px bg-gray-100" />
              </>
            )}

            {isChat && (
              <>
                <ResolutionPanel
                  ticketId={ticket.id}
                  initialNotes={ticket.resolution_notes}
                  readonly={isClosed}
                  onSaved={handleResolutionSaved}
                  compact
                />
                <div className="h-px bg-gray-100" />
              </>
            )}

            {isEmail && (
              <>
                <ResolutionPanel
                  ticketId={ticket.id}
                  initialNotes={ticket.resolution_notes}
                  readonly={isClosed}
                  onSaved={handleResolutionSaved}
                  compact
                />
                <div className="h-px bg-gray-100" />
              </>
            )}

            <TagSelector ticketId={ticket.id} readonly={isClosed} />
            <div className="h-px bg-gray-100" />

            {ticket.customer && (
              <section>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">Cliente</p>
                <div className="flex items-start gap-2.5">
                  <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-sm font-bold text-slate-600 shrink-0 border border-slate-200">
                    {(ticket.customer.name || ticket.customer.email || '?')[0].toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">
                      {ticket.customer.name || 'Desconhecido'}
                    </p>
                    {ticket.customer.email && (
                      <p className="text-xs text-gray-400 truncate mt-0.5">{ticket.customer.email}</p>
                    )}
                    {ticket.customer.phone && (
                      <p className="text-xs text-gray-400 mt-0.5">{ticket.customer.phone}</p>
                    )}
                  </div>
                </div>
              </section>
            )}

            <div className="h-px bg-gray-100" />

            <section>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">Atribuído a</p>
              {ticket.assigned_user ? (
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700 shrink-0">
                    {(ticket.assigned_user.full_name || ticket.assigned_user.email)[0].toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">
                      {ticket.assigned_user.full_name || ticket.assigned_user.email}
                    </p>
                    {ticket.assigned_user.full_name && (
                      <p className="text-xs text-gray-400 truncate">{ticket.assigned_user.email}</p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-400 italic">Não atribuído</p>
              )}
            </section>

            <div className="h-px bg-gray-100" />

            <section>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">Atividade</p>
              <div className="space-y-2.5">
                {!isPhone && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Mensagens</span>
                    <span className="text-xs font-semibold text-gray-800 tabular-nums">{totalMessages}</span>
                  </div>
                )}
                {isPhone && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Anotações</span>
                    <span className="text-xs font-semibold text-gray-800 tabular-nums">
                      {messages.filter((m) => m.sender_type === 'operator' || m.sender_type === 'agent').length}
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{isPhone ? 'Data da ligação' : 'Criado'}</span>
                  <span className="text-xs font-medium text-gray-700">
                    {new Date(ticket.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Atualizado</span>
                  <span className="text-xs font-medium text-gray-700">
                    {new Date(ticket.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                {ticket.closed_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Fechado</span>
                    <span className="text-xs font-medium text-gray-700">
                      {new Date(ticket.closed_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                )}
              </div>
            </section>

            {(ticket.source || ticket.channel) && (
              <>
                <div className="h-px bg-gray-100" />
                <section>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">Origem</p>
                  <div className="space-y-2">
                    {ticket.channel && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Canal</span>
                        <span className="text-xs font-medium text-gray-700 capitalize">{ticket.channel.name}</span>
                      </div>
                    )}
                    {ticket.source && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Fonte</span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-lg bg-gray-100 text-xs text-gray-600 font-medium capitalize">
                          {ticket.source}
                        </span>
                      </div>
                    )}
                  </div>
                </section>
              </>
            )}

            {conversation && !isPhone && (
              <>
                <div className="h-px bg-gray-100" />
                <section>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">Conversa</p>
                  <p className="text-xs font-mono text-gray-400 break-all leading-relaxed">
                    {conversation.id.slice(0, 20)}...
                  </p>
                  {conversation.last_message_at && (
                    <p className="text-xs text-gray-400 mt-1.5">
                      Última atividade: {new Date(conversation.last_message_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  )}
                </section>
              </>
            )}

            <div className="h-px bg-gray-100" />
            <AnswerFeedback
              ticketId={ticket.id}
              conversationId={conversation?.id ?? null}
            />
          </div>
        </aside>
      </div>

      {showAssignModal && ticket && (
        <AssignTicketModal
          ticket={ticket}
          currentUserId={user!.id}
          onConfirm={handleAssignConfirm}
          onClose={() => setShowAssignModal(false)}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
