"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowRightLeft,
  Award,
  BarChart3,
  Crown,
  Layers,
  Lightbulb,
  Package,
  Table2,
  Target,
  TrendingDown,
  TrendingUp,
  Users,
} from "lucide-react";
import { HorizontalBar } from "@/components/dashboard/HorizontalBar";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { ReallocationTable } from "@/components/dashboard/ReallocationTable";
import {
  CollapsibleCard,
  PeopleFocus,
  RecommendationCard,
  type FocusPerson,
} from "@/components/shared/CollapsibleCard";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  agentsForUser,
  managerRankings,
  productPerformance,
  scopedAnalytics,
  scopedClosedDeals,
  scopedOpenDeals,
  sectorPerformance,
  sellerSpecMap,
  teamReallocationPlan,
  type SellerReallocPlan,
} from "@/lib/scope";
import { cn, formatMoney, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { user, hydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && user?.role === "seller") router.replace("/pipeline");
  }, [hydrated, user, router]);

  const context = useMemo(() => {
    if (!user || user.role === "seller") return null;
    const openDeals = scopedOpenDeals(user);
    const closedTeamDeals = scopedClosedDeals(user);
    const teamAgents = agentsForUser(user);
    const analytics = scopedAnalytics(user);
    const isGestor = user.role === "gestor";
    return {
      openDeals,
      closedTeamDeals,
      teamAgents,
      analytics,
      isGestor,
      mgrRankings: isGestor ? managerRankings() : [],
      sectors: sectorPerformance(user, isGestor ? 30 : 15),
      products: isGestor ? productPerformance(user, 30) : [],
      spec: !isGestor ? sellerSpecMap(user) : [],
      reallocPlan: !isGestor ? teamReallocationPlan(user) : [],
    };
  }, [user]);

  if (!user || !context || user.role === "seller") return null;

  const {
    openDeals,
    teamAgents,
    analytics,
    isGestor,
    mgrRankings,
    sectors,
    products,
    spec,
    reallocPlan,
  } = context;

  const reallocated = openDeals.filter((d) => d.isReallocated);
  const reallocatedValue = reallocated.reduce((s, d) => s + d.price, 0);
  const totalOpen = openDeals.length;
  const overallTeamWr =
    analytics.conversion.wonDealCount /
    Math.max(
      analytics.conversion.wonDealCount + analytics.losses.lostDealCount,
      1,
    );

  const maxDelta =
    reallocated.length > 0
      ? Math.max(
          ...reallocated.map((d) => d.optimalAgentWr - d.currentAgentWr),
        )
      : 0;

  const worstManager = mgrRankings
    .slice()
    .sort((a, b) => b.reallocations - a.reallocations)[0];

  const gestorRecs = isGestor
    ? buildGestorRecommendations({
        reallocatedValue,
        reallocatedCount: reallocated.length,
        maxDelta,
        sectors,
        products,
        worstManager,
      })
    : [];

  const gerenteRecs = !isGestor
    ? buildGerenteRecommendations({
        spec,
        reallocPlan,
        overallTeamWr,
        maxDelta,
      })
    : [];

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <PageHeader
        title={isGestor ? "Painel gerencial" : "Painel do seu time"}
        subtitle={
          isGestor
            ? "A tese: reorganizar por especialização setorial é a maior alavanca disponível."
            : `Time de ${user.name} — como reorganizar por especialização setorial para fechar mais.`
        }
      />

      {/* SEÇÃO 1: FOCO AGORA — pessoas */}
      <section className="space-y-4">
        <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
          <span className="text-red-500">●</span>
          Foco agora
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-[var(--shadow-metric)]">
          <div className="flex items-baseline gap-2 mb-1">
            <div className="font-semibold text-slate-900">
              {isGestor
                ? "Gerentes que precisam da sua atenção"
                : "Vendedores que precisam da sua atenção"}
            </div>
            <div className="text-[11px] text-slate-500 ml-auto">
              {formatMoney(reallocatedValue)} · {reallocated.length}{" "}
              negociações desalinhadas ({formatPercent(reallocated.length / Math.max(totalOpen, 1))})
            </div>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            {isGestor
              ? "Cada gerente cuida do seu time. Foque nos que têm o maior desalinhamento setorial."
              : "Cada vendedor tem seu setor forte. Foque nos que estão recebendo leads fora dele."}
          </p>
          {isGestor ? (
            <GestorFocus
              rankings={mgrRankings}
              overallWr={overallTeamWr}
            />
          ) : (
            <GerenteFocus agents={teamAgents} openDeals={openDeals} />
          )}
        </div>
      </section>

      {/* SEÇÃO 2: RECOMENDAÇÕES */}
      {(isGestor ? gestorRecs : gerenteRecs).length > 0 && (
        <section className="space-y-4">
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
            <Lightbulb className="h-3 w-3 text-amber-500" />
            Recomendações
          </div>
          <RecommendationCard items={(isGestor ? gestorRecs : gerenteRecs).slice(0, 3)} />
        </section>
      )}

      {/* SEÇÃO 3: DADOS DE SUPORTE */}
      <section className="space-y-4">
        <div className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold flex items-center gap-1.5">
          <BarChart3 className="h-3 w-3 text-slate-400" />
          Dados de suporte
        </div>

        <div className="space-y-3">
          {isGestor && (
            <CollapsibleCard
              icon={<Layers className="h-4 w-4" />}
              title="Setores que mais vendem"
              hint={`top ${Math.min(6, sectors.length)} · receita fechada + melhor gerente`}
            >
              <GestorSectorTable sectors={sectors.slice(0, 6)} />
            </CollapsibleCard>
          )}

          {isGestor && products.length > 0 && (
            <CollapsibleCard
              icon={<Package className="h-4 w-4" />}
              title="Produtos que mais vendem"
              hint={`top ${Math.min(5, products.length)} · receita fechada`}
            >
              <ProductTable products={products.slice(0, 5)} />
            </CollapsibleCard>
          )}

          {!isGestor && (
            <CollapsibleCard
              icon={<Users className="h-4 w-4" />}
              title="Mapa de especialização do seu time"
              hint="ordenado por deals fora do setor"
            >
              <GerenteSpecTable rows={spec} />
            </CollapsibleCard>
          )}

          {isGestor && (
            <CollapsibleCard
              icon={<Crown className="h-4 w-4" />}
              title="Ranking completo de gerentes"
              hint={`${mgrRankings.length} gerentes · conversão média ponderada`}
            >
              <ManagerRankingTable rankings={mgrRankings} />
            </CollapsibleCard>
          )}

          <CollapsibleCard
            icon={<Award className="h-4 w-4" />}
            title={
              isGestor
                ? "Performance completa por setor"
                : "Performance de cada vendedor por setor"
            }
            hint={
              isGestor
                ? `${sectors.length} setores com histórico`
                : `${teamAgents.length} vendedores no time`
            }
          >
            {isGestor ? (
              <FullSectorList sectors={sectors} />
            ) : (
              <FullSellerSpec agents={teamAgents} />
            )}
          </CollapsibleCard>

          {isGestor && products.length > 0 && (
            <CollapsibleCard
              icon={<Package className="h-4 w-4" />}
              title="Performance de cada produto"
              hint={`${products.length} produtos com histórico`}
            >
              <FullProductList products={products} />
            </CollapsibleCard>
          )}

          <CollapsibleCard
            icon={<TrendingUp className="h-4 w-4" />}
            title="Análise de vendas fechadas"
            hint={`${analytics.conversion.wonDealCount} vendas · ${formatMoney(analytics.conversion.totalWonRevenue)} fechados`}
          >
            <ConversionAnalysis analytics={analytics} isGestor={isGestor} />
          </CollapsibleCard>

          <CollapsibleCard
            icon={<TrendingDown className="h-4 w-4" />}
            title="Análise de vendas perdidas"
            hint={`${analytics.losses.lostDealCount} perdidas · ${formatMoney(analytics.losses.totalLostRevenue)} de potencial`}
          >
            <LossAnalysis analytics={analytics} isGestor={isGestor} />
          </CollapsibleCard>

          <CollapsibleCard
            icon={<Table2 className="h-4 w-4" />}
            title="Tabela de remanejamentos"
            hint={`${reallocated.length} negociações · ordenadas pelo maior ganho potencial`}
          >
            {reallocated.length === 0 ? (
              <div className="text-center text-sm text-slate-400 py-6">
                Sem remanejamentos sugeridos no escopo atual.
              </div>
            ) : (
              <ReallocationTable deals={reallocated} />
            )}
          </CollapsibleCard>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Foco: people (Gestor & Gerente)
