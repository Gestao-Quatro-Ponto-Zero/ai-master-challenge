/**
 * data.ts — Fetch and merge data from Supabase
 *
 * All functions are async (Supabase is a remote API).
 * Interfaces kept identical so the rest of the app doesn't need to change.
 */

import { supabase } from "./supabase";

// ─── Paginated fetch — Supabase REST API returns max 1000 rows by default ─────
async function fetchAll<T>(table: string): Promise<T[]> {
  const PAGE_SIZE = 1000;
  const result: T[] = [];
  let from = 0;

  while (true) {
    const { data, error } = await supabase
      .from(table)
      .select("*")
      .range(from, from + PAGE_SIZE - 1);

    if (error || !data || data.length === 0) break;
    result.push(...(data as T[]));
    if (data.length < PAGE_SIZE) break; // last page
    from += PAGE_SIZE;
  }

  return result;
}

// ─── Raw types (match Supabase column names 1:1) ──────────────────────────────

export interface RawAccount {
  account: string;
  sector: string;
  year_established: string;
  revenue: string | number;
  employees: string | number;
  office_location: string;
  subsidiary_of: string;
}

export interface RawProduct {
  product: string;
  series: string;
  sales_price: string | number;
}

export interface RawSalesTeam {
  sales_agent: string;
  manager: string;
  regional_office: string;
}

export interface RawPipelineRow {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: string;
  engage_date: string;
  close_date: string;
  close_value: string | number;
}

// ─── Enriched deal type (used everywhere in the UI) ──────────────────────────

export interface Deal {
  opportunity_id: string;
  sales_agent: string;
  manager: string;
  regional_office: string;
  product: string;
  product_price: number;
  account: string;
  account_sector: string;
  account_country: string;
  account_revenue: number;
  account_employees: number;
  account_has_parent: boolean;
  deal_stage: "Engaging" | "Prospecting" | "Won" | "Lost";
  engage_date: Date | null;
  close_date: Date | null;
  close_value: number;
  days_in_stage: number;
}

// ─── Reference date ───────────────────────────────────────────────────────────
// Fixed to end of the historical dataset period (2016-2017) for a realistic
// demo distribution. When using live/fresh data in production,
// change this to: new Date()
const REFERENCE_DATE = new Date("2017-12-31");

function daysSince(date: Date | null): number {
  if (!date) return 0;
  const diff = REFERENCE_DATE.getTime() - date.getTime();
  return Math.max(0, Math.floor(diff / (1000 * 60 * 60 * 24)));
}

// ─── Win rate calculation (synchronous — works on already-fetched data) ───────

export interface AgentStats {
  won: number;
  lost: number;
  winRate: number;
}

export function calcAgentWinRates(
  pipeline: RawPipelineRow[]
): Map<string, AgentStats> {
  const stats = new Map<string, { won: number; lost: number }>();

  pipeline.forEach((row) => {
    if (row.deal_stage !== "Won" && row.deal_stage !== "Lost") return;
    const key = row.sales_agent?.toLowerCase() ?? "";
    if (!stats.has(key)) stats.set(key, { won: 0, lost: 0 });
    const s = stats.get(key)!;
    if (row.deal_stage === "Won") s.won++;
    else s.lost++;
  });

  const result = new Map<string, AgentStats>();
  stats.forEach((s, agent) => {
    const total = s.won + s.lost;
    result.set(agent, {
      won: s.won,
      lost: s.lost,
      winRate: total > 0 ? s.won / total : 0,
    });
  });
  return result;
}

// ─── Main: fetch all sources and merge into enriched Deal objects ─────────────

export async function loadDeals(): Promise<Deal[]> {
  const [pipeline, accounts, products, teams] = await Promise.all([
    fetchAll<RawPipelineRow>("sales_pipeline"),
    fetchAll<RawAccount>("accounts"),
    fetchAll<RawProduct>("products"),
    fetchAll<RawSalesTeam>("sales_teams"),
  ]);

  // Build lookup maps
  const accountMap = new Map<string, RawAccount>();
  accounts.forEach((r) => {
    if (r.account) accountMap.set(r.account.toLowerCase(), r);
  });

  const productMap = new Map<string, RawProduct>();
  products.forEach((r) => {
    if (r.product) {
      productMap.set(r.product.toLowerCase().replace(/\s+/g, ""), r);
      productMap.set(r.product.toLowerCase(), r);
    }
  });

  const teamMap = new Map<string, RawSalesTeam>();
  teams.forEach((r) => {
    if (r.sales_agent) teamMap.set(r.sales_agent.toLowerCase(), r);
  });

  return pipeline.map((row): Deal => {
    const acct = accountMap.get(row.account?.toLowerCase() ?? "");
    const productKey = row.product?.toLowerCase().replace(/\s+/g, "");
    const prod =
      productMap.get(productKey ?? "") ??
      productMap.get(row.product?.toLowerCase() ?? "");
    const team = teamMap.get(row.sales_agent?.toLowerCase() ?? "");

    const engage_date = row.engage_date ? new Date(row.engage_date) : null;
    const close_date  = row.close_date  ? new Date(row.close_date)  : null;

    return {
      opportunity_id:     row.opportunity_id,
      sales_agent:        row.sales_agent,
      manager:            team?.manager           ?? "Unknown",
      regional_office:    team?.regional_office   ?? "Unknown",
      product:            row.product,
      product_price:      prod ? Number(prod.sales_price) || 0 : 0,
      account:            row.account,
      account_sector:     acct?.sector?.trim()          || "—",
      account_country:    acct?.office_location?.trim() || "—",
      account_revenue:    acct ? Number(acct.revenue)   || 0 : 0,
      account_employees:  acct ? Number(acct.employees) || 0 : 0,
      account_has_parent: acct ? !!acct.subsidiary_of : false,
      deal_stage:         row.deal_stage as Deal["deal_stage"],
      engage_date,
      close_date,
      close_value:        Number(row.close_value) || 0,
      days_in_stage:      daysSince(engage_date),
    };
  });
}

export async function loadPipeline(): Promise<RawPipelineRow[]> {
  return fetchAll<RawPipelineRow>("sales_pipeline");
}

// ─── Helpers for the UI (synchronous — same as before) ───────────────────────

export function getActiveDeals(deals: Deal[]): Deal[] {
  return deals.filter(
    (d) => d.deal_stage !== "Won" && d.deal_stage !== "Lost"
  );
}

export function getUniqueAgents(deals: Deal[]): string[] {
  return Array.from(new Set(deals.map((d) => d.sales_agent))).sort();
}

export function getUniqueManagers(deals: Deal[]): string[] {
  return Array.from(new Set(deals.map((d) => d.manager))).sort();
}

export function getUniqueRegions(deals: Deal[]): string[] {
  return Array.from(new Set(deals.map((d) => d.regional_office))).sort();
}

export function getUniqueStages(deals: Deal[]): string[] {
  return Array.from(new Set(deals.map((d) => d.deal_stage))).sort();
}
