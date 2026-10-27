import type { z } from "zod";
import type { Account, Dataset, Deal, Product, QualityIssue, SalesAgent } from "@/domain/types";
import {
  accountRow,
  pipelineRow,
  productRow,
  salesTeamRow,
  type AccountRow,
  type PipelineRow,
  type ProductRow,
  type SalesTeamRow,
} from "./schemas";
import { isProductAlias, isSectorAlias, normalizeProduct, normalizeSector } from "./normalize";

export interface RawTables {
  accounts: Record<string, string>[];
  products: Record<string, string>[];
  salesTeams: Record<string, string>[];
  pipeline: Record<string, string>[];
}

export class DataValidationError extends Error {}

function parseRows<S extends z.ZodTypeAny>(table: string, schema: S, rows: Record<string, string>[]): z.infer<S>[] {
  return rows.map((row, i) => {
    const result = schema.safeParse(row);
    if (!result.success) {
      const issue = result.error.issues[0];
      throw new DataValidationError(
        `${table}, linha ${i + 2}: campo "${issue.path.join(".")}" — ${issue.message}`,
      );
    }
    return result.data;
  });
}

/**
 * Valida, normaliza e liga as 4 tabelas do CRM. Inconsistências corrigidas ou
 * contornadas são registradas em `quality` para aparecerem nos docs e na UI.
 */
export function buildDataset(raw: RawTables): Dataset {
  const accountRows: AccountRow[] = parseRows("accounts.csv", accountRow, raw.accounts);
  const productRows: ProductRow[] = parseRows("products.csv", productRow, raw.products);
  const teamRows: SalesTeamRow[] = parseRows("sales_teams.csv", salesTeamRow, raw.salesTeams);
  const pipelineRows: PipelineRow[] = parseRows("sales_pipeline.csv", pipelineRow, raw.pipeline);

  const accounts: Account[] = accountRows.map((a) => ({
    name: a.account,
    sector: normalizeSector(a.sector),
    yearEstablished: a.year_established,
    revenue: a.revenue,
    employees: a.employees,
    officeLocation: a.office_location,
    subsidiaryOf: a.subsidiary_of,
  }));
  const products: Product[] = productRows.map((p) => ({
    name: p.product,
    series: p.series,
    salesPrice: p.sales_price,
  }));
  const agents: SalesAgent[] = teamRows.map((t) => ({
    name: t.sales_agent,
    manager: t.manager,
    regionalOffice: t.regional_office,
  }));

  const accountByName = new Map(accounts.map((a) => [a.name, a]));
  const productByName = new Map(products.map((p) => [p.name, p]));
  const agentByName = new Map(agents.map((a) => [a.name, a]));

  const deals: Deal[] = pipelineRows.map((row) => {
    const productName = normalizeProduct(row.product);
    const product = productByName.get(productName);
    if (!product) {
      throw new DataValidationError(`Deal ${row.opportunity_id}: produto desconhecido "${row.product}"`);
    }
    const agent = agentByName.get(row.sales_agent);
    if (!agent) {
      throw new DataValidationError(`Deal ${row.opportunity_id}: vendedor desconhecido "${row.sales_agent}"`);
    }
    const account = row.account ? accountByName.get(row.account) : undefined;
    if (row.account && !account) {
      throw new DataValidationError(`Deal ${row.opportunity_id}: conta desconhecida "${row.account}"`);
    }
    return {
      id: row.opportunity_id,
      stage: row.deal_stage,
      agent: agent.name,
      manager: agent.manager,
      regionalOffice: agent.regionalOffice,
      product: product.name,
      productSeries: product.series,
      listPrice: product.salesPrice,
      account: account?.name ?? null,
      sector: account?.sector ?? null,
      accountEmployees: account?.employees ?? null,
      engageDate: row.engage_date,
      closeDate: row.close_date,
      closeValue: row.close_value,
    };
  });

  const dates = deals.flatMap((d) => [d.engageDate, d.closeDate]).filter((d): d is string => d !== null);
  if (dates.length === 0) {
    throw new DataValidationError("sales_pipeline.csv: nenhum deal tem data; impossível definir a data de referência");
  }
  const referenceDate = dates.reduce((max, d) => (d > max ? d : max));

  return {
    referenceDate,
    deals,
    accounts,
    products,
    agents,
    quality: qualityReport(accountRows, pipelineRows, deals, agents),
  };
}

function qualityReport(
  accountRows: AccountRow[],
  pipelineRows: PipelineRow[],
  deals: Deal[],
  agents: SalesAgent[],
): QualityIssue[] {
  const open = deals.filter((d) => d.stage === "Prospecting" || d.stage === "Engaging");
  const openWithoutAccount = open.filter((d) => d.account === null).length;
  const closedWithoutAccount = deals.filter(
    (d) => (d.stage === "Won" || d.stage === "Lost") && d.account === null,
  ).length;
  const agentsWithDeals = new Set(deals.map((d) => d.agent));
  const idleAgents = agents.filter((a) => !agentsWithDeals.has(a.name));

  const issues: QualityIssue[] = [
    {
      code: "product-alias",
      description: 'O pipeline grafa "GTXPro"; o catálogo de produtos usa "GTX Pro".',
      affected: pipelineRows.filter((r) => isProductAlias(r.product)).length,
      treatment: 'Unificado como "GTX Pro" para ligar preço e série.',
    },
    {
      code: "sector-typo",
      description: 'Setor grafado "technolgy" no cadastro de contas.',
      affected: accountRows.filter((a) => isSectorAlias(a.sector)).length,
      treatment: 'Corrigido para "technology".',
    },
    {
      code: "open-without-account",
      description: "Deals abertos sem conta associada.",
      affected: openWithoutAccount,
      treatment:
        "Setor e porte da conta ficam indisponíveis para esses deals; o score usa só os fatores existentes e a UI sinaliza a lacuna.",
    },
    {
      code: "closed-without-account",
      description: "Deals fechados sem conta associada.",
      affected: closedWithoutAccount,
      treatment: "Nenhum tratamento necessário.",
    },
    {
      code: "prospecting-without-date",
      description: "Deals em Prospecting não têm data de engajamento.",
      affected: deals.filter((d) => d.stage === "Prospecting" && d.engageDate === null).length,
      treatment: "Sem relógio de urgência; priorizados por chance × valor.",
    },
    {
      code: "idle-agents",
      description: `Vendedores cadastrados sem nenhum deal: ${idleAgents.map((a) => a.name).join(", ")}.`,
      affected: idleAgents.length,
      treatment: "Mantidos no cadastro; não aparecem nos rankings.",
    },
  ];
  return issues.filter((i) => i.affected > 0);
}
