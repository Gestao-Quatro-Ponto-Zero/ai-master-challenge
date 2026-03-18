import { useEffect, useRef } from 'react';
import type { ChatMessage } from './types';

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

interface Props {
  messages: ChatMessage[];
}

export default function ChatMessages({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.sender === 'customer' ? 'justify-end' : 'justify-start'}`}
        >
          {msg.sender === 'system' ? (
            <div className="text-center w-full">
              <span className="inline-block px-3 py-1 rounded-full text-xs text-gray-400 bg-gray-100">
                {msg.content}
              </span>
            </div>
          ) : (
            <div className="max-w-[80%]">
              <div className="bg-blue-600 text-white text-sm px-3.5 py-2.5 rounded-2xl rounded-tr-sm shadow-sm">
                {msg.content}
              </div>
              <p className="text-right text-xs text-gray-400 mt-1 px-1">
                {formatTime(msg.timestamp)}
              </p>
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
