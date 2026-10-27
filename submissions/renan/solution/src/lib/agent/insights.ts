import { count, pct, usdCompact } from "@/lib/format";
import { applyFilters, dataset, history, pipeline, summarize, type Filters } from "@/lib/pipeline";

export type Severity = "alta" | "media" | "info";

export interface Insight {
  id: string;
  severity: Severity;
  title: string;
  detail: string;
  metric: string;
  /** Pergunta que o agente responde para aprofundar o alerta. */
  question: string;
  /** Página da Régua que mostra os deals do alerta. */
  href: string;
}

/** Janela de antecedência para avisar que um deal vai passar do maior ciclo histórico. */
const COOLING_WINDOW_DAYS = 14;

const query = (params: Record<string, string | undefined>) => {
  const q = new URLSearchParams(Object.entries(params).filter((e): e is [string, string] => Boolean(e[1])));
  return q.size ? `?${q}` : "";
};

/**
 * Radar: alertas calculados direto dos dados, sem IA. É o lado ativo do agente:
 * aparece sem ninguém perguntar e cada alerta vira uma pergunta pronta.
 */
export function buildInsights(scope: Pick<Filters, "agent" | "manager"> = {}): Insight[] {
  const deals = applyFilters(pipeline, scope);
  const { active, stalled } = summarize(deals);
  const who = scope.agent ?? (scope.manager ? `o time de ${scope.manager}` : "o time");
  const ofWho = scope.agent ? `de ${scope.agent}` : scope.manager ? `do time de ${scope.manager}` : "do time";
  const insights: Insight[] = [];

  const cooling = active.filter((s) => s.daysOpen !== null && s.daysOpen > history.maxCycle - COOLING_WINDOW_DAYS);
  if (cooling.length > 0) {
    const value = cooling.reduce((sum, s) => sum + s.expectedValue, 0);
    insights.push({
      id: "esfriando",
      severity: "alta",
      title: `${count(cooling.length)} deals passam de ${history.maxCycle} dias nos próximos ${COOLING_WINDOW_DAYS} dias`,
      detail: `Depois disso não há histórico de fechamento. Valor esperado em risco para ${who}.`,
      metric: usdCompact(value),
      question: `Quais deals ${ofWho} vão passar de ${history.maxCycle} dias nos próximos ${COOLING_WINDOW_DAYS} dias e o que fazer com cada um?`,
      href: `/pipeline${query({ vendedor: scope.agent, manager: scope.manager, momento: "closing" })}`,
    });
  }

  const closing = active.filter((s) => s.momentum === "closing");
  if (closing.length > 0) {
    const value = closing.reduce((sum, s) => sum + s.expectedValue, 0);
    insights.push({
      id: "reta-final",
      severity: "media",
      title: `${count(closing.length)} deals na reta final`,
      detail: `Entre ${history.wonP75Cycle} e ${history.maxCycle} dias: 75% dos ganhos já teriam fechado. É a hora de pedir o fechamento.`,
      metric: usdCompact(value),
      question: `Quais são os deals de maior valor esperado ${ofWho} na reta final?`,
      href: `/pipeline${query({ vendedor: scope.agent, manager: scope.manager, momento: "closing" })}`,
    });
  }

  if (stalled.length > 0) {
    const byProduct = new Map<string, number>();
    for (const s of stalled) byProduct.set(s.deal.product, (byProduct.get(s.deal.product) ?? 0) + s.deal.listPrice);
    const total = [...byProduct.values()].reduce((a, b) => a + b, 0);
    const [product, value] = [...byProduct].sort((a, b) => b[1] - a[1])[0];
    insights.push({
      id: "travado",
      severity: "media",
      title: `${pct(value / total)} do valor parado está em ${product}`,
      detail: `${count(stalled.length)} deals ${ofWho} passaram de ${history.maxCycle} dias. Revisar ou desqualificar limpa a previsão.`,
      metric: usdCompact(total),
      question: `Quais deals parados de ${product} ${ofWho} têm mais valor travado?`,
      href: `/parados${query({ vendedor: scope.agent, manager: scope.manager, produto: product })}`,
    });
  }

  if (!scope.agent) {
    const agents = dataset.agents
      .filter((a) => !scope.manager || a.manager === scope.manager)
      .map((a) => ({ name: a.name, ...summarize(deals.filter((s) => s.deal.agent === a.name)) }))
      .filter((a) => a.active.length + a.stalled.length >= 20);
    const worst = agents.sort((a, b) => b.stalledValueShare - a.stalledValueShare)[0];
    if (worst) {
      insights.push({
        id: "higiene",
        severity: "info",
        title: `${worst.name} tem ${pct(worst.stalledValueShare)} do pipeline parado`,
        detail: "Maior parcela parada do recorte. É higiene de CRM, não desempenho: vale uma revisão conjunta da fila.",
        metric: `${count(worst.stalled.length)} parados`,
        question: `Quais deals parados de ${worst.name} revisar primeiro?`,
        href: `/parados${query({ vendedor: worst.name })}`,
      });
    }
  }

  const focus = active.slice(0, 20);
  const missing = focus.filter((s) => s.deal.account === null).length;
  if (missing > 0) {
    insights.push({
      id: "sem-conta",
      severity: "info",
      title: `${missing} dos ${focus.length} deals prioritários estão sem conta no CRM`,
      detail: "Sem conta, setor e porte ficam fora da análise e o histórico do cliente se perde.",
      metric: `${missing}/${focus.length}`,
      question: `Quais deals prioritários ${ofWho} estão sem conta cadastrada?`,
      href: `/pipeline${query({ vendedor: scope.agent, manager: scope.manager })}`,
    });
  }

  return insights;
}
