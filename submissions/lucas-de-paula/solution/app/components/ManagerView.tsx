"use client";

import { type ScoredDeal } from "@/lib/scoring";
import { ScoreBadge } from "./ScoreBadge";
import { InfoTooltip } from "./InfoTooltip";

interface ManagerViewProps {
  deals: ScoredDeal[];
  allDeals: ScoredDeal[]; // includes Won/Lost for win rate
}

interface AgentCard {
  agent: string;
  manager: string;
  activeDeals: number;
  avgScore: number;
  atRisk: number;
  won: number;
  lost: number;
  winRate: number;
}

function buildAgentCards(
  activeDeals: ScoredDeal[],
  allDeals: ScoredDeal[]
): AgentCard[] {
  const agents = new Map<string, AgentCard>();

  activeDeals.forEach((deal) => {
    const key = deal.sales_agent;
    if (!agents.has(key)) {
      agents.set(key, {
        agent: deal.sales_agent,
        manager: deal.manager,
        activeDeals: 0,
        avgScore: 0,
        atRisk: 0,
        won: 0,
        lost: 0,
        winRate: 0,
      });
    }
    const card = agents.get(key)!;
    card.activeDeals++;
    card.avgScore += deal.score;
    if (deal.deal_stage === "Engaging" && deal.days_in_stage > 30) {
      card.atRisk++;
    }
  });

  agents.forEach((card) => {
    if (card.activeDeals > 0) {
      card.avgScore = Math.round(card.avgScore / card.activeDeals);
    }
  });

  allDeals.forEach((deal) => {
    if (deal.deal_stage !== "Won" && deal.deal_stage !== "Lost") return;
    const key = deal.sales_agent;
    if (!agents.has(key)) return;
    const card = agents.get(key)!;
    if (deal.deal_stage === "Won") card.won++;
    else card.lost++;
  });

  agents.forEach((card) => {
    const total = card.won + card.lost;
    card.winRate = total > 0 ? card.won / total : 0;
  });

  return Array.from(agents.values()).sort((a, b) => b.winRate - a.winRate);
}

