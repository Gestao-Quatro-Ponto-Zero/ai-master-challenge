"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

export interface Message {
  id: string;
  conversation_id: string;
  role: "customer" | "assistant" | "operator" | "system";
  content: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface GroupedSendPayload {
  content: string;
  grouped_messages?: string[];
}

interface ChatWidgetProps {
  messages: Message[];
  onSendMessage: (payload: GroupedSendPayload) => Promise<void>;
  isLoading: boolean;
  conversationStatus?: string;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  onOptimisticMessage?: (message: Message) => void;
  identityComplete?: boolean;
  conversationId?: string;
}

// ─── Buffer Indicator ───────────────────────────────────────────────

function BufferIndicator({ count, countdown }: { count: number; countdown: number }) {
  return (
    <div className="flex items-center gap-2 px-4 py-1">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
      </span>
      <span className="text-xs text-muted-foreground">
        Aguardando mais mensagens... ({count} recebida{count > 1 ? "s" : ""}) [{countdown}s]
      </span>
    </div>
  );
}

// ─── Typing Indicator ───────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-start gap-2 px-4 py-2">
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        <div className="flex gap-1">
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

// ─── Message Bubble ─────────────────────────────────────────────────

function MessageBubble({ message }: { message: Message }) {
  const isCustomer = message.role === "customer";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center px-4 py-2">
        <div className="max-w-[85%] rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
          <p className="mb-1 text-xs font-semibold uppercase text-orange-600">
            Sistema
          </p>
          {message.content}
        </div>
      </div>
    );
  }

  const time = new Date(message.created_at).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={cn(
        "flex px-4 py-1 animate-in slide-in-from-bottom-2 fade-in duration-300",
        isCustomer ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5",
          isCustomer
            ? "rounded-tr-sm bg-primary text-primary-foreground"
            : "rounded-tl-sm bg-muted text-foreground"
        )}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
        </p>
        <p
          className={cn(
            "mt-1 text-[10px]",
            isCustomer ? "text-primary-foreground/60" : "text-muted-foreground"
          )}
        >
          {time}
        </p>
      </div>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

const BUFFER_SECONDS = 4;

export function ChatWidget({
  messages,
  onSendMessage,
  isLoading,
  conversationStatus,
  inputRef: externalInputRef,
  onOptimisticMessage,
  identityComplete,
  conversationId,
}: ChatWidgetProps) {
  const [inputValue, setInputValue] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const internalInputRef = useRef<HTMLInputElement>(null);
  const inputRef = externalInputRef || internalInputRef;

  // Buffer state
  const [messageBuffer, setMessageBuffer] = useState<string[]>([]);
  const [isBuffering, setIsBuffering] = useState(false);
  const [bufferCountdown, setBufferCountdown] = useState(0);
  const bufferTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Clear buffer on conversation change
  useEffect(() => {
    setMessageBuffer([]);
    setIsBuffering(false);
    setBufferCountdown(0);
    if (bufferTimerRef.current) clearTimeout(bufferTimerRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
  }, [conversationId]);

  // Flush buffer: send grouped or single message
  const flushBuffer = useCallback(
    async (buffer: string[]) => {
      if (buffer.length === 0) return;

      setIsBuffering(false);
      setBufferCountdown(0);
      setMessageBuffer([]);

      if (buffer.length === 1) {
        await onSendMessage({ content: buffer[0] });
      } else {
        await onSendMessage({
          content: buffer.join("\n"),
          grouped_messages: buffer,
        });
      }
    },
    [onSendMessage]
  );

  // Start or reset buffer timer
  const resetBufferTimer = useCallback(
    (updatedBuffer: string[]) => {
      // Clear existing timers
      if (bufferTimerRef.current) clearTimeout(bufferTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);

      // Start countdown
      setBufferCountdown(BUFFER_SECONDS);
      countdownTimerRef.current = setInterval(() => {
        setBufferCountdown((prev) => {
          if (prev <= 1) {
            if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      // Set flush timer
      bufferTimerRef.current = setTimeout(() => {
        flushBuffer(updatedBuffer);
      }, BUFFER_SECONDS * 1000);
    },
    [flushBuffer]
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (bufferTimerRef.current) clearTimeout(bufferTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, []);

  const handleSend = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;

    setInputValue("");

    // If identity flow is not complete, send immediately (no buffering)
    if (!identityComplete) {
      await onSendMessage({ content: trimmed });
      inputRef.current?.focus();
      return;
    }

    // Identity complete: buffer messages
    // Show message optimistically
    if (onOptimisticMessage) {
      const optimisticMsg: Message = {
        id: `optimistic-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        conversation_id: conversationId || "",
        role: "customer",
        content: trimmed,
        created_at: new Date().toISOString(),
      };
      onOptimisticMessage(optimisticMsg);
    }

    // Add to buffer
    const updatedBuffer = [...messageBuffer, trimmed];
    setMessageBuffer(updatedBuffer);
    setIsBuffering(true);

    // Reset timer
    resetBufferTimer(updatedBuffer);

    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled =
    isLoading ||
    conversationStatus === "escalated" ||
    conversationStatus === "resolved";

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
          Chat de Atendimento
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <ScrollArea
          ref={scrollRef}
          className="h-[calc(100vh-22rem)] overflow-y-auto"
        >
          <div className="space-y-1 py-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
          </div>
        </ScrollArea>
      </CardContent>

      {isBuffering && (
        <BufferIndicator count={messageBuffer.length} countdown={bufferCountdown} />
      )}

      <CardFooter className="gap-2">
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isDisabled
              ? "Conversa encerrada"
              : "Digite sua mensagem..."
          }
          disabled={isDisabled}
          className="flex-1"
          data-walkthrough="chat-input"
        />
        <Button
          onClick={handleSend}
          disabled={isDisabled || !inputValue.trim()}
          size="icon"
        >
          <Send className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
