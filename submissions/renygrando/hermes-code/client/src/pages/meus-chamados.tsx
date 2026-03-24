import { useMyTickets } from "@/hooks/use-tickets";
import { AppLayout } from "@/components/layout/app-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/tickets/ticket-badge";
import { Link } from "wouter";
import { MessageSquarePlus, Inbox, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/auth";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

export default function MeusChamados() {
  const { user } = useAuth();
  const { data: tickets, isLoading } = useMyTickets();

  return (
    <AppLayout>
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-display font-bold text-foreground mb-1" data-testid="text-page-title">Meus Chamados</h1>
          <p className="text-muted-foreground">Olá, <span className="font-semibold text-foreground">{user?.name}</span> — acompanhe seus chamados de suporte abaixo.</p>
        </div>
        <Link href="/abrir-chamado">
          <Button className="gap-2" data-testid="button-open-ticket">
            <MessageSquarePlus className="w-4 h-4" />
            Abrir Chamado
          </Button>
        </Link>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          [...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-xl" />)
        ) : !tickets || tickets.length === 0 ? (
          <Card className="border-dashed border-2 border-border/50">
            <CardContent className="py-16 flex flex-col items-center gap-4 text-center">
              <div className="p-4 rounded-full bg-muted">
                <Inbox className="w-8 h-8 text-muted-foreground" />
              </div>
              <div>
                <p className="font-semibold text-foreground mb-1">Nenhum chamado ainda</p>
                <p className="text-sm text-muted-foreground">Abra seu primeiro chamado de suporte para começar.</p>
              </div>
              <Link href="/abrir-chamado">
                <Button variant="outline" className="gap-2" data-testid="button-open-first-ticket">
                  <MessageSquarePlus className="w-4 h-4" />
                  Abrir primeiro chamado
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          tickets.map(ticket => (
            <Link key={ticket.id} href={`/chamado/${ticket.id}`} data-testid={`link-ticket-${ticket.id}`}>
              <Card className="border-border/50 hover-elevate cursor-pointer transition-all">
                <CardContent className="p-5 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className="font-semibold text-foreground truncate" data-testid={`text-ticket-title-${ticket.id}`}>{ticket.title}</span>
                      <span className="text-xs text-muted-foreground font-mono shrink-0">#{ticket.id}</span>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1 mb-3">{ticket.description}</p>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={ticket.status} />
                      <PriorityBadge priority={ticket.priority} />
                      <span className="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">{ticket.category}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      {ticket.createdAt ? formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true, locale: ptBR }) : ""}
                    </span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </AppLayout>
  );
}
