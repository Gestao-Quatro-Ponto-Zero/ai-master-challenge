"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { PageHeader } from "@/components/page-header";
import { TicketDetail } from "@/components/prototype/ticket-detail";
import { OperatorCard } from "@/components/prototype/operator-card";
import { ConversationQueue } from "@/components/prototype/conversation-queue";
import {
  ClassificationPanel,
  type ClassificationData,
} from "@/components/prototype/classification-panel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Users, FileText, MessageSquare, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";

// ─── Types ───────────────────────────────────────────────────────────

interface Operator {
  id: string;
  name: string;
  status: string;
  level?: string;
  active_tickets: number;
  max_capacity: number;
  specialties: string[] | null;
  total_resolved: number;
}

interface Message {
  id: string;
  conversation_id: string;
  role: "customer" | "assistant" | "operator" | "system";
  content: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

interface ConversationDetail {
  id: string;
  channel: string;
  status: string;
  customer_name: string | null;
  subject_classified: string | null;
  category_classified: string | null;
  scenario: string | null;
  confidence: number | null;
  assigned_operator_id: string | null;
  summary: string | null;
  turn_count: number | null;
  sla_deadline: string | null;
  created_at: string;
}

// ─── Role styling for chat bubbles ──────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  customer: "Cliente",
  assistant: "Assistente IA",
  operator: "Operador",
  system: "Sistema",
};

// ─── Chat bubble component ──────────────────────────────────────────

