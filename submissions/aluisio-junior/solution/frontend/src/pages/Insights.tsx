import { useQuery } from "@tanstack/react-query";
import { fetchInsights } from "@/lib/api";
import { formatPercent } from "@/lib/formatters";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Lightbulb, AlertCircle, TrendingDown, Info, Zap, BarChart3 } from "lucide-react";

const priorityVariant = (p: string) => {
  switch (p?.toLowerCase()) {
    case "high": case "alta": return "destructive" as const;
    case "medium": case "média": return "secondary" as const;
    default: return "outline" as const;
  }
};

const severityIcon = (s: string) => {
  switch (s?.toLowerCase()) {
    case "high": case "alta": return <AlertCircle className="h-4 w-4 text-destructive" />;
    case "medium": case "média": return <TrendingDown className="h-4 w-4 text-[hsl(var(--chart-warning))]" />;
    default: return <Info className="h-4 w-4 text-primary" />;
  }
};

const Insights = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["insights"],
    queryFn: fetchInsights,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-destructive text-sm">
        Dados indisponíveis. Verifique se o servidor está ativo.
      </div>
    );
  }

  const headlines = data?.headlines ?? [];
  const rootCauses = data?.root_causes ?? [];
  const recommendedActions = data?.recommended_actions ?? [];
  const featureImportance = data?.feature_importance ?? [];
  const temporal = data?.temporal_kpis;

  return (
    <div className="space-y-6">
      <MetricTooltip tip="AI-generated executive interpretation of churn risk, root causes, and next actions.">
        <div className="cursor-default">
          <h1 className="text-2xl font-bold tracking-tight">Insights</h1>
          <p className="text-muted-foreground text-sm mt-1">Interpretação executiva de churn gerada por IA</p>
        </div>
      </MetricTooltip>

      {/* Executive Summary */}
      {data?.executive_summary && (
        <Card className="border-l-4 border-l-primary">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <Lightbulb className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <p className="text-sm leading-relaxed">{data.executive_summary}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Headlines */}
      {headlines.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Destaques</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {headlines.map((h: any, i: number) => (
              <Card key={i} className="transition-shadow hover:shadow-md">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2">
                      <Zap className="h-4 w-4 text-primary shrink-0" />
                      {h.title}
                    </CardTitle>
                    <Badge variant={priorityVariant(h.priority)} className="text-xs shrink-0">{h.priority}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{h.message}</p>
                  {h.metric && <p className="text-xs text-muted-foreground mt-1 italic">Métrica: {h.metric}</p>}
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Root Causes */}
      {rootCauses.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Causas Raiz</h2>
          <div className="space-y-2">
            {rootCauses.map((rc: any, i: number) => (
              <div key={i} className="glass-card p-4 flex items-start gap-3">
                {severityIcon(rc.severity)}
                <div>
                  <p className="text-sm font-medium">{rc.driver}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{rc.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recommended Actions */}
      {recommendedActions.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Ações Recomendadas</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {recommendedActions.map((a: any, i: number) => (
              <Card key={i}>
                <CardContent className="py-4">
                  <p className="text-sm font-medium">{a.title ?? a.action ?? a}</p>
                  {a.description && <p className="text-xs text-muted-foreground mt-1">{a.description}</p>}
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Feature Importance */}
      {featureImportance.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            Importância das Features
          </h2>
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-2">
                {featureImportance.map((f: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs font-medium w-32 truncate">{f.feature ?? f.name}</span>
                    <div className="flex-1 bg-muted rounded-full h-2">
                      <div
                        className="bg-primary rounded-full h-2 transition-all"
                        style={{ width: `${(f.importance ?? f.value ?? 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-12 text-right">
                      {((f.importance ?? f.value ?? 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>
      )}

      {/* Temporal KPIs */}
      {temporal && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">KPIs Temporais</h2>
          <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
            {[
              { label: "Churn Histórico", value: formatPercent(temporal.historical_churn_rate) },
              { label: "Churn 30d", value: formatPercent(temporal.period_churn_30d) },
              { label: "Churn 90d", value: formatPercent(temporal.period_churn_90d) },
              { label: "Churn Receita 30d", value: formatPercent(temporal.revenue_churn_30d) },
            ].map((kpi) => (
              <div key={kpi.label} className="kpi-card">
                <span className="text-[10px] font-medium text-muted-foreground uppercase">{kpi.label}</span>
                <p className="text-lg font-bold mt-1">{kpi.value}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default Insights;
