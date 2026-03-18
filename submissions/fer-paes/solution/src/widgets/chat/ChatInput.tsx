import { useState } from 'react';
import { Send } from 'lucide-react';

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({ onSend, disabled = false, placeholder = 'Type a message...' }: Props) {
  const [text, setText] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 px-3 py-3 border-t border-gray-100">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as unknown as React.FormEvent);
          }
        }}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-50 disabled:opacity-50 transition-all"
        style={{ maxHeight: 120, overflowY: 'auto' }}
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="w-9 h-9 flex items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
      >
        <Send className="w-4 h-4" />
      </button>
    </form>
  );
}
