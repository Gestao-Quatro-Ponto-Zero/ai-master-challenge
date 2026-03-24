import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge, PriorityBadge } from "@/components/tickets/ticket-badge";
import { useTickets, useUpdateTicket } from "@/hooks/use-tickets";
import { Link } from "wouter";
import { Search, ChevronRight, Filter } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

const STATUSES = ["Todos", "Aberto", "Em Andamento", "Resolvido", "Fechado"];
const PRIORITIES = ["Todas", "Baixa", "Média", "Alta", "Crítica"];

export default function AdminChamados() {
  const { data: tickets, isLoading } = useTickets();
  const updateTicket = useUpdateTicket();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("Todos");
  const [priorityFilter, setPriorityFilter] = useState("Todas");

  const filtered = (tickets || []).filter(t => {
    const matchSearch = !search || t.title.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "Todos" || t.status === statusFilter;
    const matchPriority = priorityFilter === "Todas" || t.priority === priorityFilter;
    return matchSearch && matchStatus && matchPriority;
  });

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Gerenciar Chamados</h1>
        <p className="text-muted-foreground">Visualize e gerencie todos os chamados de suporte.</p>
      </div>

      {/* Filters */}
      <Card className="border-border/50 mb-6">
        <CardContent className="p-4 flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Buscar chamados..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 border-border/50"
              data-testid="input-search"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-44 border-border/50" data-testid="select-status">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className="w-44 border-border/50" data-testid="select-priority">
              <SelectValue placeholder="Prioridade" />
            </SelectTrigger>
            <SelectContent>
              {PRIORITIES.map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Ticket list */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="font-display text-lg">
            {isLoading ? "Carregando..." : `${filtered.length} chamado${filtered.length !== 1 ? "s" : ""}`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border/30">
            {isLoading ? (
              [...Array(5)].map((_, i) => <Skeleton key={i} className="h-20 mx-6 my-3 rounded-lg" />)
            ) : filtered.length === 0 ? (
              <p className="text-muted-foreground text-sm p-6">Nenhum chamado encontrado.</p>
            ) : (
              filtered.map(ticket => (
                <div key={ticket.id} className="flex items-center gap-4 px-6 py-4" data-testid={`row-ticket-${ticket.id}`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-foreground truncate">{ticket.title}</span>
                      <span className="text-xs text-muted-foreground font-mono shrink-0">#{ticket.id}</span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-1 mb-2">{ticket.description}</p>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge status={ticket.status} />
                      <PriorityBadge priority={ticket.priority} />
                      <span className="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">{ticket.category}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <Select
                      value={ticket.status}
                      onValueChange={value => updateTicket.mutate({ id: ticket.id, status: value })}
                    >
                      <SelectTrigger className="w-36 h-8 text-xs border-border/50" data-testid={`select-status-${ticket.id}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["Aberto", "Em Andamento", "Resolvido", "Fechado"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    <Link href={`/tickets/${ticket.id}`}>
                      <Button variant="ghost" size="sm" className="h-8 px-2" data-testid={`button-view-ticket-${ticket.id}`}>
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
