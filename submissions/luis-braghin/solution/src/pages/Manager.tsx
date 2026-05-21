import { useMemo, useState } from "react";
import { useDeals, useAgents } from "@/hooks/useG4Data";
import { KPICard } from "@/components/dashboard/KPICard";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DollarSign, Users, AlertTriangle, TrendingUp, Target, Crown } from "lucide-react";
import { formatUSD, formatPercent } from "@/lib/formatters";
import { DeadDealsTable } from "@/components/manager/DeadDealsTable";
import { ManagerComparisonTab } from "@/components/manager/ManagerComparisonTab";
import { TeamPerformanceTab } from "@/components/manager/TeamPerformanceTab";
import type { ManagerStats } from "@/components/manager/types";


export default function Manager() {
  const { data: deals = [] } = useDeals();
  const { data: agents = [] } = useAgents();
  
  
  const [filterManager, setFilterManager] = useState("all");

  const managers = useMemo(() => [...new Set(agents.map(a => a.manager))].sort(), [agents]);

  const filteredDeals = useMemo(() =>
    filterManager === "all" ? deals : deals.filter(d => d.manager === filterManager),
    [deals, filterManager]
  );
  const filteredAgents = useMemo(() =>
    filterManager === "all" ? agents : agents.filter(a => a.manager === filterManager),
    [agents, filterManager]
  );

  const totalPipeline = useMemo(() => filteredDeals.reduce((s, d) => s + d.salesPrice, 0), [filteredDeals]);
  const totalEV = useMemo(() => filteredDeals.reduce((s, d) => s + d.expectedValue, 0), [filteredDeals]);
  const avgWinRate = useMemo(() => filteredAgents.length > 0 ? filteredAgents.reduce((s, a) => s + a.winRate, 0) / filteredAgents.length : 0, [filteredAgents]);
  const deadDeals = useMemo(() => filteredDeals.filter(d => d.daysInPipeline > 130), [filteredDeals]);

  const agentChartData = useMemo(() =>
    filteredAgents
      .sort((a, b) => b.winRate - a.winRate)
      .slice(0, 15)
      .map(a => ({
        name: a.name.split(" ")[0],
        winRate: +(a.winRate * 100).toFixed(1),
        deals: a.activeDeals,
      })),
    [filteredAgents]
  );

  const managerStats = useMemo((): ManagerStats[] => {
    const managersToCalc = filterManager === "all" ? managers : managers.filter(m => m === filterManager);
    return managersToCalc.map(mgr => {
      const mAgents = agents.filter(a => a.manager === mgr);
      const mDeals = deals.filter(d => d.manager === mgr);
      const pipeline = mDeals.reduce((s, d) => s + d.salesPrice, 0);
      const ev = mDeals.reduce((s, d) => s + d.expectedValue, 0);
      const avgWR = mAgents.length > 0 ? mAgents.reduce((s, a) => s + a.winRate, 0) / mAgents.length : 0;
      const avgScore = mDeals.length > 0 ? mDeals.reduce((s, d) => s + d.score, 0) / mDeals.length : 0;
      const hotWarm = mDeals.filter(d => d.category === "HOT" || d.category === "WARM").length;
      const coldDead = mDeals.filter(d => d.category === "COLD" || d.category === "DEAD").length;
      const over130d = mDeals.filter(d => d.daysInPipeline > 130).length;
      const avgDays = mDeals.length > 0 ? mDeals.reduce((s, d) => s + d.daysInPipeline, 0) / mDeals.length : 0;
      const totalRev = mAgents.reduce((s, a) => s + a.totalRevenue, 0);
      const engaging = mDeals.filter(d => d.stage === "Engaging").length;

      const prodMap: Record<string, { won: number; total: number }> = {};
      mAgents.forEach(a => {
        Object.entries(a.productWinRates).forEach(([p, v]) => {
          if (!prodMap[p]) prodMap[p] = { won: 0, total: 0 };
          prodMap[p].won += v.won;
          prodMap[p].total += v.total;
        });
      });
      const bestProd = Object.entries(prodMap)
        .filter(([, v]) => v.total >= 10)
        .sort(([, a], [, b]) => (b.won / b.total) - (a.won / a.total))[0];

      return {
        name: mgr,
        agents: mAgents.length,
        totalDeals: mDeals.length,
        pipeline,
        ev,
        avgWinRate: avgWR,
        avgScore,
        hotWarm,
        coldDead,
        over130d,
        avgDaysInPipeline: avgDays,
        totalRevenue: totalRev,
        evPerAgent: mAgents.length > 0 ? ev / mAgents.length : 0,
        pipelinePerAgent: mAgents.length > 0 ? pipeline / mAgents.length : 0,
        pctEngaging: mDeals.length > 0 ? engaging / mDeals.length : 0,
        topProduct: bestProd ? bestProd[0] : "—",
        topProductWR: bestProd ? bestProd[1].won / bestProd[1].total : 0,
      };
    });
  }, [managers, agents, deals, filterManager]);

  const categoryBarData = useMemo(() =>
    managerStats.map(m => {
      const mDeals = deals.filter(d => d.manager === m.name);
      return {
        name: m.name.split(" ")[0],
        HOT: mDeals.filter(d => d.category === "HOT").length,
        WARM: mDeals.filter(d => d.category === "WARM").length,
        COOL: mDeals.filter(d => d.category === "COOL").length,
        COLD: mDeals.filter(d => d.category === "COLD").length,
        DEAD: mDeals.filter(d => d.category === "DEAD").length,
      };
    }),
    [managerStats, deals]
  );

  const managerInsights = useMemo(() => {
    if (managerStats.length < 2) return [`${managerStats[0]?.name ?? "Manager"}: Win Rate ${formatPercent(managerStats[0]?.avgWinRate ?? 0)}, Pipeline ${formatUSD(managerStats[0]?.pipeline ?? 0)}, ${managerStats[0]?.totalDeals ?? 0} deals, Score médio ${(managerStats[0]?.avgScore ?? 0).toFixed(0)}.`];
    const msgs: string[] = [];
    const bestWR = [...managerStats].sort((a, b) => b.avgWinRate - a.avgWinRate)[0];
    const worstWR = [...managerStats].sort((a, b) => a.avgWinRate - b.avgWinRate)[0];
    msgs.push(`🏆 Maior win rate: ${bestWR.name} (${formatPercent(bestWR.avgWinRate)}) — ${((bestWR.avgWinRate - worstWR.avgWinRate) * 100).toFixed(1)}pp acima de ${worstWR.name} (${formatPercent(worstWR.avgWinRate)}).`);
    const bestEVPerAgent = [...managerStats].sort((a, b) => b.evPerAgent - a.evPerAgent)[0];
    msgs.push(`💰 Maior EV por vendedor: ${bestEVPerAgent.name} (${formatUSD(bestEVPerAgent.evPerAgent)}/vendedor com ${bestEVPerAgent.agents} vendedores).`);
    const mostInflated = [...managerStats].sort((a, b) => b.over130d - a.over130d)[0];
    if (mostInflated.over130d > 0) {
      const pct = mostInflated.totalDeals > 0 ? (mostInflated.over130d / mostInflated.totalDeals * 100).toFixed(0) : "0";
      msgs.push(`🧹 Pipeline mais envelhecido: ${mostInflated.name} com ${mostInflated.over130d} deals >130d (${pct}% do pipeline).`);
    }
    const bestScore = [...managerStats].sort((a, b) => b.avgScore - a.avgScore)[0];
    const worstScore = [...managerStats].sort((a, b) => a.avgScore - b.avgScore)[0];
    msgs.push(`📊 Score médio: ${bestScore.name} lidera com ${bestScore.avgScore.toFixed(0)} vs ${worstScore.name} com ${worstScore.avgScore.toFixed(0)} (diferença de ${(bestScore.avgScore - worstScore.avgScore).toFixed(0)} pontos).`);
    return msgs;
  }, [managerStats]);

  const affinityInsights = useMemo(() => {
    const insights: string[] = [];
    filteredAgents.forEach(agent => {
      const best = Object.entries(agent.productWinRates)
        .filter(([, v]) => v.total >= 5)
        .sort(([, a], [, b]) => b.winRate - a.winRate);
      if (best.length > 0) {
        const [prod, stats] = best[0];
        if (stats.winRate >= 0.75) {
          insights.push(`${agent.name} tem ${(stats.winRate * 100).toFixed(0)}% de win rate com ${prod} (${stats.won}/${stats.total} deals).`);
        }
      }
    });
    return insights;
  }, [filteredAgents]);

  const lowAffinityInsights = useMemo(() => {
    const insights: string[] = [];
    filteredAgents.forEach(agent => {
      const worst = Object.entries(agent.productWinRates)
        .filter(([, v]) => v.total >= 5)
        .sort(([, a], [, b]) => a.winRate - b.winRate);
      if (worst.length > 0) {
        const [prod, stats] = worst[0];
        if (stats.winRate <= 0.50) {
          insights.push(`${agent.name} tem apenas ${(stats.winRate * 100).toFixed(0)}% de win rate com ${prod} (${stats.won}/${stats.total} deals).`);
        }
      }
    });
    return insights.sort((a, b) => {
      const pctA = parseInt(a.match(/(\d+)%/)?.[1] || "100");
      const pctB = parseInt(b.match(/(\d+)%/)?.[1] || "100");
      return pctA - pctB;
    }).slice(0, 20);
  }, [filteredAgents]);

  const redistributionSuggestions = useMemo(() => {
    const msgs: string[] = [];
    if (filteredAgents.length < 2) return msgs;
    const sorted = [...filteredAgents].sort((a, b) => b.activeDeals - a.activeDeals);
    sorted.slice(0, 5).forEach(agent => {
      const extra = agent.winRate < 0.56 ? ` — win rate baixa (${(agent.winRate * 100).toFixed(1)}%), revise alocação` : "";
      msgs.push(`⬆️ ${agent.name} com ${agent.activeDeals} deals ativos${extra}. Considere redistribuir.`);
    });
    sorted.slice(-5).reverse().forEach(agent => {
      const highWR = agent.winRate >= 0.65;
      msgs.push(`⬇️ ${agent.name} com apenas ${agent.activeDeals} deals ativos${highWR ? ` e win rate alta (${(agent.winRate * 100).toFixed(0)}%) — pode absorver mais deals` : " — tem capacidade disponível"}.`);
    });
    return msgs;
  }, [filteredAgents]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Visão Manager</h1>
          <p className="text-muted-foreground">Pipeline do time, comparativo de vendedores e alertas</p>
        </div>
        <Select value={filterManager} onValueChange={setFilterManager}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Todos os Managers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os Managers</SelectItem>
            {managers.map(m => (
              <SelectItem key={m} value={m}>{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard title="Pipeline Total" value={formatUSD(totalPipeline)} icon={DollarSign} />
        <KPICard title="Expected Value" value={formatUSD(totalEV)} icon={Target} variant="success" />
        <KPICard title="Vendedores" value={String(filteredAgents.length)} icon={Users} />
        <KPICard title="Win Rate Média" value={formatPercent(avgWinRate)} icon={TrendingUp} variant="success" />
        <KPICard title="Envelhecidos (>130d)" value={String(deadDeals.length)} icon={AlertTriangle} variant="destructive" />
      </div>

      <Tabs defaultValue="managers">
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="managers">
            <Crown className="h-3.5 w-3.5 mr-1" />
            Comparativo Managers
          </TabsTrigger>
          <TabsTrigger value="team">Performance do Time</TabsTrigger>
          <TabsTrigger value="alerts">Alertas</TabsTrigger>
          <TabsTrigger value="affinity">Afinidade Produto</TabsTrigger>
          <TabsTrigger value="redistribution">Distribuição Ótima</TabsTrigger>
        </TabsList>

        <TabsContent value="managers" className="space-y-6">
          <ManagerComparisonTab
            managerStats={managerStats}
            managerInsights={managerInsights}
            categoryBarData={categoryBarData}
          />
        </TabsContent>

        <TabsContent value="team" className="space-y-6">
          <TeamPerformanceTab agentChartData={agentChartData} filteredAgents={filteredAgents} />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <DeadDealsTable deals={deadDeals} />
        </TabsContent>

        <TabsContent value="affinity" className="space-y-6">
          <InsightsPanel title="🔝 Maiores Afinidades Vendedor-Produto" insights={affinityInsights.length > 0 ? affinityInsights : ["Nenhuma afinidade forte detectada."]} />
          <InsightsPanel title="⚠️ Menores Afinidades Vendedor-Produto" insights={lowAffinityInsights.length > 0 ? lowAffinityInsights : ["Nenhuma afinidade baixa detectada."]} />
        </TabsContent>

        <TabsContent value="redistribution">
          <InsightsPanel title="Sugestões de Redistribuição" insights={redistributionSuggestions.length > 0 ? redistributionSuggestions : ["Pipeline equilibrado. Sem sugestões no momento."]} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
