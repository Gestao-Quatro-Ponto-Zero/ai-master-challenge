import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, MessageCircle, StickyNote } from 'lucide-react';
import {
  getConversation, getMessages, pollMessages, sendOperatorMessage, sendAttachmentMessage,
  type WorkspaceTicket, type MessageWithAttachments,
} from '../../services/workspaceService';
import MessageBubble      from './MessageBubble';
import MessageComposer    from './MessageComposer';
import TicketActionsMenu  from './TicketActionsMenu';
import InternalNotesPanel from './InternalNotesPanel';

interface Props {
  ticket:    WorkspaceTicket;
  userId:    string;
  onUpdated: () => void;
}

type PanelTab = 'conversation' | 'notes';

const POLL_INTERVAL = 3000;

const TABS: { id: PanelTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'conversation', label: 'Conversation',   icon: MessageCircle },
  { id: 'notes',        label: 'Internal Notes', icon: StickyNote    },
];

export default function ConversationPanel({ ticket, userId, onUpdated }: Props) {
  const [activeTab,      setActiveTab]     = useState<PanelTab>('conversation');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages,       setMessages]      = useState<MessageWithAttachments[]>([]);
  const [loading,        setLoading]       = useState(true);
  const bottomRef   = useRef<HTMLDivElement>(null);
  const pollRef     = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastMsgTime = useRef<string>(new Date(0).toISOString());

  const scrollToBottom = () =>
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });

  const loadConversation = useCallback(async () => {
    setLoading(true);
    setMessages([]);
    try {
      const conv = await getConversation(ticket.id);
      if (!conv) { setLoading(false); return; }

      setConversationId(conv.id);
      const msgs = await getMessages(conv.id, 50, 0);
      setMessages(msgs);
      if (msgs.length > 0) {
        lastMsgTime.current = msgs[msgs.length - 1].created_at;
      }
    } catch { } finally { setLoading(false); }
  }, [ticket.id]);

  useEffect(() => {
    setActiveTab('conversation');
    loadConversation();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [loadConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!conversationId) return;

    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const newMsgs = await pollMessages(conversationId, lastMsgTime.current);
        if (newMsgs.length > 0) {
          setMessages((prev) => [...prev, ...newMsgs]);
          lastMsgTime.current = newMsgs[newMsgs.length - 1].created_at;
        }
      } catch { }
    }, POLL_INTERVAL);

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [conversationId]);

  const handleSend = useCallback(async (text: string) => {
    if (!conversationId) return;
    const msg = await sendOperatorMessage(conversationId, ticket.id, userId, text);
    setMessages((prev) => [...prev, msg]);
    lastMsgTime.current = msg.created_at;
    onUpdated();
  }, [conversationId, ticket.id, userId, onUpdated]);

  const handleAttach = useCallback(async (file: File) => {
    if (!conversationId) return;
    const msg = await sendAttachmentMessage(conversationId, ticket.id, userId, file);
    setMessages((prev) => [...prev, msg]);
    lastMsgTime.current = msg.created_at;
  }, [conversationId, ticket.id, userId]);

  const isResolved = ticket.status === 'resolved' || ticket.status === 'closed';
  const customer   = ticket.customer as { name?: string; email?: string } | null;

  return (
    <div className="flex flex-col h-full bg-slate-950 min-w-0">
      {/* Header */}
      <div className="px-5 pt-3.5 pb-0 border-b border-white/5 shrink-0">
        <div className="flex items-start justify-between gap-4 pb-3">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-white truncate">
              {ticket.subject || 'No subject'}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {customer?.name || customer?.email || 'Unknown customer'}
              {ticket.channel && (
                <span className="ml-2 capitalize text-slate-600">
                  · {(ticket.channel as { name?: string }).name}
                </span>
              )}
            </p>
          </div>

          <TicketActionsMenu
            ticketId={ticket.id}
            status={ticket.status}
            priority={ticket.priority}
            userId={userId}
            onUpdated={onUpdated}
          />
        </div>

        {/* Tab bar */}
        <div className="flex gap-0">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                activeTab === id
                  ? id === 'notes'
                    ? 'text-amber-400 border-amber-400'
                    : 'text-blue-400 border-blue-400'
                  : 'text-slate-600 border-transparent hover:text-slate-400'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
              {id === 'notes' && (
                <span className="text-xs text-slate-700 font-normal ml-0.5">internal</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Panel content */}
      {activeTab === 'conversation' ? (
        <>
          <div className="flex-1 overflow-y-auto px-5 py-4">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-5 h-5 animate-spin text-slate-700" />
              </div>
            ) : !conversationId ? (
              <div className="flex flex-col items-center justify-center h-full gap-3">
                <MessageCircle className="w-10 h-10 text-slate-800" />
                <p className="text-xs text-slate-700">No conversation found for this ticket.</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full gap-3">
                <MessageCircle className="w-10 h-10 text-slate-800" />
                <p className="text-xs text-slate-700">No messages yet.</p>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
              </>
            )}
            <div ref={bottomRef} />
          </div>

          <MessageComposer
            disabled={isResolved || !conversationId}
            onSend={handleSend}
            onAttach={handleAttach}
          />
        </>
      ) : (
        <InternalNotesPanel
          key={ticket.id}
          ticketId={ticket.id}
          userId={userId}
        />
      )}
    </div>
  );
}
