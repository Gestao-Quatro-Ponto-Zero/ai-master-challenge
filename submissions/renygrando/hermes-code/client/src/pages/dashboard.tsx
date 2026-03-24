import { AppLayout } from "@/components/layout/app-layout";
import { useDashboardMetrics } from "@/hooks/use-dashboard";
import { StatCard } from "@/components/ui/stat-card";
import { Activity, AlertTriangle, Clock, BrainCircuit } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";

export default function Dashboard() {
  const { data: metrics, isLoading } = useDashboardMetrics();

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin w-8 h-8 border-4 border-secondary border-t-transparent rounded-full"></div>
        </div>
      </AppLayout>
    );
  }

  const categoryData = metrics ? Object.entries(metrics.ticketsByCategory).map(([name, value]) => ({
    name, value
  })) : [];

  const trendData = [
    { time: '08h', volume: 12, resolved: 8 },
    { time: '10h', volume: 25, resolved: 15 },
    { time: '12h', volume: 45, resolved: 30 },
    { time: '14h', volume: 30, resolved: 40 },
    { time: '16h', volume: 20, resolved: 35 },
    { time: '18h', volume: 15, resolved: 20 },
  ];

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Inteligência Operacional</h1>
        <p className="text-muted-foreground text-lg">Métricas do sistema e desempenho da IA em tempo real.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Chamados Ativos" 
          value={metrics?.activeTickets || 0}
          icon={Activity}
          trend={{ value: 12, isPositive: false }}
          description="vs últimas 24h"
        />
        <StatCard 
          title="Tempo Médio de Resolução" 
          value={`${metrics?.avgResolutionTime || 0}h`}
          icon={Clock}
          trend={{ value: 15, isPositive: true }}
          description="melhoria"
        />
        <StatCard 
          title="Riscos de SLA" 
          value={metrics?.slaRiskCount || 0}
          icon={AlertTriangle}
          className={metrics?.slaRiskCount && metrics.slaRiskCount > 10 ? "border-destructive/50" : ""}
        />
        <StatCard 
          title="Automação IA" 
          value={`${metrics?.automationRate || 0}%`}
          icon={BrainCircuit}
          trend={{ value: 5, isPositive: true }}
          description="resolvidos automaticamente"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2 border-border/50">
          <CardHeader>
            <CardTitle className="font-display text-xl text-foreground" data-testid="text-chart-title-trend">Volume e Tendência de Resolução</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--secondary))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--secondary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
                  <Area type="monotone" dataKey="volume" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" name="Recebidos" />
                  <Area type="monotone" dataKey="resolved" stroke="hsl(var(--secondary))" strokeWidth={2} fillOpacity={1} fill="url(#colorResolved)" name="Resolvidos" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="font-display text-xl text-foreground" data-testid="text-chart-title-category">Distribuição por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} layout="vertical" margin={{ top: 0, right: 0, left: 20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" stroke="hsl(var(--foreground))" fontSize={11} tickLine={false} axisLine={false} width={80} />
                  <Tooltip cursor={{fill: 'hsl(var(--muted))'}} contentStyle={{ borderRadius: '8px' }} />
                  <Bar dataKey="value" fill="hsl(var(--secondary))" radius={[0, 4, 4, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {metrics?.bottlenecks && metrics.bottlenecks.length > 0 && (
        <Card className="border-border/50 relative">
          <div className="absolute top-0 left-0 w-1 h-full bg-destructive rounded-l-md"></div>
          <CardHeader>
            <CardTitle className="font-display text-xl text-foreground flex items-center gap-2" data-testid="text-bottlenecks-title">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Gargalos e Riscos do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left" data-testid="table-bottlenecks">
                <thead className="text-xs uppercase bg-muted/50 text-muted-foreground border-b border-border/50">
                  <tr>
                    <th className="px-4 py-3 rounded-tl-md font-semibold tracking-wider">Categoria</th>
                    <th className="px-4 py-3 font-semibold tracking-wider">Volume</th>
                    <th className="px-4 py-3 font-semibold tracking-wider">Atraso Médio (h)</th>
                    <th className="px-4 py-3 rounded-tr-md font-semibold tracking-wider">Risco</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.bottlenecks.map((b, i) => (
                    <tr key={i} className="border-b border-border/30" data-testid={`row-bottleneck-${i}`}>
                      <td className="px-4 py-4 font-medium" data-testid={`text-bottleneck-category-${i}`}>{b.category}</td>
                      <td className="px-4 py-4">{b.ticketCount} chamados</td>
                      <td className="px-4 py-4">{b.avgResolution}</td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-secondary/20 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${b.riskScore > 0.7 ? 'bg-destructive' : 'bg-secondary'}`} style={{ width: `${b.riskScore * 100}%` }}></div>
                          </div>
                          <span className="text-xs font-semibold" data-testid={`text-risk-score-${i}`}>{(b.riskScore * 10).toFixed(1)}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </AppLayout>
  );
}
