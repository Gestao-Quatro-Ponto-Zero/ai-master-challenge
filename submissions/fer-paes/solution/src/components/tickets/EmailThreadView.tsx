import { useEffect, useRef, useState } from 'react';
import { ChevronUp, Paperclip, FileText, Image, Film, Music, File, Download, Mail, Bot, Settings } from 'lucide-react';
import type { Attachment, SenderType } from '../../types';
import type { MessageWithAttachments } from '../../services/messageService';

function formatEmailDate(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (date.toDateString() === today.toDateString()) return `Hoje às ${timeStr}`;
  if (date.toDateString() === yesterday.toDateString()) return `Ontem às ${timeStr}`;
  return date.toLocaleDateString('pt-BR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(fileType: string | null) {
  const t = fileType || '';
  if (t.startsWith('video/')) return Film;
  if (t.startsWith('audio/')) return Music;
  if (t === 'application/pdf' || t.startsWith('text/')) return FileText;
  if (t.startsWith('image/')) return Image;
  return File;
}

function EmailAttachment({ attachment }: { attachment: Attachment }) {
  const isImage = attachment.file_type?.startsWith('image/') ?? false;

  if (isImage && attachment.file_url) {
    return (
      <a
        href={attachment.file_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block rounded-lg overflow-hidden border border-gray-200 hover:border-gray-300 transition-colors"
        style={{ maxWidth: 280 }}
      >
        <img
          src={attachment.file_url}
          alt="attachment"
          className="w-full object-cover"
          style={{ maxHeight: 200 }}
        />
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 text-xs text-gray-500">
          <Image className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">{attachment.file_url.split('/').pop() || 'image'}</span>
          {attachment.file_size && <span className="shrink-0">{formatBytes(attachment.file_size)}</span>}
        </div>
      </a>
    );
  }

  const Icon = getFileIcon(attachment.file_type);
  return (
    <a
      href={attachment.file_url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 text-xs text-gray-600 transition-colors"
    >
      <Icon className="w-4 h-4 shrink-0 text-gray-400" />
      <span className="truncate max-w-[160px]">{attachment.file_url?.split('/').pop() || 'file'}</span>
      {attachment.file_size && <span className="text-gray-400 shrink-0">{formatBytes(attachment.file_size)}</span>}
      <Download className="w-3.5 h-3.5 shrink-0 text-gray-400" />
    </a>
  );
}

interface EmailCardProps {
  message: MessageWithAttachments;
  customerName?: string;
  customerEmail?: string;
  operatorName?: string;
  operatorEmail?: string;
  replyIndex: number;
  isFirst: boolean;
}

function getSenderInfo(
  senderType: SenderType,
  customerName?: string,
  customerEmail?: string,
  operatorName?: string,
  operatorEmail?: string,
): { name: string; email?: string; initials: string; bgColor: string; textColor: string } {
  switch (senderType) {
    case 'customer':
      return {
        name: customerName || 'Cliente',
        email: customerEmail,
        initials: (customerName || customerEmail || 'C')[0].toUpperCase(),
        bgColor: 'bg-slate-100',
        textColor: 'text-slate-600',
      };
    case 'operator':
      return {
        name: operatorName || 'Operador',
        email: operatorEmail,
        initials: (operatorName || operatorEmail || 'O')[0].toUpperCase(),
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
      };
    case 'agent':
    case 'bot':
      return {
        name: 'Agente IA',
        initials: 'IA',
        bgColor: 'bg-teal-100',
        textColor: 'text-teal-700',
      };
    case 'system':
    default:
      return {
        name: 'Sistema',
        initials: 'S',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-500',
      };
  }
}

function isDeleted(msg: MessageWithAttachments): boolean {
  return !!(msg.metadata as Record<string, unknown> | null)?.deleted;
}

function EmailCard({
  message,
  customerName,
  customerEmail,
  operatorName,
  operatorEmail,
  replyIndex,
  isFirst,
}: EmailCardProps) {
  const [collapsed, setCollapsed] = useState(!isFirst && replyIndex > 0 && replyIndex < -1);

  if (message.sender_type === 'system') {
    return (
      <div className="flex items-center gap-3 py-1">
        <div className="flex-1 h-px bg-gray-100" />
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-100">
          <Settings className="w-3 h-3 text-gray-400" />
          <span className="text-xs text-gray-400">{message.message}</span>
        </div>
        <div className="flex-1 h-px bg-gray-100" />
      </div>
    );
  }

  const sender = getSenderInfo(
    message.sender_type,
    customerName,
    customerEmail,
    operatorName,
    operatorEmail,
  );

  const isCustomer = message.sender_type === 'customer';
  const isAgent = message.sender_type === 'agent' || message.sender_type === 'bot';
  const deleted = isDeleted(message);

  return (
    <div className={`rounded-xl border transition-all ${
      isCustomer
        ? 'border-gray-200 bg-white'
        : isAgent
        ? 'border-teal-100 bg-teal-50/40'
        : 'border-blue-100 bg-blue-50/40'
    }`}>
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer select-none"
        onClick={() => setCollapsed((c) => !c)}
      >
        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${sender.bgColor} ${sender.textColor}`}>
          {isAgent ? <Bot className="w-4 h-4" /> : sender.initials}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-2">
            <div className="flex items-baseline gap-2 min-w-0">
              <span className="text-sm font-semibold text-gray-800 truncate">{sender.name}</span>
              {sender.email && (
                <span className="text-xs text-gray-400 truncate hidden sm:block">&lt;{sender.email}&gt;</span>
              )}
            </div>
            <span className="text-xs text-gray-400 shrink-0">{formatEmailDate(message.created_at)}</span>
          </div>

          {collapsed && message.message && (
            <p className="text-xs text-gray-400 mt-0.5 truncate">{message.message}</p>
          )}
        </div>

        {message.attachments?.length > 0 && (
          <div className="flex items-center gap-1 text-gray-400 shrink-0">
            <Paperclip className="w-3.5 h-3.5" />
            <span className="text-xs">{message.attachments.length}</span>
          </div>
        )}
      </div>

      {!collapsed && (
        <div className="px-4 pb-4">
          <div className="h-px bg-gray-100 mb-3" />

          {deleted ? (
            <p className="text-sm text-gray-400 italic">Mensagem removida</p>
          ) : (
            <>
              {message.message && (
                <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {message.message}
                </div>
              )}

              {message.attachments?.length > 0 && (
                <div className={`flex flex-wrap gap-2 ${message.message ? 'mt-4' : ''}`}>
                  {message.attachments.map((att) => (
                    <EmailAttachment key={att.id} attachment={att} />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

interface EmailThreadViewProps {
  messages: MessageWithAttachments[];
  hasMore: boolean;
  onLoadMore: () => void;
  loadingMore?: boolean;
  scrollToBottom?: boolean;
  customerName?: string;
  customerEmail?: string;
  operatorName?: string;
  operatorEmail?: string;
  ticketSubject?: string | null;
  ticketDescription?: string | null;
}

export default function EmailThreadView({
  messages,
  hasMore,
  onLoadMore,
  loadingMore,
  scrollToBottom,
  customerName,
  customerEmail,
  operatorName,
  operatorEmail,
  ticketSubject,
  ticketDescription,
}: EmailThreadViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollToBottom && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [scrollToBottom, messages.length]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-start justify-center py-10 px-6">
        <div className="w-full max-w-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
              <Mail className="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-700">{ticketSubject || 'Sem assunto'}</p>
              <p className="text-xs text-gray-400">Nenhuma mensagem ainda</p>
            </div>
          </div>

          {ticketDescription && (
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold bg-slate-100 text-slate-600`}>
                  {(customerName || customerEmail || 'C')[0].toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700">{customerName || 'Cliente'}</p>
                  {customerEmail && <p className="text-xs text-gray-400">{customerEmail}</p>}
                </div>
              </div>
              <div className="h-px bg-gray-100 mb-3" />
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{ticketDescription}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-5">
      <div className="max-w-3xl mx-auto space-y-3">
        {hasMore && (
          <div className="flex justify-center mb-2">
            <button
              onClick={onLoadMore}
              disabled={loadingMore}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 text-xs text-gray-500 hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              <ChevronUp className="w-3.5 h-3.5" />
              {loadingMore ? 'Carregando...' : 'Carregar mensagens anteriores'}
            </button>
          </div>
        )}

        {messages.map((msg, idx) => (
          <EmailCard
            key={msg.id}
            message={msg}
            customerName={customerName}
            customerEmail={customerEmail}
            operatorName={operatorName}
            operatorEmail={operatorEmail}
            replyIndex={idx}
            isFirst={idx === 0}
          />
        ))}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
