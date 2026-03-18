import { useState, useRef, useCallback } from 'react';
import { Send, Reply } from 'lucide-react';
import AttachmentUploader, { type PendingAttachment } from './AttachmentUploader';
import MacroSelector from './MacroSelector';
import { applyMacro } from '../../services/macroService';
import type { CreateMessageData } from '../../services/messageService';
import type { Macro, MacroContext } from '../../types';

interface EmailComposerProps {
  onSend: (data: Pick<CreateMessageData, 'message' | 'attachments'>) => Promise<void>;
  disabled?: boolean;
  toName?: string;
  toEmail?: string;
  subject?: string | null;
  macroContext?: MacroContext;
}

export default function EmailComposer({
  onSend,
  disabled,
  toName,
  toEmail,
  subject,
  macroContext,
}: EmailComposerProps) {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [sending, setSending] = useState(false);
  const [macroMode, setMacroMode] = useState(false);
  const [macroQuery, setMacroQuery] = useState('');
  const [expanded, setExpanded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const toDisplay = toName ? `${toName}${toEmail ? ` <${toEmail}>` : ''}` : toEmail || 'Cliente';

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
        message: trimmed || (attachments.length > 0 ? `[${attachments.length} anexo(s)]` : ''),
        attachments: attachments.map(({ file_url, file_type, file_size }) => ({
          file_url,
          file_type,
          file_size,
        })),
      });
      setText('');
      setAttachments([]);
      setMacroMode(false);
      setExpanded(false);
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (macroMode && (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Enter' || e.key === 'Escape')) {
      return;
    }
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const canSend = (text.trim().length > 0 || attachments.length > 0) && !sending && !disabled;

  if (!expanded) {
    return (
      <div className="bg-white border-t border-gray-100 px-6 py-3">
        <button
          onClick={() => { setExpanded(true); setTimeout(() => textareaRef.current?.focus(), 50); }}
          disabled={disabled}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-sm text-gray-400 hover:border-gray-300 hover:bg-gray-100 transition-all disabled:opacity-50 text-left"
        >
          <Reply className="w-4 h-4 shrink-0 text-gray-400" />
          <span>Responder para {toDisplay}...</span>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border-t border-gray-100">
      <div className="border-b border-gray-100 px-6 py-2.5 flex items-center gap-3">
        <Reply className="w-4 h-4 text-gray-400 shrink-0" />
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span className="text-gray-400">Para:</span>
          <span className="font-medium text-gray-700">{toDisplay}</span>
        </div>
        {subject && (
          <>
            <div className="h-3 w-px bg-gray-200" />
            <div className="flex items-center gap-1.5 text-xs text-gray-500 min-w-0">
              <span className="text-gray-400">Assunto:</span>
              <span className="font-medium text-gray-700 truncate">Re: {subject}</span>
            </div>
          </>
        )}
      </div>

      <div className="px-6 py-3 relative">
        {macroMode && (
          <MacroSelector
            query={macroQuery}
            onSelect={handleMacroSelect}
            onClose={closeMacro}
          />
        )}

        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || sending}
          placeholder="Escreva sua resposta... (/ para macros)"
          rows={6}
          className="w-full bg-transparent resize-none text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none leading-relaxed disabled:opacity-50"
        />

        <div className="flex items-center justify-between pt-3 border-t border-gray-100 mt-1">
          <div className="flex items-center gap-2">
            <AttachmentUploader
              attachments={attachments}
              onChange={setAttachments}
              disabled={sending}
            />
            {attachments.length === 0 && (
              <span className="text-xs text-gray-400">Ctrl+Enter para enviar · / para macros</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => { setExpanded(false); setText(''); setAttachments([]); }}
              className="px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-gray-100 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSend}
              disabled={!canSend}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                canSend
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-200'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              {sending ? (
                <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
