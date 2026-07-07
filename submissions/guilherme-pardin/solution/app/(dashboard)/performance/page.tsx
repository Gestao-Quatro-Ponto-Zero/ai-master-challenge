"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRightLeft,
  BarChart3,
  Calendar,
  Lightbulb,
  Snowflake,
  Trophy,
  Zap,
} from "lucide-react";
import { DealDetailDrawer } from "@/components/deals/DealDetailDrawer";
import { FunnelDealCard } from "@/components/deals/FunnelDealCard";
import { HorizontalBar } from "@/components/dashboard/HorizontalBar";
import {
  CollapsibleCard,
  RecommendationCard,
} from "@/components/shared/CollapsibleCard";
import { PageHeader } from "@/components/shared/PageHeader";
import { agentByName, deals, tierEmoji } from "@/lib/data";
import { useAuth } from "@/lib/hooks/useAuth";
import { formatMoney, formatPercent } from "@/lib/utils";
import type { ScoredDeal } from "@/lib/types";

export default function PerformancePage() {
  const { user, hydrated } = useAuth();
  const router = useRouter();
  const [selected, setSelected] = useState<ScoredDeal | null>(null);

  useEffect(() => {
    if (hydrated && user?.role !== "seller") router.replace("/pipeline");
  }, [hydrated, user, router]);

  const context = useMemo(() => {
    if (!user || user.role !== "seller") return null;
    const agent = agentByName(user.name);
    if (!agent) return null;
    const myDeals = deals.filter((d) => d.currentAgent === user.name);
    const outOfZone = myDeals.filter((d) => d.isReallocated);
    const strongSectors = agent.sectors
      .filter((s) => s.wr >= 0.6)
      .slice(0, 3);
    const weakSectors = agent.sectors
      .filter((s) => s.wr < 0.5)
      .sort((a, b) => a.wr - b.wr)
      .slice(0, 3);
    const bestSector = agent.sectors[0];
    const dealsInBestSector = bestSector
      ? myDeals.filter((d) => d.sector === bestSector.sector)
      : ([] as ScoredDeal[]);
    const dealsInWeakSectors = myDeals.filter((d) =>
      weakSectors.some((w) => w.sector === d.sector),
    );
    const warmInBest = dealsInBestSector.filter((d) => d.tier === "warm");
    const coldInWeak = dealsInWeakSectors.filter(
      (d) => d.tier === "cold" || d.tier === "at_risk",
    );

    return {
      agent,
      myDeals,
      outOfZone,
      strongSectors,
      weakSectors,
      bestSector,
      dealsInBestSector,
      dealsInWeakSectors,
      warmInBest,
      coldInWeak,
    };
  }, [user]);

  if (!user || user.role !== "seller" || !context) return null;

  const {
    agent,
    myDeals,
    outOfZone,
    strongSectors,
    weakSectors,
    bestSector,
    dealsInBestSector,
    dealsInWeakSectors,
    warmInBest,
    coldInWeak,
  } = context;

  const pipelineValue = myDeals.reduce((s, d) => s + d.price, 0);
  const maxSectorWr = agent.sectors[0]?.wr ?? 1;
  const hotDeals = myDeals
    .filter((d) => d.tier === "hot")
    .sort((a, b) => b.score - a.score);
  // If no hot deals, fall back to top-scored warm deals for focus
  const focusPool = hotDeals.length > 0 ? hotDeals : myDeals
    .filter((d) => d.tier === "warm")
    .sort((a, b) => b.score - a.score);
  // Prioritize deals in best sector at the top
  const topFocus = bestSector
    ? [
        ...focusPool.filter((d) => d.sector === bestSector.sector),
        ...focusPool.filter((d) => d.sector !== bestSector.sector),
      ].slice(0, 3)
    : focusPool.slice(0, 3);
  const dealsInWeakSectorsCount = dealsInWeakSectors.length;

  const recommendations: { title: string; body: string }[] = [];
  if (strongSectors.length > 0) {
    const list = strongSectors
      .map((s) => `${s.sector} (${formatPercent(s.wr)})`)
      .join(", ");
    recommendations.push({
      title: "Concentre sua energia nos setores fortes.",
      body: `Você fecha mais em ${list}. Priorize deals nesses setores — cada hora aqui rende mais que em setores fracos.`,
    });
  }
  if (warmInBest.length > 0 && bestSector) {
    recommendations.push({
      title: `${warmInBest.length} negociaç${warmInBest.length > 1 ? "ões mornas" : "ão morna"} no seu setor forte esperando follow-up.`,
      body: `Setor ${bestSector.sector} — sua conversão histórica é ${formatPercent(bestSector.wr)}. Reavive esses leads antes de esfriar.`,
    });
  }
  if (coldInWeak.length > 0) {
    recommendations.push({
      title: `${coldInWeak.length} negociações frias em setores fracos — redirecionar ou arquivar.`,
      body: `Esses deals têm baixa conversão histórica. Converse com seu gerente sobre remanejar ou arquive para focar no que fecha.`,
    });
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <PageHeader
        title="Meu desempenho"
        subtitle="Sua narrativa é setorial — foque onde você fecha, evite onde não fecha."
      />

      {/* SEÇÃO 1: FOCO AGORA — negociações prioritárias */}
      <section className="space-y-4">
        <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
          <span className="text-red-500">●</span>
          Foco agora
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-[var(--shadow-metric)]">
          <div className="flex items-baseline gap-2 mb-4">
            <div className="font-semibold text-slate-900">
              Negociações que precisam da sua atenção hoje
            </div>
            {bestSector && (
              <div className="text-[11px] text-slate-500 ml-auto">
                Seu melhor setor: <b>{bestSector.sector}</b>{" "}
                <span className="tabular-nums">
                  ({formatPercent(bestSector.wr)})
                </span>
              </div>
            )}
          </div>

          {topFocus.length === 0 ? (
            <div className="text-sm text-slate-500 py-3">
              Sem negociações quentes agora — foque em nutrir as mornas e
              reengajar as frias.
            </div>
          ) : (
            <div className="space-y-2">
              {topFocus.map((d, i) => (
                <FocusDealRow
                  key={d.id}
                  deal={d}
                  isBestSector={
                    !!bestSector && d.sector === bestSector.sector
                  }
                  position={i}
                  onClick={() => setSelected(d)}
                />
              ))}
            </div>
          )}

          {dealsInWeakSectorsCount > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-start gap-3">
              <span className="text-base leading-none pt-0.5">⚠️</span>
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-900">
                  {dealsInWeakSectorsCount} negociações em setores fora da sua
                  zona forte
                </div>
                <div className="text-xs text-slate-600 mt-0.5">
                  {weakSectors
                    .map((s) => `${s.sector} (${formatPercent(s.wr)})`)
                    .join(" · ")}
                  . Converse com seu gerente sobre redirecionar.
                </div>
              </div>
            </div>
          )}

          {outOfZone.length > 0 && (
            <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5">
              <ArrowRightLeft className="h-3 w-3 text-blue-500 shrink-0" />
              <span>
                O sistema já identificou <b>{outOfZone.length}</b> negociações
                suas com sugestão de remanejamento. Veja em{" "}
                <Link
                  href="/scores"
                  className="text-blue-600 font-medium underline"
                >
                  Priorização
                </Link>
                .
              </span>
            </div>
          )}
        </div>
      </section>

      {/* SEÇÃO 2: RECOMENDAÇÕES */}
      {recommendations.length > 0 && (
        <section className="space-y-4">
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
            <Lightbulb className="h-3 w-3 text-amber-500" />
            Recomendações
          </div>
          <RecommendationCard items={recommendations.slice(0, 3)} />
        </section>
      )}

      {/* SEÇÃO 3: DADOS DE SUPORTE */}
      <section className="space-y-4">
        <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
          <BarChart3 className="h-3 w-3 text-slate-400" />
          Dados de suporte
        </div>

        <div className="space-y-3">
          <CollapsibleCard
            icon={<Trophy className="h-4 w-4" />}
            title="Todos os meus setores com taxa de conversão"
            hint={`${agent.totalClosed} negociações fechadas · min. 10 por setor`}
          >
            {agent.sectors.length === 0 ? (
              <div className="text-sm text-slate-400 py-6 text-center">
                Ainda sem histórico suficiente para calcular afinidade por
                setor.
              </div>
            ) : (
              <div className="space-y-2.5">
                {agent.sectors.map((s) => (
                  <HorizontalBar
                    key={s.sector}
                    label={s.sector}
                    value={s.wr}
                    max={maxSectorWr}
                    displayValue={formatPercent(s.wr)}
                    hint={`${s.deals} negociações`}
                    color={
                      s.wr >= 0.75
                        ? "bg-emerald-500"
                        : s.wr >= 0.55
                          ? "bg-blue-500"
                          : "bg-slate-400"
                    }
                  />
                ))}
              </div>
            )}
          </CollapsibleCard>

          <CollapsibleCard
            icon={<AlertTriangle className="h-4 w-4" />}
            title="Negociações fora do setor forte"
            hint={`${outOfZone.length} negociações · ${formatMoney(outOfZone.reduce((s, d) => s + d.price, 0))} em jogo`}
          >
            {outOfZone.length === 0 ? (
              <div className="text-sm text-slate-400 py-6 text-center">
                Todas as suas negociações estão em setores alinhados ao seu
                perfil.
              </div>
            ) : (
              <DealGrid deals={outOfZone} onSelect={setSelected} />
            )}
          </CollapsibleCard>

          <CollapsibleCard
            icon={<Zap className="h-4 w-4" />}
            title="Todas as negociações mornas"
            hint={`${myDeals.filter((d) => d.tier === "warm").length} negociações`}
          >
            <DealGrid
              deals={myDeals
                .filter((d) => d.tier === "warm")
                .sort((a, b) => b.score - a.score)}
              onSelect={setSelected}
            />
          </CollapsibleCard>

          <CollapsibleCard
            icon={<Snowflake className="h-4 w-4" />}
            title="Todas as negociações frias e em risco"
            hint={`${myDeals.filter((d) => d.tier === "cold" || d.tier === "at_risk").length} negociações`}
          >
            <DealGrid
              deals={myDeals
                .filter((d) => d.tier === "cold" || d.tier === "at_risk")
                .sort((a, b) => b.score - a.score)}
              onSelect={setSelected}
            />
          </CollapsibleCard>

          <CollapsibleCard
            icon={<Calendar className="h-4 w-4" />}
            title="Meu perfil"
            hint={`${myDeals.length} abertas · ${formatMoney(pipelineValue)}`}
          >
            <div className="grid grid-cols-2 gap-3 text-sm">
              <ProfileRow
                label="Taxa de conversão"
                value={formatPercent(agent.overallWr)}
              />
              <ProfileRow
                label="Negociações fechadas"
                value={agent.totalClosed.toString()}
              />
              <ProfileRow label="Gerente" value={agent.manager} />
              <ProfileRow label="Região" value={agent.region} />
              <ProfileRow
                label="Melhor setor"
                value={
                  agent.bestSector === "—"
                    ? "—"
                    : `${agent.bestSector} · ${formatPercent(agent.bestSectorWr)}`
                }
              />
              <ProfileRow
                label="Distribuição atual"
                value={`🔥 ${agent.hotDeals} · ⚡ ${agent.warmDeals} · ❄️ ${agent.coldDeals} · ⚠️ ${agent.atRiskDeals}`}
              />
            </div>
          </CollapsibleCard>
        </div>
      </section>

      <DealDetailDrawer
        deal={selected}
        open={!!selected}
        onOpenChange={(o) => !o && setSelected(null)}
      />
    </div>
  );
}