function ChatBubble({ message }: { message: Message }) {
  const time = new Date(message.created_at).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const isCustomer = message.role === "customer";
  const isSystem = message.role === "system";
  const isAssistant = message.role === "assistant";

  if (isSystem) {
    return (
      <div className="flex justify-center py-1">
        <div className="rounded-full bg-orange-100 px-3 py-1 text-[10px] text-orange-700">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex", isCustomer ? "justify-start" : "justify-end")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-3 py-2",
          isCustomer
            ? "rounded-bl-sm bg-gray-100 text-foreground"
            : isAssistant
              ? "rounded-br-sm bg-violet-100 text-violet-900"
              : "rounded-br-sm bg-blue-100 text-blue-900"
        )}
      >
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-[10px] font-semibold opacity-70">
            {ROLE_LABELS[message.role] || message.role}
          </span>
          <span className="text-[9px] opacity-50">{time}</span>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
        </p>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────

export default function OperadorPage() {
  // State
  const [operators, setOperators] = useState<Operator[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [selectedConversation, setSelectedConversation] =
    useState<ConversationDetail | null>(null);
  const [selectedMessages, setSelectedMessages] = useState<Message[]>([]);
  const [currentOperatorId, setCurrentOperatorId] = useState<string | null>(
    null
  );
  const [detailLoading, setDetailLoading] = useState(false);
  const [classification, setClassification] =
    useState<ClassificationData | null>(null);

  // Ref for polling interval
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Sort operators by load (busiest first)
  const sortedOperators = useMemo(() => {
    return [...operators].sort((a, b) => {
      const loadA = a.max_capacity > 0 ? a.active_tickets / a.max_capacity : 0;
      const loadB = b.max_capacity > 0 ? b.active_tickets / b.max_capacity : 0;
      return loadB - loadA;
    });
  }, [operators]);

  // ─── Data Fetchers ─────────────────────────────────────────────────

  const fetchOperators = useCallback(async () => {
    try {
      const res = await fetch("/api/prototype/operators");
      if (!res.ok) return;
      const data = await res.json();
      setOperators(data.operators || []);

      // Auto-select first operator if none selected
      if (!currentOperatorId && data.operators?.length > 0) {
        setCurrentOperatorId(data.operators[0].id);
      }
    } catch {
      // Silently fail
    }
  }, [currentOperatorId]);

  const fetchConversationDetail = useCallback(async (id: string) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/prototype/conversations/${id}`);
      if (!res.ok) return;
      const data = await res.json();
      setSelectedConversation(data.conversation);
      setSelectedMessages(data.messages || []);

      // Build ClassificationData from conversation detail
      const conv = data.conversation as ConversationDetail | null;
      if (conv && conv.category_classified) {
        setClassification({
          category: conv.category_classified,
          subject: conv.subject_classified,
          scenario: conv.scenario,
          confidence: conv.confidence,
          action: null,
          auto_routed: false,
          escalated: conv.status === "escalated",
          turn_count: conv.turn_count || 0,
        });
      } else {
        setClassification(null);
      }
    } catch {
      // Silently fail
    } finally {
      setDetailLoading(false);
    }
  }, []);

  // ─── ConversationQueue onSelect handler ──────────────────────────

  const handleQueueSelect = useCallback(
    (conv: {
      id: string;
      channel: string;
      status: string;
      category_classified: string | null;
      subject_classified: string | null;
      scenario: string | null;
      turn_count: number;
    }) => {
      setSelectedTicketId(conv.id);
      fetchConversationDetail(conv.id);
    },
    [fetchConversationDetail]
  );

  // ─── Initial Load + Polling ────────────────────────────────────────

  useEffect(() => {
    fetchOperators();

    // Poll every 3 seconds
    pollRef.current = setInterval(() => {
      fetchOperators();
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchOperators]);

  // ─── Actions ───────────────────────────────────────────────────────

  const handleAccept = async (conversationId: string) => {
    if (!currentOperatorId) return;
    const res = await fetch("/api/prototype/queue/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: conversationId,
        operator_id: currentOperatorId,
      }),
    });
    if (res.ok) {
      await fetchOperators();
      await fetchConversationDetail(conversationId);
    }
  };

  const handleResolve = async (conversationId: string, csatRating?: number) => {
    if (!currentOperatorId) return;
    const payload: Record<string, unknown> = { operator_id: currentOperatorId };
    if (csatRating !== undefined) {
      payload.csat_rating = csatRating;
    }
    const res = await fetch(
      `/api/prototype/conversations/${conversationId}/resolve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    if (res.ok) {
      setSelectedTicketId(null);
      setSelectedConversation(null);
      setSelectedMessages([]);
      setClassification(null);
      await fetchOperators();
    }
  };

  const handleTransfer = async (
    conversationId: string,
    toOperatorId: string
  ) => {
    if (!currentOperatorId) return;
    const res = await fetch("/api/prototype/queue/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: conversationId,
        from_operator_id: currentOperatorId,
        to_operator_id: toOperatorId,
      }),
    });
    if (res.ok) {
      await fetchOperators();
      await fetchConversationDetail(conversationId);
    }
  };

  // ─── Determine visible actions based on ticket status ─────────────

  const isAssignedToMe = selectedConversation?.assigned_operator_id === currentOperatorId;
  const isUnassigned = !selectedConversation?.assigned_operator_id &&
    (selectedConversation?.status === "escalated" ||
     selectedConversation?.status === "active");
  const canAccept = isUnassigned && !!currentOperatorId;
  const canResolve = isAssignedToMe;
  const canTransfer = isAssignedToMe;

  // ─── Render ────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen flex-col">
      <PageHeader
        title="Painel do Operador"
        description="Fila de tickets, detalhes e gestao de atendimento."
      />

      {/* Top bar: Operator selector */}
      <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          <span>Operador ativo:</span>
        </div>
        <select
          value={currentOperatorId || ""}
          onChange={(e) => setCurrentOperatorId(e.target.value || null)}
          className="rounded-md border bg-background px-2 py-1 text-sm"
        >
          {operators.map((op) => (
            <option key={op.id} value={op.id}>
              {op.name} ({op.level ? op.level.charAt(0).toUpperCase() + op.level.slice(1) : "Junior"})
            </option>
          ))}
        </select>
      </div>

      {/* Main content: Kanban (left ~60%) + Tabbed Panel (right ~40%) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Kanban board */}
        <div className="w-[60%] min-w-0 shrink-0" data-walkthrough="queue-list">
          <ConversationQueue
            selectedId={selectedTicketId}
            onSelect={handleQueueSelect}
            onAccept={handleAccept}
            operators={operators}
            currentOperatorId={currentOperatorId}
            onTransfer={handleTransfer}
          />
        </div>

        {/* Right: Tabbed panel */}
        <div className="w-[40%] shrink-0 border-l flex flex-col overflow-hidden">
          <Tabs defaultValue={0} className="flex flex-1 flex-col overflow-hidden">
            <TabsList className="mx-3 mt-2 w-auto shrink-0">
              <TabsTrigger value={0}>
                <FileText className="h-3.5 w-3.5 mr-1" />
                Ticket
              </TabsTrigger>
              <TabsTrigger value={1}>
                <Users className="h-3.5 w-3.5 mr-1" />
                Operadores
                <span className="ml-1 rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-medium text-primary">
                  {operators.length}
                </span>
              </TabsTrigger>
            </TabsList>

            {/* ─── Ticket Tab ─── */}
            <TabsContent value={0} className="flex-1 overflow-hidden flex flex-col">
              {!selectedConversation ? (
                <div className="flex flex-1 items-center justify-center text-center text-muted-foreground">
                  <div>
                    <FileText className="mx-auto h-12 w-12 opacity-30" />
                    <p className="mt-3 text-sm">Selecione um ticket no kanban</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-1 flex-col overflow-hidden">
                  {/* Classification strip — compact horizontal badges */}
                  {classification && (
                    <div className="shrink-0 border-b bg-muted/20 px-3 py-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {classification.category && (
                          <span className="rounded-md bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-800">
                            {classification.category}
                          </span>
                        )}
                        {classification.subject && (
                          <span className="rounded-md bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">
                            {classification.subject}
                          </span>
                        )}
                        {classification.scenario && (
                          <ScenarioBadge scenario={classification.scenario} className="text-xs px-2 py-0.5" />
                        )}
                        {classification.confidence != null && (
                          <span
                            className={cn(
                              "rounded-md px-2 py-0.5 text-xs font-semibold",
                              classification.confidence >= 0.85
                                ? "bg-green-100 text-green-800"
                                : classification.confidence >= 0.5
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-red-100 text-red-800"
                            )}
                          >
                            {Math.round(classification.confidence * 100)}%
                          </span>
                        )}
                        {classification.escalated && (
                          <span className="rounded-md bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800">
                            Escalado
                          </span>
                        )}
                        {selectedConversation.assigned_operator_id ? (
                          <span className="ml-auto text-[10px] text-muted-foreground flex items-center gap-1">
                            <Bot className="h-3 w-3" />
                            {operators.find(o => o.id === selectedConversation.assigned_operator_id)?.name || "Operador"}
                          </span>
                        ) : (
                          <span className="ml-auto text-[10px] text-violet-600 flex items-center gap-1">
                            <Bot className="h-3 w-3" />
                            IA
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Chat history — scrollable */}
                  <ScrollArea className="flex-1">
                    <div className="space-y-2 p-3">
                      {detailLoading && selectedMessages.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">
                          Carregando mensagens...
                        </p>
                      ) : selectedMessages.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">
                          Nenhuma mensagem ainda.
                        </p>
                      ) : (
                        selectedMessages.map((msg) => (
                          <ChatBubble key={msg.id} message={msg} />
                        ))
                      )}
                    </div>
                  </ScrollArea>

                  {/* Action buttons — bottom strip */}
                  {(canAccept || canResolve || canTransfer) && (
                    <div className="shrink-0 border-t bg-background p-3">
                      <TicketActionBar
                        conversation={selectedConversation}
                        operators={operators}
                        currentOperatorId={currentOperatorId}
                        canAccept={canAccept}
                        canResolve={canResolve}
                        canTransfer={canTransfer}
                        onAccept={handleAccept}
                        onResolve={handleResolve}
                        onTransfer={handleTransfer}
                      />
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            {/* ─── Operadores Tab ─── */}
            <TabsContent value={1} className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-2 p-3">
                  {sortedOperators.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      Nenhum operador cadastrado.
                    </p>
                  ) : (
                    sortedOperators.map((op) => (
                      <OperatorCard
                        key={op.id}
                        operator={op}
                        isSelected={currentOperatorId === op.id}
                        onClick={() => setCurrentOperatorId(op.id)}
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

// ─── Ticket Action Bar ──────────────────────────────────────────────

function TicketActionBar({
  conversation,
  operators,
  currentOperatorId,
  canAccept,
  canResolve,
  canTransfer,
  onAccept,
  onResolve,
  onTransfer,
}: {
  conversation: ConversationDetail;
  operators: Operator[];
  currentOperatorId: string | null;
  canAccept: boolean;
  canResolve: boolean;
  canTransfer: boolean;
  onAccept: (conversationId: string) => Promise<void>;
  onResolve: (conversationId: string, csatRating?: number) => Promise<void>;
  onTransfer: (conversationId: string, toOperatorId: string) => Promise<void>;
}) {
  const [actionLoading, setActionLoading] = useState(false);
  const [showTransfer, setShowTransfer] = useState(false);
  const [showCsat, setShowCsat] = useState(false);
  const [csatRating, setCsatRating] = useState(0);

  const availableOperators = operators.filter(
    (op) =>
      op.id !== currentOperatorId &&
      op.status === "available" &&
      (op.active_tickets || 0) < (op.max_capacity || 5)
  );

  const handleAcceptClick = async () => {
    setActionLoading(true);
    try {
      await onAccept(conversation.id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveClick = async () => {
    setActionLoading(true);
    try {
      await onResolve(conversation.id, csatRating > 0 ? csatRating : undefined);
      setShowCsat(false);
      setCsatRating(0);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransferClick = async (toOpId: string) => {
    setActionLoading(true);
    try {
      await onTransfer(conversation.id, toOpId);
      setShowTransfer(false);
    } finally {
      setActionLoading(false);
    }
  };

  if (showCsat) {
    return (
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground">
          Avaliacao do cliente (CSAT):
        </p>
        <div className="flex items-center justify-center gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => setCsatRating(star)}
              disabled={actionLoading}
              className={cn(
                "rounded-md px-3 py-1.5 text-lg transition-all",
                csatRating >= star
                  ? "text-amber-500 scale-110"
                  : "text-gray-300 hover:text-amber-300"
              )}
            >
              ★
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setShowCsat(false); setCsatRating(0); }}
            className="flex-1 rounded-md border px-3 py-1.5 text-xs hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            onClick={handleResolveClick}
            disabled={actionLoading}
            className="flex-1 rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {csatRating > 0 ? "Resolver com CSAT" : "Resolver sem nota"}
          </button>
        </div>
      </div>
    );
  }

  if (showTransfer) {
    return (
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground">
          Transferir para:
        </p>
        {availableOperators.length === 0 ? (
          <p className="text-xs text-muted-foreground">Nenhum operador disponivel</p>
        ) : (
          <div className="space-y-1">
            {availableOperators.map((op) => (
              <button
                key={op.id}
                onClick={() => handleTransferClick(op.id)}
                disabled={actionLoading}
                className="flex w-full items-center justify-between rounded-md border px-3 py-1.5 text-xs hover:bg-muted disabled:opacity-50"
              >
                <span>{op.name}</span>
                <span className="text-muted-foreground">{op.active_tickets}/{op.max_capacity}</span>
              </button>
            ))}
          </div>
        )}
        <button
          onClick={() => setShowTransfer(false)}
          className="w-full rounded-md border px-3 py-1.5 text-xs hover:bg-muted"
        >
          Cancelar
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      {canAccept && (
        <button
          onClick={handleAcceptClick}
          disabled={actionLoading}
          className="flex-1 rounded-md bg-green-600 px-3 py-2 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
        >
          Aceitar
        </button>
      )}
      {canTransfer && (
        <button
          onClick={() => setShowTransfer(true)}
          disabled={actionLoading}
          className="flex-1 rounded-md border px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
        >
          Transferir
        </button>
      )}
      {canResolve && (
        <button
          onClick={() => setShowCsat(true)}
          disabled={actionLoading}
          className="flex-1 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          Resolver
        </button>
      )}
    </div>
  );
}
