/**
 * Global filters (design: "filtros globais", ISC-20). They apply on every screen.
 *
 * - Sector, country and source are account attributes.
 * - Plan follows the identifier (D23, D27): account numbers use accounts.plan_tier,
 *   subscription numbers use subscriptions.plan_tier.
 * - Alert: "com" keeps every record (default, D21); "sem" drops the records an alert flags.
 *
 * Values only enter SQL after matching a value that exists in the database, so no
 * free text ever reaches a query.
 */
import { runQuery } from "./warehouse";

export interface Filtros {
  setor?: string;
  pais?: string;
  origem?: string;
  plano?: string;
  alerta: "com" | "sem";
}

export interface OpcoesFiltro {
  setor: string[];
  pais: string[];
  origem: string[];
  plano: string[];
}

let cache: OpcoesFiltro | null = null;

const distinct = (sql: string): string[] => runQuery(sql).rows.map((r) => String(Object.values(r)[0]));

/** The allowed values of each filter, read from the database. */
export function opcoesFiltro(): OpcoesFiltro {
  if (cache) return cache;
  cache = {
    setor: distinct("SELECT DISTINCT industry FROM accounts ORDER BY 1"),
    pais: distinct("SELECT DISTINCT country FROM accounts ORDER BY 1"),
    origem: distinct("SELECT DISTINCT referral_source FROM accounts ORDER BY 1"),
    plano: distinct("SELECT DISTINCT plan_tier FROM accounts UNION SELECT DISTINCT plan_tier FROM subscriptions ORDER BY 1"),
  };
  return cache;
}

type Params = Record<string, string | string[] | undefined>;

const first = (v: string | string[] | undefined): string | undefined => (Array.isArray(v) ? v[0] : v);

/** Reads the filters from the URL; anything not in the database is dropped. */
export function lerFiltros(params: Params): Filtros {
  const o = opcoesFiltro();
  const pick = (key: keyof OpcoesFiltro): string | undefined => {
    const v = first(params[key]);
    return v && o[key].includes(v) ? v : undefined;
  };
  return {
    setor: pick("setor"),
    pais: pick("pais"),
    origem: pick("origem"),
    plano: pick("plano"),
    alerta: first(params.alerta) === "sem" ? "sem" : "com",
  };
}

/** A filter as a URL query string (for links that keep the filters). */
export function filtrosQuery(f: Filtros): string {
  const p = new URLSearchParams();
  if (f.setor) p.set("setor", f.setor);
  if (f.pais) p.set("pais", f.pais);
  if (f.origem) p.set("origem", f.origem);
  if (f.plano) p.set("plano", f.plano);
  if (f.alerta === "sem") p.set("alerta", "sem");
  const s = p.toString();
  return s ? `?${s}` : "";
}

const lit = (v: string): string => `'${v.replace(/'/g, "''")}'`;

/** Account attributes only (sector, country, source), on an `accounts` alias. */
function atributosConta(f: Filtros, a: string): string[] {
  const w: string[] = [];
  if (f.setor) w.push(`${a}.industry = ${lit(f.setor)}`);
  if (f.pais) w.push(`${a}.country = ${lit(f.pais)}`);
  if (f.origem) w.push(`${a}.referral_source = ${lit(f.origem)}`);
  return w;
}

/** WHERE for account numbers, on an `accounts` (or vw_conta) alias: plan = the account's plan. */
export function whereConta(f: Filtros, a = "a"): string {
  const w = atributosConta(f, a);
  if (f.plano) w.push(`${a}.plan_tier = ${lit(f.plano)}`);
  return w.length ? w.join(" AND ") : "1 = 1";
}

/** WHERE for subscription numbers, on a `subscriptions` alias: plan = the subscription's plan. */
export function whereAssinatura(f: Filtros, s = "s"): string {
  const w: string[] = [];
  const conta = atributosConta(f, "fa");
  if (conta.length) w.push(`${s}.account_id IN (SELECT fa.account_id FROM accounts fa WHERE ${conta.join(" AND ")})`);
  if (f.plano) w.push(`${s}.plan_tier = ${lit(f.plano)}`);
  return w.length ? w.join(" AND ") : "1 = 1";
}

/** Human-readable summary of the active filters. */
export function descreverFiltros(f: Filtros): string {
  const parts = [f.setor, f.pais, f.origem, f.plano && `plano ${f.plano}`].filter(Boolean) as string[];
  if (f.alerta === "sem") parts.push("sem registros em alerta");
  return parts.length ? parts.join(" · ") : "sem filtros";
}
