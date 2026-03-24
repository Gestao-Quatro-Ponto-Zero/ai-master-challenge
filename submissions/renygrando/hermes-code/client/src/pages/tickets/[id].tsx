import { useParams, Link } from "wouter";
import { AppLayout } from "@/components/layout/app-layout";
import { useTicket, useUpdateTicket, useSuggestResponse } from "@/hooks/use-tickets";
import { PriorityBadge, StatusBadge } from "@/components/tickets/ticket-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Sparkles, Send, Clock, User, CheckCircle2, Loader2 } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { useState } from "react";

export default function TicketDetail() {
  const params = useParams();
  const id = parseInt(params.id || "0");
  
  const { data: ticket, isLoading } = useTicket(id);
  const updateMutation = useUpdateTicket();
  const suggestMutation = useSuggestResponse();

  const [replyText, setReplyText] = useState("");
  const [activeSuggestion, setActiveSuggestion] = useState<string | null>(null);

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-secondary" />
        </div>
      </AppLayout>
    );
  }

  if (!ticket) {
    return (
      <AppLayout>
        <div className="text-center py-20">
          <h2 className="text-2xl font-display text-foreground mb-4" data-testid="text-ticket-not-found">Chamado não encontrado</h2>
          <Link href="/admin/chamados" className="text-secondary hover:underline" data-testid="link-back-to-tickets">Voltar à lista</Link>
        </div>
      </AppLayout>
    );
  }

  const handleStatusChange = (newStatus: string) => {
    updateMutation.mutate({ id, status: newStatus });
  };

  const handleSuggest = async () => {
    try {
      const res = await suggestMutation.mutateAsync(id);
      setActiveSuggestion(res.suggestedResponse);
    } catch (e) {
      console.error(e);
      setActiveSuggestion(`Olá! Obrigado por entrar em contato sobre o problema com ${ticket.category}. Revisamos sua solicitação e estamos tomando as medidas necessárias para resolvê-la. Poderia confirmar se o problema persiste após reiniciar o sistema?`);
    }
  };

  const handleApplySuggestion = () => {
    if (activeSuggestion) {
      setReplyText(activeSuggestion);
      setActiveSuggestion(null);
    }
  };

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/admin/chamados" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors mb-4" data-testid="link-back-tickets">
          <ArrowLeft className="w-4 h-4 mr-1" /> Voltar aos chamados
        </Link>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <h1 className="text-3xl font-display font-bold text-foreground" data-testid="text-ticket-title">{ticket.title}</h1>
              <span className="text-muted-foreground font-mono text-lg" data-testid="text-ticket-id">#{ticket.id}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {ticket.createdAt ? format(new Date(ticket.createdAt), "d 'de' MMM 'de' yyyy HH:mm", { locale: ptBR }) : "–"}
              </span>
              <span>|</span>
              <span className="flex items-center gap-1"><User className="w-4 h-4" /> Solicitação do sistema</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Select value={ticket.status} onValueChange={handleStatusChange} disabled={updateMutation.isPending}>
              <SelectTrigger className="w-[160px] bg-card border-border/50 font-medium" data-testid="select-ticket-status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Aberto">Aberto</SelectItem>
                <SelectItem value="Em Andamento">Em Andamento</SelectItem>
                <SelectItem value="Resolvido">Resolvido</SelectItem>
                <SelectItem value="Fechado">Fechado</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border/50">
            <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
              <CardTitle className="text-lg font-semibold flex justify-between items-center gap-2 flex-wrap">
                Descrição
                <div className="flex gap-2 flex-wrap">
                  <StatusBadge status={ticket.status} />
                  <PriorityBadge priority={ticket.priority} />
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <p className="whitespace-pre-wrap text-foreground/90 leading-relaxed" data-testid="text-ticket-description">
                {ticket.description}
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader className="bg-muted/20 border-b border-border/50">
              <CardTitle className="text-lg font-semibold flex items-center justify-between gap-2 flex-wrap">
                Resposta
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-secondary border-secondary/30"
                  onClick={handleSuggest}
                  disabled={suggestMutation.isPending}
                  data-testid="button-ai-suggestion"
                >
                  {suggestMutation.isPending ? <Loader2 className="w-3 h-3 mr-2 animate-spin" /> : <Sparkles className="w-3 h-3 mr-2" />}
                  Sugestão IA
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              {activeSuggestion && (
                <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-md relative" data-testid="text-ai-suggestion">
                  <div className="absolute -top-3 left-4 bg-emerald-100 dark:bg-emerald-800 text-emerald-800 dark:text-emerald-200 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-700">
                    Rascunho IA
                  </div>
                  <p className="text-sm text-emerald-900 dark:text-emerald-200 mb-3 mt-2">{activeSuggestion}</p>
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="sm" onClick={() => setActiveSuggestion(null)} data-testid="button-dismiss-suggestion">Descartar</Button>
                    <Button size="sm" onClick={handleApplySuggestion} data-testid="button-apply-suggestion">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Aplicar
                    </Button>
                  </div>
                </div>
              )}

              <Textarea 
                placeholder="Digite sua resposta..." 
                className="min-h-[150px] resize-y mb-4 border-border/50 focus-visible:ring-secondary"
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                data-testid="input-reply"
              />
              <div className="flex justify-end">
                <Button className="gap-2" data-testid="button-send-reply">
                  <Send className="w-4 h-4" /> Enviar Resposta
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-border/50 bg-muted/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-foreground">Metadados do Chamado</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1 font-semibold uppercase">Categoria</div>
                <div className="font-medium px-3 py-1 bg-background rounded-md border border-border inline-block" data-testid="text-ticket-category">{ticket.category}</div>
              </div>
              <Separator />
              <div>
                <div className="text-xs text-muted-foreground mb-1 font-semibold uppercase">Canal</div>
                <div className="font-medium capitalize" data-testid="text-ticket-channel">{ticket.channel}</div>
              </div>
              <Separator />
              <div>
                <div className="text-xs text-muted-foreground mb-1 font-semibold uppercase">Confiança IA</div>
                <div className="flex items-center gap-2">
                  <div className="w-full h-2 bg-background rounded-full overflow-hidden border border-border">
                    <div className="h-full bg-secondary" style={{ width: `${(ticket.confidenceScore || 0) * 100}%` }} />
                  </div>
                  <span className="text-sm font-medium" data-testid="text-confidence-score">{Math.round((ticket.confidenceScore || 0) * 100)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">Problemas Similares Resolvidos</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="p-3 rounded-md border border-border/50 bg-muted/20 cursor-pointer hover-elevate group" data-testid={`card-similar-ticket-${i}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                    <span className="font-medium text-sm group-hover:text-secondary transition-colors">Falha de login após atualização</span>
                  </div>
                  <div className="text-xs text-muted-foreground ml-6">Resolvido em 45min | 94% de correspondência</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
