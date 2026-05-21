import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useDeals, useEnrichment } from "@/hooks/useG4Data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScoreCircle } from "@/components/dashboard/ScoreCircle";
import { BreakdownChart } from "@/components/dashboard/BreakdownChart";
import { DealCard } from "@/components/dashboard/DealCard";
import { getCategoryBadgeClasses, formatUSD, formatPercent } from "@/lib/formatters";
import { ArrowLeft, Building2, Users, Globe, AlertTriangle, Sparkles, MessageSquare } from "lucide-react";
import { useState, useEffect } from "react";

export default function DealDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: deals = [] } = useDeals();
  const deal = deals.find(d => d.id === id);
  const { data: enrichment } = useEnrichment(deal?.account ?? "");
  const [showAiDetail, setShowAiDetail] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Track the original page the user came from (before any similar deal clicks)
  const [originPath] = useState<string | undefined>(
    () => (location.state as any)?.from
  );

  const goBack = () => {
    if (originPath) {
      navigate(originPath);
    } else {
      navigate(-1);
    }
  };

  if (!deal) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-muted-foreground">Deal não encontrado.</p>
        <button onClick={goBack} className="mt-4 text-primary hover:underline">Voltar</button>
      </div>
    );
  }

  const similarDeals = deals
    .filter(d => d.id !== deal.id && d.product === deal.product && d.sector === deal.sector && d.category !== "DEAD" && Math.abs(d.score - deal.score) <= 25)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={goBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{deal.account}</h1>
          <p className="text-muted-foreground">{deal.product} • {deal.agent} • {deal.stage}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score + Breakdown */}
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex flex-col items-center gap-4">
              <ScoreCircle score={deal.score} category={deal.category} size={96} />
              <Badge variant="outline" className={getCategoryBadgeClasses(deal.category)}>
                {deal.category}
              </Badge>
              <div className="text-center space-y-1">
                <p className="text-sm text-muted-foreground">Expected Value</p>
                <p className="text-xl font-bold text-primary">{formatUSD(deal.expectedValue)}</p>
                <p className="text-xs text-muted-foreground">de {formatUSD(deal.salesPrice)}</p>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Score Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <BreakdownChart breakdown={deal.breakdown} />
            </CardContent>
          </Card>
        </div>

        {/* AI + Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="h-4 w-4 text-primary" />
                Análise IA
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">{deal.aiSummary}</p>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => setShowAiDetail(!showAiDetail)}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                {deal.aiButton}
              </Button>
              {showAiDetail && (
                <div className="rounded-lg bg-muted/50 p-4 text-sm text-muted-foreground space-y-2 animate-fade-in">
                  <p className="font-medium text-foreground">Recomendações:</p>
                  {deal.daysInPipeline > 90 && (
                    <p>⚠️ Este deal está há {deal.daysInPipeline} dias no pipeline. Deals acima de 90 dias tendem a estagnar. Considere uma ação decisiva esta semana.</p>
                  )}
                  {deal.daysInPipeline >= 14 && deal.daysInPipeline <= 30 && (
                    <p>🎯 Janela de ouro! Deals entre 14-30 dias têm win rate de ~72.8%. Priorize este deal agora.</p>
                  )}
                  {deal.breakdown.agentProductAffinity >= 75 && (
                    <p>✅ {deal.agent} tem forte afinidade com {deal.product}. Isso é um diferencial competitivo.</p>
                  )}
                  {deal.breakdown.accountQuality < 50 && (
                    <p>⚠️ Qualidade da conta abaixo da média ({deal.breakdown.accountQuality}/100). Valide o fit antes de investir mais tempo.</p>
                  )}
                  {(deal.breakdown.velocity ?? deal.breakdown.opportunityWindow ?? 100) < 50 && (
                    <p>🐌 Velocidade baixa ({deal.breakdown.velocity ?? deal.breakdown.opportunityWindow}/100). Tente criar urgência com uma proposta com prazo limitado.</p>
                  )}
                  <p>📊 Score geral: {deal.score}/100. Expected value ajustado: {formatUSD(deal.expectedValue)}.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Account Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Building2 className="h-4 w-4" />
                Dados da Conta
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Setor</p>
                  <p className="font-medium capitalize">{deal.sector}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Faturamento Anual</p>
                  <p className="font-medium">{formatUSD(deal.accountRevenue * 1000)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Funcionários</p>
                  <p className="font-medium">{deal.accountEmployees.toLocaleString("pt-BR")}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Região</p>
                  <p className="font-medium">{deal.regionalOffice}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Enrichment Easter Egg */}
          {enrichment && (
            <Card className="border-warning/30">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertTriangle className="h-4 w-4 text-warning" />
                  Enriquecimento — {deal.account}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p className="text-muted-foreground">{enrichment.description}</p>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={
                    enrichment.risk === "ALTO"
                      ? "bg-destructive/10 text-destructive border-destructive/30"
                      : "bg-warning/10 text-warning border-warning/30"
                  }>
                    Risco: {enrichment.risk}
                  </Badge>
                </div>
                <p className="text-muted-foreground">{enrichment.riskDetail}</p>
                {enrichment.news && (
                  <div className="rounded-md bg-muted/50 p-3">
                    <p className="text-xs font-medium text-foreground mb-1">📰 Notícias</p>
                    <p className="text-xs text-muted-foreground">{enrichment.news}</p>
                  </div>
                )}
                {enrichment.contacts.length > 0 && (
                  <div>
                    <p className="font-medium flex items-center gap-1 mb-2"><Users className="h-3 w-3" /> Contatos</p>
                    {enrichment.contacts.map((c, i) => (
                      <p key={i} className="text-muted-foreground">{c.name} — {c.role}</p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Similar Deals */}
          {similarDeals.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-base font-semibold">Deals Similares</h3>
              {similarDeals.map(d => <DealCard key={d.id} deal={d} linkState={{ from: originPath || location.state?.from || "/" }} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
