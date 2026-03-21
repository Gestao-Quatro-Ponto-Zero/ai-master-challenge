import React, { useMemo, useState } from "react";
import { useData } from "@/context/DataContext";
import type { Lead, ScoreGrade } from "@/lib/types";
import { daysBetween } from "@/lib/dataHelpers";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RTooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Info, TrendingUp, TrendingDown, Minus, AlertTriangle, Clock, Target, Users } from "lucide-react";

function calcMetrics(leads: Lead[]) {
  const closed = leads.filter(l => l.deal_stage === "Won" || l.deal_stage === "Lost");
  const won = closed.filter(l => l.deal_stage === "Won");
  const winRate = closed.length > 0 ? won.length / closed.length : 0;
  const withDates = closed.filter(l => l.engage_date && l.close_date);
  const avgTime = withDates.length > 0
    ? withDates.reduce((s, l) => s + daysBetween(l.engage_date!, l.close_date!), 0) / withDates.length
    : 0;
  const incomplete = leads.filter(l => l.isIncomplete);
  const gradeCount = (g: ScoreGrade) => leads.filter(l => l.scoreGrade === g).length;
  const classified = leads.filter(l => l.scoreGrade !== null);
  const qualityIndex = classified.length > 0
    ? classified.reduce((s, l) => s + ({ A: 4, B: 3, C: 2, D: 1 }[l.scoreGrade!] || 0), 0) / classified.length
    : 0;
  const qualityIndex100 = qualityIndex > 0 ? ((qualityIndex - 1) / 3) * 100 : 0;

  return {
    total: leads.length,
    complete: leads.length - incomplete.length,
    incomplete: incomplete.length,
    incompletePct: leads.length > 0 ? (incomplete.length / leads.length * 100) : 0,
    winRate,
    avgTime,
    scoreA: gradeCount("A"),
    scoreB: gradeCount("B"),
    scoreC: gradeCount("C"),
    scoreD: gradeCount("D"),
    qualityIndex100,
  };
}

