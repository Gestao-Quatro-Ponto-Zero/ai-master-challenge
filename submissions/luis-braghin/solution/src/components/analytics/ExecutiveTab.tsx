import { useMemo } from "react";
import { useDeals, useAnalytics, useClosedDeals } from "@/hooks/useG4Data";
import { KPICard } from "@/components/dashboard/KPICard";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { DollarSign, Target, TrendingUp, AlertTriangle, Calendar, HelpCircle } from "lucide-react";
import { formatUSD } from "@/lib/formatters";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

const tooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "8px",
};

export default function ExecutiveTab() {
  const { data: deals = [] } = useDeals();
  const { data: analytics } = useAnalytics();
  const { data: closedDeals = [] } = useClosedDeals();

  const totalPipeline = useMemo(() => deals.reduce((s, d) => s + d.salesPrice, 0), [deals]);
  const totalEV = useMemo(() => deals.reduce((s, d) => s + d.expectedValue, 0), [deals]);

  const top20 = useMemo(() => {
    const sorted = [...deals].sort((a, b) => b.score - a.score);
    const cutoff = Math.ceil(sorted.length * 0.2);
    const top = sorted.slice(0, cutoff);
    return {
      count: top.length,
      ev: top.reduce((s, d) => s + d.expectedValue, 0),
      pipeline: top.reduce((s, d) => s + d.salesPrice, 0),
    };
  }, [deals]);

  const categoryData = useMemo(() => {
    const counts: Record<string, number> = {};
    deals.forEach(d => { counts[d.category] = (counts[d.category] || 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [deals]);

  const seasonalityData = useMemo(() => {
    if (!analytics) return [];
    return [
      { quarter: "Fim de Trimestre", winRate: +(analytics.seasonality.pushMonths.avgWinRate * 100).toFixed(1) },
      { quarter: "Outros Meses", winRate: +(analytics.seasonality.nonPushMonths.avgWinRate * 100).toFixed(1) },
    ];
  }, [analytics]);

  const velocityData = useMemo(() => {
    if (!analytics) return [];
    return analytics.velocityCurve.map(v => ({
      ...v,
      winRate: +(v.winRate * 100).toFixed(1),
    }));
  }, [analytics]);

  const insights = useMemo(() => {
    const msgs: React.ReactNode[] = [];
    if (analytics) {
      msgs.push(`Se focarem nos top 20% dos deals (${top20.count} deals), o expected value é de ${formatUSD(top20.ev)} — ${((top20.ev / totalEV) * 100).toFixed(0)}% do EV total.`);
      msgs.push(`Pipeline inflado: ${(analytics.pipelineHealth.pctInflated * 100).toFixed(0)}% dos deals estão há mais de 90 dias no pipeline. EV ajustado deveria considerar desconto nesses deals.`);
      msgs.push(`Sazonalidade forte: fim de trimestre tem win rate ${(analytics.seasonality.difference * 100).toFixed(0)}pp maior. Alinhe push comercial com esses meses.`);
      const wonDeals = closedDeals.filter(d => d.stage === "Won");
      const totalClosed = closedDeals.length;
      if (totalClosed > 0) {
        const realWR = wonDeals.length / totalClosed;
        msgs.push(
          <span key="backtest" className="inline-flex items-center gap-1 flex-wrap">
            Backtest: win rate real histórica {(realWR * 100).toFixed(1)}% vs modelo {(analytics.overallWinRate * 100).toFixed(1)}%.
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help inline shrink-0" />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs text-xs">
                <p><strong>Win rate real</strong>: taxa de vitória observada nos deals históricos já fechados (Won ÷ total Won+Lost).</p>
                <p className="mt-1"><strong>Win rate do modelo</strong>: taxa prevista pelo sistema de scoring. Quanto mais próximos os valores, mais calibrado está o modelo.</p>
              </TooltipContent>
            </Tooltip>
          </span>
        );
      }
    }
    return msgs;
  }, [analytics, top20, totalEV, closedDeals]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Pipeline Total" value={formatUSD(totalPipeline)} icon={DollarSign} />
        <KPICard title="Expected Value" value={formatUSD(totalEV)} icon={Target} variant="success" />
        <KPICard title="EV Top 20%" value={formatUSD(top20.ev)} subtitle={`${top20.count} deals prioritários`} icon={TrendingUp} variant="success" />
        <KPICard
          title="Pipeline Inflado"
          value={analytics ? `${(analytics.pipelineHealth.pctInflated * 100).toFixed(0)}%` : "—"}
          subtitle={`${analytics?.pipelineHealth.over90Days ?? 0} deals >90d`}
          icon={AlertTriangle}
          variant="destructive"
        />
      </div>

      <InsightsPanel title="Insights Estratégicos" insights={insights} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Sazonalidade — Win Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={seasonalityData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="quarter" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <RechartsTooltip contentStyle={tooltipStyle} />
                <Bar dataKey="winRate" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} name="Win Rate %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Distribuição por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" nameKey="name" label>
                  {categoryData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={tooltipStyle} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Curva de Velocidade — Win Rate por Tempo no Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={velocityData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="range" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <RechartsTooltip contentStyle={tooltipStyle} />
                <Bar dataKey="winRate" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} name="Win Rate %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