function FocusDealRow({
  deal,
  isBestSector,
  position,
  onClick,
}: {
  deal: ScoredDeal;
  isBestSector: boolean;
  position: number;
  onClick: () => void;
}) {
  let context = "";
  if (isBestSector) {
    context = "Seu melhor setor. Ligar hoje.";
  } else if (position === 0) {
    context = "Alta pontuação — ligar hoje.";
  } else if (deal.daysSinceEngage !== null && deal.daysSinceEngage > 30) {
    context = "Deal antigo — fechar esta semana.";
  } else {
    context = "Fechar esta semana.";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left flex items-start gap-3 rounded-lg border border-slate-200 hover:border-blue-300 bg-white p-3 transition-colors duration-150 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-card-hover)]"
    >
      <span className="text-base leading-none pt-0.5">
        {tierEmoji[deal.tier]}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-900 truncate">
          <b>{deal.account}</b>{" "}
          <span className="text-slate-500">
            · {deal.product} · {deal.sector} ·{" "}
            <span className="tabular-nums font-medium text-slate-700">
              {formatMoney(deal.price)}
            </span>
          </span>
        </div>
        <div className="text-xs text-slate-600 mt-0.5">
          <span className="tabular-nums font-medium">
            Pontuação {deal.score}
          </span>{" "}
          — {context}
        </div>
      </div>
    </button>
  );
}

function DealGrid({
  deals,
  onSelect,
}: {
  deals: ScoredDeal[];
  onSelect: (d: ScoredDeal) => void;
}) {
  const [showAll, setShowAll] = useState(false);
  const limit = 6;
  const visible = showAll ? deals : deals.slice(0, limit);
  if (deals.length === 0) {
    return (
      <div className="text-sm text-slate-400 py-6 text-center">
        Sem negociações nesta categoria.
      </div>
    );
  }
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {visible.map((d) => (
          <FunnelDealCard
            key={d.id}
            deal={d}
            showAgent={false}
            onClick={() => onSelect(d)}
          />
        ))}
      </div>
      {deals.length > limit && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="mt-3 mx-auto block text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          {showAll ? "Mostrar menos" : `Ver todas as ${deals.length}`}
        </button>
      )}
    </>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 border border-slate-100 p-2.5">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="text-sm font-medium text-slate-900 mt-0.5 truncate">
        {value}
      </div>
    </div>
  );
}
