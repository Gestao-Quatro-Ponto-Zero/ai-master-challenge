import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import Papa from "papaparse";
import { buildDataset, DataValidationError } from "../src/lib/data/build-dataset";

const RAW_DIR = path.join(process.cwd(), "data", "raw");
const OUT_DIR = path.join(process.cwd(), "data", "generated");

function readCsv(file: string): Record<string, string>[] {
  const text = readFileSync(path.join(RAW_DIR, file), "utf8");
  const { data, errors } = Papa.parse<Record<string, string>>(text, { header: true, skipEmptyLines: true });
  if (errors.length > 0) {
    throw new DataValidationError(`${file}: ${errors[0].message} (linha ${errors[0].row})`);
  }
  return data;
}

try {
  const dataset = buildDataset({
    accounts: readCsv("accounts.csv"),
    products: readCsv("products.csv"),
    salesTeams: readCsv("sales_teams.csv"),
    pipeline: readCsv("sales_pipeline.csv"),
  });

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(path.join(OUT_DIR, "dataset.json"), JSON.stringify(dataset));

  const open = dataset.deals.filter((d) => d.stage === "Prospecting" || d.stage === "Engaging").length;
  console.log(`✓ ${dataset.deals.length} deals (${open} abertos) · data de referência ${dataset.referenceDate}`);
  for (const issue of dataset.quality) {
    console.log(`  ⚠ ${issue.description} [${issue.affected}]`);
  }
} catch (error) {
  if (error instanceof DataValidationError) {
    console.error(`✗ Dados inválidos: ${error.message}`);
    process.exit(1);
  }
  throw error;
}