// ---------------------------------------------------------------------------

function GestorFocus({
  rankings,
  overallWr,
}: {
  rankings: ReturnType<typeof managerRankings>;
  overallWr: number;
}) {
  const scored = rankings
    .filter((r) => r.openDeals > 0)
    .map((r) => ({
      ...r,
      ratio: r.reallocations / Math.max(r.openDeals, 1),
    }));

  const critical: FocusPerson[] = [];
  const attention: FocusPerson[] = [];
  const healthy: string[] = [];

  const sorted = [...scored].sort((a, b) => b.reallocations - a.reallocations);
  const worstReallocations = sorted[0]?.reallocations ?? 0;

  for (const r of sorted) {
    const wrDelta = r.avgTeamWr - overallWr;
    const isCritical =
      r.reallocations >= worstReallocations * 0.9 &&
      r.reallocations > 130;
    const isAttention =
      !isCritical && r.reallocations > 100 && r.ratio > 0.27;

    if (isCritical) {
      critical.push({
        name: r.manager,
        subtitle: `— ${r.region}`,
        metrics: `${formatPercent(r.avgTeamWr)} conversão · ${r.reallocations} remanejamentos pendentes (${Math.round(r.ratio * 100)}% do time)`,
        context:
          wrDelta < -0.02
            ? "Time com maior desalinhamento setorial da operação."
            : "Volume elevado de negociações fora da zona forte dos vendedores.",
      });
    } else if (isAttention) {
      attention.push({
        name: r.manager,
        subtitle: `— ${r.region}`,
        metrics: `${formatPercent(r.avgTeamWr)} conversão · ${r.reallocations} remanejamentos pendentes`,
        context:
          "Alto volume de negociações fora da zona forte dos vendedores.",
      });
    } else {
      healthy.push(r.manager);
    }
  }

  return (
    <PeopleFocus
      critical={critical}
      attention={attention}
      healthy={healthy}
      healthyLabel="operando dentro do esperado"
      emptyAttention="Todos os gerentes com pipeline saudável."
    />
  );
}

