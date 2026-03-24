import { useState, useRef, useEffect } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Send, CheckCircle, Bot, User } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { queryClient } from "@/lib/queryClient";
import { useAuth } from "@/context/auth";
import { useLocation } from "wouter";

type Message = { role: "user" | "assistant"; content: string };

export default function AbrirChamado() {
  const { user } = useAuth();
  const [, setLocation] = useLocation();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: `Olá, ${user?.name || ""}! Sou o Assistente Hermes. 👋\n\nPode me descrever o problema que está enfrentando? Vou coletar as informações necessárias e abrir o chamado para você.` },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ticketCreated, setTicketCreated] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const newMessages: Message[] = [...messages, { role: "user" as const, content: text }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await apiRequest("POST", "/api/ai/chat", {
        messages: newMessages.filter(m => m.role !== undefined),
      });
      const data = await res.json();

      setMessages(prev => [...prev, { role: "assistant", content: data.reply }]);

      if (data.ticketData) {
        // Create the ticket
        const ticketRes = await apiRequest("POST", "/api/tickets", {
          ...data.ticketData,
          status: "Aberto",
        });
        const ticket = await ticketRes.json();
        setTicketCreated(ticket.id);
        queryClient.invalidateQueries({ queryKey: ["/api/tickets/mine"] });
      }
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Desculpe, ocorreu um erro. Por favor, tente novamente." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (ticketCreated) {
    return (
      <AppLayout>
        <div className="max-w-xl mx-auto py-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/40 mb-6">
            <CheckCircle className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h1 className="text-3xl font-display font-bold text-foreground mb-3">Chamado Aberto!</h1>
          <p className="text-muted-foreground mb-8">Seu chamado <span className="font-bold text-foreground">#{ticketCreated}</span> foi registrado com sucesso. Nossa equipe de suporte entrará em contato em breve.</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={() => setLocation(`/chamado/${ticketCreated}`)} data-testid="button-view-ticket">
              Ver chamado
            </Button>
            <Button variant="outline" onClick={() => setLocation("/meus-chamados")} data-testid="button-my-tickets">
              Meus chamados
            </Button>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="mb-6">
        <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Abrir Chamado</h1>
        <p className="text-muted-foreground">Converse com nosso assistente de IA para registrar seu chamado de suporte.</p>
      </div>

      <div className="max-w-3xl mx-auto">
        <Card className="border-border/50">
          <CardContent className="p-0">
            {/* Chat messages */}
            <div className="h-[480px] overflow-y-auto p-6 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === "assistant" ? "bg-primary text-secondary" : "bg-secondary text-primary"}`}>
                    {msg.role === "assistant" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>
                  <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "assistant"
                      ? "bg-card border border-border/50 text-foreground"
                      : "bg-primary text-primary-foreground"
                  }`} data-testid={`message-${msg.role}-${i}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-primary text-secondary">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-card border border-border/50 rounded-xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t border-border/50 p-4 flex gap-3">
              <Textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Descreva seu problema... (Enter para enviar)"
                className="resize-none border-border/50 bg-background/50 min-h-[48px] max-h-[120px]"
                rows={1}
                disabled={loading}
                data-testid="input-chat-message"
              />
              <Button onClick={sendMessage} disabled={loading || !input.trim()} className="shrink-0" data-testid="button-send-message">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
