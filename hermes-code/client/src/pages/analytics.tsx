import { AppLayout } from "@/components/layout/app-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useDashboardMetrics } from "@/hooks/use-dashboard";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function Analytics() {
  const { data: metrics } = useDashboardMetrics();

  const performanceData = [
    { day: 'Seg', speed: 85, quality: 92 },
    { day: 'Ter', speed: 82, quality: 94 },
    { day: 'Qua', speed: 90, quality: 91 },
    { day: 'Qui', speed: 87, quality: 95 },
    { day: 'Sex', speed: 92, quality: 96 },
    { day: 'Sáb', speed: 95, quality: 98 },
    { day: 'Dom', speed: 96, quality: 97 },
  ];

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-display font-bold text-foreground mb-2" data-testid="text-page-title">Analytics Executivo</h1>
        <p className="text-muted-foreground text-lg">Análise aprofundada do desempenho da organização de suporte.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="font-display text-xl text-foreground" data-testid="text-chart-title-performance">Matriz de Desempenho da Equipe</CardTitle>
            <CardDescription>Velocidade de resolução vs pontuação de qualidade</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" domain={[70, 100]} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '8px' }} />
                  <Line type="monotone" dataKey="speed" stroke="hsl(var(--primary))" strokeWidth={3} dot={{ r: 4 }} name="Velocidade" />
                  <Line type="monotone" dataKey="quality" stroke="hsl(var(--secondary))" strokeWidth={3} dot={{ r: 4 }} name="Qualidade" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="font-display text-xl text-foreground" data-testid="text-chart-title-deflection">Taxa de Deflexão da IA</CardTitle>
            <CardDescription>Percentual de chamados resolvidos sem intervenção humana</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center flex-col h-[300px]">
            <div className="relative w-48 h-48 rounded-full border-8 border-muted flex items-center justify-center">
              <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                <circle
                  cx="96" cy="96" r="88"
                  fill="none"
                  stroke="hsl(var(--secondary))"
                  strokeWidth="16"
                  strokeDasharray={`${(metrics?.automationRate || 68) * 5.53} 553`}
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="text-center">
                <div className="text-5xl font-display font-bold text-foreground" data-testid="text-deflection-rate">{metrics?.automationRate || 68}%</div>
                <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider mt-1">Deflectido</div>
              </div>
            </div>
            <p className="mt-8 text-sm text-center text-muted-foreground max-w-sm">
              A IA resolveu <strong>{(metrics?.automationRate || 68) * 12}</strong> consultas esta semana, economizando aproximadamente <strong>45 horas</strong> de trabalho.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
