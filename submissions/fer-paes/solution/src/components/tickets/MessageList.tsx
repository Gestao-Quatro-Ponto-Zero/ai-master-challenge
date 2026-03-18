import { useEffect, useRef } from 'react';
import { Bot, User, Settings, Headphones, ChevronUp, FileText, Image, Film, Music, File, Download } from 'lucide-react';
import type { SenderType, Attachment } from '../../types';
import type { MessageWithAttachments } from '../../services/messageService';

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
}

function groupMessagesByDate(messages: MessageWithAttachments[]): { date: string; messages: MessageWithAttachments[] }[] {
  const groups: { date: string; messages: MessageWithAttachments[] }[] = [];
  let lastDate = '';

  for (const msg of messages) {
    const dateStr = formatDate(msg.created_at);
    if (dateStr !== lastDate) {
      groups.push({ date: dateStr, messages: [] });
      lastDate = dateStr;
    }
    groups[groups.length - 1].messages.push(msg);
  }

  return groups;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function AttachmentItem({ attachment, isRight }: { attachment: Attachment; isRight: boolean }) {
  const isImage = attachment.file_type?.startsWith('image/') ?? false;

  if (isImage && attachment.file_url) {
    return (
      <a
        href={attachment.file_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block mt-2 max-w-[200px]"
      >
        <img
          src={attachment.file_url}
          alt="attachment"
          className="rounded-xl object-cover w-full max-h-[200px]"
        />
      </a>
    );
  }

  function getIcon() {
    const t = attachment.file_type || '';
    if (t.startsWith('video/')) return Film;
    if (t.startsWith('audio/')) return Music;
    if (t === 'application/pdf' || t.startsWith('text/')) return FileText;
    if (t.startsWith('image/')) return Image;
    return File;
  }

  const Icon = getIcon();

  return (
    <a
      href={attachment.file_url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-center gap-2 mt-2 px-3 py-2 rounded-xl text-xs transition-opacity hover:opacity-80 ${
        isRight
          ? 'bg-white/20 text-white'
          : 'bg-gray-100 text-gray-600'
      }`}
    >
      <Icon className="w-4 h-4 shrink-0" />
      <span className="truncate max-w-[120px]">
        {attachment.file_url?.split('/').pop() || 'file'}
      </span>
      {attachment.file_size && (
        <span className="opacity-70 shrink-0">{formatBytes(attachment.file_size)}</span>
      )}
      <Download className="w-3 h-3 shrink-0 opacity-70" />
    </a>
  );
}

interface SenderConfig {
  align: 'left' | 'right' | 'center';
  bubble: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  avatarBg: string;
  avatarIcon: string;
}

const SENDER_CONFIG: Record<SenderType, SenderConfig> = {
  customer: {
    align: 'left',
    bubble: 'bg-white border border-gray-200 text-gray-800',
    label: 'Customer',
    icon: User,
    avatarBg: 'bg-gray-100',
    avatarIcon: 'text-gray-500',
  },
  operator: {
    align: 'right',
    bubble: 'bg-blue-600 text-white',
    label: 'Operator',
    icon: Headphones,
    avatarBg: 'bg-blue-100',
    avatarIcon: 'text-blue-600',
  },
  agent: {
    align: 'right',
    bubble: 'bg-teal-600 text-white',
    label: 'Agent',
    icon: Bot,
    avatarBg: 'bg-teal-100',
    avatarIcon: 'text-teal-600',
  },
  system: {
    align: 'center',
    bubble: 'bg-gray-100 text-gray-500 text-xs',
    label: 'System',
    icon: Settings,
    avatarBg: 'bg-gray-100',
    avatarIcon: 'text-gray-400',
  },
  bot: {
    align: 'right',
    bubble: 'bg-teal-600 text-white',
    label: 'Bot',
    icon: Bot,
    avatarBg: 'bg-teal-100',
    avatarIcon: 'text-teal-600',
  },
};

interface MessageBubbleProps {
  message: MessageWithAttachments;
  showAvatar: boolean;
  senderLabel?: string;
}

function isDeleted(msg: MessageWithAttachments): boolean {
  return !!(msg.metadata as Record<string, unknown> | null)?.deleted;
}

function MessageBubble({ message, showAvatar, senderLabel }: MessageBubbleProps) {
  const cfg = SENDER_CONFIG[message.sender_type] || SENDER_CONFIG.system;
  const deleted = isDeleted(message);

  if (cfg.align === 'center') {
    return (
      <div className="flex justify-center my-2">
        <span className="px-3 py-1 rounded-full bg-gray-100 text-xs text-gray-500">
          {message.message}
        </span>
      </div>
    );
  }

  const isRight = cfg.align === 'right';
  const Icon = cfg.icon;
  const displayName = senderLabel || cfg.label;

  return (
    <div className={`flex items-end gap-2 ${isRight ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-opacity ${
          showAvatar ? 'opacity-100' : 'opacity-0'
        } ${cfg.avatarBg}`}
        title={displayName}
      >
        {senderLabel ? (
          <span className={`text-xs font-semibold ${cfg.avatarIcon}`}>
            {senderLabel[0].toUpperCase()}
          </span>
        ) : (
          <Icon className={`w-3.5 h-3.5 ${cfg.avatarIcon}`} />
        )}
      </div>

      <div className={`max-w-[70%] flex flex-col gap-1 ${isRight ? 'items-end' : 'items-start'}`}>
        {showAvatar && (
          <span className="text-xs text-gray-400 px-1 font-medium">{displayName}</span>
        )}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm ${cfg.bubble} ${
            isRight ? 'rounded-br-sm' : 'rounded-bl-sm'
          } ${deleted ? 'opacity-50 italic' : ''}`}
        >
          {deleted ? (
            <span className="text-xs">Message deleted</span>
          ) : (
            <>
              {message.message && <p>{message.message}</p>}
              {message.attachments?.length > 0 && (
                <div className={`flex flex-col gap-1 ${message.message ? 'mt-2' : ''}`}>
                  {message.attachments.map((att) => (
                    <AttachmentItem key={att.id} attachment={att} isRight={isRight} />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
        <span className="text-xs text-gray-400 px-1">{formatTime(message.created_at)}</span>
      </div>
    </div>
  );
}

interface MessageListProps {
  messages: MessageWithAttachments[];
  hasMore: boolean;
  onLoadMore: () => void;
  loadingMore?: boolean;
  scrollToBottom?: boolean;
  customerName?: string;
  operatorName?: string;
}

export default function MessageList({
  messages,
  hasMore,
  onLoadMore,
  loadingMore,
  scrollToBottom,
  customerName,
  operatorName,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const senderLabels: Partial<Record<SenderType, string>> = {};
  if (customerName) senderLabels.customer = customerName;
  if (operatorName) senderLabels.operator = operatorName;

  const groups = groupMessagesByDate(messages);

  useEffect(() => {
    if (scrollToBottom && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [scrollToBottom, messages.length]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-center py-20">
        <div>
          <div className="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
            <Headphones className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 font-medium text-sm">No messages yet</p>
          <p className="text-gray-400 text-xs mt-1">Start the conversation below</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
      {hasMore && (
        <div className="flex justify-center">
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 text-xs text-gray-500 hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            <ChevronUp className="w-3.5 h-3.5" />
            {loadingMore ? 'Loading...' : 'Load previous messages'}
          </button>
        </div>
      )}

      {groups.map((group) => (
        <div key={group.date}>
          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400 font-medium px-2">{group.date}</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          <div className="space-y-1.5">
            {group.messages.map((msg, idx) => {
              const prev = idx > 0 ? group.messages[idx - 1] : null;
              const showAvatar = !prev || prev.sender_type !== msg.sender_type;
              const label = senderLabels[msg.sender_type];
              return (
                <MessageBubble key={msg.id} message={msg} showAvatar={showAvatar} senderLabel={label} />
              );
            })}
          </div>
        </div>
      ))}

      <div ref={bottomRef} />
    </div>
  );
}