function GerenteFocus({
  agents,
  openDeals,
}: {
  agents: ReturnType<typeof agentsForUser>;
  openDeals: ReturnType<typeof scopedOpenDeals>;
}) {
  const active = agents.filter((a) => a.openDeals > 0);
  const critical: FocusPerson[] = [];
  const attention: FocusPerson[] = [];
  const healthy: string[] = [];

  const primaryOffSectorBySeller = computePrimaryOffSectorBySeller(
    agents,
    openDeals,
  );

  for (const a of active) {
    const ratio = a.reallocatedOut / Math.max(a.openDeals, 1);
    const isCritical = a.reallocatedOut >= 25 || ratio > 0.5;
    const isAttention =
      !isCritical && (a.reallocatedOut >= 15 || ratio > 0.3);
    const bestSectorLabel =
      a.bestSector === "—"
        ? null
        : `${a.bestSector} (${formatPercent(a.bestSectorWr)})`;
    const offSectorInfo = primaryOffSectorBySeller.get(a.name);

    if (isCritical) {
      let context = "";
      if (bestSectorLabel && offSectorInfo) {
        context = `Converte ${formatPercent(a.bestSectorWr)} em ${a.bestSector}, mas ${Math.round(ratio * 100)}% dos deals são de outros setores.`;
      } else if (bestSectorLabel) {
        context = `${Math.round(ratio * 100)}% da carteira está em setores fora da zona forte.`;
      }
      critical.push({
        name: a.name,
        metrics: `${formatPercent(a.overallWr)} conversão · ${a.reallocatedOut} negociações fora da zona forte`,
        context,
      });
    } else if (isAttention) {
      let context = "";
      if (bestSectorLabel && offSectorInfo && offSectorInfo.sector) {
        context = `Forte em ${a.bestSector} (${formatPercent(a.bestSectorWr)}), mas recebendo leads de ${offSectorInfo.sector}${offSectorInfo.wr > 0 ? ` (${formatPercent(offSectorInfo.wr)})` : ""}.`;
      } else if (bestSectorLabel) {
        context = `Forte em ${a.bestSector} (${formatPercent(a.bestSectorWr)}), mas ${a.reallocatedOut} deals em outros setores.`;
      }
      attention.push({
        name: a.name,
        metrics: `${formatPercent(a.overallWr)} conversão · ${a.reallocatedOut} negociações fora da zona forte`,
        context,
      });
    } else {
      healthy.push(a.name);
    }
  }

  return (
    <PeopleFocus
      critical={critical}
      attention={attention}
      healthy={healthy}
      healthyLabel="alinhados aos setores fortes"
      emptyAttention="Todos os vendedores do seu time estão alinhados."
    />
  );
}