function KpiCard({ label, value, sub, tooltip }: { label: string; value: string | number; sub?: string; tooltip?: string }) {
  return (
    <div className="rounded-lg bg-card p-4 shadow-[0_0_0_1px_rgba(0,0,0,.05),0_1px_3px_0_rgba(0,0,0,.03)]">
      <div className="flex items-center gap-1.5 mb-1">
        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
        {tooltip && (
          <Tooltip>
            <TooltipTrigger><Info className="w-3 h-3 text-muted-foreground/50" /></TooltipTrigger>
            <TooltipContent className="max-w-xs text-xs">{tooltip}</TooltipContent>
          </Tooltip>
        )}
      </div>
      <p className="text-2xl font-bold font-tabular text-foreground">{value}</p>
      {sub && <p className="text-[11px] text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

function CompareIndicator({ value, unit = "", invert = false }: { value: number; unit?: string; invert?: boolean }) {
  if (Math.abs(value) < 0.1) return <Minus className="w-3 h-3 text-muted-foreground inline" />;
  const positive = invert ? value < 0 : value > 0;
  const sign = value > 0 ? "+" : "";
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold ${positive ? "text-[hsl(var(--chart-green))]" : "text-destructive"}`}>
      {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {sign}{value.toFixed(1)}{unit}
    </span>
  );
}

const SCORE_COLORS: Record<string, string> = {
  A: "hsl(45, 100%, 51%)",
  B: "hsl(45, 60%, 70%)",
  C: "hsl(0, 0%, 70%)",
  D: "hsl(0, 0%, 82%)",
};

interface AlertItem {
  icon: React.ReactNode;
  label: string;
  detail: string;
  severity: "high" | "medium";
}

export function DashboardView() {
  const { leads, managers } = useData();
  const [selectedManager, setSelectedManager] = useState("all");
  const [selectedAgent, setSelectedAgent] = useState("all");

  const managerLeads = useMemo(() => {
    return selectedManager === "all" ? leads : leads.filter(l => l.manager === selectedManager);
  }, [leads, selectedManager]);

  const agentsInManager = useMemo(() => [...new Set(managerLeads.map(l => l.sales_agent))].sort(), [managerLeads]);

  const displayLeads = useMemo(() => {
    return selectedAgent === "all" ? managerLeads : managerLeads.filter(l => l.sales_agent === selectedAgent);
  }, [managerLeads, selectedAgent]);

  const team = useMemo(() => calcMetrics(displayLeads), [displayLeads]);

  const agents = useMemo(() => {
    const map = new Map<string, Lead[]>();
    for (const l of displayLeads) {
      if (!map.has(l.sales_agent)) map.set(l.sales_agent, []);
      map.get(l.sales_agent)!.push(l);
    }
    return Array.from(map.entries())
      .map(([agent, agentLeads]) => ({ agent, ...calcMetrics(agentLeads) }))
      .sort((a, b) => a.agent.localeCompare(b.agent));
  }, [displayLeads]);

  const teamAvg = useMemo(() => {
    if (agents.length === 0) return { total: 0, incompletePct: 0, avgTime: 0, winRate: 0, qualityIndex100: 0 };
    return {
      total: agents.reduce((s, a) => s + a.total, 0) / agents.length,
      incompletePct: agents.reduce((s, a) => s + a.incompletePct, 0) / agents.length,
      avgTime: agents.reduce((s, a) => s + a.avgTime, 0) / agents.length,
      winRate: agents.reduce((s, a) => s + a.winRate, 0) / agents.length,
      qualityIndex100: agents.reduce((s, a) => s + a.qualityIndex100, 0) / agents.length,
    };
  }, [agents]);

  // Attention alerts
  const alerts = useMemo<AlertItem[]>(() => {
    if (agents.length < 2) return [];
    const items: AlertItem[] = [];
    
    // Highest incomplete %
    const maxIncomplete = agents.reduce((best, a) => a.incompletePct > best.incompletePct ? a : best, agents[0]);
    if (maxIncomplete.incompletePct > 15) {
      items.push({
        icon: <AlertTriangle className="w-4 h-4 text-[hsl(var(--action-fix))]" />,
        label: `${maxIncomplete.agent}`,
        detail: `${maxIncomplete.incompletePct.toFixed(0)}% de dados incompletos`,
        severity: maxIncomplete.incompletePct > 30 ? "high" : "medium",
      });
    }

    // Highest load
    const maxLoad = agents.reduce((best, a) => a.total > best.total ? a : best, agents[0]);
    if (maxLoad.total > teamAvg.total * 1.4) {
      items.push({
        icon: <Users className="w-4 h-4 text-[hsl(var(--chart-blue))]" />,
        label: `${maxLoad.agent}`,
        detail: `${maxLoad.total} leads — carga ${((maxLoad.total / teamAvg.total - 1) * 100).toFixed(0)}% acima da média`,
        severity: "medium",
      });
    }

    // Slowest time
    const agentsWithTime = agents.filter(a => a.avgTime > 0);
    if (agentsWithTime.length > 0) {
      const slowest = agentsWithTime.reduce((best, a) => a.avgTime > best.avgTime ? a : best, agentsWithTime[0]);
      if (slowest.avgTime > teamAvg.avgTime * 1.3 && teamAvg.avgTime > 0) {
        items.push({
          icon: <Clock className="w-4 h-4 text-[hsl(var(--chart-blue))]" />,
          label: `${slowest.agent}`,
          detail: `${Math.round(slowest.avgTime)} dias — ${Math.round(slowest.avgTime - teamAvg.avgTime)} dias acima da média`,
          severity: "medium",
        });
      }
    }

    // Lowest win rate
    const agentsWithWR = agents.filter(a => a.winRate > 0 || a.total > 5);
    if (agentsWithWR.length > 0) {
      const lowest = agentsWithWR.reduce((best, a) => a.winRate < best.winRate ? a : best, agentsWithWR[0]);
      if (lowest.winRate < teamAvg.winRate * 0.7 && teamAvg.winRate > 0) {
        items.push({
          icon: <Target className="w-4 h-4 text-destructive" />,
          label: `${lowest.agent}`,
          detail: `Win rate de ${(lowest.winRate * 100).toFixed(1)}% — abaixo da média do time`,
          severity: "high",
        });
      }
    }

    return items;
  }, [agents, teamAvg]);

  // Chart data
  const leadsChartData = agents.map(a => ({ name: a.agent.split(" ")[0], Leads: a.total }));
  const scoreChartData = agents.map(a => ({ name: a.agent.split(" ")[0], A: a.scoreA, B: a.scoreB, C: a.scoreC, D: a.scoreD }));
  const incompleteChartData = agents.map(a => ({ name: a.agent.split(" ")[0], Incompletos: a.incomplete }));
  const timeChartData = agents.map(a => ({ name: a.agent.split(" ")[0], "Tempo Médio": Math.round(a.avgTime * 10) / 10 }));
  const winRateChartData = agents.map(a => ({ name: a.agent.split(" ")[0], "Win Rate": Math.round(a.winRate * 1000) / 10 }));
  const qualityChartData = agents.map(a => ({ name: a.agent.split(" ")[0], Qualidade: Math.round(a.qualityIndex100 * 10) / 10 }));

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">
          Painel Gerencial{selectedManager !== "all" ? `: ${selectedManager}` : ""}
        </h1>
        <div className="flex gap-2">
          <Select value={selectedManager} onValueChange={v => { setSelectedManager(v); setSelectedAgent("all"); }}>
            <SelectTrigger className="w-48 h-9 text-sm"><SelectValue placeholder="Manager" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Managers</SelectItem>
              {managers.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={selectedAgent} onValueChange={setSelectedAgent}>
            <SelectTrigger className="w-48 h-9 text-sm"><SelectValue placeholder="Vendedor" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos Vendedores</SelectItem>
              {agentsInManager.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      {selectedManager === "all" && (
        <p className="text-sm text-muted-foreground">Selecione um manager para ver o desempenho do time.</p>
      )}

      {/* Attention Alerts */}
      {alerts.length > 0 && (
        <div className="rounded-lg bg-card border border-[hsl(var(--action-fix))]/20 p-4 shadow-[0_0_0_1px_rgba(0,0,0,.05)]">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[hsl(var(--action-fix))]" />
            Atenção Imediata
          </h3>
          <div className="space-y-2">
            {alerts.map((alert, i) => (
              <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm ${alert.severity === "high" ? "bg-destructive/5" : "bg-muted/50"}`}>
                {alert.icon}
                <span className="font-semibold text-foreground">{alert.label}</span>
                <span className="text-muted-foreground">—</span>
                <span className="text-muted-foreground">{alert.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <KpiCard label="Total Leads" value={team.total} />
        <KpiCard label="Completos" value={team.complete} />
        <KpiCard label="Incompletos" value={team.incomplete} sub={`${team.incompletePct.toFixed(1)}%`} />
        <KpiCard label="% Incompletos" value={`${team.incompletePct.toFixed(1)}%`} />
        <KpiCard label="Tempo Médio" value={`${Math.round(team.avgTime)} dias`} tooltip="Calculado apenas com deals fechados (Won + Lost) com datas válidas" />
        <KpiCard label="Win Rate" value={`${(team.winRate * 100).toFixed(1)}%`} tooltip="Won / (Won + Lost)" />
        <KpiCard label="Qualidade" value={`${team.qualityIndex100.toFixed(0)}/100`} tooltip="Índice de Qualidade da Carteira: média ponderada (A=4, B=3, C=2, D=1) convertida para 0-100. Mais alto = carteira estruturalmente melhor." />
      </div>

      {/* Table */}
      <div className="rounded-lg bg-card shadow-[0_0_0_1px_rgba(0,0,0,.05),0_1px_3px_0_rgba(0,0,0,.03)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-foreground/[.03]">
                <th className="text-left p-3 font-bold text-foreground text-xs uppercase tracking-wide">Vendedor</th>
                <th className="text-center p-3 font-bold text-foreground text-xs uppercase tracking-wide">Total</th>
                <th className="text-center p-3 font-bold text-xs uppercase tracking-wide" style={{ color: "hsl(45, 100%, 40%)" }}>A</th>
                <th className="text-center p-3 font-bold text-xs uppercase tracking-wide" style={{ color: "hsl(45, 60%, 50%)" }}>B</th>
                <th className="text-center p-3 font-bold text-foreground text-xs uppercase tracking-wide">C</th>
                <th className="text-center p-3 font-bold text-muted-foreground text-xs uppercase tracking-wide">D</th>
                <th className="text-center p-3 font-bold text-destructive text-xs uppercase tracking-wide">Incompl.</th>
                <th className="text-center p-3 font-bold text-foreground text-xs uppercase tracking-wide">Qualidade</th>
                <th className="text-center p-3 font-bold text-foreground text-xs uppercase tracking-wide">Tempo</th>
                <th className="text-center p-3 font-bold text-foreground text-xs uppercase tracking-wide">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(a => (
                <tr key={a.agent} className="border-b border-border hover:bg-background/50 transition-colors">
                  <td className="p-3 font-semibold text-foreground">{a.agent}</td>
                  <td className="p-3 text-center font-tabular">
                    {a.total}
                    <br />
                    <CompareIndicator value={a.total - teamAvg.total} />
                  </td>
                  <td className="p-3 text-center font-tabular font-semibold">{a.scoreA}</td>
                  <td className="p-3 text-center font-tabular">{a.scoreB}</td>
                  <td className="p-3 text-center font-tabular">{a.scoreC}</td>
                  <td className="p-3 text-center font-tabular text-muted-foreground">{a.scoreD}</td>
                  <td className="p-3 text-center font-tabular">
                    <span className="text-destructive font-semibold">{a.incomplete}</span>
                    <span className="text-muted-foreground ml-1">({a.incompletePct.toFixed(0)}%)</span>
                    <br />
                    <CompareIndicator value={a.incompletePct - teamAvg.incompletePct} unit="pp" invert />
                  </td>
                  <td className="p-3 text-center font-tabular">
                    {a.qualityIndex100.toFixed(0)}
                    <br />
                    <CompareIndicator value={a.qualityIndex100 - teamAvg.qualityIndex100} />
                  </td>
                  <td className="p-3 text-center font-tabular">
                    {Math.round(a.avgTime)} dias
                    <br />
                    <CompareIndicator value={a.avgTime - teamAvg.avgTime} unit="d" invert />
                  </td>
                  <td className="p-3 text-center font-tabular">
                    {(a.winRate * 100).toFixed(1)}%
                    <br />
                    <CompareIndicator value={(a.winRate - teamAvg.winRate) * 100} unit="pp" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
        <ChartCard title="Leads por Vendedor">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={leadsChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={70} />
              <RTooltip />
              <Bar dataKey="Leads" fill="hsl(0,0%,20%)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Score Size por Vendedor">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={scoreChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <RTooltip />
              <Legend />
              <Bar dataKey="A" stackId="s" fill={SCORE_COLORS.A} />
              <Bar dataKey="B" stackId="s" fill={SCORE_COLORS.B} />
              <Bar dataKey="C" stackId="s" fill={SCORE_COLORS.C} />
              <Bar dataKey="D" stackId="s" fill={SCORE_COLORS.D} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Incompletos por Vendedor">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={incompleteChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <RTooltip />
              <Bar dataKey="Incompletos" fill="hsl(0, 85%, 55%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Tempo Médio por Vendedor (dias)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={timeChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={70} />
              <RTooltip />
              <Bar dataKey="Tempo Médio" fill="hsl(210, 70%, 55%)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Win Rate por Vendedor (%)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={winRateChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={70} />
              <RTooltip />
              <Bar dataKey="Win Rate" fill="hsl(140, 60%, 45%)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Qualidade da Carteira (0-100)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={qualityChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(0,0%,88%)" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={70} />
              <RTooltip />
              <Bar dataKey="Qualidade" fill="hsl(45, 100%, 51%)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-card p-4 shadow-[0_0_0_1px_rgba(0,0,0,.05),0_1px_3px_0_rgba(0,0,0,.03)]">
      <h3 className="text-xs font-bold text-foreground uppercase tracking-wide mb-3">{title}</h3>
      {children}
    </div>
  );
}
