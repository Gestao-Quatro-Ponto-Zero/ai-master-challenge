import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchRecommendations, approveRecommendation } from "@/lib/api";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, CheckCircle, User, Users2, Zap, Info } from "lucide-react";
import { toast } from "sonner";

const priorityVariant = (p: string) => {
  switch (p?.toLowerCase()) {
    case "high": return "destructive" as const;
    case "medium": return "secondary" as const;
    default: return "outline" as const;
  }
};

const Recommendations = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["recommendations"],
    queryFn: fetchRecommendations,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const approveMutation = useMutation({
    mutationFn: (recId: string) => approveRecommendation(recId),
    onSuccess: () => {
      toast.success("Recomendação aprovada e movida para o Kanban.");
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["kanban-projects"] });
      queryClient.invalidateQueries({ queryKey: ["open-recommendations"] });
    },
    onError: () => {
      toast.error("Falha ao aprovar recomendação.");
    },
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

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <MetricTooltip tip="Iniciativas geradas por IA para reduzir churn ou proteger receita.">
        <div className="cursor-default">
          <h1 className="text-2xl font-bold tracking-tight">Recomendações</h1>
          <p className="text-muted-foreground text-sm mt-1">Iniciativas geradas por IA para reduzir churn</p>
        </div>
      </MetricTooltip>

      {items.length === 0 && (
        <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
          Nenhuma recomendação em aberto.
        </div>
      )}

      <div className="space-y-4">
        {items.map((rec: any) => (
          <Card key={rec.recommendation_id} className="transition-shadow hover:shadow-md">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[10px] font-mono text-muted-foreground mb-1">{rec.recommendation_id}</p>
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary shrink-0" />
                    {rec.title}
                  </CardTitle>
                </div>
                <Badge variant={priorityVariant(rec.priority)} className="shrink-0 text-xs">
                  {rec.priority}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground leading-relaxed">{rec.description}</p>

              <div className="grid gap-2 grid-cols-2 text-xs text-muted-foreground">
                {rec.impact_area && (
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    <span>Área: {rec.impact_area}</span>
                  </div>
                )}
                {rec.expected_impact && (
                  <div className="flex items-center gap-1">
                    <Info className="h-3 w-3" />
                    <span>Impacto: {rec.expected_impact}</span>
                  </div>
                )}
                {rec.suggested_owner && (
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    <span>Owner: {rec.suggested_owner}</span>
                  </div>
                )}
                {rec.suggested_squad && (
                  <div className="flex items-center gap-1">
                    <Users2 className="h-3 w-3" />
                    <span>Squad: {rec.suggested_squad}</span>
                  </div>
                )}
              </div>

              {rec.evidence && (
                <div className="text-xs text-muted-foreground border-l-2 border-border pl-2 space-y-0.5">
                  <p className="font-medium text-foreground">Evidência:</p>
                  <p className="italic">{rec.evidence}</p>
                </div>
              )}

              <Button
                variant="default"
                size="sm"
                className="gap-1.5 text-xs"
                disabled={approveMutation.isPending}
                onClick={() => approveMutation.mutate(rec.recommendation_id)}
              >
                {approveMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCircle className="h-3.5 w-3.5" />
                )}
                Aprovar para Kanban
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Recommendations;
