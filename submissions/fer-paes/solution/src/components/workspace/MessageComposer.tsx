import { useState, useRef, useCallback } from 'react';
import { Send, Paperclip, Loader2, X, FileText, Image as ImageIcon } from 'lucide-react';

interface Props {
  disabled:   boolean;
  onSend:     (text: string) => Promise<void>;
  onAttach:   (file: File)   => Promise<void>;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_TYPES = [
  'image/jpeg', 'image/png', 'image/gif', 'image/webp',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function MessageComposer({ disabled, onSend, onAttach }: Props) {
  const [text,         setText]         = useState('');
  const [sending,      setSending]      = useState(false);
  const [attaching,    setAttaching]    = useState(false);
  const [pendingFile,  setPendingFile]  = useState<File | null>(null);
  const [fileError,    setFileError]    = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || sending || disabled) return;

    setSending(true);
    try {
      await onSend(trimmed);
      setText('');
      if (textRef.current) {
        textRef.current.style.height = 'auto';
      }
    } catch { } finally { setSending(false); }
  }, [text, sending, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileError('');

    if (file.size > MAX_FILE_SIZE) {
      setFileError(`File too large. Max size is ${formatBytes(MAX_FILE_SIZE)}.`);
      return;
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      setFileError('File type not allowed. Accepted: images, PDF, DOC, TXT.');
      return;
    }

    setPendingFile(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleSendFile = async () => {
    if (!pendingFile || attaching || disabled) return;
    setAttaching(true);
    try {
      await onAttach(pendingFile);
      setPendingFile(null);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Upload failed.');
    } finally { setAttaching(false); }
  };

  const isBlocked = disabled || sending || attaching;

  return (
    <div className="border-t border-white/5 bg-slate-950 shrink-0">
      {/* Pending file preview */}
      {pendingFile && (
        <div className="mx-4 mt-3 flex items-center gap-3 px-3 py-2.5 bg-slate-800/70 border border-white/8 rounded-xl">
          {pendingFile.type.startsWith('image/')
            ? <ImageIcon className="w-4 h-4 text-blue-400 shrink-0" />
            : <FileText  className="w-4 h-4 text-slate-400 shrink-0" />
          }
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-white truncate">{pendingFile.name}</p>
            <p className="text-xs text-slate-600">{formatBytes(pendingFile.size)}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleSendFile}
              disabled={isBlocked}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 disabled:opacity-40 transition-colors"
            >
              {attaching ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
              Send
            </button>
            <button
              onClick={() => { setPendingFile(null); setFileError(''); }}
              className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {fileError && (
        <p className="mx-4 mt-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">
          {fileError}
        </p>
      )}

      {/* Text area + controls */}
      <div className="flex items-end gap-2 p-4">
        <button
          onClick={() => fileRef.current?.click()}
          disabled={isBlocked}
          title="Attach file"
          className="p-2 rounded-xl text-slate-600 hover:text-slate-300 hover:bg-white/8 disabled:opacity-40 transition-colors shrink-0"
        >
          <Paperclip className="w-4 h-4" />
        </button>
        <input
          ref={fileRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          onChange={handleFileChange}
          className="hidden"
        />

        <textarea
          ref={textRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          disabled={isBlocked}
          placeholder={disabled ? 'Ticket is resolved — reopen to reply' : 'Type a message… (Enter to send, Shift+Enter for newline)'}
          rows={1}
          className="flex-1 bg-slate-800/60 border border-white/8 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/40 transition-colors resize-none leading-relaxed disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: '44px', maxHeight: '160px' }}
        />

        <button
          onClick={handleSend}
          disabled={!text.trim() || isBlocked}
          className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all shrink-0"
        >
          {sending
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Send    className="w-4 h-4" />
          }
        </button>
      </div>
    </div>
  );
}
