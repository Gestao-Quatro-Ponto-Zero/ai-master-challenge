import Papa from "papaparse";
import accountsCsv from "@/data/accounts.csv?raw";
import productsCsv from "@/data/products.csv?raw";
import salesPipelineCsv from "@/data/sales_pipeline.csv?raw";
import salesTeamsCsv from "@/data/sales_teams.csv?raw";
import type { AccountRow, Dataset, PipelineRow, ProductRow, SalesTeamRow } from "./types";

export type CsvKey = "accounts" | "products" | "sales_teams" | "sales_pipeline";

export const CSV_FILES: { key: CsvKey; label: string; file: string }[] = [
  { key: "sales_pipeline", label: "Sales pipeline", file: "sales_pipeline.csv" },
  { key: "accounts", label: "Accounts", file: "accounts.csv" },
  { key: "products", label: "Products", file: "products.csv" },
  { key: "sales_teams", label: "Sales teams", file: "sales_teams.csv" },
];

const norm = (s: string) =>
  s
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");

const REQUIRED_HEADERS: Record<CsvKey, string[]> = {
  accounts: ["account"],
  products: ["product"],
  sales_teams: ["sales_agent"],
  sales_pipeline: ["opportunity_id", "sales_agent", "product", "account", "deal_stage"],
};

function readHeaders(text: string): string[] {
  const res = Papa.parse<string[]>(text, {
    preview: 1,
    skipEmptyLines: true,
  });
  return (res.data[0] ?? []).map((h) => norm(String(h)));
}

export function missingRequiredHeaders(key: CsvKey, text: string): string[] {
  const headers = new Set(readHeaders(text));
  return REQUIRED_HEADERS[key].filter((h) => !headers.has(h));
}

function pick(row: Record<string, unknown>, ...keys: string[]): unknown {
  for (const k of keys) {
    if (row[k] != null && row[k] !== "") return row[k];
  }
  return undefined;
}

function toNum(v: unknown): number | undefined {
  if (v == null || v === "") return undefined;
  const n = typeof v === "number" ? v : Number(String(v).replace(/[, $]/g, ""));
  return Number.isFinite(n) ? n : undefined;
}

function parseCsv(text: string): Record<string, unknown>[] {
  const res = Papa.parse<Record<string, unknown>>(text, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: false,
    transformHeader: (h) => norm(h),
  });
  return (res.data || []).filter((r) => r && Object.keys(r).length > 0);
}

export function parseAccounts(text: string): AccountRow[] {
  return parseCsv(text)
    .map((r) => ({
      account: String(pick(r, "account", "company", "name") ?? "").trim(),
      sector: pick(r, "sector", "industry") as string | undefined,
      year_established: toNum(pick(r, "year_established", "year_founded")),
      revenue: toNum(pick(r, "revenue", "annual_revenue")),
      employees: toNum(pick(r, "employees", "employee_count")),
      office_location: pick(r, "office_location", "location", "country") as string | undefined,
      subsidiary_of: pick(r, "subsidiary_of", "parent") as string | undefined,
    }))
    .filter((a) => a.account);
}

export function parseProducts(text: string): ProductRow[] {
  return parseCsv(text)
    .map((r) => ({
      product: String(pick(r, "product", "product_name") ?? "").trim(),
      series: pick(r, "series", "product_series", "line") as string | undefined,
      sales_price: toNum(pick(r, "sales_price", "price", "list_price")),
    }))
    .filter((p) => p.product);
}

export function parseSalesTeams(text: string): SalesTeamRow[] {
  return parseCsv(text)
    .map((r) => ({
      sales_agent: String(pick(r, "sales_agent", "agent", "seller", "rep") ?? "").trim(),
      manager: pick(r, "manager") as string | undefined,
      regional_office: pick(r, "regional_office", "region", "office", "office_location") as
        string | undefined,
    }))
    .filter((t) => t.sales_agent);
}

export function parsePipeline(text: string): PipelineRow[] {
  return parseCsv(text)
    .map((r) => ({
      opportunity_id: String(
        pick(r, "opportunity_id", "opportunity", "deal_id", "id") ?? "",
      ).trim(),
      sales_agent: String(pick(r, "sales_agent", "agent", "seller", "rep") ?? "").trim(),
      product: String(pick(r, "product", "product_name") ?? "").trim(),
      account: String(pick(r, "account", "company") ?? "").trim(),
      deal_stage: String(pick(r, "deal_stage", "stage") ?? "").trim(),
      engage_date: pick(r, "engage_date", "engaged_date", "created_date") as string | undefined,
      close_date: pick(r, "close_date", "closed_date") as string | undefined,
      close_value: toNum(pick(r, "close_value", "value", "amount", "deal_value")),
    }))
    .filter((p) => p.opportunity_id || p.account);
}

export function parseByKey(key: CsvKey, text: string): Dataset[keyof Dataset] {
  switch (key) {
    case "accounts":
      return parseAccounts(text);
    case "products":
      return parseProducts(text);
    case "sales_teams":
      return parseSalesTeams(text);
    case "sales_pipeline":
      return parsePipeline(text);
  }
}

function datasetFromCsvTexts({
  pipeline,
  accounts,
  products,
  teams,
}: {
  pipeline: string;
  accounts?: string | null;
  products?: string | null;
  teams?: string | null;
}): Dataset {
  return {
    pipeline: parsePipeline(pipeline),
    accounts: accounts ? parseAccounts(accounts) : [],
    products: products ? parseProducts(products) : [],
    salesTeams: teams ? parseSalesTeams(teams) : [],
  };
}

function loadBundledDataset(): Dataset {
  return datasetFromCsvTexts({
    pipeline: salesPipelineCsv,
    accounts: accountsCsv,
    products: productsCsv,
    teams: salesTeamsCsv,
  });
}

/**
 * Attempt to load the CRM source tables from public assets. If the preview provider
 * does not serve them directly, fall back to the same data bundled into the app.
 */
export async function loadFromPublic(): Promise<Dataset | null> {
  try {
    const fetchText = async (file: string) => {
      const url = `/data/${file}`;

      if (typeof fetch === "function") {
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) return null;
        const ct = res.headers.get("content-type") ?? "";
        if (ct.includes("text/html")) return null; // SPA fallback, not a real CSV
        return res.text();
      }

      return new Promise<string | null>((resolve) => {
        const req = new XMLHttpRequest();
        req.open("GET", url, true);
        req.onload = () => {
          if (req.status < 200 || req.status >= 300) {
            resolve(null);
            return;
          }
          const ct = req.getResponseHeader("content-type") ?? "";
          resolve(ct.includes("text/html") ? null : req.responseText);
        };
        req.onerror = () => resolve(null);
        req.send();
      });
    };
    const [pipeline, accounts, products, teams] = await Promise.all([
      fetchText("sales_pipeline.csv"),
      fetchText("accounts.csv"),
      fetchText("products.csv"),
      fetchText("sales_teams.csv"),
    ]);
    if (!pipeline) return loadBundledDataset();
    return datasetFromCsvTexts({
      pipeline,
      accounts: accounts ?? accountsCsv,
      products: products ?? productsCsv,
      teams: teams ?? salesTeamsCsv,
    });
  } catch {
    return loadBundledDataset();
  }
}
