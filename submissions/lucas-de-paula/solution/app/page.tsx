"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { type ScoredDeal } from "@/lib/scoring";
import { DealTable } from "./components/DealTable";
import { DealModal } from "./components/DealModal";
import { ScoreBreakdown } from "./components/ScoreBreakdown";
import { Navbar } from "./components/Navbar";
import { InfoTooltip } from "./components/InfoTooltip";
import { DailyFocus } from "./components/DailyFocus";

type QuickFilter = "all" | "healthy" | "atRisk" | "prospecting" | "zombie";

interface Meta {
  agents: string[];
  managers: string[];
  regions: string[];
  stages: string[];
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-500 uppercase tracking-wider">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-gray-500 focus:outline-none min-w-[160px]"
      >
        <option value="">Todos</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

// Clickable KPI card
function KpiCard({
  label,
  value,
  sub,
  tooltip,
  color,
  active,
  borderColor,
  onClick,
}: {
  label: string;
  value: number | string;
  sub?: string;
  tooltip: string;
  color: string;
  active: boolean;
  borderColor?: string;
  onClick: () => void;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      className={`
        text-left bg-gray-900 rounded-2xl p-5 w-full transition-all cursor-pointer select-none
        ${active
          ? `${borderColor ?? "border-blue-500"} border-2 ring-1 ring-blue-500/20`
          : `border ${borderColor ?? "border-gray-800"} hover:border-gray-600`
        }
      `}
    >
      <p className="text-gray-500 text-xs uppercase tracking-wider mb-1 flex items-center">
        {label}
        <InfoTooltip text={tooltip} />
        {active && (
          <span className="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded-full font-medium">
            filtrando
          </span>
        )}
      </p>
      <p className={`text-4xl font-black tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-300 mt-1 leading-tight">{sub}</p>}
    </div>
  );
}

// Collapsible "Como usar" guide panel
function HowToUsePanel() {
  const [open, setOpen] = useState(true); // always true on SSR, corrected after mount

  useEffect(() => {
    setOpen(localStorage.getItem("pipeline-howto-closed") !== "1");
  }, []);

  function toggle() {
    const next = !open;
    setOpen(next);
    localStorage.setItem("pipeline-howto-closed", next ? "0" : "1");
  }

  return (
    <div className="bg-blue-500/5 border border-blue-500/20 rounded-2xl overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-blue-500/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-blue-400 text-sm font-semibold">📋 Como usar o Pipeline</span>
          <span className="text-xs text-blue-400/60">Guia rápido para priorizar seus leads</span>
        </div>
        <span className="text-gray-500 text-xs">{open ? "▲ Ocultar" : "▼ Mostrar"}</span>
      </button>

      {open && (
        <div className="px-5 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 border-t border-blue-500/10">
          {[
            {
              icon: "🚀",
              title: "Prioridade máxima",
              desc: "Score ≥70, Engaging ≤30 dias. Feche hoje — alta probabilidade de conversão.",
            },
            {
              icon: "⚠️",
              title: "Contato urgente",
              desc: "Engaging entre 31–90 dias (exclui zumbis). Risco crescente. Ligue, envie proposta, crie senso de urgência.",
            },
            {
              icon: "💀",
              title: "Revisar ou encerrar",
              desc: "Engaging +90 dias. Zumbi. Negocie condições novas ou encerre para limpar o pipeline.",
            },
            {
              icon: "➡️",
              title: "Mover p/ Engaging",
              desc: "Deal em Prospecting qualificado. Avance a conversa e inicie a proposta formal.",
            },
          ].map((item) => (
            <div key={item.title} className="flex gap-2 pt-3">
              <span className="text-lg shrink-0">{item.icon}</span>
              <div>
                <p className="text-xs font-semibold text-gray-300">{item.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [deals, setDeals] = useState<ScoredDeal[]>([]);
  const [selectedDeal, setSelectedDeal] = useState<ScoredDeal | null>(null);
  const [scoreBreakdownDeal, setScoreBreakdownDeal] = useState<ScoredDeal | null>(null);
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [meta, setMeta] = useState<Meta>({
    agents: [],
    managers: [],
    regions: [],
    stages: [],
  });
  const [loading, setLoading] = useState(true);

  const [agent, setAgent] = useState("");
  const [manager, setManager] = useState("");
  const [region, setRegion] = useState("");
  const [stage, setStage] = useState("");

  useEffect(() => {
    fetch("/api/meta", { cache: "no-store" })
      .then((r) => r.json())
      .then(setMeta)
      .catch(console.error);
  }, []);

  const fetchDeals = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (agent) params.set("agent", agent);
    if (manager) params.set("manager", manager);
    if (region) params.set("region", region);
    if (stage) params.set("stage", stage);

    fetch(`/api/deals?${params.toString()}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => {
        setDeals(data);
        setLoading(false);
      })
      .catch(console.error);
  }, [agent, manager, region, stage]);

