"use client";

import { useEffect, useState } from "react";
import { Navbar } from "../components/Navbar";
import { InfoTooltip } from "../components/InfoTooltip";

interface CycleBucket { label: string; count: number }
interface MonthData { month: string; closes: number; revenue: number }
interface ProductData { name: string; won: number; lost: number; revenue: number; price: number; winRate: number }
interface ProductSeason { product: string; monthly: { month: string; closes: number }[] }
interface AgentData { name: string; won: number; lost: number; total: number; winRate: number }
interface RegionData { name: string; won: number; lost: number; total: number; revenue: number; winRate: number }
interface RegionSeason { region: string; monthly: { month: string; closes: number }[] }
interface SectorData { name: string; won: number; lost: number; total: number; revenue: number; winRate: number }
interface CountryData { name: string; won: number; lost: number; total: number; revenue: number; winRate: number }
interface CorrBracket { label: string; won: number; lost: number; total: number; winRate: number }

interface InsightsData {
  avgCycleDays: number;
  totalWon: number;
  totalLost: number;
  cycleBuckets: CycleBucket[];
  seasonality: MonthData[];
  products: ProductData[];
  productSeasonality: ProductSeason[];
  topAgents: AgentData[];
  regions: RegionData[];
  regionSeasonality: RegionSeason[];
  sectors: SectorData[];
  countries: CountryData[];
  empCorrelation: CorrBracket[];
  subsidiaryCorrelation: CorrBracket[];
}

