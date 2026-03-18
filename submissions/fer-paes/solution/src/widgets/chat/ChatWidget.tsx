import { useState, useCallback } from 'react';
import { MessageSquare, X, Minus } from 'lucide-react';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { sendChatMessage } from './chatApi';
import type { ChatMessage, ChatWidgetConfig } from './types';

interface Props {
  config: ChatWidgetConfig;
}

let msgCounter = 0;
function nextId() {
  return `msg-${++msgCounter}-${Date.now()}`;
}

export default function ChatWidget({ config }: Props) {
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: nextId(),
      content: 'Hi! How can we help you today?',
      sender: 'system',
      timestamp: new Date(),
    },
  ]);
  const [sending, setSending] = useState(false);
  const [ticketCreated, setTicketCreated] = useState(false);

  const handleSend = useCallback(
    async (text: string) => {
      const userMsg: ChatMessage = {
        id: nextId(),
        content: text,
        sender: 'customer',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setSending(true);

      try {
        const result = await sendChatMessage({
          session_id: config.sessionId,
          message: text,
          name: config.name,
          email: config.email,
          phone: config.phone,
        });

        if (!ticketCreated || result.is_new_ticket) {
          setTicketCreated(true);
          setMessages((prev) => [
            ...prev,
            {
              id: nextId(),
              content: "Your message has been received. An agent will be with you shortly.",
              sender: 'system',
              timestamp: new Date(),
            },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            content: 'Failed to send message. Please try again.',
            sender: 'system',
            timestamp: new Date(),
          },
        ]);
      } finally {
        setSending(false);
      }
    },
    [config, ticketCreated],
  );

  const title = config.title ?? 'Support Chat';
  const subtitle = config.subtitle ?? 'We usually reply in a few minutes';

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-blue-600 text-white shadow-lg shadow-blue-300/50 flex items-center justify-center hover:bg-blue-700 hover:scale-105 transition-all z-50"
        title="Open chat"
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 w-80 bg-white rounded-2xl shadow-2xl shadow-gray-300/40 border border-gray-100 flex flex-col z-50 transition-all duration-200 ${
        minimized ? 'h-14 overflow-hidden' : 'h-[480px]'
      }`}
    >
      <div className="flex items-center gap-3 px-4 py-3 bg-blue-600 rounded-t-2xl shrink-0">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center shrink-0">
          <MessageSquare className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white text-sm font-semibold truncate">{title}</p>
          {!minimized && (
            <p className="text-blue-200 text-xs truncate">{subtitle}</p>
          )}
        </div>
        <button
          onClick={() => setMinimized((m) => !m)}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          title={minimized ? 'Expand' : 'Minimize'}
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setOpen(false)}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          title="Close"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {!minimized && (
        <>
          <ChatMessages messages={messages} />
          <ChatInput
            onSend={handleSend}
            disabled={sending}
            placeholder={sending ? 'Sending...' : 'Type a message...'}
          />
        </>
      )}
    </div>
  );
}
