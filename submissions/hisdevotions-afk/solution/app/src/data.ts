import { createContext, useContext } from "react";
import type { Account, Agent, Bucket, Deal, OpenDeal, RawData } from "./types";

export interface Model extends RawData {
  open: OpenDeal[];
  byId: Map<string, Deal | OpenDeal>;
  agentByName: Map<string, Agent>;
  accountByName: Map<string, Account>;
}

export const isOpen = (d: Deal): d is OpenDeal => d.stage === "Prospecting" || d.stage === "Engaging";

let pending: Promise<Model> | null = null;

export function loadModel(): Promise<Model> {
  pending ??= fetch(`${import.meta.env.BASE_URL}data.json`)
    .then((r) => {
      if (!r.ok) throw new Error(`Não consegui carregar data.json (HTTP ${r.status}). Rode "python engine/scoring.py" e recarregue.`);
      return r.json() as Promise<RawData>;
    })
    .then((raw) => ({
      ...raw,
      open: raw.deals.filter(isOpen),
      byId: new Map(raw.deals.map((d) => [d.id, d])),
      agentByName: new Map(raw.agents.map((a) => [a.name, a])),
      accountByName: new Map(raw.accounts.map((a) => [a.account, a])),
    }));
  return pending;
}

// ─── filtros globais (região → manager → vendedor) ──────────────────────────

export interface Filters {
  region: string;
  manager: string;
  agent: string;
}

export const NO_FILTERS: Filters = { region: "", manager: "", agent: "" };

// ─── filtros na URL: o recorte vira um link que dá para mandar ou guardar ────
// Ficam na query do hash (#/forecast?por=manager&regiao=West&manager=…), ao
// lado dos parâmetros de cada página, que não são tocados.

const FILTER_PARAMS: Record<keyof Filters, string> = { region: "regiao", manager: "manager", agent: "vendedor" };

function splitHash(): [string, URLSearchParams] {
  const [path, query = ""] = window.location.hash.split("?");
  return [path || "#/", new URLSearchParams(query)];
}

/** Filtros presentes na URL, ou null se o link não traz nenhum. */
export function filtersFromUrl(): Filters | null {
  const [, q] = splitHash();
  const keys = Object.keys(FILTER_PARAMS) as (keyof Filters)[];
  if (!keys.some((k) => q.has(FILTER_PARAMS[k]))) return null;
  return { region: q.get(FILTER_PARAMS.region) ?? "", manager: q.get(FILTER_PARAMS.manager) ?? "", agent: q.get(FILTER_PARAMS.agent) ?? "" };
}

/** Grava os filtros na URL atual sem criar entrada nova no histórico. */
export function writeFiltersToUrl(f: Filters) {
  const [path, q] = splitHash();
  for (const k of Object.keys(FILTER_PARAMS) as (keyof Filters)[]) (f[k] ? q.set(FILTER_PARAMS[k], f[k]) : q.delete(FILTER_PARAMS[k]));
  const qs = q.toString();
  const next = path + (qs ? `?${qs}` : "");
  if (next !== window.location.hash) history.replaceState(history.state, "", next);
}

export const sameFilters = (a: Filters, b: Filters) => a.region === b.region && a.manager === b.manager && a.agent === b.agent;

export const inScope = (x: { region: string; manager: string }, name: string, f: Filters) =>
  (!f.region || x.region === f.region) && (!f.manager || x.manager === f.manager) && (!f.agent || name === f.agent);

export const dealInScope = (d: Deal, f: Filters) => inScope(d, d.agent, f);

// ─── decisões do vendedor (requalificar/encerrar zumbi) ─────────────────────
// ponytail: localStorage por navegador; em produção isso gravaria de volta no CRM.

export type DecisionKind = "requalificado" | "encerrado";
export type Decisions = Record<string, { kind: DecisionKind; at: string; note?: string }>;

export const store = {
  read<T>(key: string, fallback: T): T {
    try {
      const v = localStorage.getItem(key);
      return v ? (JSON.parse(v) as T) : fallback;
    } catch {
      return fallback;
    }
  },
  write(key: string, value: unknown) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* modo privado / armazenamento bloqueado: segue sem persistir */
    }
  },
};

export interface AppState {
  model: Model;
  filters: Filters;
  setFilters: (f: Filters) => void;
  decisions: Decisions;
  decide: (id: string, kind: DecisionKind | null, note?: string) => void;
  importDecisions: (data: Decisions) => void;
}

export const AppContext = createContext<AppState | null>(null);

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp fora do AppContext");
  return ctx;
}

/** Deals abertos no escopo dos filtros, sem os que o vendedor já decidiu. */
export function useScopedOpen(): OpenDeal[] {
  const { model, filters, decisions } = useApp();
  return model.open.filter((d) => dealInScope(d, filters) && !decisions[d.id]);
}

/** Idade onde a chance de ganhar em 30 dias é máxima (o "pico" da curva),
    calculada pelo motor só com idades de amostra confiável. */
export const peakAge = (model: Model) => model.meta.peak_age;

/** Distância do deal ao pico da fila Fechar: 0 = exatamente no ponto de
    máxima chance de ganhar em 30 dias. Quanto menor, mais "quente". */
export const peakGap = (d: OpenDeal, peak: number) => (d.age == null ? Infinity : Math.abs(d.age - peak));

/** Ação do momento (item 1): o deal com maior receita esperada em 30 dias na
    fila Fechar — o "o que eu faço AGORA" do Meu Dia. Só quando há algo na
    janela; senão o motor recomenda destravar o funil. */
export function nextBestAction(open: OpenDeal[]): OpenDeal | null {
  const fechar = open.filter((d) => d.bucket === "fechar").sort(PRIORITY.fechar);
  return fechar[0] ?? null;
}

// ─── ordem de prioridade dentro de cada fila (usada em Meu Dia e no Pipeline) ─
// Não é o score (chance): fechar/avançar priorizam receita esperada em 30 dias
// (valor × chance), que é a coluna mostrada ao lado do score nas filas; decidir
// prioriza o que mais infla o forecast declarado; prospecção não tem score
// nem forecast (sem histórico de conversão), então prioriza pelo valor de lista.
export const PRIORITY: Record<Bucket, (a: OpenDeal, b: OpenDeal) => number> = {
  fechar: (a, b) => b.ev_soon - a.ev_soon,
  decidir: (a, b) => b.price - a.price,
  avancar: (a, b) => b.ev_soon - a.ev_soon,
  prospectar: (a, b) => b.price - a.price,
};

// ─── encerrados recentes (higiene do funil) ──────────────────────────────────
// "Encerrados na última semana" na aba do Pipeline: só o que o vendedor marcou
// como perdido na última semana, para revisar se o motivo ainda vale enquanto
// está fresco — decisão antiga não deve reaparecer como "acabou de encerrar".

export const RECENT_WINDOW_MS = 7 * 24 * 60 * 60 * 1000;

/** Deals no escopo que o vendedor marcou como encerrado nos últimos RECENT_WINDOW_MS. */
export function recentlyClosed(model: Model, filters: Filters, decisions: Decisions): OpenDeal[] {
  const cutoff = Date.now() - RECENT_WINDOW_MS;
  return model.open.filter((d) => {
    const dec = decisions[d.id];
    return dec?.kind === "encerrado" && dealInScope(d, filters) && new Date(dec.at).getTime() >= cutoff;
  });
}
