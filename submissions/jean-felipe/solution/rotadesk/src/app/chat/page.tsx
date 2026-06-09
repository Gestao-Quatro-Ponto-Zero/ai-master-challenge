"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Mail,
  MessageSquare,
  Phone,
  Plus,
  Send,
  Share2,
  Sparkles,
  Wand2,
} from "lucide-react";
import { ClassificationPanel } from "@/components/chat/ClassificationPanel";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import type { Ticket, TicketChannel, TicketMessage } from "@/lib/types";
import { normalizePtBr } from "@/lib/pt-br";
import { cn, formatDateTime } from "@/lib/utils";

interface TicketWithMessages extends Ticket {
  ticket_messages?: TicketMessage[];
}

const CHANNELS: { id: TicketChannel; label: string; icon: typeof MessageSquare }[] = [
  { id: "Chat", label: "Chat", icon: MessageSquare },
  { id: "Email", label: "E-mail", icon: Mail },
  { id: "Phone", label: "Telefone", icon: Phone },
  { id: "Social media", label: "Redes", icon: Share2 },
];

function ChatPageContent() {
  const searchParams = useSearchParams();
  const [channel, setChannel] = useState<TicketChannel>("Chat");
  const [ticket, setTicket] = useState<TicketWithMessages | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const customerMsgCount = (ticket?.ticket_messages ?? []).filter(
    (m) => m.role === "customer"
  ).length;
  const turn = ticket ? Math.max(customerMsgCount, 1) : 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [ticket?.ticket_messages]);

  useEffect(() => {
    const id = searchParams.get("ticket");
    if (!id) return;
    refreshTicket(id).then((data) => {
      if (data?.id) {
        setTicket(data);
        setChannel(data.channel);
      }
    });
  }, [searchParams]);

  async function refreshTicket(id: string) {
    const res = await fetch(`/api/tickets/${id}`);
    const data = await res.json();
    if (res.ok) setTicket(data);
    return data;
  }

  function startNewSession() {
    setTicket(null);
    setMessage("");
    setDraft(null);
    setError(null);
  }

  async function sendMessage() {
    const text = message.trim();
    if (!text || loading) return;

    setLoading(true);
    setError(null);
    setDraft(null);

    try {
      let ticketId = ticket?.id;

      if (!ticketId) {
        const createRes = await fetch("/api/tickets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_name: "Cliente Demo",
            customer_email: "cliente@example.com",
            channel,
            ticket_type: "Technical issue",
            ticket_priority: "Medium",
            subject: text.slice(0, 80),
            description: text,
          }),
        });
        const created = await createRes.json();
        if (!createRes.ok) throw new Error(created.error ?? "Erro ao criar atendimento");
        setMessage("");
        await refreshTicket(created.id);
        return;
      }

      const chatRes = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: ticketId, message: text, mode: "reply" }),
      });
      const chatData = await chatRes.json();
      if (!chatRes.ok) throw new Error(chatData.error ?? "Erro ao enviar mensagem");

      setMessage("");
      await refreshTicket(ticketId);
    } catch (e) {
      setError(
        e instanceof Error ? normalizePtBr(e.message) : "Erro ao criar conversa. Verifique a conexão."
      );
    } finally {
      setLoading(false);
    }
  }

  async function generateDraft() {
    if (!ticket?.id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: ticket.id, mode: "draft" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setDraft(data.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao gerar rascunho");
    } finally {
      setLoading(false);
    }
  }

  async function resolveAuto() {
    if (!ticket?.id) return;
    await fetch(`/api/tickets/${ticket.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolved_by: "auto_ia" }),
    });
    await refreshTicket(ticket.id);
  }

  const storedMessages = (ticket?.ticket_messages ?? [])
    .filter((m) => m.role !== "system" || messagesShowSystem(m, ticket))
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  const hasCustomerMsg = storedMessages.some((m) => m.role === "customer");
  const messages: Array<TicketMessage | { id: string; role: "customer"; content: string; created_at: string }> =
    ticket && !hasCustomerMsg && ticket.description
      ? [
          {
            id: "initial",
            role: "customer",
            content: ticket.description,
            created_at: ticket.created_at,
          },
          ...storedMessages,
        ]
      : storedMessages;

  const channelLabel = CHANNELS.find((c) => c.id === channel)?.label ?? "Chat";

  return (
    <DashboardLayout title="Atendimento">
      <div className="space-y-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">
              Simulação de atendimento com triagem sklearn, roteamento e respostas via IA
            </p>
          </div>
          {error && (
            <p className="text-sm font-medium text-red-600" role="alert">
              {error}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-wrap rounded-lg border border-border bg-muted/30 p-1">
            {CHANNELS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setChannel(id)}
                disabled={!!ticket}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors",
                  channel === id
                    ? "bg-card font-medium text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                  ticket && "cursor-not-allowed opacity-60"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>

          <Button onClick={startNewSession} className="gap-1.5">
            <Plus className="h-4 w-4" />
            Novo atendimento
          </Button>

          {ticket && (
            <>
              <Button variant="outline" onClick={generateDraft} disabled={loading} className="gap-1.5">
                <Wand2 className="h-4 w-4" />
                Rascunho RAG
              </Button>
              <Button variant="outline" onClick={resolveAuto} disabled={loading} className="gap-1.5">
                <Sparkles className="h-4 w-4" />
                Resolver com IA
              </Button>
            </>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_300px] xl:grid-cols-[1fr_320px]">
          <section className="flex min-h-[520px] flex-col rounded-xl border border-border bg-card shadow-sm">
            <header className="flex items-center gap-2 border-b border-border px-4 py-3">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
              </span>
              <h3 className="text-sm font-semibold">
                {channelLabel} · {ticket ? `#${ticket.ticket_number}` : "Nova conversa"}
              </h3>
              {ticket && (
                <span className="ml-auto text-xs text-muted-foreground">
                  {ticket.customer_name}
                </span>
              )}
            </header>

            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
              {messages.length === 0 && !draft && (
                <p className="py-12 text-center text-sm text-muted-foreground">
                  {ticket
                    ? "Nenhuma mensagem na conversa ainda."
                    : "Digite abaixo para abrir um atendimento e iniciar a triagem."}
                </p>
              )}

              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm",
                    m.role === "customer"
                      ? "ml-auto bg-primary text-primary-foreground"
                      : m.role === "agent"
                        ? "mr-auto border border-border bg-muted/40"
                        : "mx-auto border border-dashed border-border bg-muted/20 text-xs text-muted-foreground"
                  )}
                >
                  <p className="mb-0.5 text-[10px] font-medium opacity-70">
                    {m.role === "customer"
                      ? "Você"
                      : m.role === "agent"
                        ? "RotaDesk"
                        : "Sistema"}{" "}
                    · {formatDateTime(m.created_at)}
                  </p>
                  <p className="whitespace-pre-wrap">{normalizePtBr(m.content)}</p>
                </div>
              ))}

              {draft && (
                <div className="mr-auto max-w-[90%] rounded-xl border border-blue-200 bg-blue-50/80 p-3 text-sm">
                  <p className="mb-1 flex items-center gap-1 text-xs font-semibold text-blue-800">
                    <Wand2 className="h-3 w-3" />
                    Sugestão para o agente (RAG)
                  </p>
                  <p className="whitespace-pre-wrap text-blue-900">{normalizePtBr(draft)}</p>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-border p-3">
              <form
                className="flex items-center gap-2 rounded-xl border border-border bg-muted/30 px-3 py-2 focus-within:ring-2 focus-within:ring-ring/30"
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
              >
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  disabled={loading}
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                />
                <button
                  type="submit"
                  disabled={loading || !message.trim()}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity disabled:opacity-40"
                  aria-label="Enviar mensagem"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </section>

          <ClassificationPanel ticket={ticket} turn={turn} />
        </div>
      </div>
    </DashboardLayout>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <DashboardLayout title="Atendimento">
          <p className="text-sm text-muted-foreground">Carregando atendimento...</p>
        </DashboardLayout>
      }
    >
      <ChatPageContent />
    </Suspense>
  );
}

function messagesShowSystem(m: TicketMessage, ticket: TicketWithMessages | null) {
  if (m.role !== "system" || !ticket) return false;
  return (ticket.ticket_messages ?? []).filter((x) => x.role !== "system").length === 0;
}
