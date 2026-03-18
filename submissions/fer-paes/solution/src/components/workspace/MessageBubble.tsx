import { Download, FileText, Image as ImageIcon } from 'lucide-react';
import type { MessageWithAttachments } from '../../services/workspaceService';
import type { SenderType } from '../../types';

interface Props {
  message:       MessageWithAttachments;
  senderName?:   string;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const SENDER_STYLES: Record<SenderType, {
  container: string;
  bubble:    string;
  nameColor: string;
  align:     'left' | 'right';
}> = {
  customer: {
    container: 'items-start',
    bubble:    'bg-slate-800 border border-white/6 text-white',
    nameColor: 'text-slate-400',
    align:     'left',
  },
  operator: {
    container: 'items-end',
    bubble:    'bg-blue-600 text-white',
    nameColor: 'text-blue-300',
    align:     'right',
  },
  agent: {
    container: 'items-start',
    bubble:    'bg-teal-900/60 border border-teal-500/20 text-teal-100',
    nameColor: 'text-teal-400',
    align:     'left',
  },
  bot: {
    container: 'items-start',
    bubble:    'bg-amber-900/50 border border-amber-500/20 text-amber-100',
    nameColor: 'text-amber-400',
    align:     'left',
  },
  system: {
    container: 'items-center',
    bubble:    'bg-transparent border-0 text-slate-600 italic text-xs',
    nameColor: '',
    align:     'left',
  },
};

const SENDER_LABELS: Record<SenderType, string> = {
  customer: 'Customer',
  operator: 'Operator',
  agent:    'AI Agent',
  bot:      'Bot',
  system:   '',
};

function AttachmentItem({ att }: { att: { file_url: string | null; file_type: string | null; file_size: number | null } }) {
  const isImage = att.file_type?.startsWith('image/');
  const url     = att.file_url ?? '#';

  if (isImage) {
    return (
      <a href={url} target="_blank" rel="noreferrer" className="block mt-2 rounded-xl overflow-hidden max-w-xs">
        <img src={url} alt="attachment" className="w-full max-h-60 object-cover rounded-xl" />
      </a>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="flex items-center gap-2.5 mt-2 px-3 py-2.5 rounded-xl bg-black/20 hover:bg-black/30 transition-colors max-w-xs"
    >
      {att.file_type?.includes('pdf') || att.file_type?.includes('doc')
        ? <FileText className="w-4 h-4 shrink-0 text-white/70" />
        : <ImageIcon className="w-4 h-4 shrink-0 text-white/70" />
      }
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-white/90 truncate">{url.split('/').pop() ?? 'file'}</p>
        {att.file_size && <p className="text-xs text-white/50">{formatBytes(att.file_size)}</p>}
      </div>
      <Download className="w-3.5 h-3.5 shrink-0 text-white/50" />
    </a>
  );
}

export default function MessageBubble({ message, senderName }: Props) {
  const type  = (message.sender_type ?? 'system') as SenderType;
  const style = SENDER_STYLES[type] ?? SENDER_STYLES.system;
  const isSystem = type === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-slate-600 italic px-3 py-1 bg-slate-900/50 rounded-full border border-white/4">
          {message.message}
        </span>
      </div>
    );
  }

  const deleted = (message.metadata as Record<string, unknown> | null)?.deleted === true;

  return (
    <div className={`flex flex-col ${style.container} mb-4`}>
      {/* Sender label */}
      <span className={`text-xs mb-1 ${style.nameColor}`}>
        {senderName || SENDER_LABELS[type]}
      </span>

      <div className={`max-w-sm ${style.align === 'right' ? 'ml-auto' : ''}`}>
        <div className={`px-4 py-2.5 rounded-2xl ${style.bubble} ${
          style.align === 'right' ? 'rounded-br-sm' : 'rounded-bl-sm'
        }`}>
          {deleted ? (
            <p className="text-xs opacity-50 italic">Message deleted</p>
          ) : (
            <>
              {message.message && (
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.message}</p>
              )}
              {message.attachments.length > 0 && message.attachments.map((att) => (
                <AttachmentItem key={att.id} att={att} />
              ))}
            </>
          )}
        </div>

        <p className={`text-xs text-slate-700 mt-1 ${style.align === 'right' ? 'text-right' : 'text-left'}`}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
