import { AppLayout } from "@/components/layout/app-layout";
import { StatCard } from "@/components/ui/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardMetrics } from "@/hooks/use-dashboard";
import { useTickets } from "@/hooks/use-tickets";
import { StatusBadge, PriorityBadge } from "@/components/tickets/ticket-badge";
import { Link } from "wouter";
import { Ticket, Clock, AlertTriangle, Bot, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminDashboard() {
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: tickets, isLoading: ticketsLoading } = useTickets();

  const recentTickets = tickets?.slice(0, 5) || [];

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Painel Administrativo</h1>
        <p className="text-muted-foreground text-lg">Visão geral do suporte de TI em tempo real.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metricsLoading ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-36 rounded-xl" />)
        ) : (
          <>
            <StatCard title="Chamados Ativos" value={metrics?.activeTickets ?? 0} icon={Ticket} trend={{ value: 12, isPositive: false }} description="Aguardando resolução" />
            <StatCard title="Tempo Médio de Resolução" value={metrics?.avgResolutionTime ? `${Math.round(metrics.avgResolutionTime)}min` : "–"} icon={Clock} description="Nos últimos 30 dias" />
            <StatCard title="Risco de SLA" value={metrics?.slaRiskCount ?? 0} icon={AlertTriangle} trend={{ value: 5, isPositive: false }} description="Alta e Crítica" />
            <StatCard title="Taxa de Automação" value={`${metrics?.automationRate ?? 0}%`} icon={Bot} trend={{ value: 8, isPositive: true }} description="Resolvidos pela IA" />
          </>
        )}
      </div>

      {/* Recent tickets */}
      <Card className="border-border/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-display text-xl">Chamados Recentes</CardTitle>
          <Link href="/admin/chamados" className="text-sm text-secondary hover:underline flex items-center gap-1" data-testid="link-all-tickets">
            Ver todos <ChevronRight className="w-4 h-4" />
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border/30">
            {ticketsLoading ? (
              [...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 mx-6 my-3 rounded-lg" />)
            ) : recentTickets.length === 0 ? (
              <p className="text-muted-foreground text-sm p-6">Nenhum chamado encontrado.</p>
            ) : (
              recentTickets.map(ticket => (
                <Link key={ticket.id} href={`/tickets/${ticket.id}`} data-testid={`link-admin-ticket-${ticket.id}`}>
                  <div className="flex items-center gap-4 px-6 py-4 hover:bg-muted/30 transition-colors cursor-pointer">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-foreground truncate text-sm">{ticket.title}</span>
                        <span className="text-xs text-muted-foreground font-mono shrink-0">#{ticket.id}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <StatusBadge status={ticket.status} />
                        <PriorityBadge priority={ticket.priority} />
                        <span className="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">{ticket.category}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Category breakdown */}
      {metrics?.ticketsByCategory && Object.keys(metrics.ticketsByCategory).length > 0 && (
        <Card className="border-border/50 mt-6">
          <CardHeader>
            <CardTitle className="font-display text-xl">Distribuição por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(metrics.ticketsByCategory).map(([cat, count]) => {
                const total = metrics.totalTickets || 1;
                const pct = Math.round(((count as number) / total) * 100);
                return (
                  <div key={cat} className="flex items-center gap-3">
                    <span className="text-sm font-medium w-40 shrink-0 text-foreground">{cat}</span>
                    <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }}></div>
                    </div>
                    <span className="text-xs text-muted-foreground w-12 text-right">{count as number} ({pct}%)</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </AppLayout>
  );
}