// ─────────────────────────────────────────────
// Mini bar chart
// ─────────────────────────────────────────────
function BarChart({
  data,
  valueKey,
  labelKey,
  color = "blue",
  formatValue,
  highlightIndex,
}: {
  data: Record<string, unknown>[] | object[];
  valueKey: string;
  labelKey: string;
  color?: string;
  formatValue?: (v: number) => string;
  highlightIndex?: number;
}) {
  const rows = data as Record<string, unknown>[];
  const max = Math.max(...rows.map((d) => (d[valueKey] as number) || 0), 1);
  const baseColor = {
    blue:   "bg-blue-500",
    emerald:"bg-emerald-500",
    amber:  "bg-amber-500",
    purple: "bg-purple-500",
  }[color] ?? "bg-blue-500";

  return (
    <div className="flex items-end gap-1.5 h-40">
      {rows.map((item, i) => {
        const val = (item[valueKey] as number) || 0;
        const pct = (val / max) * 100;
        const isHighlight = highlightIndex === i;
        return (
          <div key={i} className="flex flex-col items-center flex-1 gap-1.5 group">
            <div className="relative w-full flex items-end justify-center" style={{ height: "96px" }}>
              <div
                className={`w-full rounded-t transition-all ${
                  isHighlight
                    ? "bg-emerald-400 opacity-100 ring-2 ring-emerald-400/50"
                    : `${baseColor} opacity-70 group-hover:opacity-100`
                }`}
                style={{ height: `${Math.max(2, pct)}%` }}
              />
              <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {formatValue ? formatValue(val) : val}
              </div>
            </div>
            <span className={`text-[10px] text-center leading-tight ${isHighlight ? "text-emerald-400 font-semibold" : "text-gray-500"}`}>
              {item[labelKey] as string}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SectionCard({
  title,
  tooltip,
  children,
}: {
  title: string;
  tooltip: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <h3 className="text-white font-semibold mb-5 flex items-center gap-1 text-base">
        {title}
        <InfoTooltip text={tooltip} />
      </h3>
      {children}
    </div>
  );
}

// Peak callout chip
function PeakChip({ label, value, suffix = "" }: { label: string; value: string | number; suffix?: string }) {
  return (
    <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/25 rounded-full px-3 py-1">
      <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
      <span className="text-xs text-gray-400">{label}:</span>
      <span className="text-xs font-semibold text-emerald-400">{value}{suffix}</span>
    </div>
  );
}

// Collapsible "Como usar" guide for Insights
function HowToUseInsightsPanel() {
  const [open, setOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("insights-howto-closed") !== "1";
  });

  function toggle() {
    const next = !open;
    setOpen(next);
    localStorage.setItem("insights-howto-closed", next ? "0" : "1");
  }

  return (
    <div className="bg-purple-500/5 border border-purple-500/20 rounded-2xl overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-purple-500/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-purple-400 text-sm font-semibold">📊 Como ler os Insights</span>
          <span className="text-xs text-purple-400/60">Panorama histórico da empresa — todos os deals e regiões</span>
        </div>
        <span className="text-gray-500 text-xs">{open ? "▲ Ocultar" : "▼ Mostrar"}</span>
      </button>

      {open && (
        <div className="px-5 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 border-t border-purple-500/10">
          {[
            {
              icon: "⏱",
              title: "Ciclo de fechamento",
              desc: "Quanto tempo os deals levam para fechar. Use para identificar quando um deal do pipeline está fora do prazo normal.",
            },
            {
              icon: "📅",
              title: "Sazonalidade",
              desc: "Quais meses concentram mais closes e receita. Planeje prospecção nos meses fracos e intensifique esforço nos picos.",
            },
            {
              icon: "📦",
              title: "Produtos",
              desc: "Win rate e receita por produto. Produtos com maior ticket e win rate alta são os melhores alvos para o pipeline.",
            },
            {
              icon: "🏆",
              title: "Top vendedores",
              desc: "Ranking de win rate dos vendedores. Use para identificar boas práticas e quem precisa de coaching.",
            },
            {
              icon: "🗺",
              title: "Regiões",
              desc: "Performance por região — win rate e receita gerada. Aponta onde concentrar recursos e onde há oportunidade de melhoria.",
            },
            {
              icon: "💡",
              title: "Dica de uso",
              desc: "Os insights são agregados históricos. Para ver o pipeline ao vivo com filtros por vendedor, use a aba Pipeline.",
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

export default function InsightsPage() {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/insights", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(console.error);
  }, []);

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <Navbar />
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 mt-4">Analisando o pipeline...</p>
          </div>
        </div>
      </div>
    );
  }

  const overallWinRate = data.totalWon + data.totalLost > 0
    ? ((data.totalWon / (data.totalWon + data.totalLost)) * 100).toFixed(1)
    : "—";

  const formatRevenue = (v: number) =>
    v >= 1_000_000 ? `$${(v / 1_000_000).toFixed(1)}M` : v >= 1_000 ? `$${(v / 1_000).toFixed(0)}k` : `$${v}`;

  const riskThreshold = Math.round(data.avgCycleDays * 1.5);

  // Top 2 peaks for seasonality (closes)
  const sortedByCloses = [...data.seasonality].sort((a, b) => b.closes - a.closes);
  const top2ClosesMonths = sortedByCloses.slice(0, 2);
  const top2ClosesIdx = top2ClosesMonths.map((m) => data.seasonality.indexOf(m));

  // Top 2 peaks for revenue
  const sortedByRevenue = [...data.seasonality].sort((a, b) => b.revenue - a.revenue);
  const top2RevenueMonths = sortedByRevenue.slice(0, 2);
  const top2RevenueIdx = top2RevenueMonths.map((m) => data.seasonality.indexOf(m));

  // Products sorted by revenue (already sorted from API)
  // Product seasonality quarters
  const quarters = [
    { label: "Q1 Jan–Mar", months: [0, 1, 2] },
    { label: "Q2 Abr–Jun", months: [3, 4, 5] },
    { label: "Q3 Jul–Set", months: [6, 7, 8] },
    { label: "Q4 Out–Dez", months: [9, 10, 11] },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Navbar />

      <main className="max-w-screen-2xl mx-auto px-6 py-10 space-y-10">

        {/* Page header */}
        <div>
          <h2 className="text-2xl font-bold text-white">Insights do Pipeline</h2>
          <p className="text-gray-500 text-sm mt-1">
            Padrões históricos baseados em {data.totalWon + data.totalLost} deals fechados
          </p>
        </div>

        {/* How-to guide — collapsible */}
        <HowToUseInsightsPanel />

        {/* Summary KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 flex items-center gap-1">
              Ciclo médio
              <InfoTooltip text="Tempo médio entre a data de engajamento e o fechamento nos deals ganhos. Use para saber quando um deal está fora do prazo normal." />
            </p>
            <p className="text-4xl font-black text-white tabular-nums">{data.avgCycleDays}</p>
            <p className="text-gray-500 text-xs mt-1">dias para fechar</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 flex items-center gap-1">
              Win rate geral
              <InfoTooltip text="Percentual de deals que foram ganhos (Won) sobre o total de deals encerrados (Won + Perdidos). Quanto maior, melhor o aproveitamento do pipeline." />
            </p>
            <p className="text-4xl font-black text-emerald-400 tabular-nums">{overallWinRate}%</p>
            <p className="text-gray-500 text-xs mt-1">{data.totalWon} ganhos · {data.totalLost} perdidos</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">Deals ganhos</p>
            <p className="text-4xl font-black text-emerald-400 tabular-nums">{data.totalWon}</p>
            <p className="text-gray-500 text-xs mt-1">vitórias no histórico</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">Deals perdidos</p>
            <p className="text-4xl font-black text-red-400 tabular-nums">{data.totalLost}</p>
            <p className="text-gray-500 text-xs mt-1">derrotas no histórico</p>
          </div>
        </div>

        {/* ── 1. Ciclo de Fechamento ── */}
        <SectionCard
          title="Distribuição do Ciclo de Fechamento"
          tooltip="Mostra em quantos dias os deals são fechados. A maioria dos deals saudáveis fecha em menos de 90 dias. Deals que passam do limiar de risco têm probabilidade muito menor de fechar."
        >
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Chart */}
            <div className="flex-1 min-w-0">
              <BarChart
                data={data.cycleBuckets}
                valueKey="count"
                labelKey="label"
                color="blue"
              />
            </div>
            {/* Stat highlights */}
            <div className="flex flex-col gap-4 lg:w-64 shrink-0">
              <div className="bg-blue-500/10 border border-blue-500/25 rounded-xl p-5 text-center">
                <p className="text-blue-400 text-xs uppercase tracking-wider mb-1">Ciclo Médio</p>
                <p className="text-5xl font-black text-white tabular-nums">{data.avgCycleDays}</p>
                <p className="text-gray-400 text-sm mt-1">dias para fechar</p>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-5">
                <p className="text-amber-400 text-xs uppercase tracking-wider mb-2">⚠ Limiar de risco</p>
                <p className="text-3xl font-black text-amber-400 tabular-nums">{riskThreshold} dias</p>
                <p className="text-gray-400 text-xs mt-2 leading-relaxed">
                  Deals que ultrapassam esse prazo têm <span className="text-amber-300 font-semibold">chance muito reduzida</span> de fechar. Priorize ação imediata.
                </p>
              </div>
            </div>
          </div>
        </SectionCard>

        {/* ── 2. Sazonalidade — Closes por Mês ── */}
        <SectionCard
          title="Sazonalidade — Closes por Mês"
          tooltip="Em quais meses o time fecha mais negócios. Use para planejar cotas, antecipar prospecção nos meses fracos e concentrar esforço nos meses de pico."
        >
          <BarChart
            data={data.seasonality}
            valueKey="closes"
            labelKey="month"
            color="emerald"
            highlightIndex={top2ClosesIdx[0]}
          />
          <div className="flex flex-wrap gap-3 mt-4">
            {top2ClosesMonths.map((m) => (
              <PeakChip key={m.month} label="Pico de closes" value={`${m.month} — ${m.closes} fechamentos`} />
            ))}
          </div>
          <p className="text-gray-500 text-xs mt-3">
            Meses abaixo da média indicam períodos para intensificar prospecção e nutrir o pipeline antecipadamente.
          </p>
        </SectionCard>

        {/* ── 3. Receita por Mês ── */}
        <SectionCard
          title="Receita por Mês (deals ganhos)"
          tooltip="Soma do valor dos deals fechados por mês. Diferente do volume de closes — um GTK 500 pode valer mais que 10 deals menores. Use para entender quando o time gera mais caixa."
        >
          <BarChart
            data={data.seasonality}
            valueKey="revenue"
            labelKey="month"
            color="purple"
            formatValue={formatRevenue}
            highlightIndex={top2RevenueIdx[0]}
          />
          <div className="flex flex-wrap gap-3 mt-4">
            {top2RevenueMonths.map((m) => (
              <PeakChip key={m.month} label="Pico de receita" value={`${m.month} — ${formatRevenue(m.revenue)}`} />
            ))}
          </div>
        </SectionCard>

        {/* ── 4. Performance por Produto ── */}
        <SectionCard
          title="Performance por Produto"
          tooltip="Ranking dos produtos ordenado por receita gerada. Win rate alto + receita alta = produto estrela. Win rate baixo + receita alta = oportunidade para melhorar o processo."
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 pr-3 text-gray-500 font-medium w-8">#</th>
                  <th className="text-left py-2 pr-4 text-gray-400 font-medium">Produto</th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">
                    Preço
                    <InfoTooltip text="Valor médio do produto (ticket)." />
                  </th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">
                    Ganhos
                    <InfoTooltip text="Número de deals Won com este produto." />
                  </th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">
                    Perdidos
                    <InfoTooltip text="Número de deals Lost com este produto." />
                  </th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">
                    Win Rate
                    <InfoTooltip text="Ganhos ÷ (Ganhos + Perdidos). Quanto maior, mais fácil de vender este produto." />
                  </th>
                  <th className="text-right py-2 pl-4 text-gray-400 font-medium">Receita Total</th>
                </tr>
              </thead>
              <tbody>
                {data.products.map((p, i) => (
                  <tr key={p.name} className={`border-b border-gray-800/50 ${i % 2 === 0 ? "" : "bg-gray-900/20"}`}>
                    <td className="py-3 pr-3 text-gray-500 font-medium tabular-nums">{i + 1}</td>
                    <td className="py-3 pr-4 text-white font-medium">{p.name}</td>
                    <td className="py-3 px-4 text-right text-gray-400 tabular-nums">
                      ${p.price.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 tabular-nums font-medium">{p.won}</td>
                    <td className="py-3 px-4 text-right text-red-400 tabular-nums">{p.lost}</td>
                    <td className="py-3 px-4 text-right tabular-nums">
                      <span className={
                        p.winRate > 0.6 ? "text-emerald-400 font-semibold" :
                        p.winRate > 0.4 ? "text-amber-400" : "text-red-400"
                      }>
                        {(p.winRate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 pl-4 text-right text-gray-300 tabular-nums font-medium">
                      {formatRevenue(p.revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        {/* ── 5. Sazonalidade por Produto — Tabela Trimestral ── */}
        <SectionCard
          title="Melhor época de venda por produto (Top 3)"
          tooltip="Mostra em qual trimestre do ano cada produto é mais vendido. Verde = trimestre forte, cinza = fraco. Use para saber quando intensificar cada produto na carteira."
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 pr-6 text-gray-400 font-medium">Produto</th>
                  {quarters.map((q) => (
                    <th key={q.label} className="text-center py-2 px-3 text-gray-400 font-medium whitespace-nowrap">
                      {q.label}
                    </th>
                  ))}
                  <th className="text-center py-2 pl-4 text-gray-400 font-medium">Pico</th>
                </tr>
              </thead>
              <tbody>
                {data.productSeasonality.map((ps) => {
                  const qTotals = quarters.map((q) =>
                    q.months.reduce((sum, m) => sum + (ps.monthly[m]?.closes ?? 0), 0)
                  );
                  const maxQ = Math.max(...qTotals);
                  const peakMonth = ps.monthly.reduce((a, b) => (b.closes > a.closes ? b : a));
                  return (
                    <tr key={ps.product} className="border-b border-gray-800/50">
                      <td className="py-3 pr-6 text-white font-medium">{ps.product}</td>
                      {qTotals.map((total, qi) => (
                        <td key={qi} className="py-3 px-3 text-center tabular-nums">
                          {total === maxQ ? (
                            <span className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-400 font-semibold px-2.5 py-0.5 rounded-full text-xs">
                              {total} closes ★
                            </span>
                          ) : (
                            <span className="text-gray-500">{total}</span>
                          )}
                        </td>
                      ))}
                      <td className="py-3 pl-4 text-center text-amber-400 font-semibold text-xs">
                        {peakMonth.month}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-gray-500 text-xs mt-4">
            ★ = trimestre de maior volume para aquele produto. Use para planejar campanhas e esforço de prospecção no momento certo.
          </p>
        </SectionCard>

        {/* ── 6. Top Vendedores ── */}
        <SectionCard
          title="Top Vendedores por Win Rate"
          tooltip="Ranking dos vendedores com pelo menos 10 deals encerrados. Vendedores com win rate alto têm padrões que valem ser estudados e ensinados ao time inteiro."
        >
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mb-5 p-4 bg-gray-950/60 rounded-xl border border-gray-800/60 text-xs text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500" /> Win Rate ≥ 60% — Excelente
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500" /> 40–59% — Regular
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500" /> &lt; 40% — Precisa de suporte
            </span>
            <span className="ml-auto text-gray-500 italic">
              Win Rate = deals ganhos ÷ total de deals encerrados
            </span>
          </div>

          <div className="space-y-3">
            {data.topAgents.map((agent, i) => (
              <div key={agent.name} className="flex items-center gap-3">
                {/* Rank */}
                <span className={`text-sm w-6 text-right font-bold tabular-nums shrink-0 ${
                  i === 0 ? "text-yellow-400" : i === 1 ? "text-gray-300" : i === 2 ? "text-amber-600" : "text-gray-600"
                }`}>
                  {i + 1}
                </span>
                {/* Name */}
                <span className="text-white text-sm w-44 truncate shrink-0">{agent.name}</span>
                {/* Bar */}
                <div className="flex-1 h-2.5 rounded-full bg-gray-800 min-w-0">
                  <div
                    className={`h-full rounded-full transition-all ${
                      agent.winRate > 0.6 ? "bg-emerald-500" :
                      agent.winRate > 0.4 ? "bg-amber-500" : "bg-red-500"
                    }`}
                    style={{ width: `${agent.winRate * 100}%` }}
                  />
                </div>
                {/* Win rate % */}
                <span className={`text-sm tabular-nums font-bold w-12 text-right shrink-0 ${
                  agent.winRate > 0.6 ? "text-emerald-400" :
                  agent.winRate > 0.4 ? "text-amber-400" : "text-red-400"
                }`}>
                  {(agent.winRate * 100).toFixed(0)}%
                </span>
                {/* Wins / Losses */}
                <div className="text-xs text-right shrink-0 w-32">
                  <span className="text-emerald-400 font-semibold">{agent.won} vitórias</span>
                  <span className="text-gray-600 mx-1">/</span>
                  <span className="text-red-400">{agent.lost} derrotas</span>
                </div>
              </div>
            ))}
          </div>

          <p className="text-gray-600 text-xs mt-5 border-t border-gray-800/60 pt-4">
            Somente vendedores com pelo menos 10 deals encerrados aparecem neste ranking, para evitar distorção por amostras pequenas.
          </p>
        </SectionCard>

        {/* ── 7. Performance por Região ── */}
        {data.regions.length > 0 && (
          <>
            <SectionCard
              title="Performance por Região"
              tooltip="Compara receita, volume e win rate por regional. Ajuda a identificar onde o time está performando melhor e onde concentrar esforços de coaching ou prospecção."
            >
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-2 pr-6 text-gray-400 font-medium">Região</th>
                      <th className="text-right py-2 px-4 text-gray-400 font-medium">
                        Ganhos
                        <InfoTooltip text="Número de deals Won nessa região." />
                      </th>
                      <th className="text-right py-2 px-4 text-gray-400 font-medium">
                        Perdidos
                        <InfoTooltip text="Número de deals Lost nessa região." />
                      </th>
                      <th className="text-right py-2 px-4 text-gray-400 font-medium">
                        Win Rate
                        <InfoTooltip text="Ganhos ÷ (Ganhos + Perdidos). Indica a eficiência do time nessa região." />
                      </th>
                      <th className="text-right py-2 pl-4 text-gray-400 font-medium">
                        Receita Total
                        <InfoTooltip text="Soma do valor dos deals ganhos nessa região." />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.regions.map((r, i) => (
                      <tr key={r.name} className={`border-b border-gray-800/50 ${i % 2 === 0 ? "" : "bg-gray-900/20"}`}>
                        <td className="py-3 pr-6">
                          <span className="text-white font-semibold">{r.name}</span>
                          <span className="text-gray-500 text-xs ml-2">{r.total} deals encerrados</span>
                        </td>
                        <td className="py-3 px-4 text-right text-emerald-400 tabular-nums font-medium">{r.won}</td>
                        <td className="py-3 px-4 text-right text-red-400 tabular-nums">{r.lost}</td>
                        <td className="py-3 px-4 text-right tabular-nums">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-20 h-1.5 rounded-full bg-gray-800 hidden sm:block">
                              <div
                                className={`h-full rounded-full ${r.winRate > 0.6 ? "bg-emerald-500" : r.winRate > 0.4 ? "bg-amber-500" : "bg-red-500"}`}
                                style={{ width: `${r.winRate * 100}%` }}
                              />
                            </div>
                            <span className={`font-bold ${r.winRate > 0.6 ? "text-emerald-400" : r.winRate > 0.4 ? "text-amber-400" : "text-red-400"}`}>
                              {(r.winRate * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-3 pl-4 text-right text-gray-300 tabular-nums font-semibold">
                          {formatRevenue(r.revenue)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>

            {/* Region Seasonality */}
            <SectionCard
              title="Sazonalidade por Região — Quando cada região vende mais"
              tooltip="Mostra em qual trimestre cada região fecha mais negócios. Use para planejar ações regionais no momento certo — campanhas, reforço de equipe, metas por período."
            >
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-2 pr-6 text-gray-400 font-medium">Região</th>
                      {[
                        { label: "Q1 Jan–Mar", months: [0,1,2] },
                        { label: "Q2 Abr–Jun", months: [3,4,5] },
                        { label: "Q3 Jul–Set", months: [6,7,8] },
                        { label: "Q4 Out–Dez", months: [9,10,11] },
                      ].map((q) => (
                        <th key={q.label} className="text-center py-2 px-3 text-gray-400 font-medium whitespace-nowrap">
                          {q.label}
                        </th>
                      ))}
                      <th className="text-center py-2 pl-4 text-gray-400 font-medium">Pico</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.regionSeasonality.map((rs) => {
                      const qDefs = [
                        { label: "Q1 Jan–Mar", months: [0,1,2] },
                        { label: "Q2 Abr–Jun", months: [3,4,5] },
                        { label: "Q3 Jul–Set", months: [6,7,8] },
                        { label: "Q4 Out–Dez", months: [9,10,11] },
                      ];
                      const qTotals = qDefs.map((q) =>
                        q.months.reduce((sum, m) => sum + (rs.monthly[m]?.closes ?? 0), 0)
                      );
                      const maxQ = Math.max(...qTotals);
                      const peakMonth = rs.monthly.reduce((a, b) => (b.closes > a.closes ? b : a));
                      return (
                        <tr key={rs.region} className="border-b border-gray-800/50">
                          <td className="py-3 pr-6 text-white font-medium">{rs.region}</td>
                          {qTotals.map((total, qi) => (
                            <td key={qi} className="py-3 px-3 text-center tabular-nums">
                              {total === maxQ && total > 0 ? (
                                <span className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-400 font-semibold px-2.5 py-0.5 rounded-full text-xs">
                                  {total} closes ★
                                </span>
                              ) : (
                                <span className="text-gray-500">{total}</span>
                              )}
                            </td>
                          ))}
                          <td className="py-3 pl-4 text-center text-amber-400 font-semibold text-xs">
                            {peakMonth.closes > 0 ? peakMonth.month : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-gray-500 text-xs mt-4">
                ★ = trimestre de maior volume para aquela região. Use para reforçar prospecção e campanhas no período certo.
              </p>
            </SectionCard>
          </>
        )}

        {/* ── 8. Setor — win rate e receita por setor ── */}
        <SectionCard
          title="Performance por Setor"
          tooltip="Win rate e receita agrupados por setor da conta. Setores com win rate acima da média são alvos prioritários para prospecção."
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                  <th className="text-left py-2">Setor</th>
                  <th className="text-center py-2">Win Rate</th>
                  <th className="text-right py-2">Deals</th>
                  <th className="text-right py-2">Receita</th>
                </tr>
              </thead>
              <tbody>
                {data.sectors.map((s) => (
                  <tr key={s.name} className="border-b border-gray-800/40">
                    <td className="py-2 text-gray-200 capitalize">{s.name}</td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-800 rounded-full h-1.5 min-w-[60px]">
                          <div
                            className={`h-1.5 rounded-full ${s.winRate > 0.64 ? "bg-emerald-500" : s.winRate > 0.61 ? "bg-blue-500" : "bg-amber-500"}`}
                            style={{ width: `${(s.winRate * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-semibold tabular-nums ${s.winRate > 0.64 ? "text-emerald-400" : s.winRate > 0.61 ? "text-blue-400" : "text-amber-400"}`}>
                          {(s.winRate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2 text-right text-gray-400 tabular-nums">{s.total}</td>
                    <td className="py-2 text-right text-gray-300 tabular-nums">{formatRevenue(s.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-gray-500 text-xs mt-3">
            Spread de win rate entre setores é pequeno (61–65%) — o setor sozinho não prediz o resultado, mas ajuda a priorizar contas similares.
          </p>
        </SectionCard>

        {/* ── 9. País — win rate e volume ── */}
        <SectionCard
          title="Performance por País"
          tooltip="Países com maior volume de deals e win rate. Use para identificar onde concentrar esforços de expansão e onde a equipe já tem tração."
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                  <th className="text-left py-2">País</th>
                  <th className="text-center py-2">Win Rate</th>
                  <th className="text-right py-2">Deals</th>
                  <th className="text-right py-2">Receita</th>
                </tr>
              </thead>
              <tbody>
                {data.countries.map((c) => (
                  <tr key={c.name} className="border-b border-gray-800/40">
                    <td className="py-2 text-gray-200">{c.name}</td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-800 rounded-full h-1.5 min-w-[60px]">
                          <div
                            className={`h-1.5 rounded-full ${c.winRate > 0.66 ? "bg-emerald-500" : c.winRate > 0.60 ? "bg-blue-500" : "bg-amber-500"}`}
                            style={{ width: `${Math.min(100, c.winRate * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-semibold tabular-nums ${c.winRate > 0.66 ? "text-emerald-400" : c.winRate > 0.60 ? "text-blue-400" : "text-amber-400"}`}>
                          {(c.winRate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2 text-right text-gray-400 tabular-nums">{c.total}</td>
                    <td className="py-2 text-right text-gray-300 tabular-nums">{formatRevenue(c.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        {/* ── 10. Correlações ── */}
        <SectionCard
          title="Análise de Correlação"
          tooltip="Correlação entre características da conta e taxa de fechamento. Ajuda a entender quais tipos de conta têm mais chance de converter."
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Employee bracket */}
            <div>
              <p className="text-gray-400 text-sm font-semibold mb-3">Funcionários da conta × Win Rate</p>
              <div className="space-y-2">
                {data.empCorrelation.map((b) => (
                  <div key={b.label} className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-20 shrink-0">{b.label}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-blue-500"
                        style={{ width: `${(b.winRate * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 tabular-nums w-12 text-right">
                      {(b.winRate * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs text-gray-600 tabular-nums w-16 text-right">
                      {b.total} deals
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-gray-600 text-xs mt-3">Diferença máxima de ~5pp — tamanho da empresa tem impacto pequeno no resultado.</p>
            </div>

            {/* Subsidiary */}
            <div>
              <p className="text-gray-400 text-sm font-semibold mb-3">Subsidiária × Win Rate</p>
              <div className="space-y-2">
                {data.subsidiaryCorrelation.map((b) => (
                  <div key={b.label} className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-28 shrink-0">{b.label}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-purple-500"
                        style={{ width: `${(b.winRate * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 tabular-nums w-12 text-right">
                      {(b.winRate * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs text-gray-600 tabular-nums w-16 text-right">
                      {b.total} deals
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-gray-600 text-xs mt-3">Diferença de ~0.5pp — pertencer a um grupo maior não muda significativamente a probabilidade de fechar.</p>
            </div>
          </div>

          <div className="mt-5 bg-gray-800/40 rounded-xl p-4 border border-gray-700">
            <p className="text-xs text-gray-400 font-semibold mb-1">💡 Conclusão para o Score</p>
            <p className="text-xs text-gray-500 leading-relaxed">
              As correlações analisadas (setor, país, funcionários, subsidiária) mostram spread de win rate menor que 5%.
              Os maiores preditores de fechamento nesse dataset são: <span className="text-gray-300 font-medium">momentum do stage (dias em Engaging)</span>,
              <span className="text-gray-300 font-medium"> ticket do produto</span> e <span className="text-gray-300 font-medium">win rate histórico do vendedor</span>.
              Esses três fatores já compõem 75pts dos 100pts do score.
            </p>
          </div>
        </SectionCard>
      </main>
    </div>
  );
}
