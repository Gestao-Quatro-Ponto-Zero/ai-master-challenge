import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useDeals, useAgents, useAnalytics } from "@/hooks/useG4Data";
import { KPICard } from "@/components/dashboard/KPICard";
import { DealCard } from "@/components/dashboard/DealCard";
import { LeaderboardTable } from "@/components/dashboard/LeaderboardTable";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DollarSign, Target, TrendingUp, AlertTriangle, BarChart3, Layers } from "lucide-react";
import { formatUSD, formatCompact } from "@/lib/formatters";

export default function Index() {
  const { data: deals = [] } = useDeals();
  const { data: agents = [] } = useAgents();
  const { data: analytics } = useAnalytics();
  const [searchParams, setSearchParams] = useSearchParams();

  const filterManager = searchParams.get("manager") || "all";
  const filterAgent = searchParams.get("agent") || "all";
  const filterProduct = searchParams.get("product") || "all";
  const filterStage = searchParams.get("stage") || "all";
  const filterCategory = searchParams.get("category") || "all";
  const [sortBy, setSortBy] = useState<"score" | "expectedValue">("score");
  const [currentPage, setCurrentPage] = useState(1);

  const uniqueManagers = useMemo(() => [...new Set(deals.map(d => d.manager))].sort(), [deals]);
  const uniqueAgents = useMemo(() => {
    const base = filterManager !== "all" ? deals.filter(d => d.manager === filterManager) : deals;
    return [...new Set(base.map(d => d.agent))].sort();
  }, [deals, filterManager]);
  const uniqueProducts = useMemo(() => {
    let base = deals;
    if (filterManager !== "all") base = base.filter(d => d.manager === filterManager);
    if (filterAgent !== "all") base = base.filter(d => d.agent === filterAgent);
    return [...new Set(base.map(d => d.product))].sort();
  }, [deals, filterManager, filterAgent]);

  const filtered = useMemo(() => {
    let result = deals;
    if (filterManager !== "all") result = result.filter(d => d.manager === filterManager);
    if (filterAgent !== "all") result = result.filter(d => d.agent === filterAgent);
    if (filterProduct !== "all") result = result.filter(d => d.product === filterProduct);
    if (filterStage !== "all") result = result.filter(d => d.stage === filterStage);
    if (filterCategory !== "all") result = result.filter(d => d.category === filterCategory);
    return [...result].sort((a, b) =>
      sortBy === "score" ? b.score - a.score : b.expectedValue - a.expectedValue
    );
  }, [deals, filterManager, filterAgent, filterProduct, filterStage, filterCategory, sortBy]);

  const totalPipeline = useMemo(() => filtered.reduce((s, d) => s + d.salesPrice, 0), [filtered]);
  const totalEV = useMemo(() => filtered.reduce((s, d) => s + d.expectedValue, 0), [filtered]);
  const warmCount = useMemo(() => filtered.filter(d => d.category === "WARM").length, [filtered]);
  const coolCount = useMemo(() => filtered.filter(d => d.category === "COOL").length, [filtered]);
  const coldCount = useMemo(() => filtered.filter(d => d.category === "COLD").length, [filtered]);
  const over90Count = useMemo(() => filtered.filter(d => d.daysInPipeline > 90).length, [filtered]);

  const setFilter = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value === "all") newParams.delete(key);
    else newParams.set(key, value);
    // Reset dependent filters when parent changes
    if (key === "manager") {
      newParams.delete("agent");
      newParams.delete("product");
    } else if (key === "agent") {
      newParams.delete("product");
    }
    setSearchParams(newParams);
    setCurrentPage(1);
  };

  const insights = useMemo(() => {
    const msgs: string[] = [];
    if (analytics) {
      msgs.push(`Win rate geral da equipe: ${(analytics.overallWinRate * 100).toFixed(1)}%. Tempo mediano de fechamento: ${analytics.medianCloseTime} dias.`);
      const pctOver130 = (analytics.pipelineHealth.over130Days / analytics.pipelineHealth.totalActive * 100).toFixed(0);
      msgs.push(`${analytics.pipelineHealth.over130Days} deals (${pctOver130}% do pipeline) estão há mais de 130 dias. Pipeline envelhecido.`);
      msgs.push(`Sazonalidade: fim de trimestre tem win rate de ${(analytics.seasonality.pushMonths.avgWinRate * 100).toFixed(1)}% vs ${(analytics.seasonality.nonPushMonths.avgWinRate * 100).toFixed(1)}% nos demais meses.`);
    }
    const quickWins = filtered.filter(d => d.daysInPipeline >= 14 && d.daysInPipeline <= 30 && d.score >= 60);
    if (quickWins.length > 0) {
      msgs.push(`${quickWins.length} deals na janela de ouro (14-30 dias, score ≥60). Priorize ação imediata.`);
    }
    return msgs;
  }, [analytics, filtered]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard de Vendas</h1>
        <p className="text-muted-foreground">Visão geral do pipeline e deals ranqueados por score</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard title="Pipeline Total" value={formatUSD(totalPipeline)} icon={DollarSign} />
        <KPICard title="Expected Value" value={formatUSD(totalEV)} icon={Target} variant="success" />
        <KPICard title="WARM" value={String(warmCount)} subtitle="Score 60-79" icon={TrendingUp} variant="warning" />
        <KPICard title="COOL" value={String(coolCount)} subtitle="Score 40-59" icon={BarChart3} />
        <KPICard title="COLD" value={String(coldCount)} subtitle="Score < 40" icon={AlertTriangle} variant="destructive" />
        <KPICard title="Deals Ativos" value={String(filtered.length)} subtitle={`${over90Count} com >90d no pipeline`} icon={Layers} />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-3 items-end">
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Gerente</label>
              <Select value={filterManager} onValueChange={v => setFilter("manager", v)}>
                <SelectTrigger className="w-[180px]"><SelectValue placeholder="Gerente" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os gerentes</SelectItem>
                  {uniqueManagers.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Vendedor</label>
              <Select value={filterAgent} onValueChange={v => setFilter("agent", v)}>
                <SelectTrigger className="w-[180px]"><SelectValue placeholder="Vendedor" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os vendedores</SelectItem>
                  {uniqueAgents.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Produto</label>
              <Select value={filterProduct} onValueChange={v => setFilter("product", v)}>
                <SelectTrigger className="w-[160px]"><SelectValue placeholder="Produto" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os produtos</SelectItem>
                  {uniqueProducts.map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Stage</label>
              <Select value={filterStage} onValueChange={v => setFilter("stage", v)}>
                <SelectTrigger className="w-[140px]"><SelectValue placeholder="Stage" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="Engaging">Engaging</SelectItem>
                  <SelectItem value="Prospecting">Prospecting</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Categoria</label>
              <Select value={filterCategory} onValueChange={v => setFilter("category", v)}>
                <SelectTrigger className="w-[140px]"><SelectValue placeholder="Categoria" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  <SelectItem value="WARM">WARM</SelectItem>
                  <SelectItem value="COOL">COOL</SelectItem>
                  <SelectItem value="COLD">COLD</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Ordenar por</label>
              <Select value={sortBy} onValueChange={v => setSortBy(v as "score" | "expectedValue")}>
                <SelectTrigger className="w-[160px]"><SelectValue placeholder="Ordenar por" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="score">Score (maior)</SelectItem>
                  <SelectItem value="expectedValue">Expected Value</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Deals grid */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Deals ({filtered.length})</h2>
          </div>
          {(() => {
            const ITEMS_PER_PAGE = 20;
            const page = currentPage;
            const setPage = setCurrentPage;
            const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
            const paged = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);
            return (
              <>
                <div className="space-y-3">
                  {paged.map(deal => (
                    <DealCard key={deal.id} deal={{
                      ...deal,
                      aiSummary: deal.aiSummary
                        .replace(/[Ss]eu hist[oó]rico/g, (m) => m[0] === 'S' ? 'O histórico do vendedor' : 'o histórico do vendedor')
                        .replace('Mantenha ritmo', 'Manter ritmo')
                        .replace('Considere pedir apoio de colega', 'Considere direcionar apoio de colega')
                        .replace('Libere foco', 'Liberar foco')
                        .replace('Investigue bloqueios ou considere encerrar', 'Investigar bloqueios ou considerar encerramento')
                        .replace('Avalie o fit', 'Avaliar o fit')
                        .replace('Priorize', 'Priorizar')
                    }} />
                  ))}
                </div>
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-1 pt-4">
                    <button
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                      className="px-3 py-1.5 text-sm rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      ←
                    </button>
                    {(() => {
                      const maxVisible = 7;
                      const half = Math.floor(maxVisible / 2);
                      let start = Math.max(1, page - half);
                      let end = Math.min(totalPages, start + maxVisible - 1);
                      if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);
                      const pages: (number | "...")[] = [];
                      if (start > 1) { pages.push(1); if (start > 2) pages.push("..."); }
                      for (let i = start; i <= end; i++) pages.push(i);
                      if (end < totalPages) { if (end < totalPages - 1) pages.push("..."); pages.push(totalPages); }
                      return pages.map((p, idx) =>
                        p === "..." ? (
                          <span key={`ellipsis-${idx}`} className="px-2 py-1.5 text-sm text-muted-foreground">…</span>
                        ) : (
                          <button
                            key={p}
                            onClick={() => setPage(p)}
                            className={`px-3 py-1.5 text-sm rounded-md border ${
                              p === page
                                ? "bg-primary text-primary-foreground border-primary"
                                : "border-border text-muted-foreground hover:bg-accent"
                            }`}
                          >
                            {p}
                          </button>
                        )
                      );
                    })()}
                    <button
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1.5 text-sm rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      →
                    </button>
                  </div>
                )}
                <p className="text-center text-sm text-muted-foreground">
                  Página {page} de {totalPages} — {filtered.length} deals
                </p>
              </>
            );
          })()}
        </div>

        {/* Sidebar: Insights + Leaderboard */}
        <div className="space-y-6">
          <InsightsPanel insights={insights} />
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Leaderboard — Top Vendedores</CardTitle>
            </CardHeader>
            <CardContent>
              <LeaderboardTable agents={agents} limit={5} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
