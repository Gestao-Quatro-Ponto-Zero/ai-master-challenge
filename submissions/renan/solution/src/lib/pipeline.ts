import analysisJson from "../../data/generated/analysis.json";
import datasetJson from "../../data/generated/dataset.json";
import type { Dataset } from "@/domain/types";
import { buildHistory } from "./scoring/history";
import { rankPipeline, type Momentum, type ScoredDeal } from "./scoring/score";

/*
 * Dados lidos no escopo do módulo: são os mesmos para toda requisição e
 * gerados no build (`npm run analyze`), então entram no shell estático.
 */
export const dataset = datasetJson as unknown as Dataset;
export const analysis = analysisJson;
export const history = buildHistory(dataset.deals);
export const pipeline: ScoredDeal[] = rankPipeline(dataset.deals, history, dataset.referenceDate);

const byId = new Map(pipeline.map((s) => [s.deal.id, s]));
export const findDeal = (id: string) => byId.get(id);

const sorted = (values: Iterable<string>) => [...new Set(values)].sort((a, b) => a.localeCompare(b, "pt-BR"));

export const options = {
  agents: sorted(pipeline.map((s) => s.deal.agent)),
  managers: sorted(dataset.agents.map((a) => a.manager)),
  offices: sorted(dataset.agents.map((a) => a.regionalOffice)),
  products: sorted(dataset.products.map((p) => p.name)),
};

export const MOMENTUM_ORDER: Momentum[] = ["prospecting", "early", "progressing", "closing", "stalled"];

export interface Filters {
  agent?: string;
  manager?: string;
  office?: string;
  product?: string;
  momentum?: Momentum;
  /** Busca livre por código do deal, conta, vendedor ou produto. */
  query?: string;
}

type RawParams = Record<string, string | string[] | undefined>;

const pick = (params: RawParams, key: string, allowed: readonly string[]) => {
  const value = params[key];
  const single = Array.isArray(value) ? value[0] : value;
  return single && allowed.includes(single) ? single : undefined;
};

const text = (params: RawParams, key: string) => {
  const value = params[key];
  const single = (Array.isArray(value) ? value[0] : value)?.trim();
  return single ? single.slice(0, 80) : undefined;
};

/** Lê filtros da URL, ignorando valores que não existem no dataset. */
export function parseFilters(params: RawParams): Filters {
  return {
    agent: pick(params, "vendedor", options.agents),
    manager: pick(params, "manager", options.managers),
    office: pick(params, "escritorio", options.offices),
    product: pick(params, "produto", options.products),
    momentum: pick(params, "momento", MOMENTUM_ORDER) as Momentum | undefined,
    query: text(params, "q"),
  };
}

export function applyFilters(deals: ScoredDeal[], f: Filters): ScoredDeal[] {
  const q = f.query?.toLocaleLowerCase("pt-BR");
  return deals.filter(
    (s) =>
      (!f.agent || s.deal.agent === f.agent) &&
      (!f.manager || s.deal.manager === f.manager) &&
      (!f.office || s.deal.regionalOffice === f.office) &&
      (!f.product || s.deal.product === f.product) &&
      (!f.momentum || s.momentum === f.momentum) &&
      (!q || [s.deal.id, s.deal.account ?? "", s.deal.agent, s.deal.product].some((v) => v.toLocaleLowerCase("pt-BR").includes(q))),
  );
}

/** Monta a query string dos filtros ativos (para links que preservam o contexto). */
export function filterQuery(f: Filters, extra: Record<string, string> = {}): string {
  const params = new URLSearchParams();
  if (f.agent) params.set("vendedor", f.agent);
  if (f.manager) params.set("manager", f.manager);
  if (f.office) params.set("escritorio", f.office);
  if (f.product) params.set("produto", f.product);
  if (f.momentum) params.set("momento", f.momentum);
  if (f.query) params.set("q", f.query);
  for (const [k, v] of Object.entries(extra)) params.set(k, v);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function summarize(deals: ScoredDeal[]) {
  const active = deals.filter((s) => s.momentum !== "stalled");
  const stalled = deals.filter((s) => s.momentum === "stalled");
  const listValue = (xs: ScoredDeal[]) => xs.reduce((sum, s) => sum + s.deal.listPrice, 0);
  const total = listValue(deals);
  return {
    active,
    stalled,
    activeExpectedValue: active.reduce((sum, s) => sum + s.expectedValue, 0),
    stalledValueShare: total === 0 ? 0 : listValue(stalled) / total,
    withoutAccount: deals.filter((s) => s.deal.account === null).length,
  };
}

/** Ciclo (engajamento → fechamento, em dias) de todos os deals já fechados. */
export const closedCycles: number[] = dataset.deals
  .filter((d) => (d.stage === "Won" || d.stage === "Lost") && d.engageDate && d.closeDate)
  .map((d) => Math.round((Date.parse(d.closeDate!) - Date.parse(d.engageDate!)) / 86_400_000));