function computePrimaryOffSectorBySeller(
  agents: ReturnType<typeof agentsForUser>,
  openDeals: ReturnType<typeof scopedOpenDeals>,
): Map<string, { sector: string; wr: number }> {
  const result = new Map<string, { sector: string; wr: number }>();
  for (const a of agents) {
    const off = openDeals.filter(
      (d) => d.currentAgent === a.name && d.isReallocated,
    );
    if (off.length === 0) continue;
    const bySector = new Map<string, { count: number; wrSum: number }>();
    for (const d of off) {
      const cur = bySector.get(d.sector) ?? { count: 0, wrSum: 0 };
      cur.count += 1;
      cur.wrSum += d.currentAgentWr;
      bySector.set(d.sector, cur);
    }
    const top = Array.from(bySector.entries()).sort(
      (a, b) => b[1].count - a[1].count,
    )[0];
    if (top) {
      result.set(a.name, {
        sector: top[0],
        wr: top[1].wrSum / top[1].count,
      });
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Foco: tables (legacy — kept for Support section)
// ---------------------------------------------------------------------------

function GestorSectorTable({
  sectors,
}: {
  sectors: ReturnType<typeof sectorPerformance>;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-[var(--shadow-metric)]">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
        <Layers className="h-4 w-4 text-blue-500" />
        <div className="font-semibold text-slate-900 text-sm">
          Setores que mais vendem
        </div>
        <span className="text-[11px] text-slate-400 ml-auto">
          top {sectors.length} · receita fechada
        </span>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50/60 text-[10px] uppercase tracking-wide text-slate-500">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Setor</th>
            <th className="text-right px-3 py-2 font-medium">Receita fechada</th>
            <th className="text-right px-3 py-2 font-medium">Conversão</th>
            <th className="text-left px-4 py-2 font-medium">Melhor gerente</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {sectors.map((s) => (
            <tr key={s.sector}>
              <td className="px-4 py-2.5 text-slate-900 font-medium">
                {s.sector}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums font-medium text-slate-900">
                {formatMoney(s.wonRevenue)}
              </td>
              <td className="px-3 py-2.5 text-right">
                <Badge
                  variant="outline"
                  className={cn(
                    "tabular-nums font-medium",
                    s.conversionRate >= 0.65
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : s.conversionRate >= 0.55
                        ? "bg-blue-50 text-blue-700 border-blue-200"
                        : "bg-amber-50 text-amber-700 border-amber-200",
                  )}
                >
                  {formatPercent(s.conversionRate)}
                </Badge>
              </td>
              <td className="px-4 py-2.5 text-slate-700">
                {s.bestManager ? (
                  <span>
                    <b>{s.bestManager}</b>{" "}
                    <span className="text-[10px] text-slate-400 tabular-nums">
                      ({formatPercent(s.bestManagerWr ?? 0)})
                    </span>
                  </span>
                ) : (
                  <span className="text-slate-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductTable({
  products,
}: {
  products: ReturnType<typeof productPerformance>;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-[var(--shadow-metric)]">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
        <Package className="h-4 w-4 text-emerald-500" />
        <div className="font-semibold text-slate-900 text-sm">
          Produtos que mais vendem
        </div>
        <span className="text-[11px] text-slate-400 ml-auto">
          top {products.length} · receita fechada
        </span>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50/60 text-[10px] uppercase tracking-wide text-slate-500">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Produto</th>
            <th className="text-right px-3 py-2 font-medium">Receita fechada</th>
            <th className="text-right px-3 py-2 font-medium">Conversão</th>
            <th className="text-right px-4 py-2 font-medium">Vendas</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {products.map((p) => (
            <tr key={p.product}>
              <td className="px-4 py-2.5 text-slate-900 font-medium">
                {p.product}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums font-medium text-slate-900">
                {formatMoney(p.wonRevenue)}
              </td>
              <td className="px-3 py-2.5 text-right">
                <Badge
                  variant="outline"
                  className={cn(
                    "tabular-nums font-medium",
                    p.conversionRate >= 0.65
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : "bg-slate-50 text-slate-700 border-slate-200",
                  )}
                >
                  {formatPercent(p.conversionRate)}
                </Badge>
              </td>
              <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                {p.wonDeals}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GerenteSpecTable({
  rows,
}: {
  rows: ReturnType<typeof sellerSpecMap>;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-[var(--shadow-metric)]">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
        <Users className="h-4 w-4 text-blue-500" />
        <div className="font-semibold text-slate-900 text-sm">
          Mapa de especialização do seu time
        </div>
        <span className="text-[11px] text-slate-400 ml-auto">
          ordenado por deals fora do setor
        </span>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50/60 text-[10px] uppercase tracking-wide text-slate-500">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Vendedor</th>
            <th className="text-left px-3 py-2 font-medium">Melhor setor</th>
            <th className="text-right px-3 py-2 font-medium">Conversão</th>
            <th className="text-right px-4 py-2 font-medium">Deals fora</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => {
            const attention = r.offSector >= 15;
            return (
              <tr
                key={r.agent}
                className={attention ? "bg-amber-50/40" : undefined}
              >
                <td className="px-4 py-2.5 text-slate-900 font-medium">
                  {r.agent}
                </td>
                <td className="px-3 py-2.5 text-slate-700">
                  {r.bestSector === "—" ? (
                    <span className="text-slate-400">—</span>
                  ) : (
                    <>
                      <b>{r.bestSector}</b>{" "}
                      <span className="text-[10px] text-slate-400 tabular-nums">
                        ({formatPercent(r.bestSectorWr)})
                      </span>
                    </>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className="text-slate-700 tabular-nums font-medium">
                    {formatPercent(r.overallWr)}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <Badge
                    variant="outline"
                    className={cn(
                      "tabular-nums font-medium",
                      attention
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200",
                    )}
                  >
                    {r.offSector === 0 ? "✅ 0" : `⚠️ ${r.offSector}`}
                  </Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recomendações
// ---------------------------------------------------------------------------

function buildGestorRecommendations(args: {
  reallocatedValue: number;
  reallocatedCount: number;
  maxDelta: number;
  sectors: ReturnType<typeof sectorPerformance>;
  products: ReturnType<typeof productPerformance>;
  worstManager: ReturnType<typeof managerRankings>[number] | undefined;
}) {
  const list: { title: string; body: string }[] = [];
  const topSectors = args.sectors.slice(0, 3);
  if (topSectors.length > 0 && topSectors.every((s) => s.bestManager)) {
    const parts = topSectors
      .map((s) => `${s.bestManager} domina ${s.sector}`)
      .join(", ");
    list.push({
      title: "Organize times por setor dominante.",
      body: `${parts}. Distribuir leads por setor entre os gerentes aumenta a conversão. Impacto potencial da reorganização: ${formatMoney(args.reallocatedValue)}.`,
    });
  }
  if (args.worstManager && args.worstManager.reallocations > 0) {
    list.push({
      title: `Priorize o remanejamento no time de ${args.worstManager.manager}.`,
      body: `${args.worstManager.reallocations} negociações desalinhadas — a maior oportunidade de melhoria da operação. Conversão do time hoje: ${formatPercent(args.worstManager.avgTeamWr)}.`,
    });
  }
  const worstSector = [...args.sectors]
    .filter((s) => s.conversionRate > 0)
    .sort((a, b) => a.conversionRate - b.conversionRate)[0];
  if (worstSector) {
    list.push({
      title: `O setor ${worstSector.sector} tem a pior conversão (${formatPercent(worstSector.conversionRate)}).`,
      body: `É onde o gap entre vendedor atual e ideal mais penaliza. Concentre vendedores desse setor num time especializado e reduza distribuição indiscriminada de leads.`,
    });
  }
  return list.slice(0, 3);
}

function buildGerenteRecommendations(args: {
  spec: ReturnType<typeof sellerSpecMap>;
  reallocPlan: SellerReallocPlan[];
  overallTeamWr: number;
  maxDelta: number;
}) {
  const list: { title: string; body: string }[] = [];
  const topPlans = args.reallocPlan.slice(0, 2);
  for (const plan of topPlans) {
    const dests = plan.suggestions
      .slice(0, 2)
      .map(
        (s) =>
          `${s.sector} → ${s.targetAgent} (${formatPercent(s.targetWr)})`,
      );
    if (dests.length > 0) {
      list.push({
        title: `${plan.agent} deve focar em ${plan.bestSector} (${formatPercent(plan.bestSectorWr)}).`,
        body: `Mova ${plan.totalDeals} negociações (${formatMoney(plan.totalValue)}) para vendedores com melhor fit: ${dests.join(" · ")}.`,
      });
    }
  }
  if (args.maxDelta > 0.05) {
    const projected = args.overallTeamWr + args.maxDelta * 0.25;
    list.push({
      title: `Estimativa com remanejamento setorial: conversão do time sobe para ${formatPercent(Math.min(projected, 0.95))}.`,
      body: `Hoje o time converte ${formatPercent(args.overallTeamWr)}. Cada negociação redirecionada para o vendedor com melhor fit adiciona pontos percentuais. O potencial máximo por deal chega a +${Math.round(args.maxDelta * 100)} pp.`,
    });
  }
  return list.slice(0, 3);
}

// ---------------------------------------------------------------------------
// Support: rankings & analysis
// ---------------------------------------------------------------------------

function ManagerRankingTable({
  rankings,
}: {
  rankings: ReturnType<typeof managerRankings>;
}) {
  return (
    <div>
      <div className="grid grid-cols-6 gap-2 px-2 pb-2 text-[10px] uppercase tracking-wide text-slate-400">
        <div className="col-span-2">Gerente</div>
        <div className="text-right">Time</div>
        <div className="text-right">Receita fechada</div>
        <div className="text-right">Quentes</div>
        <div className="text-right">Remanej.</div>
      </div>
      <div className="space-y-1.5">
        {rankings.map((r) => (
          <div
            key={r.manager}
            className="grid grid-cols-6 gap-2 items-center px-2 py-2 rounded-md hover:bg-slate-50 text-sm"
          >
            <div className="col-span-2 flex items-center gap-2 min-w-0">
              <span className="text-slate-900 font-medium truncate">
                {r.manager}
              </span>
              <Badge
                variant="outline"
                className={cn(
                  "tabular-nums font-medium ml-auto shrink-0",
                  r.avgTeamWr >= 0.65
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : r.avgTeamWr >= 0.55
                      ? "bg-blue-50 text-blue-700 border-blue-200"
                      : "bg-amber-50 text-amber-700 border-amber-200",
                )}
              >
                {formatPercent(r.avgTeamWr)}
              </Badge>
            </div>
            <div className="text-right text-slate-600 tabular-nums">
              {r.agents}
            </div>
            <div className="text-right text-slate-900 font-medium tabular-nums">
              {formatMoney(r.totalRevenue)}
            </div>
            <div className="text-right text-emerald-600 font-medium tabular-nums">
              {r.hotDeals}
            </div>
            <div className="text-right text-blue-700 font-medium tabular-nums">
              {r.reallocations}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FullSectorList({
  sectors,
}: {
  sectors: ReturnType<typeof sectorPerformance>;
}) {
  return (
    <div className="space-y-1.5">
      {sectors.map((s) => (
        <div
          key={s.sector}
          className="grid grid-cols-4 gap-2 items-center px-2 py-2 rounded-md hover:bg-slate-50 text-sm border-b border-slate-100 last:border-0"
        >
          <div className="text-slate-900 font-medium">{s.sector}</div>
          <div className="text-right text-slate-900 tabular-nums font-medium">
            {formatMoney(s.wonRevenue)}
          </div>
          <div className="text-right">
            <Badge
              variant="outline"
              className={cn(
                "tabular-nums font-medium",
                s.conversionRate >= 0.65
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-slate-50 text-slate-700 border-slate-200",
              )}
            >
              {formatPercent(s.conversionRate)}
            </Badge>
          </div>
          <div className="text-right text-xs text-slate-500 truncate">
            {s.bestManager ? (
              <span>
                <b>{s.bestManager}</b>
              </span>
            ) : (
              "—"
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function FullSellerSpec({
  agents,
}: {
  agents: ReturnType<typeof agentsForUser>;
}) {
  return (
    <div className="space-y-3">
      {agents.map((a) => (
        <div
          key={a.name}
          className="rounded-lg border border-slate-100 bg-slate-50/40 p-3"
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-slate-900 text-sm">
              {a.name}
            </span>
            <span className="text-[11px] text-slate-500 tabular-nums">
              · geral {formatPercent(a.overallWr)} · {a.totalClosed} negociações
            </span>
            <span className="ml-auto text-[11px] text-blue-700 flex items-center gap-1">
              <ArrowRight className="h-3 w-3" />
              {a.reallocatedOut} deals para redirecionar
            </span>
          </div>
          {a.sectors.length === 0 ? (
            <div className="text-xs text-slate-400">
              Sem histórico suficiente por setor.
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {a.sectors.slice(0, 6).map((s) => (
                <Badge
                  key={s.sector}
                  variant="outline"
                  className={cn(
                    "font-medium text-[11px]",
                    s.wr >= 0.75
                      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                      : s.wr >= 0.55
                        ? "border-blue-200 bg-blue-50 text-blue-700"
                        : "border-slate-200 bg-slate-50 text-slate-600",
                  )}
                >
                  {s.sector} · {formatPercent(s.wr)}
                </Badge>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function FullProductList({
  products,
}: {
  products: ReturnType<typeof productPerformance>;
}) {
  return (
    <div className="space-y-1.5">
      {products.map((p) => (
        <div
          key={p.product}
          className="grid grid-cols-4 gap-2 items-center px-2 py-2 rounded-md text-sm border-b border-slate-100 last:border-0"
        >
          <div className="text-slate-900 font-medium">{p.product}</div>
          <div className="text-right text-slate-900 tabular-nums font-medium">
            {formatMoney(p.wonRevenue)}
          </div>
          <div className="text-right">
            <Badge
              variant="outline"
              className="bg-slate-50 text-slate-700 border-slate-200 tabular-nums font-medium"
            >
              {formatPercent(p.conversionRate)}
            </Badge>
          </div>
          <div className="text-right text-xs text-slate-500 tabular-nums">
            {p.wonDeals} vendas
          </div>
        </div>
      ))}
    </div>
  );
}

function ConversionAnalysis({
  analytics,
  isGestor,
}: {
  analytics: ReturnType<typeof scopedAnalytics>;
  isGestor: boolean;
}) {
  const maxSector = analytics.conversion.topSectorsByRevenue[0]?.revenue ?? 1;
  const maxProduct = analytics.conversion.topProductsByRevenue[0]?.revenue ?? 1;
  const maxAgent = analytics.conversion.topAgentsByRevenue[0]?.revenue ?? 1;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Receita fechada"
          value={formatMoney(analytics.conversion.totalWonRevenue)}
          hint={`${analytics.conversion.wonDealCount} vendas`}
        />
        <MetricCard
          label="Ticket médio"
          value={formatMoney(
            analytics.conversion.totalWonRevenue /
              Math.max(analytics.conversion.wonDealCount, 1),
          )}
        />
        <MetricCard
          label="Melhor setor"
          value={analytics.conversion.topSectorsByRevenue[0]?.key ?? "—"}
          hint={formatMoney(
            analytics.conversion.topSectorsByRevenue[0]?.revenue ?? 0,
          )}
        />
        <MetricCard
          label="Melhor produto"
          value={analytics.conversion.topProductsByRevenue[0]?.key ?? "—"}
          hint={formatMoney(
            analytics.conversion.topProductsByRevenue[0]?.revenue ?? 0,
          )}
        />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <RankingBlock
          title="Setores por receita"
          buckets={analytics.conversion.topSectorsByRevenue}
          max={maxSector}
          color="bg-blue-500"
        />
        <RankingBlock
          title="Produtos por receita"
          buckets={analytics.conversion.topProductsByRevenue}
          max={maxProduct}
          color="bg-emerald-500"
        />
        <RankingBlock
          title={isGestor ? "Vendedores por receita" : "Vendedores do seu time"}
          buckets={analytics.conversion.topAgentsByRevenue.slice(0, 10)}
          max={maxAgent}
          color="bg-indigo-500"
        />
      </div>
    </div>
  );
}

function LossAnalysis({
  analytics,
  isGestor,
}: {
  analytics: ReturnType<typeof scopedAnalytics>;
  isGestor: boolean;
}) {
  const maxLoss = analytics.losses.sectorsByLossRate[0]?.lossRate ?? 1;
  return (
    <div className="space-y-4">
      {analytics.losses.actionableInsights.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-4 space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Lightbulb className="h-4 w-4 text-amber-600" />
            Ações sugeridas para pós-venda
          </div>
          <ul className="space-y-1.5">
            {analytics.losses.actionableInsights.map((insight, i) => (
              <li
                key={i}
                className="text-sm text-slate-800 leading-relaxed pl-6 relative"
              >
                <span className="absolute left-0 top-0 text-amber-500">→</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <div className="font-semibold text-slate-900 text-sm mb-3">
            Setores com menor conversão
          </div>
          {analytics.losses.sectorsByLossRate.length === 0 ? (
            <div className="text-sm text-slate-400 py-6 text-center">
              Amostra insuficiente para análise setorial.
            </div>
          ) : (
            <div className="space-y-2">
              {analytics.losses.sectorsByLossRate.slice(0, 8).map((s) => (
                <HorizontalBar
                  key={s.sector}
                  label={s.sector}
                  value={s.lossRate}
                  max={maxLoss}
                  displayValue={formatPercent(s.lossRate)}
                  hint={`${s.lostDeals}/${s.totalClosed}`}
                  color="bg-red-500"
                />
              ))}
            </div>
          )}
        </div>
        <div>
          <div className="font-semibold text-slate-900 text-sm mb-3">
            Onde estão as perdas (setor × produto)
          </div>
          {analytics.losses.sectorProductPatterns.length === 0 ? (
            <div className="text-sm text-slate-400 py-6 text-center">
              Sem padrões suficientes para reportar.
            </div>
          ) : (
            <div className="space-y-1.5">
              {analytics.losses.sectorProductPatterns.map((p, i) => (
                <div
                  key={`${p.sector}-${p.product}-${i}`}
                  className="flex items-center justify-between text-sm py-1.5 border-b border-slate-100 last:border-0"
                >
                  <div>
                    <div className="text-slate-900 font-medium">
                      {p.sector}{" "}
                      <span className="text-slate-400 font-normal">·</span>{" "}
                      {p.product}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {p.lostDeals} perdidas · {formatMoney(p.lostValue)}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn(
                      "tabular-nums font-medium",
                      p.shareOfSectorLosses >= 0.3
                        ? "bg-red-50 text-red-700 border-red-200"
                        : "bg-slate-50 text-slate-600 border-slate-200",
                    )}
                  >
                    {(p.shareOfSectorLosses * 100).toFixed(0)}%
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      {analytics.losses.worstAgentBySector.length > 0 && (
        <div>
          <div className="font-semibold text-slate-900 text-sm mb-3">
            {isGestor
              ? "Vendedores com menor afinidade em setores problemáticos"
              : "Ajustes sugeridos no seu time"}
          </div>
          <div className="space-y-2">
            {analytics.losses.worstAgentBySector.map((w) => (
              <div
                key={w.sector}
                className="flex flex-wrap items-center gap-2 py-2 border-b border-slate-100 last:border-0"
              >
                <Badge
                  variant="outline"
                  className="bg-red-50 text-red-700 border-red-200"
                >
                  {w.sector}
                </Badge>
                <span className="text-sm text-slate-700">
                  <b>{w.worstAgent}</b>{" "}
                  <span className="text-red-600 tabular-nums text-xs">
                    {formatPercent(w.worstWr)}
                  </span>
                </span>
                <ArrowRightLeft className="h-3 w-3 text-slate-400" />
                <span className="text-sm text-slate-700">
                  <b>{w.bestAgent}</b>{" "}
                  <span className="text-emerald-600 tabular-nums text-xs">
                    {formatPercent(w.bestWr)}
                  </span>
                </span>
                <Badge
                  variant="outline"
                  className="ml-auto bg-blue-50 text-blue-700 border-blue-200 tabular-nums"
                >
                  +{(w.deltaPP * 100).toFixed(0)} pp
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RankingBlock({
  title,
  buckets,
  max,
  color,
}: {
  title: string;
  buckets: { key: string; revenue: number; deals: number }[];
  max: number;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-[var(--shadow-metric)]">
      <div className="font-semibold text-slate-900 text-sm mb-3">{title}</div>
      {buckets.length === 0 ? (
        <div className="text-sm text-slate-400 py-6 text-center">
          Amostra insuficiente.
        </div>
      ) : (
        <div className="space-y-2">
          {buckets.map((b) => (
            <HorizontalBar
              key={b.key}
              label={b.key}
              value={b.revenue}
              max={max}
              displayValue={formatMoney(b.revenue)}
              hint={`${b.deals} vendas`}
              color={color}
              labelWidth="w-24"
            />
          ))}
        </div>
      )}
    </div>
  );
}
