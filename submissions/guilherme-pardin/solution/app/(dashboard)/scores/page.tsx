"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRightLeft,
  Flame,
  Snowflake,
  Trophy,
  Zap,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { SellerFilter } from "@/components/shared/SellerFilter";
import { GreetingHeader } from "@/components/scores/GreetingHeader";
import { ScoreSection } from "@/components/scores/ScoreSection";
import { Badge } from "@/components/ui/badge";
import { agentByName } from "@/lib/data";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  agentsForUser,
  dealsRecommendedForUser,
  scopedOpenDeals,
} from "@/lib/scope";
import { cn, formatMoney, formatPercent } from "@/lib/utils";

export default function ScoresPage() {
  const { user } = useAuth();
  const [sellerFilter, setSellerFilter] = useState<string>("__all");

  const isTeamView = user?.role !== "seller" && sellerFilter === "__all";

  const context = useMemo(() => {
    if (!user) return null;

    const baseline = scopedOpenDeals(user);
    let scoped = baseline;
    if (user.role !== "seller" && sellerFilter !== "__all") {
      scoped = baseline.filter((d) => d.currentAgent === sellerFilter);
    }

    const hot = scoped.filter((d) => d.tier === "hot");
    const warm = scoped.filter((d) => d.tier === "warm");
    const cold = scoped.filter((d) => d.tier === "cold");
    const atRisk = scoped.filter((d) => d.tier === "at_risk");

    let recommended: typeof scoped = [];
    let outOfZone: typeof scoped = [];
    if (user.role === "seller") {
      recommended = dealsRecommendedForUser(user);
      outOfZone = scoped.filter((d) => d.isReallocated);
    } else if (sellerFilter !== "__all") {
      recommended = baseline.filter(
        (d) =>
          d.optimalAgent === sellerFilter && d.currentAgent !== sellerFilter,
      );
      outOfZone = scoped.filter((d) => d.isReallocated);
    } else {
      outOfZone = baseline.filter((d) => d.isReallocated);
    }

    return {
      scoped,
      hot,
      warm,
      cold,
      atRisk,
      recommended,
      outOfZone,
      pipelineValue: scoped.reduce((s, d) => s + d.price, 0),
    };
  }, [user, sellerFilter]);

  if (!user || !context) return null;

  const teamAgents = user.role !== "seller" ? agentsForUser(user) : [];

  const agent =
    user.role === "seller"
      ? agentByName(user.name)
      : sellerFilter !== "__all"
        ? agentByName(sellerFilter)
        : null;

  const greetingName =
    user.role === "seller"
      ? user.name
      : sellerFilter !== "__all"
        ? sellerFilter
        : user.name;


  return (
    <div className="p-6 lg:p-8 space-y-5">
      <PageHeader
        title="Priorização"
        subtitle="Negociações ranqueadas por pontuação composta (0-100) e agrupadas por ação recomendada."
        action={
          user.role !== "seller" ? (
            <SellerFilter
              value={sellerFilter}
              onChange={setSellerFilter}
              agentPool={teamAgents}
              placeholder={
                user.role === "gestor" ? "Toda operação" : "Todo o seu time"
              }
            />
          ) : null
        }
      />

      <GreetingHeader
        name={greetingName}
        hotCount={context.hot.length}
        reallocatedCount={
          user.role === "seller"
            ? context.recommended.length
            : context.outOfZone.length
        }
        role={user.role}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiTile label="Quentes" value={context.hot.length} accent="text-emerald-700 bg-emerald-50" />
        <KpiTile label="Mornas" value={context.warm.length} accent="text-amber-700 bg-amber-50" />
        <KpiTile
          label="Frias + em risco"
          value={context.cold.length + context.atRisk.length}
          accent="text-slate-700 bg-slate-100"
        />
        <KpiTile
          label="Valor do pipeline"
          value={formatMoney(context.pipelineValue)}
          accent="text-blue-600 bg-blue-50"
        />
      </div>

      {agent && agent.sectors.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 mb-3">
            <Trophy className="h-4 w-4 text-blue-500" />
            <div className="text-sm font-semibold text-slate-900">
              Seus melhores setores
            </div>
            <div className="text-[11px] text-slate-400 ml-auto">
              baseado em {agent.totalClosed} negociações fechadas
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {agent.sectors.slice(0, 6).map((s) => (
              <Badge
                key={s.sector}
                variant="outline"
                className={cn(
                  "font-medium",
                  s.wr >= 0.75
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : s.wr >= 0.55
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-slate-50 text-slate-600",
                )}
              >
                {s.sector} · {formatPercent(s.wr)}{" "}
                <span className="text-[10px] font-normal opacity-70 ml-1">
                  ({s.deals})
                </span>
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        <ScoreSection
          title="Fechar agora"
          subtitle="Negociações quentes — prioridade máxima, ligar hoje, proposta na mesa."
          icon={<Flame className="h-4 w-4 text-emerald-600" />}
          accent="bg-emerald-50"
          deals={[...context.hot].sort((a, b) => b.score - a.score)}
          showAgent={isTeamView}
          emptyMessage="Sem negociações quentes no momento. Ótimo trabalho — mantenha as mornas aquecidas."
        />

        {(user.role === "seller" || sellerFilter !== "__all") && (
          <ScoreSection
            title="Recomendadas para você"
            subtitle="Vindas de outros vendedores. Você tem a melhor afinidade no setor."
            icon={<ArrowRightLeft className="h-4 w-4 text-blue-600" />}
            accent="bg-blue-50"
            deals={[...context.recommended].sort((a, b) => b.score - a.score)}
            showAgent
            emptyMessage="Sem recomendações no momento. Sua carteira está bem distribuída."
            defaultCollapsed={context.recommended.length === 0}
          />
        )}

        {isTeamView && (
          <ScoreSection
            title="Remanejamentos sugeridos"
            subtitle="Negociações que outro vendedor do time fecharia melhor. Revise antes de aprovar."
            icon={<ArrowRightLeft className="h-4 w-4 text-blue-600" />}
            accent="bg-blue-50"
            deals={[...context.outOfZone].sort((a, b) => b.score - a.score)}
            showAgent
          />
        )}

        <ScoreSection
          title="Nutrir com cadência"
          subtitle="Mornas — acompanhar a cada 2-3 dias. Envie case ou conteúdo relevante."
          icon={<Zap className="h-4 w-4 text-amber-600" />}
          accent="bg-amber-50"
          deals={[...context.warm].sort((a, b) => b.score - a.score)}
          showAgent={isTeamView}
        />

        {(user.role === "seller" || sellerFilter !== "__all") &&
          context.outOfZone.length > 0 && (
            <ScoreSection
              title="Fora da sua zona forte"
              subtitle="Negociações suas onde outro vendedor tem afinidade maior. Considere redirecionar."
              icon={<AlertTriangle className="h-4 w-4 text-amber-600" />}
              accent="bg-amber-50"
              deals={[...context.outOfZone].sort((a, b) => b.score - a.score)}
              defaultCollapsed
            />
          )}

        <ScoreSection
          title="Reengajar ou descartar"
          subtitle="Frias e em risco — última tentativa antes de arquivar."
          icon={<Snowflake className="h-4 w-4 text-slate-600" />}
          accent="bg-slate-100"
          deals={[...context.cold, ...context.atRisk].sort(
            (a, b) => b.score - a.score,
          )}
          showAgent={isTeamView}
          defaultCollapsed
        />
      </div>
    </div>
  );
}

function KpiTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-[var(--shadow-metric)]">
      <div
        className={cn(
          "inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium uppercase tracking-wide",
          accent,
        )}
      >
        {label}
      </div>
      <div className="text-2xl font-bold text-slate-900 tabular-nums mt-2">
        {value}
      </div>
    </div>
  );
}
