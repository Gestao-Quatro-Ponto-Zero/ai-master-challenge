import { useState } from "react";
import { Link } from "wouter";
import { AppLayout } from "@/components/layout/app-layout";
import { useTickets, useCreateTicket, useClassifyTicket } from "@/hooks/use-tickets";
import { PriorityBadge, StatusBadge } from "@/components/tickets/ticket-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Plus, Filter, Sparkles, Loader2 } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

export default function TicketsList() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("todos");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: tickets, isLoading } = useTickets(statusFilter !== "todos" ? statusFilter : undefined);

  const filteredTickets = tickets?.filter(t => 
    t.title.toLowerCase().includes(search.toLowerCase()) || 
    t.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Chamados de Suporte</h1>
          <p className="text-muted-foreground text-lg">Gerenciar e resolver solicitações de suporte.</p>
        </div>
        <CreateTicketDialog open={isDialogOpen} onOpenChange={setIsDialogOpen} />
      </div>

      <Card className="mb-6 border-border/50 bg-card/80 backdrop-blur-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input 
              placeholder="Buscar por título ou conteúdo..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 border-border/50 bg-background/50 focus-visible:ring-secondary"
              data-testid="input-search-tickets"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="text-muted-foreground w-4 h-4" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px] border-border/50 bg-background/50" data-testid="select-status-filter">
                <SelectValue placeholder="Todos os status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os status</SelectItem>
                <SelectItem value="Aberto">Aberto</SelectItem>
                <SelectItem value="Em Andamento">Em Andamento</SelectItem>
                <SelectItem value="Resolvido">Resolvido</SelectItem>
                <SelectItem value="Fechado">Fechado</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-secondary" />
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredTickets?.length === 0 ? (
            <div className="text-center p-12 border border-dashed border-border rounded-md text-muted-foreground" data-testid="text-no-tickets">
              Nenhum chamado encontrado com esses critérios.
            </div>
          ) : (
            filteredTickets?.map((ticket) => (
              <Link key={ticket.id} href={`/tickets/${ticket.id}`} className="block group" data-testid={`link-ticket-${ticket.id}`}>
                <Card className="transition-all duration-200 hover-elevate border-border/50 cursor-pointer">
                  <CardContent className="p-5 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span className="text-xs font-mono text-muted-foreground font-semibold" data-testid={`text-ticket-id-${ticket.id}`}>#{ticket.id.toString().padStart(4, '0')}</span>
                        <h3 className="font-semibold text-foreground truncate text-lg group-hover:text-secondary transition-colors" data-testid={`text-ticket-title-${ticket.id}`}>{ticket.title}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-1 mb-3">{ticket.description}</p>
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusBadge status={ticket.status} />
                        <PriorityBadge priority={ticket.priority} />
                        <span className="text-xs px-2 py-1 bg-secondary/10 text-secondary rounded-full border border-secondary/20">
                          {ticket.category}
                        </span>
                        {ticket.confidenceScore && (
                          <span className="text-xs flex items-center gap-1 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-1 rounded-full">
                            <Sparkles className="w-3 h-3" /> {Math.round(ticket.confidenceScore * 100)}% Confiança
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs text-muted-foreground mb-1">Criado em</div>
                      <div className="text-sm font-medium" data-testid={`text-ticket-date-${ticket.id}`}>
                        {ticket.createdAt ? format(new Date(ticket.createdAt), "d MMM yyyy HH:mm", { locale: ptBR }) : "–"}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}
    </AppLayout>
  );
}

function CreateTicketDialog({ open, onOpenChange }: { open: boolean, onOpenChange: (val: boolean) => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Diversos");
  const [priority, setPriority] = useState("Média");
  
  const createMutation = useCreateTicket();
  const classifyMutation = useClassifyTicket();

  const handleClassify = async () => {
    if (!description) return;
    try {
      const res = await classifyMutation.mutateAsync(description);
      setCategory(res.category);
      setPriority(res.priority);
    } catch (e) { console.error(e); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createMutation.mutateAsync({ title, description, category, priority, status: "Aberto", channel: "web" });
    onOpenChange(false);
    setTitle("");
    setDescription("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button className="gap-2 font-semibold" data-testid="button-new-ticket">
          <Plus className="w-4 h-4" /> Novo Chamado
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] border-secondary/20">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl text-foreground" data-testid="text-dialog-title">Criar Chamado de Suporte</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label htmlFor="title" className="font-semibold">Título</Label>
            <Input id="title" value={title} onChange={e => setTitle(e.target.value)} placeholder="Resumo breve do problema" required data-testid="input-ticket-title" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center gap-2">
              <Label htmlFor="description" className="font-semibold">Descrição</Label>
              <Button type="button" variant="ghost" size="sm" className="text-xs text-secondary" onClick={handleClassify} disabled={classifyMutation.isPending || !description} data-testid="button-auto-classify">
                {classifyMutation.isPending ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Sparkles className="w-3 h-3 mr-1" />}
                Classificar com IA
              </Button>
            </div>
            <Textarea id="description" value={description} onChange={e => setDescription(e.target.value)} placeholder="Forneça informações detalhadas sobre o problema..." className="min-h-[120px]" required data-testid="input-ticket-description" />
          </div>
          <div className="grid grid-cols-2 gap-4 p-4 bg-muted/30 rounded-md border border-border/50">
            <div className="space-y-2">
              <Label className="text-xs uppercase text-muted-foreground font-semibold">Categoria</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger data-testid="select-ticket-category"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Acesso">Acesso</SelectItem>
                  <SelectItem value="Direitos Administrativos">Direitos Administrativos</SelectItem>
                  <SelectItem value="Suporte RH">Suporte RH</SelectItem>
                  <SelectItem value="Hardware">Hardware</SelectItem>
                  <SelectItem value="Projeto Interno">Projeto Interno</SelectItem>
                  <SelectItem value="Diversos">Diversos</SelectItem>
                  <SelectItem value="Compra">Compra</SelectItem>
                  <SelectItem value="Armazenamento">Armazenamento</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase text-muted-foreground font-semibold">Prioridade</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger data-testid="select-ticket-priority"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Baixa">Baixa</SelectItem>
                  <SelectItem value="Média">Média</SelectItem>
                  <SelectItem value="Alta">Alta</SelectItem>
                  <SelectItem value="Crítica">Crítica</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} data-testid="button-cancel-ticket">Cancelar</Button>
            <Button type="submit" disabled={createMutation.isPending} data-testid="button-submit-ticket">
              {createMutation.isPending ? "Criando..." : "Criar Chamado"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
