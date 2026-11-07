import { readFile } from "node:fs/promises";
import path from "node:path";
import { cacheLife } from "next/cache";
import Papa from "papaparse";
import { buildModel, rankPipeline, type RawDeal, type ScoredDeal, type Stage } from "./scoring";

const DATA_DIR = path.join(process.cwd(), "data");

async function readCsv<T>(file: string): Promise<T[]> {
  const text = await readFile(path.join(DATA_DIR, file), "utf8");
  const parsed = Papa.parse<T>(text, { header: true, skipEmptyLines: true });
  if (parsed.errors.length) throw new Error(`${file}: ${parsed.errors[0].message}`);
  return parsed.data;
}

type PipelineRow = Record<
  "opportunity_id" | "sales_agent" | "product" | "account" | "deal_stage" | "engage_date" | "close_date" | "close_value",
  string
>;
type TeamRow = Record<"sales_agent" | "manager" | "regional_office", string>;
type AccountRow = Record<"account" | "sector" | "revenue" | "employees", string>;
type ProductRow = Record<"product" | "sales_price", string>;

export interface Deal extends ScoredDeal {
  manager: string;
  region: string;
  sector: string | null;
}

export interface AgentInfo {
  name: string;
  manager: string;
  region: string;
  /** Taxa de vitória histórica do vendedor (contexto, não entra no score). */
  winRate: number | null;
  closedDeals: number;
}

export interface PipelineData {
  today: string;
  maxCycleDays: number;
  globalWinRate: number;
  decideCurve: number[];
  deals: Deal[];
  agents: AgentInfo[];
}

const SECTOR_FIX: Record<string, string> = { technolgy: "technology" };

export async function getPipeline(): Promise<PipelineData> {
  "use cache";
  cacheLife("max");

  const [rows, team, accounts, products] = await Promise.all([
    readCsv<PipelineRow>("sales_pipeline.csv"),
    readCsv<TeamRow>("sales_teams.csv"),
    readCsv<AccountRow>("accounts.csv"),
    readCsv<ProductRow>("products.csv"),
  ]);

  const prices = Object.fromEntries(products.map((p) => [p.product, Number(p.sales_price)]));
  const raw: RawDeal[] = rows.map((r) => ({
    id: r.opportunity_id,
    agent: r.sales_agent,
    product: r.product,
    account: r.account || null,
    stage: r.deal_stage as Stage,
    engageDate: r.engage_date || null,
    closeDate: r.close_date || null,
    closeValue: r.close_value ? Number(r.close_value) : null,
  }));

  const model = buildModel(raw, prices);
  const teamBy = new Map(team.map((t) => [t.sales_agent, t]));
  const sectorBy = new Map(accounts.map((a) => [a.account, SECTOR_FIX[a.sector] ?? a.sector]));

  const deals: Deal[] = rankPipeline(raw, model).map((d) => ({
    ...d,
    manager: teamBy.get(d.agent)?.manager ?? "—",
    region: teamBy.get(d.agent)?.regional_office ?? "—",
    sector: d.account ? (sectorBy.get(d.account) ?? null) : null,
  }));

  const closedBy = new Map<string, number>();
  for (const d of raw) if (d.stage === "Won" || d.stage === "Lost") closedBy.set(d.agent, (closedBy.get(d.agent) ?? 0) + 1);

  const agents: AgentInfo[] = team
    .map((t) => ({
      name: t.sales_agent,
      manager: t.manager,
      region: t.regional_office,
      winRate: model.agentWinRate.get(t.sales_agent) ?? null,
      closedDeals: closedBy.get(t.sales_agent) ?? 0,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  return {
    today: model.today,
    maxCycleDays: model.maxCycleDays,
    globalWinRate: model.globalWinRate,
    decideCurve: model.decideCurve,
    deals,
    agents,
  };
}
