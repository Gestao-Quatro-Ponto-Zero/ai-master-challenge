import React, { useMemo, useState } from "react";
import type { Lead, DealStage, ScoreGrade, ActionStatus } from "@/lib/types";
import { useData } from "@/context/DataContext";
import { KanbanCard } from "./KanbanCard";
import { LeadDrawer } from "./LeadDrawer";
import { AnimatePresence } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Info, AlertTriangle, Target, AlertCircle, Star, TrendingDown, CheckCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const STAGES: DealStage[] = ["Prospecting", "Engaging", "Won", "Lost"];

type SortOption = "priority" | "empresa" | "vendedor" | "score";

function sortLeads(leads: Lead[], sort: SortOption): Lead[] {
  return [...leads].sort((a, b) => {
    if (sort === "empresa") return a.account.localeCompare(b.account);
    if (sort === "vendedor") return a.sales_agent.localeCompare(b.sales_agent);
    if (sort === "score") return (b.scoreNumeric ?? -1) - (a.scoreNumeric ?? -1);
    const order = (l: Lead) => {
      if (l.isIncomplete) return 0;
      if (l.scoreGrade === "A") return 1;
      if (l.scoreGrade === "B") return 2;
      if (l.scoreGrade === "C") return 3;
      return 4;
    };
    return order(a) - order(b);
  });
}

type KpiFilter = "all" | "open" | "focusNow" | "incomplete" | "finalized";

