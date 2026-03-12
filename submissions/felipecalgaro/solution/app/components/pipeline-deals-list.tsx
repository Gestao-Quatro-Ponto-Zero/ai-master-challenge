"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import type { DealExplanationResponse } from "@/utils/deal-explanation";
import type { ScoreFactor } from "@/utils/deal-score";

export type PipelineDealView = {
  opportunityId: string;
  salesAgent: string;
  product: string;
  account: string;
  stage: string;
  score: number;
  rank: number;
  topPositiveFactors: ScoreFactor[];
  topNegativeFactors: ScoreFactor[];
};

type DealExplanationPanelProps = {
  deal: PipelineDealView;
  expanded: boolean;
};

type PipelineDealsListProps = {
  deals: PipelineDealView[];
};

function scoreTier(score: number): "Alta" | "Media" | "Baixa" {
  if (score >= 67) return "Alta";
  if (score >= 45) return "Media";
  return "Baixa";
}

function scoreTierStyles(score: number): string {
  const tier = scoreTier(score);

  if (tier === "Alta") {
    return "bg-emerald-100 text-emerald-800 border border-emerald-200";
  }

  if (tier === "Media") {
    return "bg-amber-100 text-amber-800 border border-amber-200";
  }

  return "bg-rose-100 text-rose-800 border border-rose-200";
}

function scoreBadgeStyles(score: number): string {
  const tier = scoreTier(score);

  if (tier === "Alta") {
    return "bg-emerald-700 text-white";
  }

  if (tier === "Media") {
    return "bg-amber-500 text-stone-950";
  }

  return "bg-rose-700 text-white";
}

function toFactorChip(factor: ScoreFactor): { text: string; tone: "good" | "risk" } {
  return {
    text: factor.label,
    tone: factor.signedImpact >= 0 ? "good" : "risk",
  };
}

function stageLabel(stage: string): string {
  const normalized = stage.trim().toLowerCase();

  if (normalized === "engaging") return "Engajamento";
  if (normalized === "prospecting") return "Prospecção";
  if (normalized === "won") return "Ganho";
  if (normalized === "lost") return "Perdido";

  return stage;
}

async function fetchExplanation(deal: PipelineDealView): Promise<DealExplanationResponse> {
  const response = await fetch("/api/deals/explanation", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      opportunityId: deal.opportunityId,
      salesAgent: deal.salesAgent,
      product: deal.product,
      account: deal.account,
      dealStage: deal.stage,
      score: deal.score,
      topPositiveFactors: deal.topPositiveFactors,
      topNegativeFactors: deal.topNegativeFactors,
    }),
  });

  if (!response.ok) {
    throw new Error("Não foi possivel carregar a explicação da IA.");
  }

  return (await response.json()) as DealExplanationResponse;
}

function explanationQueryKey(deal: PipelineDealView): (string | number)[] {
  return [
    "deal-explanation",
    deal.opportunityId,
    deal.score,
    deal.stage,
    deal.product,
    deal.account,
    deal.salesAgent,
  ];
}

function DealExplanationPanel({ deal, expanded }: DealExplanationPanelProps) {
  const explanationQuery = useQuery({
    queryKey: explanationQueryKey(deal),
    queryFn: () => fetchExplanation(deal),
    enabled: expanded,
  });

  if (!expanded) {
    return null;
  }

  return (
    <div
      className="mt-4 rounded-xl border border-stone-200 bg-stone-50 p-4"
      id={`explanation-${deal.opportunityId}`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
        Resumo da IA
      </p>

      {explanationQuery.isPending ? (
        <p className="mt-2 text-sm text-stone-600">Preparando explicação...</p>
      ) : null}

      {explanationQuery.isError ? (
        <p className="mt-2 text-sm text-rose-700">
          Servico de explicação temporariamente indisponivel.
        </p>
      ) : null}

      {explanationQuery.data ? (
        <div className="mt-2 space-y-3 text-sm text-stone-700">
          <p>{explanationQuery.data.summary}</p>
          <p className="rounded-lg bg-white px-3 py-2 text-stone-800">
            Proxima ação: {explanationQuery.data.nextAction}
          </p>
        </div>
      ) : null}
    </div>
  );
}

export function PipelineDealsList({ deals }: PipelineDealsListProps) {
  const queryClient = useQueryClient();

  const initiallyExpanded = useMemo(
    () => deals.slice(0, 1).map((deal) => deal.opportunityId),
    [deals],
  );

  const [expandedIds, setExpandedIds] = useState<string[]>(initiallyExpanded);

  useEffect(() => {
    setExpandedIds(initiallyExpanded);
  }, [initiallyExpanded]);

  useEffect(() => {
    const firstDeal = deals[0];
    if (!firstDeal) {
      return;
    }

    void queryClient.prefetchQuery({
      queryKey: explanationQueryKey(firstDeal),
      queryFn: () => fetchExplanation(firstDeal),
    });
  }, [deals, queryClient]);

  const toggleExplanation = (dealId: string) => {
    setExpandedIds((current) =>
      current.includes(dealId)
        ? current.filter((id) => id !== dealId)
        : [...current, dealId],
    );
  };

  return (
    <div className="space-y-4">
      {deals.map((deal) => {
        const expanded = expandedIds.includes(deal.opportunityId);
        const chips = [
          ...deal.topPositiveFactors.slice(0, 2),
          ...deal.topNegativeFactors.slice(0, 1),
        ].map(toFactorChip);

        return (
          <article
            className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm"
            key={deal.opportunityId}
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold text-stone-700">
                    #{deal.rank}
                  </span>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-semibold ${scoreTierStyles(deal.score)}`}
                  >
                    Prioridade {scoreTier(deal.score)}
                  </span>
                  <span className="rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-stone-700">
                    {stageLabel(deal.stage)}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-semibold text-stone-900">{deal.product}</h3>
                  <p className="text-sm text-stone-600">
                    {deal.account || "Conta desconhecida"} • {deal.opportunityId}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {chips.map((chip, index) => (
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${chip.tone === "good"
                        ? "bg-emerald-50 text-emerald-800"
                        : "bg-rose-50 text-rose-800"
                        }`}
                      key={`${deal.opportunityId}-chip-${index}`}
                    >
                      {chip.tone === "good" ? "+" : "-"} {chip.text}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={`rounded-xl px-3 py-2 text-sm font-semibold ${scoreBadgeStyles(deal.score)}`}
                >
                  {deal.score}
                </span>
                <button
                  aria-controls={`explanation-${deal.opportunityId}`}
                  aria-expanded={expanded}
                  className="rounded-xl border border-stone-300 px-3 py-2 text-sm font-medium text-stone-800 transition hover:border-stone-950 hover:text-stone-950"
                  onClick={() => toggleExplanation(deal.opportunityId)}
                  type="button"
                >
                  {expanded ? "Ocultar motivo" : "Mostrar motivo"}
                </button>
              </div>
            </div>

            <DealExplanationPanel deal={deal} expanded={expanded} />
          </article>
        );
      })}
    </div>
  );
}
