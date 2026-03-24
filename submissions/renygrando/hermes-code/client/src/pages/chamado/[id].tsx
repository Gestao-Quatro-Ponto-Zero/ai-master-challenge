import { useState, useRef, useEffect } from "react";
import { useParams } from "wouter";
import { AppLayout } from "@/components/layout/app-layout";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/tickets/ticket-badge";
import { Send, Bot, User, ArrowLeft } from "lucide-react";
import { Link } from "wouter";
import { useTicket, useTicketMessages, useSendTicketMessage } from "@/hooks/use-tickets";
import { useAuth } from "@/context/auth";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

export default function ChamadoChat() {
  const { id } = useParams<{ id: string }>();
  const ticketId = Number(id);
  const { user } = useAuth();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: ticket, isLoading: ticketLoading } = useTicket(ticketId);
  const { data: messages, isLoading: msgsLoading } = useTicketMessages(ticketId);
  const sendMsg = useSendTicketMessage();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sendMsg.isPending) return;
    setInput("");
    await sendMsg.mutateAsync({ ticketId, message: text });
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/meus-chamados" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors" data-testid="link-back">
          <ArrowLeft className="w-4 h-4" /> Voltar para meus chamados
        </Link>

        {ticketLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : ticket ? (
          <div>
            <div className="flex items-start gap-3 flex-wrap">
              <h1 className="text-3xl font-display font-bold text-foreground" data-testid="text-ticket-title">
                {ticket.title}
              </h1>
              <span className="text-muted-foreground font-mono text-sm mt-1">#{ticket.id}</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-3">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              <span className="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">{ticket.category}</span>
            </div>
          </div>
        ) : null}
      </div>

      <div className="max-w-3xl mx-auto">
        <Card className="border-border/50">
          <CardHeader className="border-b border-border/30 py-3 px-6">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Histórico de mensagens</p>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[420px] overflow-y-auto p-6 space-y-4">
              {ticketLoading || msgsLoading ? (
                [...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)
              ) : (
                <>
                  {ticket && (
                    <div className="flex gap-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-muted text-muted-foreground">
                        <User className="w-4 h-4" />
                      </div>
                      <div className="max-w-[80%]">
                        <p className="text-xs text-muted-foreground mb-1">Descrição original</p>
                        <div className="bg-card border border-border/50 rounded-xl px-4 py-3 text-sm text-foreground whitespace-pre-wrap">
                          {ticket.description}
                        </div>
                      </div>
                    </div>
                  )}

                  {messages && messages.map((msg: any) => (
                    <div key={msg.id} className={`flex gap-3 ${msg.senderType === "user" ? "flex-row-reverse" : "flex-row"}`} data-testid={`message-${msg.id}`}>
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.senderType === "user" ? "bg-secondary text-primary" : "bg-primary text-secondary"}`}>
                        {msg.senderType === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                      </div>
                      <div className={`max-w-[80%] ${msg.senderType === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                        <p className="text-xs text-muted-foreground">{msg.senderName}</p>
                        <div className={`rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
                          msg.senderType === "user" ? "bg-primary text-primary-foreground" : "bg-card border border-border/50 text-foreground"
                        }`}>
                          {msg.message}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {msg.timestamp ? formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true, locale: ptBR }) : ""}
                        </p>
                      </div>
                    </div>
                  ))}
                </>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="border-t border-border/50 p-4 flex gap-3">
              <Textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Digite sua mensagem... (Enter para enviar)"
                className="resize-none border-border/50 bg-background/50 min-h-[48px] max-h-[120px]"
                rows={1}
                disabled={sendMsg.isPending}
                data-testid="input-message"
              />
              <Button onClick={handleSend} disabled={sendMsg.isPending || !input.trim()} className="shrink-0" data-testid="button-send">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