export function ManagerView({ deals, allDeals }: ManagerViewProps) {
  const cards = buildAgentCards(deals, allDeals);
  const totalAtRisk = cards.reduce((sum, c) => sum + c.atRisk, 0);
  const totalActive = cards.reduce((sum, c) => sum + c.activeDeals, 0);
  const avgTeamWinRate =
    cards.length > 0
      ? (cards.reduce((s, c) => s + c.winRate, 0) / cards.length) * 100
      : 0;

  return (
    <div className="space-y-10">

      {/* ── Painel: para que serve ── */}
      <div className="bg-blue-500/8 border border-blue-500/20 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="text-2xl mt-0.5">📋</div>
          <div className="flex-1">
            <h3 className="text-blue-300 font-semibold text-base mb-1">
              Como usar o Painel do Time
            </h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-3">
              Este painel é para <span className="text-white font-medium">gestores e líderes de vendas</span> acompanharem
              o desempenho individual de cada vendedor. Use-o para identificar quem está performando bem,
              quem tem deals em risco e onde concentrar coaching.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span className="text-gray-400">
                  <span className="text-white font-medium">Win Rate</span> — % de deals ganhos sobre o total encerrado. Vendedores acima de 60% são excelentes.
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">⚠</span>
                <span className="text-gray-400">
                  <span className="text-white font-medium">Em Risco</span> — deals em Engaging há mais de 30 dias sem fechar. Requer ação ou revisão imediata.
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">★</span>
                <span className="text-gray-400">
                  <span className="text-white font-medium">Score Médio</span> — média do lead score do pipeline ativo. Abaixo de 50 indica pipeline mal-qualificado.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── KPIs do time ── */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
          <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">Deals ativos no time</p>
          <p className="text-4xl font-black text-white tabular-nums">{totalActive}</p>
        </div>
        <div className={`bg-gray-900 rounded-2xl p-5 text-center ${totalAtRisk > 0 ? "border border-amber-500/40" : "border border-gray-800"}`}>
          <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 flex items-center justify-center gap-1">
            Em risco
            <InfoTooltip text="Deals em Engaging há mais de 30 dias. O ciclo médio é 52 dias — passando de 30, a chance de fechar cai significativamente." />
          </p>
          <p className={`text-4xl font-black tabular-nums ${totalAtRisk > 0 ? "text-amber-400" : "text-gray-600"}`}>
            {totalAtRisk}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
          <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 flex items-center justify-center gap-1">
            Win rate médio do time
            <InfoTooltip text="Média das win rates individuais de todos os vendedores." />
          </p>
          <p className="text-4xl font-black text-emerald-400 tabular-nums">
            {avgTeamWinRate.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* ── Ranking por Win Rate (TOPO) ── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-white font-semibold text-base">
            Ranking por Win Rate
          </h2>
          <InfoTooltip text="Win Rate = deals ganhos (Won) ÷ total de deals encerrados (Won + Perdidos). Representa a taxa de sucesso histórica do vendedor." />
        </div>

        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/80">
                <th className="text-left px-4 py-3 text-gray-400 font-medium w-10">#</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Vendedor</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Manager</th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium">
                  Vitórias
                  <InfoTooltip text="Total de deals Won (ganhos) no histórico." />
                </th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium">
                  Derrotas
                  <InfoTooltip text="Total de deals Lost (perdidos) no histórico." />
                </th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium">
                  Win Rate
                  <InfoTooltip text="Vitórias ÷ (Vitórias + Derrotas). Quanto maior, mais eficiente o vendedor." />
                </th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium">
                  Score Médio
                  <InfoTooltip text="Média do lead score do pipeline ativo deste vendedor." />
                </th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium">
                  Em Risco
                  <InfoTooltip text="Deals em Engaging há mais de 30 dias. Vermelho = atenção necessária." />
                </th>
              </tr>
            </thead>
            <tbody>
              {cards.map((card, idx) => (
                <tr
                  key={card.agent}
                  className={`
                    border-b border-gray-800/50 transition-colors
                    ${idx % 2 === 0 ? "bg-gray-950" : "bg-gray-900/30"}
                    hover:bg-gray-800/50
                  `}
                >
                  <td className="px-4 py-3 tabular-nums font-bold text-sm">
                    <span className={
                      idx === 0 ? "text-yellow-400" :
                      idx === 1 ? "text-gray-300" :
                      idx === 2 ? "text-amber-600" : "text-gray-600"
                    }>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white font-medium">
                    <div className="flex items-center gap-2">
                      {idx < 3 && (
                        <span className="text-base">
                          {idx === 0 ? "🥇" : idx === 1 ? "🥈" : "🥉"}
                        </span>
                      )}
                      {card.agent}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{card.manager}</td>
                  <td className="px-4 py-3 text-right text-emerald-400 tabular-nums font-medium">
                    {card.won}
                  </td>
                  <td className="px-4 py-3 text-right text-red-400 tabular-nums">
                    {card.lost}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    <span className={
                      card.winRate > 0.6 ? "text-emerald-400 font-semibold" :
                      card.winRate > 0.4 ? "text-amber-400" : "text-red-400"
                    }>
                      {(card.winRate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ScoreBadge score={card.avgScore} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {card.atRisk > 0 ? (
                      <span className="text-red-400 font-semibold">{card.atRisk}</span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend below ranking */}
        <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Win Rate ≥ 60% — Excelente
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> 40–59% — Regular
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> &lt; 40% — Precisa de atenção
          </span>
        </div>
      </div>

      {/* ── Alert banner ── */}
      {totalAtRisk > 0 && (
        <div className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
          <span className="text-2xl">⚠️</span>
          <div>
            <p className="text-amber-400 font-semibold">
              {totalAtRisk} deal{totalAtRisk > 1 ? "s" : ""} em risco no time
            </p>
            <p className="text-amber-400/70 text-sm mt-0.5">
              Deals em Engaging há mais de 30 dias sem fechar. Revise com cada vendedor e decida: avançar, nutrir ou encerrar.
            </p>
          </div>
        </div>
      )}

      {/* ── Agent cards (abaixo do ranking) ── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-white font-semibold text-base">Detalhes por Vendedor</h2>
          <InfoTooltip text="Cards individuais de cada vendedor com seus deals ativos, deals em risco e win rate histórico." />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cards.map((card, idx) => (
            <div
              key={card.agent}
              className="bg-gray-900 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-colors"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    {idx < 3 && (
                      <span className="text-base">
                        {idx === 0 ? "🥇" : idx === 1 ? "🥈" : "🥉"}
                      </span>
                    )}
                    <h3 className="text-white font-semibold">{card.agent}</h3>
                  </div>
                  <p className="text-gray-500 text-xs mt-0.5">{card.manager}</p>
                </div>
                <div className="text-right">
                  <ScoreBadge score={card.avgScore} size="sm" />
                  <p className="text-gray-600 text-[10px] mt-1">score médio</p>
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-800/50 rounded-xl p-3 text-center">
                  <div className="text-2xl font-black text-white tabular-nums">
                    {card.activeDeals}
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Deals ativos</div>
                </div>

                <div className={`rounded-xl p-3 text-center ${
                  card.atRisk > 0
                    ? "bg-red-500/10 border border-red-500/20"
                    : "bg-gray-800/50"
                }`}>
                  <div className={`text-2xl font-black tabular-nums ${
                    card.atRisk > 0 ? "text-red-400" : "text-gray-600"
                  }`}>
                    {card.atRisk}
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Em risco</div>
                </div>

                <div className="bg-gray-800/50 rounded-xl p-3 text-center">
                  <div className={`text-2xl font-black tabular-nums ${
                    card.winRate > 0.6 ? "text-emerald-400" :
                    card.winRate > 0.4 ? "text-amber-400" : "text-red-400"
                  }`}>
                    {(card.winRate * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Win rate</div>
                </div>
              </div>

              {/* Win rate bar */}
              <div>
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Histórico</span>
                  <span>
                    <span className="text-emerald-400">{card.won} vitórias</span>
                    <span className="mx-1">/</span>
                    <span className="text-red-400">{card.lost} derrotas</span>
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-800">
                  <div
                    className={`h-full rounded-full transition-all ${
                      card.winRate > 0.6 ? "bg-emerald-500" :
                      card.winRate > 0.4 ? "bg-amber-500" : "bg-red-500"
                    }`}
                    style={{ width: `${Math.min(100, card.winRate * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
