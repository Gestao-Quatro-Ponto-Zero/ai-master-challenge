"use client";

import {
  AlertTriangle,
  ArrowRightLeft,
  Building2,
  Calendar,
  CheckCircle2,
  DollarSign,
  Percent,
  Star,
  Target,
  User,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { tierCadence, tierEmoji, tierLabel } from "@/lib/data";
import type { ScoredDeal } from "@/lib/types";
import {
  avatarBg,
  cn,
  formatMoney,
  formatPercent,
  initials,
  stageLabel,
} from "@/lib/utils";
import { ScoreBar } from "./ScoreBar";
import { TierBadge } from "./TierBadge";

const DIMENSION_MAX = {
  stage: 25,
  agentFit: 25,
  dealValue: 20,
  productWr: 15,
  accountQuality: 10,
  seasonality: 5,
};

const DIMENSION_LABEL = {
  stage: "Estágio da negociação",
  agentFit: "Afinidade do vendedor",
  dealValue: "Valor da negociação",
  productWr: "Conversão do produto",
  accountQuality: "Qualidade da empresa",
  seasonality: "Sazonalidade",
};

export function DealDetailDrawer({
  deal,
  open,
  onOpenChange,
}: {
  deal: ScoredDeal | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!deal) return null;
  const cadence = tierCadence[deal.tier];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto p-0 shadow-[var(--shadow-drawer)]">
        <div className="p-6 pb-4 border-b border-slate-100 space-y-3">
          <SheetHeader className="p-0">
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  "h-11 w-11 shrink-0 rounded-lg grid place-items-center text-white font-semibold",
                  avatarBg(deal.account),
                )}
              >
                {initials(deal.account)}
              </div>
              <div className="flex-1 min-w-0">
                <SheetTitle className="text-lg leading-tight">
                  {deal.account}
                </SheetTitle>
                <SheetDescription className="mt-0.5">
                  {deal.product} · {deal.sector}
                </SheetDescription>
              </div>
            </div>
          </SheetHeader>

          <div className="flex items-center gap-2">
            <TierBadge tier={deal.tier} />
            <span className="text-2xl font-bold tabular-nums text-slate-900 ml-auto">
              {deal.score}
            </span>
            <span className="text-xs text-slate-400">/100</span>
          </div>
          <ScoreBar
            score={deal.score}
            tier={deal.tier}
            showLabel={false}
            className="mt-0"
          />
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <InfoTile
              icon={<DollarSign className="h-3.5 w-3.5" />}
              label="Valor"
              value={formatMoney(deal.price)}
            />
            <InfoTile
              icon={<Target className="h-3.5 w-3.5" />}
              label="Estágio"
              value={stageLabel[deal.stage] ?? deal.stage}
            />
            <InfoTile
              icon={<User className="h-3.5 w-3.5" />}
              label="Vendedor atual"
              value={deal.currentAgent}
            />
            <InfoTile
              icon={<Building2 className="h-3.5 w-3.5" />}
              label="Gerente"
              value={deal.manager}
            />
            {deal.engageDate && (
              <InfoTile
                icon={<Calendar className="h-3.5 w-3.5" />}
                label="Engajado em"
                value={deal.engageDate}
              />
            )}
            {deal.daysSinceEngage !== null && (
              <InfoTile
                icon={<Calendar className="h-3.5 w-3.5" />}
                label="Há"
                value={`${deal.daysSinceEngage} dias`}
              />
            )}
          </div>

          {deal.isReallocated && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-3.5 space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-blue-800">
                <ArrowRightLeft className="h-4 w-4" />
                Remanejamento sugerido
              </div>
              <p className="text-sm text-blue-800">
                <span className="font-medium">{deal.optimalAgent}</span> tem
                conversão de{" "}
                <span className="font-semibold">
                  {formatPercent(deal.optimalAgentWr)}
                </span>{" "}
                em <span className="font-medium">{deal.sector}</span>, contra{" "}
                <span className="font-semibold">
                  {formatPercent(deal.currentAgentWr)}
                </span>{" "}
                do vendedor atual.
              </p>
              <p className="text-[12px] text-blue-700">
                Ganho potencial: +
                {toPtDelta(deal.optimalAgentWr - deal.currentAgentWr)} p.p. na
                probabilidade de fechar.
              </p>
            </div>
          )}

          {!deal.isReallocated && deal.currentAgentWr > 0 && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3.5 flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5" />
              <p className="text-sm text-emerald-800">
                Vendedor atual é o mais indicado para {deal.sector}. Conversão
                histórica:{" "}
                <span className="font-semibold">
                  {formatPercent(deal.currentAgentWr)}
                </span>
                .
              </p>
            </div>
          )}

          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-900">
                Detalhamento da pontuação
              </div>
              <div className="text-[11px] text-slate-400">
                6 dimensões · 100 pts
              </div>
            </div>
            <div className="space-y-2 rounded-lg border border-slate-100 bg-slate-50 p-3">
              {(Object.keys(DIMENSION_MAX) as Array<keyof typeof DIMENSION_MAX>).map(
                (k) => {
                  const value = deal.breakdown[k];
                  const max = DIMENSION_MAX[k];
                  const pct = (value / max) * 100;
                  return (
                    <div key={k}>
                      <div className="flex items-center justify-between text-[12px] mb-0.5">
                        <span className="text-slate-600">{DIMENSION_LABEL[k]}</span>
                        <span className="tabular-nums text-slate-800 font-medium">
                          {value}
                          <span className="text-slate-400">/{max}</span>
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                },
              )}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-3.5 space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Star className="h-4 w-4 text-blue-500" />
              Cadência recomendada · {tierEmoji[deal.tier]}{" "}
              {tierLabel[deal.tier]} · {cadence.cadence}
            </div>
            <p className="text-sm text-slate-600">{cadence.approach}</p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-3.5 space-y-1.5">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Percent className="h-4 w-4 text-slate-500" />
              Histórico do vendedor
            </div>
            <div className="text-[13px] text-slate-600 space-y-0.5">
              <div>
                Conversão do vendedor em <b>{deal.sector}</b>:{" "}
                <span className="tabular-nums font-medium">
                  {formatPercent(deal.currentAgentWr)}
                </span>
              </div>
              <div>
                Melhor setor do vendedor: <b>{deal.bestSector}</b>{" "}
                <span className="text-slate-400">
                  ({formatPercent(deal.bestSectorWr)})
                </span>
              </div>
            </div>
            {deal.bestSector !== deal.sector &&
              deal.bestSectorWr > deal.currentAgentWr && (
                <div className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-amber-700">
                  <AlertTriangle className="h-3 w-3" />
                  Esta negociação está fora do setor mais forte do vendedor.
                </div>
              )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function toPtDelta(delta: number): string {
  return (delta * 100).toFixed(1).replace(".", ",");
}

function InfoTile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-slate-500">
        {icon}
        {label}
      </div>
      <div className="text-sm font-medium text-slate-900 mt-0.5 truncate">
        {value}
      </div>
    </div>
  );
}
