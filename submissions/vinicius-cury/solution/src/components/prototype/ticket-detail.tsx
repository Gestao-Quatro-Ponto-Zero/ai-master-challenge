"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import { SCENARIO_LABELS } from "@/lib/routing/taxonomy";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Mail,
  Phone,
  MessageSquare,
  Share2,
  Clock,
  CheckCircle,
  ArrowRightLeft,
  UserPlus,
  FileText,
  BookOpen,
  AlertTriangle,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

interface Message {
  id: string;
  conversation_id: string;
  role: "customer" | "assistant" | "operator" | "system";
  content: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

interface Operator {
  id: string;
  name: string;
  status: string;
  active_tickets: number;
  max_capacity: number;
  specialties: string[] | null;
  total_resolved: number;
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

interface TicketDetailProps {
  conversation: ConversationDetail | null;
  messages: Message[];
  operators: Operator[];
  currentOperatorId: string | null;
  onAccept: (conversationId: string) => Promise<void>;
  onResolve: (conversationId: string, csatRating?: number) => Promise<void>;
  onTransfer: (conversationId: string, toOperatorId: string) => Promise<void>;
  isLoading: boolean;
}

// ─── Helpers ─────────────────────────────────────────────────────────

function getChannelIcon(channel: string) {
  switch (channel?.toLowerCase()) {
    case "email":
      return <Mail className="h-4 w-4" />;
    case "phone":
    case "telefone":
      return <Phone className="h-4 w-4" />;
    case "chat":
      return <MessageSquare className="h-4 w-4" />;
    case "social media":
    case "social":
      return <Share2 className="h-4 w-4" />;
    default:
      return <MessageSquare className="h-4 w-4" />;
  }
}

const ROLE_LABELS: Record<string, string> = {
  customer: "Cliente",
  assistant: "Assistente IA",
  operator: "Operador",
  system: "Sistema",
};

const ROLE_COLORS: Record<string, string> = {
  customer: "bg-blue-100 text-blue-800",
  assistant: "bg-purple-100 text-purple-800",
  operator: "bg-green-100 text-green-800",
  system: "bg-orange-100 text-orange-800",
};

// ─── SLA Timer ──────────────────────────────────────────────────────

function SlaTimer({ deadline }: { deadline: string }) {
  const [remaining, setRemaining] = useState<number>(0);

  useEffect(() => {
    const update = () => {
      const ms = new Date(deadline).getTime() - Date.now();
      setRemaining(ms);
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [deadline]);

  const isExpired = remaining <= 0;
  const totalMs = new Date(deadline).getTime() - Date.now();

  let colorClass = "text-green-600";
  if (isExpired) colorClass = "text-red-600 animate-pulse font-bold";
  else if (remaining < totalMs * 0.25) colorClass = "text-red-600";
  else if (remaining < totalMs * 0.5) colorClass = "text-yellow-600";

  const formatRemaining = () => {
    if (isExpired) return "EXPIRADO";
    const totalSeconds = Math.floor(remaining / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  return (
    <div className={cn("flex items-center gap-1 text-sm font-medium", colorClass)}>
      <Clock className="h-4 w-4" />
      <span>SLA: {formatRemaining()}</span>
    </div>
  );
}

// ─── Message Bubble (read-only) ─────────────────────────────────────

function MessageItem({ message }: { message: Message }) {
  const time = new Date(message.created_at).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="py-1.5">
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "rounded px-1.5 py-0.5 text-[10px] font-semibold",
            ROLE_COLORS[message.role] || "bg-gray-100 text-gray-800"
          )}
        >
          {ROLE_LABELS[message.role] || message.role}
        </span>
        <span className="text-[10px] text-muted-foreground">{time}</span>
      </div>
      <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-foreground">
        {message.content}
      </p>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function TicketDetail({
  conversation,
  messages,
  operators,
  currentOperatorId,
  onAccept,
  onResolve,
  onTransfer,
  isLoading,
}: TicketDetailProps) {
  const [showTransfer, setShowTransfer] = useState(false);
  const [showCsatInput, setShowCsatInput] = useState(false);
  const [csatRating, setCsatRating] = useState<number>(0);
  const [actionLoading, setActionLoading] = useState(false);

  if (!conversation) {
    return (
      <Card className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <FileText className="mx-auto h-12 w-12" />
          <p className="mt-3 text-sm">Selecione um ticket</p>
        </div>
      </Card>
    );
  }

  const scenarioInfo = conversation.scenario
    ? SCENARIO_LABELS[conversation.scenario]
    : null;

  const isAssignedToMe =
    conversation.assigned_operator_id === currentOperatorId;
  const isUnassigned =
    !conversation.assigned_operator_id &&
    (conversation.status === "escalated" ||
      conversation.status === "waiting_operator");
  const canAccept = isUnassigned && currentOperatorId;
  const canResolve = isAssignedToMe;
  const canTransfer = isAssignedToMe;

  // Extract KB articles tried from message metadata
  const kbArticlesTried = messages
    .filter(
      (m) =>
        m.metadata &&
        (m.metadata as Record<string, unknown>).type === "kb_response"
    )
    .map((m) => {
      const meta = m.metadata as Record<string, unknown>;
      return (meta.kb_title as string) || null;
    })
    .filter(Boolean);

  const handleAccept = async () => {
    setActionLoading(true);
    try {
      await onAccept(conversation.id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    setActionLoading(true);
    try {
      await onResolve(conversation.id, csatRating > 0 ? csatRating : undefined);
      setShowCsatInput(false);
      setCsatRating(0);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransfer = async (toOperatorId: string) => {
    setActionLoading(true);
    try {
      await onTransfer(conversation.id, toOperatorId);
      setShowTransfer(false);
    } finally {
      setActionLoading(false);
    }
  };

  const availableOperators = operators.filter(
    (op) =>
      op.id !== currentOperatorId &&
      op.status === "available" &&
      (op.active_tickets || 0) < (op.max_capacity || 5)
  );

  return (
    <Card className="flex h-full flex-col">
      {/* Header */}
      <CardHeader className="border-b pb-3">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base">
                {conversation.customer_name || "Cliente"}
              </CardTitle>
              <div className="flex items-center gap-1">
                {getChannelIcon(conversation.channel)}
                <span className="text-xs text-muted-foreground">{conversation.channel}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {new Date(conversation.created_at).toLocaleString("pt-BR", {
                  day: "2-digit",
                  month: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>

            {/* Classification tags — prominent */}
            {conversation.category_classified && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-violet-100 px-2 py-1 text-xs font-semibold text-violet-800">
                  {conversation.category_classified}
                </span>
                {conversation.subject_classified && (
                  <span className="rounded-md bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                    {conversation.subject_classified}
                  </span>
                )}
                {conversation.scenario && (
                  <ScenarioBadge scenario={conversation.scenario} className="text-xs px-2 py-1" />
                )}
                {conversation.confidence != null && (
                  <span
                    className={cn(
                      "rounded-md px-2 py-1 text-xs font-semibold",
                      conversation.confidence >= 0.85
                        ? "bg-green-100 text-green-800"
                        : conversation.confidence >= 0.5
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-red-100 text-red-800"
                    )}
                  >
                    {Math.round(conversation.confidence * 100)}%
                  </span>
                )}
              </div>
            )}
          </div>
          {conversation.sla_deadline && (
            <SlaTimer deadline={conversation.sla_deadline} />
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-[calc(100vh-22rem)]">
          <div className="space-y-4 p-4">
            {/* Classification section */}
            {conversation.category_classified && (
              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-muted-foreground">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Classificação
                </h3>
                <div className="rounded-lg border bg-muted/30 p-3 text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Categoria D2
                      </span>
                      <p className="font-medium">
                        {conversation.category_classified}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Assunto D1
                      </span>
                      <p className="font-medium">
                        {conversation.subject_classified}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Confiança
                      </span>
                      <p className="font-medium">
                        {conversation.confidence
                          ? `${Math.round(conversation.confidence * 100)}%`
                          : "N/A"}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Cenário
                      </span>
                      <div className="mt-0.5">
                        {conversation.scenario && (
                          <ScenarioBadge scenario={conversation.scenario} />
                        )}
                      </div>
                    </div>
                  </div>
                  {scenarioInfo && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {scenarioInfo.action}
                    </p>
                  )}
                </div>
              </section>
            )}

            {/* Conversation thread */}
            <section>
              <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-muted-foreground">
                <MessageSquare className="h-3.5 w-3.5" />
                Conversa ({messages.length} mensagens)
              </h3>
              <div className="rounded-lg border p-3">
                {isLoading && messages.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Carregando mensagens...
                  </p>
                ) : (
                  <div className="divide-y">
                    {messages.map((msg) => (
                      <MessageItem key={msg.id} message={msg} />
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* KB Articles tried */}
            {kbArticlesTried.length > 0 && (
              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-muted-foreground">
                  <BookOpen className="h-3.5 w-3.5" />
                  KB Tentado
                </h3>
                <div className="space-y-1">
                  {kbArticlesTried.map((title, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-blue-200 bg-blue-50/50 px-3 py-2 text-sm text-blue-900"
                    >
                      {title}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Summary */}
            {conversation.summary && (
              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                  Resumo
                </h3>
                <div className="rounded-lg border bg-muted/30 p-3 text-sm">
                  {conversation.summary}
                </div>
              </section>
            )}
          </div>
        </ScrollArea>
      </CardContent>

      {/* Action buttons */}
      {(canAccept || canResolve || canTransfer) && (
        <div className="border-t p-3">
          {showCsatInput ? (
            <div className="space-y-3">
              <p className="text-xs font-medium text-muted-foreground">
                Avaliação do cliente (CSAT):
              </p>
              <div className="flex items-center justify-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setCsatRating(star)}
                    disabled={actionLoading}
                    className={cn(
                      "rounded-md px-3 py-2 text-lg transition-all",
                      csatRating >= star
                        ? "text-amber-500 scale-110"
                        : "text-gray-300 hover:text-amber-300"
                    )}
                    title={`${star} estrela${star > 1 ? "s" : ""}`}
                  >
                    ★
                  </button>
                ))}
              </div>
              <p className="text-center text-[10px] text-muted-foreground">
                {csatRating === 0
                  ? "Selecione uma nota ou pule"
                  : `${csatRating}/5 estrela${csatRating > 1 ? "s" : ""}`}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowCsatInput(false);
                    setCsatRating(0);
                  }}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleResolve}
                  disabled={actionLoading}
                  className="flex-1"
                  size="sm"
                >
                  <CheckCircle className="mr-1 h-3.5 w-3.5" />
                  {csatRating > 0 ? "Resolver com CSAT" : "Resolver sem nota"}
                </Button>
              </div>
            </div>
          ) : showTransfer ? (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                Transferir para:
              </p>
              {availableOperators.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Nenhum operador disponível
                </p>
              ) : (
                <div className="space-y-1">
                  {availableOperators.map((op) => (
                    <button
                      key={op.id}
                      onClick={() => handleTransfer(op.id)}
                      disabled={actionLoading}
                      className="flex w-full items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-muted disabled:opacity-50"
                    >
                      <span>{op.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {op.active_tickets}/{op.max_capacity}
                      </span>
                    </button>
                  ))}
                </div>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTransfer(false)}
                className="w-full"
              >
                Cancelar
              </Button>
            </div>
          ) : (
            <div className="flex gap-2">
              {canAccept && (
                <Button
                  onClick={handleAccept}
                  disabled={actionLoading}
                  className="flex-1 bg-green-600 text-white hover:bg-green-700"
                  size="sm"
                >
                  <UserPlus className="mr-1 h-3.5 w-3.5" />
                  Aceitar
                </Button>
              )}
              {canTransfer && (
                <Button
                  variant="outline"
                  onClick={() => setShowTransfer(true)}
                  disabled={actionLoading}
                  className="flex-1"
                  size="sm"
                >
                  <ArrowRightLeft className="mr-1 h-3.5 w-3.5" />
                  Transferir
                </Button>
              )}
              {canResolve && (
                <Button
                  onClick={() => setShowCsatInput(true)}
                  disabled={actionLoading}
                  className="flex-1"
                  size="sm"
                >
                  <CheckCircle className="mr-1 h-3.5 w-3.5" />
                  Resolver
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
