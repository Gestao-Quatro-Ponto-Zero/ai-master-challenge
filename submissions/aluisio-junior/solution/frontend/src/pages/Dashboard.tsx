import { useQuery } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import { fetchDashboardValidation } from "@/lib/api";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/formatters";
import { MetricTooltip } from "@/components/MetricTooltip";
import {
  TrendingDown, Users, DollarSign, AlertTriangle, Info, UserCheck, UserX,
  ShieldAlert, Activity, Target, Clock, BarChart3, Wallet,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend, Line, ComposedChart,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const SEGMENT_COLORS: Record<string, string> = {
  A: "hsl(172, 66%, 50%)",
  B: "hsl(38, 92%, 50%)",
  C: "hsl(220, 9%, 46%)",
};

const RISK_COLORS: Record<string, string> = {
  high: "hsl(0, 84%, 60%)",
  medium: "hsl(38, 92%, 50%)",
  low: "hsl(152, 60%, 52%)",
};

const Dashboard = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-validation"],
    queryFn: fetchDashboardValidation,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  // Keep last valid feature_importance to prevent flicker
  const lastFeatureImportance = useRef<any[]>([]);
  const featureImportance = data?.feature_importance ?? [];
  if (featureImportance.length > 0) {
    lastFeatureImportance.current = featureImportance;
  }
  const shapData = lastFeatureImportance.current;
  const shapLoading = isLoading && shapData.length === 0;

  const cards = data?.cards;
  const riskDist = data?.risk_distribution;
  const pareto = data?.pareto ?? [];
  const segmentation = data?.segmentation ?? [];

  const kpis = cards ? [
    { label: "MRR Total", value: formatCurrency(cards.total_revenue), icon: DollarSign, tip: "Receita recorrente mensal total de todas as contas analisadas.", color: "text-[hsl(var(--chart-up))]" },
    { label: "MRR Ativos", value: formatCurrency(cards.active_mrr), icon: Wallet, tip: "Receita mensal recorrente gerada apenas pelas contas atualmente ativas.", color: "text-[hsl(var(--chart-up))]" },
    { label: "Receita em Risco", value: cards.active_mrr ? formatPercent(cards.risk_mrr / cards.active_mrr) : "—", icon: AlertTriangle, tip: "Percentual da receita ativa atualmente exposta a contas classificadas como alto risco.", color: "text-destructive", sub1: `Em risco: ${formatCurrency(cards.risk_mrr)}`, sub2: `MRR Ativo Total: ${formatCurrency(cards.active_mrr)}` },
    { label: "Taxa de Churn", value: formatPercent(cards.churn_rate), icon: TrendingDown, tip: "Percentual de contas marcadas como canceladas na base analisada.", color: "text-destructive" },
    { label: "Churn de Receita", value: formatPercent(cards.revenue_churn), icon: BarChart3, tip: "Percentual da receita associada a contas canceladas.", color: "text-destructive" },
    { label: "Total de Contas", value: formatNumber(cards.total_accounts), icon: Users, tip: "Número total de contas de clientes analisadas.", color: "text-primary" },
    { label: "Contas Ativas", value: formatNumber(cards.active_accounts), icon: UserCheck, tip: "Contas atualmente consideradas ativas no dataset.", color: "text-[hsl(var(--chart-up))]" },
    { label: "Contas Canceladas", value: formatNumber(cards.churned_accounts), icon: UserX, tip: "Contas que cancelaram na base histórica.", color: "text-destructive" },
    { label: "Contas Alto Risco", value: formatNumber(riskDist?.high), icon: ShieldAlert, tip: "Contas classificadas como alto risco de churn pelo modelo de ML.", color: "text-destructive" },
    { label: "ARPU", value: formatCurrency(cards.arpu), icon: Activity, tip: "Receita média mensal por conta ativa.", color: "text-primary" },
    { label: "LTV", value: formatCurrency(cards.ltv), icon: Target, tip: "Valor total estimado gerado por um cliente ao longo do tempo.", color: "text-primary" },
    { label: "Churn 30d", value: formatPercent(cards.period_churn_30d), icon: Clock, tip: "Percentual de contas com churn na janela dos últimos 30 dias.", color: "text-[hsl(var(--chart-warning))]" },
    { label: "Churn Receita 30d", value: formatPercent(cards.revenue_churn_30d), icon: Clock, tip: "Percentual da receita vinculada a contas que cancelaram nos últimos 30 dias.", color: "text-[hsl(var(--chart-warning))]" },
  ] : [];

  const riskPieData = riskDist ? [
    { name: "Alto", value: riskDist.high, fill: RISK_COLORS.high },
    { name: "Médio", value: riskDist.medium, fill: RISK_COLORS.medium },
    { name: "Baixo", value: riskDist.low, fill: RISK_COLORS.low },
  ] : [];

  const segChartData = segmentation.map((s: any) => ({
    faixa_mrr: s.faixa_mrr,
    active_mrr: s.active_mrr ?? (s.receita_total != null && s.inactive_mrr != null ? s.receita_total - s.inactive_mrr : s.receita_total),
    inactive_mrr: s.inactive_mrr ?? 0,
    churn_rate: s.churn_rate ?? 0,
    avg_churn_score: s.avg_churn_score ?? 0,
  }));

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="glass-card p-6 border-destructive/30 bg-destructive/5 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-destructive shrink-0" />
          <p className="text-sm text-destructive">Dados indisponíveis. Verifique se o servidor está ativo.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">Visão executiva de inteligência de churn</p>
      </div>

      {isLoading && (
        <div className="glass-card p-6 flex items-center justify-center gap-3">
          <div className="h-5 w-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Carregando dados...</p>
        </div>
      )}

      {/* KPI Cards */}
      {!isLoading && kpis.length > 0 && (
        <section className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {kpis.map((kpi, i) => (
            <MetricTooltip key={kpi.label} tip={kpi.tip}>
              <div className="kpi-card animate-fade-in cursor-default" style={{ animationDelay: `${i * 40}ms` }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{kpi.label}</span>
                  <kpi.icon className={`h-3.5 w-3.5 ${kpi.color}`} />
                </div>
                <p className="text-lg font-bold tracking-tight">{kpi.value}</p>
                {"sub1" in kpi && kpi.sub1 && (
                  <div className="mt-1 space-y-0.5">
                    <p className="text-[10px] text-muted-foreground">{kpi.sub1}</p>
                    <p className="text-[10px] text-muted-foreground">{kpi.sub2}</p>
                  </div>
                )}
              </div>
            </MetricTooltip>
          ))}
        </section>
      )}

      {/* Charts Row */}
      {!isLoading && (
        <section className="grid gap-4 lg:grid-cols-3">
          {/* Risk Distribution */}
          {riskPieData.length > 0 && (
            <MetricTooltip tip="Distribuição de contas por nível de risco de churn.">
              <Card className="cursor-default">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1">
                    Distribuição de Risco
                    <Info className="h-3.5 w-3.5 text-muted-foreground" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" nameKey="name" paddingAngle={3}>
                        {riskPieData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Legend wrapperStyle={{ fontSize: "11px" }} />
                      <RechartsTooltip contentStyle={{ borderRadius: "8px", border: "1px solid hsl(220,13%,91%)", fontSize: "11px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </MetricTooltip>
          )}

          {/* Pareto ABC */}
          {pareto.length > 0 && (
            <MetricTooltip tip="Contas agrupadas por concentração de receita. Segmento A detém a maior parte do MRR.">
              <Card className="cursor-default">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1">
                    Curva ABC (Pareto)
                    <Info className="h-3.5 w-3.5 text-muted-foreground" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={pareto} barCategoryGap="30%">
                      <XAxis dataKey="segment" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                      <RechartsTooltip
                        contentStyle={{ borderRadius: "8px", border: "1px solid hsl(220,13%,91%)", fontSize: "11px" }}
                        formatter={(value: number) => [formatCurrency(value), "MRR Total"]}
                      />
                      <Bar dataKey="total_mrr" name="MRR Total" radius={[6, 6, 0, 0]}>
                        {pareto.map((entry: any) => (
                          <Cell key={entry.segment} fill={SEGMENT_COLORS[entry.segment] || SEGMENT_COLORS.C} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-2 flex gap-3 text-[10px] text-muted-foreground">
                    {pareto.map((p: any) => (
                      <span key={p.segment}>Seg. {p.segment}: {formatPercent(p.revenue_share)} receita</span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </MetricTooltip>
          )}

          {/* Revenue at Risk Summary */}
          {cards && cards.active_mrr > 0 && (
            <MetricTooltip tip="Percentual da receita ativa atualmente exposta a contas classificadas como alto risco.">
              <Card className="cursor-default">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1">
                    Receita em Risco
                    <Info className="h-3.5 w-3.5 text-muted-foreground" />
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center h-[220px]">
                  <p className="text-4xl font-bold text-destructive">{formatPercent(cards.risk_mrr / cards.active_mrr)}</p>
                  <p className="text-xs text-muted-foreground mt-2">da receita ativa sob risco</p>
                  <div className="mt-4 text-center text-xs text-muted-foreground space-y-1">
                    <p>Em risco: {formatCurrency(cards.risk_mrr)}</p>
                    <p>MRR Ativo Total: {formatCurrency(cards.active_mrr)}</p>
                  </div>
                </CardContent>
              </Card>
            </MetricTooltip>
          )}
        </section>
      )}

      {/* Revenue Segmentation */}
      {!isLoading && segChartData.length > 0 && (
        <section className="space-y-3">
          <MetricTooltip tip="Mostra a distribuição da receita por faixa, separando contas ativas e inativas, o churn histórico e o churn preditivo por segmento.">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider cursor-default inline-flex items-center gap-1">
              Segmentação de Receita e Exposição ao Churn
              <Info className="h-3.5 w-3.5" />
            </h2>
          </MetricTooltip>
          <Card>
            <CardContent className="pt-4">
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={segChartData} barGap={0}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="faixa_mrr" tick={{ fontSize: 10 }} stroke="hsl(220, 9%, 46%)" />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} domain={[0, 1]} />
                  <RechartsTooltip
                    contentStyle={{ borderRadius: "8px", border: "1px solid hsl(220,13%,91%)", fontSize: "11px" }}
                    formatter={(value: number, name: string) => {
                      if (name === "Churn Histórico" || name === "Churn Preditivo") return [formatPercent(value), name];
                      return [formatCurrency(value), name];
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Bar yAxisId="left" dataKey="active_mrr" name="MRR Ativo" stackId="mrr" fill="hsl(172, 66%, 50%)" radius={[0, 0, 0, 0]} />
                  <Bar yAxisId="left" dataKey="inactive_mrr" name="MRR Inativo" stackId="mrr" fill="hsl(0, 84%, 60%)" radius={[4, 4, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="churn_rate" name="Churn Histórico" stroke="hsl(38, 92%, 50%)" strokeWidth={2} dot={{ r: 3 }} />
                  <Line yAxisId="right" type="monotone" dataKey="avg_churn_score" name="Churn Preditivo" stroke="hsl(280, 70%, 55%)" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </section>
      )}

      {/* SHAP / Churn Drivers */}
      <section className="space-y-3">
        <MetricTooltip tip="Mostra quais variáveis mais influenciam o modelo preditivo de churn. Quanto maior o impacto, maior a contribuição daquela variável para o risco de churn.">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider cursor-default inline-flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            Drivers do Churn (SHAP)
            <Info className="h-3.5 w-3.5" />
          </h2>
        </MetricTooltip>
        <p className="text-xs text-muted-foreground -mt-1">Impacto médio das variáveis no modelo preditivo</p>
        {shapLoading && (
          <Card>
            <CardContent className="pt-4 space-y-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-5 w-full" />
              ))}
            </CardContent>
          </Card>
        )}
        {!shapLoading && shapData.length === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              Dados indisponíveis
            </CardContent>
          </Card>
        )}
        {shapData.length > 0 && (
          <Card>
            <CardContent className="pt-4">
              <ResponsiveContainer width="100%" height={Math.max(200, shapData.slice(0, 10).length * 36)}>
                <BarChart
                  data={shapData.slice(0, 10).map((f: any) => ({
                    feature: f.feature ?? f.name,
                    importance: f.importance ?? f.value ?? 0,
                  }))}
                  layout="vertical"
                  barCategoryGap="20%"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} label={{ value: "Impacto", position: "insideBottom", offset: -5, fontSize: 11 }} />
                  <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={140} />
                  <RechartsTooltip
                    contentStyle={{ borderRadius: "8px", border: "1px solid hsl(220,13%,91%)", fontSize: "11px" }}
                    formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, "Impacto médio"]}
                  />
                  <Bar dataKey="importance" name="Impacto médio" fill="hsl(172, 66%, 50%)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
