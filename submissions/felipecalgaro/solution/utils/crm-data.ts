import { readFile } from "node:fs/promises";
import path from "node:path";

export type SalesPipelineRow = {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: string;
  engage_date: string;
  close_date?: string | null;
  close_value?: string | null;
};

export type AccountRow = {
  account: string;
  sector: string;
  revenue: string;
};

export type ProductRow = {
  product: string;
  sales_price: string;
};

const DOCS_DIR = path.join(process.cwd(), "public", "docs");

function parseCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let insideQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];

    if (char === '"') {
      const nextChar = line[index + 1];
      if (insideQuotes && nextChar === '"') {
        current += '"';
        index += 1;
        continue;
      }
      insideQuotes = !insideQuotes;
      continue;
    }

    if (char === "," && !insideQuotes) {
      values.push(current.trim());
      current = "";
      continue;
    }

    current += char;
  }

  values.push(current.trim());
  return values;
}

function splitCsvRows(fileContents: string): {
  headers: string[];
  rows: string[][];
} {
  const [headerLine, ...lineRows] = fileContents
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!headerLine) {
    return { headers: [], rows: [] };
  }

  return {
    headers: parseCsvLine(headerLine),
    rows: lineRows.map(parseCsvLine),
  };
}

function ensureHeaders(
  fileName: string,
  actualHeaders: string[],
  expectedHeaders: string[],
) {
  const isValid =
    actualHeaders.length === expectedHeaders.length &&
    expectedHeaders.every((header, index) => actualHeaders[index] === header);

  if (!isValid) {
    throw new Error(`${fileName} headers do not match expected schema.`);
  }
}

export async function getSalesPipelineRows(): Promise<SalesPipelineRow[]> {
  const fileContents = await readFile(
    path.join(DOCS_DIR, "sales_pipeline.csv"),
    "utf8",
  );
  const { headers, rows } = splitCsvRows(fileContents);

  ensureHeaders("sales_pipeline.csv", headers, [
    "opportunity_id",
    "sales_agent",
    "product",
    "account",
    "deal_stage",
    "engage_date",
    "close_date",
    "close_value",
  ]);

  return rows.map((row) => ({
    opportunity_id: row[0] ?? "",
    sales_agent: row[1] ?? "",
    product: row[2] ?? "",
    account: row[3] ?? "",
    deal_stage: row[4] ?? "",
    engage_date: row[5] ?? "",
    close_date: row[6] || null,
    close_value: row[7] || null,
  }));
}

export async function getAccountsRows(): Promise<AccountRow[]> {
  const fileContents = await readFile(
    path.join(DOCS_DIR, "accounts.csv"),
    "utf8",
  );
  const { headers, rows } = splitCsvRows(fileContents);

  ensureHeaders("accounts.csv", headers, [
    "account",
    "sector",
    "year_established",
    "revenue",
    "employees",
    "office_location",
    "subsidiary_of",
  ]);

  return rows.map((row) => ({
    account: row[0] ?? "",
    sector: row[1] ?? "",
    revenue: row[3] ?? "0",
  }));
}

export async function getProductRows(): Promise<ProductRow[]> {
  const fileContents = await readFile(
    path.join(DOCS_DIR, "products.csv"),
    "utf8",
  );
  const { headers, rows } = splitCsvRows(fileContents);

  ensureHeaders("products.csv", headers, ["product", "series", "sales_price"]);

  return rows.map((row) => ({
    product: row[0] ?? "",
    sales_price: row[2] ?? "0",
  }));
}
