"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ChatWidget, type Message, type GroupedSendPayload } from "@/components/prototype/chat-widget";
import {
  ClassificationPanel,
  type ClassificationData,
  type ClassificationHistoryEntry,
} from "@/components/prototype/classification-panel";
import {
  WalkthroughOverlay,
  StartTourButton,
  useWalkthrough,
} from "@/components/prototype/walkthrough-overlay";
import { cn } from "@/lib/utils";
import { Plus, MessageSquare, Mail, Phone, Share2 } from "lucide-react";

// ─── Channel Config ─────────────────────────────────────────────────

const CHANNELS = [
  { id: "Chat", label: "Chat", icon: MessageSquare },
  { id: "Email", label: "Email", icon: Mail },
  { id: "Phone", label: "Telefone", icon: Phone },
  { id: "Social media", label: "Redes Sociais", icon: Share2 },
] as const;

// ─── Main Page ──────────────────────────────────────────────────────

export default function AtendimentoPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [classification, setClassification] =
    useState<ClassificationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState("Chat");
  const [conversationStatus, setConversationStatus] = useState("active");
  const [turnCount, setTurnCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [identityComplete, setIdentityComplete] = useState(false);
  const [classificationHistory, setClassificationHistory] = useState<ClassificationHistoryEntry[]>([]);

  const chatInputRef = useRef<HTMLInputElement | null>(null);
  const walkthrough = useWalkthrough();

  // ─── Start new conversation ───────────────────────────────────────

  const startConversation = useCallback(
    async (channel?: string) => {
      setIsLoading(true);
      setClassification(null);
      setTurnCount(0);
      setConversationStatus("active");
      setError(null);
      setIdentityComplete(false);
      setClassificationHistory([]);

      try {
        const res = await fetch("/api/prototype/conversations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            channel: channel || selectedChannel,
          }),
        });

        if (!res.ok) {
          throw new Error("Falha ao criar conversa");
        }

        const data = await res.json();
        if (data.conversation) {
          setConversationId(data.conversation.id);
          setMessages(data.messages || []);
          if (channel) setSelectedChannel(channel);
        }
      } catch (err) {
        console.error("Erro ao criar conversa:", err);
        setError("Erro ao criar conversa. Verifique a conexão.");
      } finally {
        setIsLoading(false);
      }
    },
    [selectedChannel]
  );

  // Auto-start conversation on mount
  useEffect(() => {
    if (!conversationId) {
      startConversation();
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ─── Optimistic message handler ─────────────────────────────────

  const handleOptimisticMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  // ─── Send message ─────────────────────────────────────────────────

  const handleSendMessage = useCallback(
    async (payload: GroupedSendPayload) => {
      if (!conversationId) return;

      const { content, grouped_messages } = payload;

      // If buffering is active, optimistic messages are already shown by ChatWidget.
      // If not buffering (identity flow), add optimistic message here.
      const isGrouped = grouped_messages && grouped_messages.length > 1;
      let tempId: string | null = null;

      if (!isGrouped) {
        // Single message (identity flow or single buffered message)
        // Check if an optimistic message for this content already exists
        const alreadyShown = messages.some(
          (m) => m.role === "customer" && m.id.startsWith("optimistic-") && m.content === content
        );

        if (!alreadyShown) {
          tempId = `temp-${Date.now()}`;
          const optimisticMsg: Message = {
            id: tempId,
            conversation_id: conversationId,
            role: "customer",
            content,
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, optimisticMsg]);
        }
      }

      setIsLoading(true);
      setError(null);

      try {
        const body: Record<string, unknown> = { role: "customer", content };
        if (grouped_messages && grouped_messages.length > 1) {
          body.grouped_messages = grouped_messages;
        }

        const res = await fetch(
          `/api/prototype/conversations/${conversationId}/messages`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }
        );

        if (!res.ok) {
          throw new Error("Falha ao enviar mensagem");
        }

        const data = await res.json();

        if (data.messages) {
          // Replace optimistic messages with real ones and add assistant response
          setMessages((prev) => {
            // Remove all optimistic/temp messages that are part of this send
            const cleaned = prev.filter((m) => {
              if (tempId && m.id === tempId) return false;
              if (isGrouped && m.id.startsWith("optimistic-") && m.role === "customer") {
                // Remove optimistic messages whose content matches one of the grouped messages
                return !grouped_messages.includes(m.content);
              }
              return true;
            });
            // Deduplicate by content+role to prevent duplicate display
            const existingKeys = new Set(
              cleaned.map((m) => `${m.role}:${m.content}`)
            );
            const newMessages = (data.messages as Message[]).filter(
              (m) => !existingKeys.has(`${m.role}:${m.content}`)
            );
            return [...cleaned, ...newMessages];
          });
        }

        // Track identity state from API response
        if (data.identity_state === "support" || data.identity_state === "ready") {
          setIdentityComplete(true);
        }

        if (data.classification) {
          // Add grouped_count to classification data
          const classificationWithGrouping: ClassificationData = {
            ...data.classification,
            grouped_count: grouped_messages ? grouped_messages.length : undefined,
          };
          setClassification(classificationWithGrouping);
          setTurnCount(data.classification.turn_count || 0);

          if (data.classification.escalated) {
            setConversationStatus("escalated");
          }
        }
      } catch (err) {
        console.error("Erro ao enviar mensagem:", err);
        // Remove optimistic messages on error
        setMessages((prev) =>
          prev.filter((m) => {
            if (tempId && m.id === tempId) return false;
            if (isGrouped && m.id.startsWith("optimistic-")) return false;
            return true;
          })
        );
        setError("Classificação indisponível. Tente novamente.");
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, messages]
  );

  // Walkthrough adapter: wraps string-based send for the walkthrough overlay
  const handleWalkthroughSend = useCallback(
    async (content: string) => {
      await handleSendMessage({ content });
    },
    [handleSendMessage]
  );

  // ─── New conversation handler ─────────────────────────────────────

  const handleNewConversation = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setClassification(null);
    setTurnCount(0);
    setConversationStatus("active");
    setError(null);
    setIdentityComplete(false);
    setClassificationHistory([]);
    // Start a new conversation immediately
    startConversation();
  }, [startConversation]);

  // ─── Render ───────────────────────────────────────────────────────

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center justify-between border-b bg-background px-6 py-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Atendimento
          </h1>
          <p className="text-sm text-muted-foreground">
            Simulação de atendimento ao cliente com classificação e roteamento
            automático.
          </p>
        </div>
        <StartTourButton onClick={walkthrough.start} />
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 border-b px-6 py-3">
        {/* Channel selector */}
        <div className="flex items-center gap-1 rounded-lg border p-1">
          {CHANNELS.map((ch) => {
            const Icon = ch.icon;
            return (
              <button
                key={ch.id}
                onClick={() => setSelectedChannel(ch.id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  selectedChannel === ch.id
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {ch.label}
              </button>
            );
          })}
        </div>

        <Button onClick={handleNewConversation} size="sm" className="gap-1.5">
          <Plus className="h-4 w-4" />
          Novo Atendimento
        </Button>

        {conversationStatus === "escalated" && (
          <span className="ml-auto rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-medium text-orange-700">
            Escalonado
          </span>
        )}

        {error && (
          <span className="ml-auto rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
            {error}
          </span>
        )}
      </div>

      {/* Main content: 2-column layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat: flexible center */}
        <div
          className="flex flex-1 flex-col border-r"
          data-walkthrough="chat-widget"
        >
          <ChatWidget
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            conversationStatus={conversationStatus}
            inputRef={chatInputRef}
            onOptimisticMessage={handleOptimisticMessage}
            identityComplete={identityComplete}
            conversationId={conversationId || undefined}
          />
        </div>

        {/* Classification Panel: 350px fixed */}
        <div
          className="w-[350px] shrink-0 overflow-y-auto p-4"
          data-walkthrough="classification-panel"
        >
          <ClassificationPanel
            classification={classification}
            isLoading={isLoading}
            turnCount={turnCount}
            history={classificationHistory}
          />
        </div>
      </div>

      {/* Walkthrough overlay */}
      <WalkthroughOverlay
        isActive={walkthrough.isActive}
        onClose={walkthrough.close}
        onSendMessage={handleWalkthroughSend}
        chatInputRef={chatInputRef}
      />
    </div>
  );
}
