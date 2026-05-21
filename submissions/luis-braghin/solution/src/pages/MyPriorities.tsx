import { useMemo, useState } from "react";
import { useSearchParams, useLocation } from "react-router-dom";
import { useDeals, useAgents, useClosedDeals } from "@/hooks/useG4Data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Target, MousePointerClick } from "lucide-react";
import { formatUSD } from "@/lib/formatters";
import { AgentProfileCard } from "@/components/priorities/AgentProfileCard";
import { PriorityDealRow } from "@/components/priorities/PriorityDealRow";
import { PipelineCleanupSection } from "@/components/priorities/PipelineCleanupSection";
import { AllDealsTable } from "@/components/priorities/AllDealsTable";

export default function MyPriorities() {
  const { data: deals = [] } = useDeals();
  const { data: agents = [] } = useAgents();
  const { data: closedDeals = [] } = useClosedDeals();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const fromState = { from: location.pathname + location.search };

  const selectedAgent = searchParams.get("agent") || "";

  const uniqueAgents = useMemo(() => [...new Set(deals.map(d => d.agent))].sort(), [deals]);

  const agentData = useMemo(() => {
    if (!selectedAgent) return null;
    return agents.find(a => a.name === selectedAgent) ?? null;
  }, [agents, selectedAgent]);

  const agentDeals = useMemo(() => {
    if (!selectedAgent) return [];
    return deals.filter(d => d.agent === selectedAgent).sort((a, b) => b.score - a.score);
  }, [deals, selectedAgent]);

  const top10Deals = useMemo(() => agentDeals.slice(0, 10), [agentDeals]);
  const top10EV = useMemo(() => top10Deals.reduce((s, d) => s + d.expectedValue, 0), [top10Deals]);

  const cleanupDeals = useMemo(
    () => agentDeals.filter(d => d.daysInPipeline > 130 && d.stage === "Engaging").sort((a, b) => b.score - a.score),
    [agentDeals]
  );

  const accountWonCounts = useMemo(() => {
    const map = new Map<string, number>();
    closedDeals.filter(d => d.stage === "Won" && d.account).forEach(d => {
      map.set(d.account, (map.get(d.account) ?? 0) + 1);
    });
    return map;
  }, [closedDeals]);

  const handleAgentChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value === "") {
      newParams.delete("agent");
    } else {
      newParams.set("agent", value);
    }
    setSearchParams(newParams);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Minhas Prioridades</h1>
        <p className="text-sm text-muted-foreground">Saiba exatamente onde focar hoje</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="max-w-md">
            <label className="text-sm font-medium text-foreground mb-2 block">Quem é você?</label>
            <Select value={selectedAgent} onValueChange={handleAgentChange}>
              <SelectTrigger className="h-12 text-base">
                <SelectValue placeholder="Selecione seu nome" />
              </SelectTrigger>
              <SelectContent>
                {uniqueAgents.map(a => (
                  <SelectItem key={a} value={a}>{a}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {!selectedAgent && (
        <Card>
          <CardContent className="py-16 text-center">
            <Target className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-lg font-medium text-muted-foreground">Selecione seu nome acima para ver suas prioridades da semana</p>
            <p className="text-sm text-muted-foreground mt-1">Você verá seus deals mais importantes, dicas personalizadas e métricas de performance.</p>
          </CardContent>
        </Card>
      )}

      {selectedAgent && agentData && (
        <>
          <AgentProfileCard agent={agentData} deals={agentDeals} />

          <Tabs defaultValue="priorities">
            <TabsList className="w-full justify-start flex-wrap h-auto gap-1 p-1">
              <TabsTrigger value="priorities">
                <Target className="h-4 w-4 mr-1" />Prioridades ({top10Deals.length})
              </TabsTrigger>
              <TabsTrigger value="all-deals">
                Todos os Deals ({agentDeals.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="priorities" className="space-y-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <p className="text-sm">
                      <span className="font-semibold text-foreground">
                        Suas {top10Deals.length} maiores prioridades.
                      </span>
                      {" "}Se focar nestes deals, o expected value é{" "}
                      <span className="font-semibold text-primary">{formatUSD(top10EV)}</span>
                    </p>
                    <span className="inline-flex items-center gap-1.5 text-xs text-primary font-medium bg-primary/10 px-3 py-1.5 rounded-full whitespace-nowrap">
                      <MousePointerClick className="h-3.5 w-3.5" />
                      Clique em um deal para ver a análise completa
                    </span>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2">
                {top10Deals.map(deal => (
                  <PriorityDealRow key={deal.id} deal={deal} agent={agentData} fromState={fromState} accountWonCounts={accountWonCounts} />
                ))}
                {top10Deals.length === 0 && (
                  <Card>
                    <CardContent className="py-8 text-center text-muted-foreground">
                      Nenhum deal encontrado. Confira a aba "Todos os Deals".
                    </CardContent>
                  </Card>
                )}
              </div>

              <PipelineCleanupSection deals={cleanupDeals} fromState={fromState} />
            </TabsContent>

            <TabsContent value="all-deals">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Todos os Deals — {agentDeals.length} deals ativos</CardTitle>
                  <p className="text-sm text-muted-foreground">Lista completa ordenada por score.</p>
                </CardHeader>
                <CardContent>
                  <AllDealsTable deals={agentDeals} fromState={fromState} />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
