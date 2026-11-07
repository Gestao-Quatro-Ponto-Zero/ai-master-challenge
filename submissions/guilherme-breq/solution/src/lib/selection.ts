import type { AgentInfo, Deal } from "./data";
import { WINDOW_ALERT_DAYS } from "./scoring";

export interface Selection {
  region: string;
  manager: string;
  agent: string;
}

export const EMPTY_SELECTION: Selection = { region: "", manager: "", agent: "" };

const matches = (x: { region: string; manager: string }, s: Selection) =>
  (!s.region || x.region === s.region) && (!s.manager || x.manager === s.manager);

export function filterDeals(deals: Deal[], s: Selection): Deal[] {
  return deals.filter((d) => matches(d, s) && (!s.agent || d.agent === s.agent));
}

export function agentOptions(agents: AgentInfo[], s: Selection): AgentInfo[] {
  return agents.filter((a) => matches(a, s));
}

export interface Summary {
  open: number;
  live: number;
  windowClosing: number;
  zombies: number;
  zombieValue: number;
  /** Fração do pipeline engajado que é zumbi. */
  zombieShare: number;
  prospects: number;
  /** Número esperado de deals vivos que se decidem nos próximos 30 dias. */
  decide30Count: number;
  /** Valor de tabela esperado a ser decidido nos próximos 30 dias. */
  decide30Value: number;
}

export function summarize(deals: Deal[]): Summary {
  const s: Summary = {
    open: deals.length, live: 0, windowClosing: 0, zombies: 0, zombieValue: 0,
    zombieShare: 0, prospects: 0, decide30Count: 0, decide30Value: 0,
  };
  for (const d of deals) {
    if (d.status === "ativo") {
      s.live++;
      if ((d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS) s.windowClosing++;
      s.decide30Count += d.pDecide ?? 0;
      s.decide30Value += (d.pDecide ?? 0) * d.price;
    } else if (d.status === "zumbi") {
      s.zombies++;
      s.zombieValue += d.price;
    } else {
      s.prospects++;
    }
  }
  const engaged = s.live + s.zombies;
  s.zombieShare = engaged ? s.zombies / engaged : 0;
  return s;
}

export interface TeamRow extends AgentInfo {
  summary: Summary;
  topDeal: Deal | null;
}

/** Deals já vêm ordenados por prioridade, então o primeiro "ativo" de cada vendedor é o foco dele. */
export function teamRows(deals: Deal[], agents: AgentInfo[]): TeamRow[] {
  const byAgent = new Map<string, Deal[]>();
  for (const d of deals) byAgent.set(d.agent, [...(byAgent.get(d.agent) ?? []), d]);
  return agents
    .map((a) => {
      const own = byAgent.get(a.name) ?? [];
      return { ...a, summary: summarize(own), topDeal: own.find((d) => d.status === "ativo") ?? null };
    })
    .sort((x, y) => y.summary.decide30Value - x.summary.decide30Value || y.summary.open - x.summary.open);
}
