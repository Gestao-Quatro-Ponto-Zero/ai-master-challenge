import { useState, useRef, useEffect, useCallback } from 'react';
import { Send } from 'lucide-react';
import AttachmentUploader, { type PendingAttachment } from './AttachmentUploader';
import MacroSelector from './MacroSelector';
import { applyMacro } from '../../services/macroService';
import type { CreateMessageData } from '../../services/messageService';
import type { Macro, MacroContext } from '../../types';

interface MessageComposerProps {
  onSend: (data: Pick<CreateMessageData, 'message' | 'attachments'>) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  macroContext?: MacroContext;
}

export default function MessageComposer({ onSend, disabled, placeholder, macroContext }: MessageComposerProps) {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [sending, setSending] = useState(false);
  const [macroMode, setMacroMode] = useState(false);
  const [macroQuery, setMacroQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  function detectMacroTrigger(value: string) {
    const cursorPos = textareaRef.current?.selectionStart ?? value.length;
    const before = value.slice(0, cursorPos);
    const match = before.match(/(?:^|[\s\n])\/(\S*)$/);
    if (match) {
      setMacroQuery(match[1]);
      setMacroMode(true);
    } else {
      setMacroMode(false);
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value);
    detectMacroTrigger(e.target.value);
  }

  const handleMacroSelect = useCallback(
    (macro: Macro) => {
      const cursorPos = textareaRef.current?.selectionStart ?? text.length;
      const before = text.slice(0, cursorPos);
      const after = text.slice(cursorPos);
      const slashIndex = before.search(/(?:^|[\s\n])\/\S*$/);
      const insertPos = slashIndex === -1 ? before.length : slashIndex === 0 ? 0 : slashIndex + 1;
      const resolved = applyMacro(macro.content, macroContext ?? {});
      const newText = before.slice(0, insertPos) + resolved + after;
      setText(newText);
      setMacroMode(false);
      setTimeout(() => textareaRef.current?.focus(), 0);
    },
    [text, macroContext],
  );

  const closeMacro = useCallback(() => setMacroMode(false), []);

  async function handleSend() {
    const trimmed = text.trim();
    if ((!trimmed && attachments.length === 0) || sending || disabled) return;
    setSending(true);
    try {
      await onSend({
        message: trimmed || (attachments.length > 0 ? `[${attachments.length} attachment(s)]` : ''),
        attachments: attachments.map(({ file_url, file_type, file_size }) => ({
          file_url,
          file_type,
          file_size,
        })),
      });
      setText('');
      setAttachments([]);
      setMacroMode(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (macroMode && (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Enter' || e.key === 'Escape')) {
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const canSend = (text.trim().length > 0 || attachments.length > 0) && !sending && !disabled;

  return (
    <div className="bg-white border-t border-gray-100 px-4 py-3">
      <div className="relative">
        {macroMode && (
          <MacroSelector
            query={macroQuery}
            onSelect={handleMacroSelect}
            onClose={closeMacro}
          />
        )}

        <div className="rounded-2xl border border-gray-200 bg-gray-50 focus-within:border-blue-300 focus-within:ring-2 focus-within:ring-blue-50 transition-all overflow-hidden">
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 px-4 pt-3 pb-1">
              <AttachmentUploader
                attachments={attachments}
                onChange={setAttachments}
                disabled={sending}
              />
            </div>
          )}

          <div className="flex items-end gap-3 px-4 py-3">
            {attachments.length === 0 && (
              <AttachmentUploader
                attachments={attachments}
                onChange={setAttachments}
                disabled={sending}
              />
            )}

            <textarea
              ref={textareaRef}
              value={text}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={disabled || sending}
              placeholder={placeholder || 'Type a message... (/ for macros)'}
              rows={1}
              className="flex-1 bg-transparent resize-none text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none leading-relaxed disabled:opacity-50 min-h-[24px]"
            />

            <button
              onClick={handleSend}
              disabled={!canSend}
              className={`w-8 h-8 flex items-center justify-center rounded-xl transition-all shrink-0 ${
                canSend
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-200'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
              title="Send message"
            >
              {sending ? (
                <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-2 px-1">Enter to send · Shift+Enter for new line · / for macros</p>
    </div>
  );
}