function SummaryCard({ label, value, icon, active, onClick }: { label: string; value: number; icon: React.ReactNode; active?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-lg bg-card p-3 shadow-[0_0_0_1px_rgba(0,0,0,.05),0_1px_3px_0_rgba(0,0,0,.03)] flex items-center gap-3 text-left transition-all
        ${active ? "ring-2 ring-primary shadow-md" : "hover:shadow-[0_0_0_1px_rgba(0,0,0,.08),0_3px_6px_0_rgba(0,0,0,.05)]"}
        ${onClick ? "cursor-pointer" : "cursor-default"}`}
    >
      <div className="shrink-0 w-9 h-9 rounded-lg bg-secondary flex items-center justify-center">
        {icon}
      </div>
      <div>
        <p className="text-xl font-bold font-tabular text-foreground leading-none">{value}</p>
        <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
      </div>
    </button>
  );
}

export function KanbanView() {
  const { leads, managers, salesAgents } = useData();
  const [managerFilter, setManagerFilter] = useState("all");
  const [agentFilter, setAgentFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [bucketFilter, setBucketFilter] = useState("all");
  const [incompleteOnly, setIncompleteOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("priority");
  const [kpiFilter, setKpiFilter] = useState<KpiFilter>("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const sectors = useMemo(() => [...new Set(leads.map(l => l.sector).filter(Boolean) as string[])].sort(), [leads]);
  const buckets = useMemo(() => [...new Set(leads.map(l => l.employeeBucket).filter(Boolean) as string[])].sort(), [leads]);

  const filtered = useMemo(() => {
    let f = leads;
    if (managerFilter !== "all") f = f.filter(l => l.manager === managerFilter);
    if (agentFilter !== "all") f = f.filter(l => l.sales_agent === agentFilter);
    if (scoreFilter !== "all") f = f.filter(l => l.scoreGrade === scoreFilter);
    if (actionFilter !== "all") f = f.filter(l => l.actionStatus === actionFilter);
    if (stageFilter !== "all") f = f.filter(l => l.deal_stage === stageFilter);
    if (sectorFilter !== "all") f = f.filter(l => l.sector === sectorFilter);
    if (bucketFilter !== "all") f = f.filter(l => l.employeeBucket === bucketFilter);
    if (incompleteOnly) f = f.filter(l => l.isIncomplete);
    if (search.trim()) {
      const q = search.toLowerCase();
      f = f.filter(l => l.account.toLowerCase().includes(q) || l.opportunity_id.toLowerCase().includes(q));
    }
    // KPI quick filters
    if (kpiFilter === "open") f = f.filter(l => l.deal_stage === "Prospecting" || l.deal_stage === "Engaging");
    if (kpiFilter === "focusNow") f = f.filter(l => l.actionStatus === "Foco agora");
    if (kpiFilter === "incomplete") f = f.filter(l => l.isIncomplete);
    if (kpiFilter === "finalized") f = f.filter(l => l.deal_stage === "Won" || l.deal_stage === "Lost");
    return f;
  }, [leads, managerFilter, agentFilter, scoreFilter, actionFilter, stageFilter, sectorFilter, bucketFilter, incompleteOnly, search, kpiFilter]);

  const summaryData = useMemo(() => {
    // Base counts (before kpi filter) but after other filters
    let base = leads;
    if (managerFilter !== "all") base = base.filter(l => l.manager === managerFilter);
    if (agentFilter !== "all") base = base.filter(l => l.sales_agent === agentFilter);
    return {
      open: base.filter(l => l.deal_stage === "Prospecting" || l.deal_stage === "Engaging").length,
      focusNow: base.filter(l => l.actionStatus === "Foco agora").length,
      incomplete: base.filter(l => l.isIncomplete).length,
      finalized: base.filter(l => l.deal_stage === "Won" || l.deal_stage === "Lost").length,
    };
  }, [leads, managerFilter, agentFilter]);

  const byStage = (stage: DealStage) => sortLeads(filtered.filter(l => l.deal_stage === stage), sortBy);

  const handleCardClick = (lead: Lead) => {
    // Find the latest version of this lead from context
    const current = leads.find(l => l.opportunity_id === lead.opportunity_id) || lead;
    setSelectedLead(current);
    setDrawerOpen(true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="shrink-0 px-6 py-4 border-b border-border bg-card">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-foreground">Pipeline de Priorização</h1>
            <Tooltip>
              <TooltipTrigger>
                <Info className="w-4 h-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-xs">
                Score Size representa o potencial estrutural do lead com base em histórico de conversão e velocidade por segmento e porte. Não é predição absoluta.
              </TooltipContent>
            </Tooltip>
          </div>
          {summaryData.incomplete > 0 && (
            <div className="flex items-center gap-1.5 text-xs font-semibold text-destructive">
              <AlertTriangle className="w-3.5 h-3.5" />
              {summaryData.incomplete} leads com dados incompletos
            </div>
          )}
        </div>

        {/* KPI summary cards (clickable as filters) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <SummaryCard
            label="Leads em Aberto"
            value={summaryData.open}
            icon={<span className="text-sm font-bold text-foreground">#</span>}
            active={kpiFilter === "open"}
            onClick={() => setKpiFilter(kpiFilter === "open" ? "all" : "open")}
          />
          <SummaryCard
            label="Foco Agora"
            value={summaryData.focusNow}
            icon={<Target className="w-4 h-4 text-foreground" />}
            active={kpiFilter === "focusNow"}
            onClick={() => setKpiFilter(kpiFilter === "focusNow" ? "all" : "focusNow")}
          />
          <SummaryCard
            label="Dados Incompletos"
            value={summaryData.incomplete}
            icon={<AlertCircle className="w-4 h-4 text-destructive" />}
            active={kpiFilter === "incomplete"}
            onClick={() => setKpiFilter(kpiFilter === "incomplete" ? "all" : "incomplete")}
          />
          <SummaryCard
            label="Finalizados"
            value={summaryData.finalized}
            icon={<CheckCircle className="w-4 h-4 text-muted-foreground" />}
            active={kpiFilter === "finalized"}
            onClick={() => setKpiFilter(kpiFilter === "finalized" ? "all" : "finalized")}
          />
        </div>

        {/* Filters row */}
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Buscar conta ou ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-48 h-8 text-xs"
          />
          <Select value={managerFilter} onValueChange={setManagerFilter}>
            <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder="Manager" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Managers</SelectItem>
              {managers.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={agentFilter} onValueChange={setAgentFilter}>
            <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder="Vendedor" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Vendedores</SelectItem>
              {salesAgents.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={scoreFilter} onValueChange={setScoreFilter}>
            <SelectTrigger className="w-28 h-8 text-xs"><SelectValue placeholder="Score" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Scores</SelectItem>
              {(["A", "B", "C", "D"] as ScoreGrade[]).map(g => <SelectItem key={g} value={g}>Score {g}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={actionFilter} onValueChange={setActionFilter}>
            <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder="Ação" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas Ações</SelectItem>
              {(["Foco agora", "Foco depois", "Baixa prioridade", "Corrigir cadastro", "Ganho", "Perdido"] as ActionStatus[]).map(s => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={stageFilter} onValueChange={setStageFilter}>
            <SelectTrigger className="w-32 h-8 text-xs"><SelectValue placeholder="Etapa" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas Etapas</SelectItem>
              {STAGES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={sectorFilter} onValueChange={setSectorFilter}>
            <SelectTrigger className="w-32 h-8 text-xs"><SelectValue placeholder="Setor" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Setores</SelectItem>
              {sectors.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={bucketFilter} onValueChange={setBucketFilter}>
            <SelectTrigger className="w-28 h-8 text-xs"><SelectValue placeholder="Porte" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Portes</SelectItem>
              {buckets.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-1.5">
            <Switch id="incomplete" checked={incompleteOnly} onCheckedChange={setIncompleteOnly} className="scale-90" />
            <Label htmlFor="incomplete" className="text-[11px] text-muted-foreground cursor-pointer">Só incompletos</Label>
          </div>
          <Select value={sortBy} onValueChange={v => setSortBy(v as SortOption)}>
            <SelectTrigger className="w-32 h-8 text-xs"><SelectValue placeholder="Ordenar" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="priority">Prioridade</SelectItem>
              <SelectItem value="empresa">Empresa</SelectItem>
              <SelectItem value="vendedor">Vendedor</SelectItem>
              <SelectItem value="score">Score</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Kanban board */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="grid grid-cols-4 gap-4 min-w-[1200px] h-full">
          {STAGES.map(stage => {
            const stageLeads = byStage(stage);
            return (
              <div key={stage} className="flex flex-col rounded-xl bg-kanban-column p-3">
                <div className="flex items-center justify-between mb-3 px-1">
                  <h2 className="text-sm font-bold text-foreground">{stage}</h2>
                  <span className="text-xs font-tabular text-muted-foreground bg-background rounded-full px-2 py-0.5 font-semibold">
                    {stageLeads.length}
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  <AnimatePresence mode="popLayout">
                    {stageLeads.map(l => (
                      <KanbanCard key={l.opportunity_id} lead={l} onClick={() => handleCardClick(l)} />
                    ))}
                  </AnimatePresence>
                  {stageLeads.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-8">
                      Nenhum lead neste estágio.
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Lead drawer */}
      <LeadDrawer lead={selectedLead} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
