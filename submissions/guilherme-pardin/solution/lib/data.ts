import scoredDealsRaw from "./data/scored-deals.json";
import closedDealsRaw from "./data/closed-deals.json";
import teamDataRaw from "./data/team-data.json";
import analyticsRaw from "./data/analytics.json";
import metaRaw from "./data/meta.json";
import type {
  AgentProfile,
  Analytics,
  ClosedDeal,
  DatasetMeta,
  ManagerSummary,
  ScoredDeal,
  Tier,
} from "./types";

export const deals: ScoredDeal[] = scoredDealsRaw as ScoredDeal[];
export const closedDeals: ClosedDeal[] = closedDealsRaw as ClosedDeal[];
export const analytics: Analytics = analyticsRaw as Analytics;
export const agents: AgentProfile[] = (
  teamDataRaw as { agents: AgentProfile[]; managers: ManagerSummary[] }
).agents;
export const managers: ManagerSummary[] = (
  teamDataRaw as { agents: AgentProfile[]; managers: ManagerSummary[] }
).managers;
export const meta: DatasetMeta = metaRaw as DatasetMeta;

export const tierOrder: Tier[] = ["hot", "warm", "cold", "at_risk"];

export const tierLabel: Record<Tier, string> = {
  hot: "Quente",
  warm: "Morno",
  cold: "Frio",
  at_risk: "Em risco",
};

export const tierEmoji: Record<Tier, string> = {
  hot: "🔥",
  warm: "⚡",
  cold: "❄️",
  at_risk: "⚠️",
};

export const tierCadence: Record<
  Tier,
  { cadence: string; approach: string }
> = {
  hot: {
    cadence: "Diária",
    approach:
      "Prioridade máxima — ligar hoje, proposta na mesa, ser assertivo.",
  },
  warm: {
    cadence: "A cada 2-3 dias",
    approach:
      "Acompanhar com follow-up estruturado. Envie um case ou conteúdo relevante.",
  },
  cold: {
    cadence: "Semanal",
    approach: "E-mail automatizado. Reavaliar em 15 dias.",
  },
  at_risk: {
    cadence: "Última tentativa",
    approach:
      "Ligar uma vez. Se não responder, redirecionar para outro vendedor ou descartar.",
  },
};

export function dealsForCurrentAgent(agent: string): ScoredDeal[] {
  return deals.filter((d) => d.currentAgent === agent);
}

export function dealsRecommendedForAgent(agent: string): ScoredDeal[] {
  return deals.filter(
    (d) => d.optimalAgent === agent && d.currentAgent !== agent,
  );
}

export function dealsAgentShouldLose(agent: string): ScoredDeal[] {
  return deals.filter(
    (d) => d.currentAgent === agent && d.isReallocated,
  );
}

export function agentByName(name: string): AgentProfile | undefined {
  return agents.find((a) => a.name === name);
}