  useEffect(() => {
    fetchDeals();
  }, [fetchDeals]);

  // KPI counts always from full filtered set
  // "Saudável" = Engaging ≤30 dias (on-track, dentro do ciclo ideal)
  const healthy       = deals.filter(
    (d) => d.deal_stage === "Engaging" && d.days_in_stage <= 30
  ).length;
  // "Em risco" = 31–90 dias — EXCLUI zumbis (que já têm card próprio)
  const atRisk        = deals.filter(
    (d) => d.deal_stage === "Engaging" && d.days_in_stage > 30 && d.days_in_stage <= 90
  ).length;
  const prospecting   = deals.filter((d) => d.deal_stage === "Prospecting").length;
  const zombies       = deals.filter(
    (d) => d.deal_stage === "Engaging" && d.days_in_stage > 90
  ).length;
  const avgScore =
    deals.length > 0
      ? Math.round(deals.reduce((s, d) => s + d.score, 0) / deals.length)
      : 0;

  // Quick-filter applied client-side on top of API results
  const displayedDeals = useMemo(() => {
    if (quickFilter === "healthy")
      return deals.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage <= 30);
    if (quickFilter === "atRisk")
      return deals.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 30 && d.days_in_stage <= 90);
    if (quickFilter === "prospecting")
      return deals.filter((d) => d.deal_stage === "Prospecting");
    if (quickFilter === "zombie")
      return deals.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 90);
    return deals;
  }, [deals, quickFilter]);

  // Extra stats derived from current displayed set (updates with vendor/region/quick filters)
  const avgDays = useMemo(() => {
    if (displayedDeals.length === 0) return 0;
    return Math.round(
      displayedDeals.reduce((s, d) => s + d.days_in_stage, 0) / displayedDeals.length
    );
  }, [displayedDeals]);

  const topProduct = useMemo(() => {
    if (displayedDeals.length === 0) return "—";
    const freq: Record<string, number> = {};
    for (const d of displayedDeals) {
      if (d.product) freq[d.product] = (freq[d.product] ?? 0) + 1;
    }
    return Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
  }, [displayedDeals]);

  const handleKpiClick = (filter: QuickFilter) => {
    setQuickFilter((prev) => (prev === filter ? "all" : filter));
  };

  const quickFilterLabel: Record<QuickFilter, string> = {
    all:          "",
    healthy:      "Saudável (Engaging ≤30d)",
    atRisk:       "Em risco (Engaging 31–90d)",
    prospecting:  "Prospecting — aguardando engajamento",
    zombie:       "Zumbis (Engaging +90d)",
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Deal detail modal */}
      {selectedDeal && (
        <DealModal
          deal={selectedDeal}
          onClose={() => setSelectedDeal(null)}
          onUpdate={() => { setSelectedDeal(null); fetchDeals(); }}
        />
      )}

      {/* Score breakdown — opened directly by clicking the score badge in the table */}
      {scoreBreakdownDeal && (
        <ScoreBreakdown
          score={scoreBreakdownDeal.score}
          components={scoreBreakdownDeal.components}
          dealName={scoreBreakdownDeal.account || scoreBreakdownDeal.opportunity_id}
          onClose={() => setScoreBreakdownDeal(null)}
        />
      )}

      <Navbar />

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-4 sm:py-8 space-y-4 sm:space-y-6">
        {/* KPI cards — clicáveis para filtrar */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <KpiCard
            label="Deals ativos"
            value={deals.length}
            tooltip="Total de deals em Engaging ou Prospecting. Exclui Won e Lost. Clique para ver todos os deals."
            color="text-white"
            active={quickFilter === "all"}
            borderColor={quickFilter === "all" ? "border-blue-600" : "border-gray-800"}
            onClick={() => setQuickFilter("all")}
          />
          <KpiCard
            label="Saudável (≤30d)"
            value={healthy}
            sub={`${deals.length > 0 ? Math.round(healthy / deals.length * 100) : 0}% dos ${deals.length} ativos · ✅ Engaging no prazo`}
            tooltip="Deals em Engaging há 30 dias ou menos — dentro do ciclo ideal de 52 dias. Foco: avançar proposta e fechar enquanto o momentum está alto. Clique para filtrar."
            color="text-emerald-400"
            active={quickFilter === "healthy"}
            borderColor={quickFilter === "healthy" ? "border-emerald-500" : "border-gray-800"}
            onClick={() => handleKpiClick("healthy")}
          />
          <KpiCard
            label="Em risco (31–90d)"
            value={atRisk}
            sub={`${deals.length > 0 ? Math.round(atRisk / deals.length * 100) : 0}% dos ${deals.length} ativos · só ⚠️ Contato urgente`}
            tooltip="Deals em Engaging entre 31 e 90 dias — ciclo saudável é 52d. Exclui zumbis (+90d), que aparecem no card ao lado. Clique para filtrar."
            color="text-amber-400"
            active={quickFilter === "atRisk"}
            borderColor={quickFilter === "atRisk" ? "border-amber-500" : "border-amber-900/40"}
            onClick={() => handleKpiClick("atRisk")}
          />
          <KpiCard
            label="Prospecting"
            value={prospecting}
            sub={`${deals.length > 0 ? Math.round(prospecting / deals.length * 100) : 0}% dos ${deals.length} ativos · ➡️ Mover p/ Engaging`}
            tooltip="Deals ainda em Prospecting — não iniciaram Engaging. Qualifique a conta e avance a conversa para não perder momentum. Clique para filtrar."
            color="text-purple-400"
            active={quickFilter === "prospecting"}
            borderColor={quickFilter === "prospecting" ? "border-purple-500" : "border-purple-900/40"}
            onClick={() => handleKpiClick("prospecting")}
          />
          <KpiCard
            label="Zumbis (+90d)"
            value={zombies}
            sub={`${deals.length > 0 ? Math.round(zombies / deals.length * 100) : 0}% dos ${deals.length} ativos · 💀 Revisar ou encerrar`}
            tooltip="Deals em Engaging há mais de 90 dias. Com ciclo médio de 52 dias, esses deals estão muito além do esperado — precisam de revisão urgente: avançar, renegociar ou encerrar. Clique para filtrar."
            color="text-red-400"
            active={quickFilter === "zombie"}
            borderColor={quickFilter === "zombie" ? "border-red-500" : "border-red-900/40"}
            onClick={() => handleKpiClick("zombie")}
          />
        </div>

        {/* Daily Focus — top 3 deals críticos que precisam de ação hoje */}
        <DailyFocus deals={deals} onSelectDeal={setSelectedDeal} />

        {/* How-to guide — collapsible, persisted in localStorage */}
        <HowToUsePanel />

        {/* Filters + Stats bar */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-wrap gap-4 items-end">
            <Select label="Vendedor" value={agent} onChange={setAgent} options={meta.agents} />
            <Select label="Manager" value={manager} onChange={setManager} options={meta.managers} />
            <Select label="Região" value={region} onChange={setRegion} options={meta.regions} />
            <Select label="Stage" value={stage} onChange={setStage} options={meta.stages} />

            {(agent || manager || region || stage) && (
              <button
                onClick={() => {
                  setAgent(""); setManager(""); setRegion(""); setStage("");
                }}
                className="text-sm text-gray-400 hover:text-white px-3 py-2 rounded-lg border border-gray-700 hover:border-gray-500 transition-colors"
              >
                Limpar filtros ✕
              </button>
            )}

            {/* Stats — update dynamically with every filter change */}
            <div className="ml-auto flex items-end gap-6">
              <div className="text-right">
                <p className="text-xs text-gray-500 flex items-center justify-end gap-1">
                  Produto top
                  <InfoTooltip text="Produto mais presente no pipeline filtrado. Útil para entender onde o vendedor ou região concentra mais volume." />
                </p>
                <p className="text-lg font-black text-white truncate max-w-[120px]" title={topProduct}>
                  {topProduct}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500 flex items-center justify-end gap-1">
                  Dias médios
                  <InfoTooltip text="Média de dias no stage atual dos deals exibidos. Ciclo saudável = 52 dias. Acima disso, o pipeline está envelhecendo." />
                </p>
                <p className={`text-2xl font-black tabular-nums ${
                  avgDays > 52 ? "text-amber-400" : avgDays > 30 ? "text-yellow-300" : "text-white"
                }`}>
                  {avgDays}d
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500 flex items-center justify-end gap-1">
                  Score médio
                  <InfoTooltip text="Média dos scores do pipeline filtrado. Abaixo de 50 indica pipeline fraco ou mal-qualificado." />
                </p>
                <p className="text-2xl font-black text-white tabular-nums">{avgScore}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 mt-4">Calculando scores...</p>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3 flex-wrap">
                <p className="text-sm text-gray-500">
                  {displayedDeals.length} deal{displayedDeals.length !== 1 ? "s" : ""}
                  {quickFilter !== "all" && (
                    <span className="text-gray-600"> (de {deals.length} totais)</span>
                  )}{" "}
                  · ordenados por score · clique na linha para detalhes · clique no score para breakdown
                </p>
                {quickFilter !== "all" && (
                  <span className="inline-flex items-center gap-1.5 text-xs bg-blue-500/15 text-blue-400 border border-blue-500/30 px-2.5 py-1 rounded-full">
                    🔍 {quickFilterLabel[quickFilter]}
                    <button
                      onClick={() => setQuickFilter("all")}
                      className="ml-0.5 hover:text-white transition-colors"
                    >
                      ✕
                    </button>
                  </span>
                )}
              </div>
            </div>
            <DealTable
              deals={displayedDeals}
              onRowClick={setSelectedDeal}
              onScoreClick={setScoreBreakdownDeal}
            />
          </div>
        )}
      </main>
    </div>
  );
}
