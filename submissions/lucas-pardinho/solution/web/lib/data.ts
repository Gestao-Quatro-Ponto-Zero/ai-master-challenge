import { promises as fs } from "node:fs";
import path from "node:path";
import {
  SAMPLE_DATA_QUALITY,
  SAMPLE_MODEL_REPORT,
  SAMPLE_OPPORTUNITIES,
} from "@/lib/sample-data";
import type {
  DashboardFile,
  DataQualityReport,
  DataStatus,
  ModelReport,
  Opportunity,
} from "@/lib/types";

const EXPECTED_FILES = [
  "opportunities.json",
  "dashboard.json",
  "model-report.json",
  "data-quality.json",
] as const;

function generatedDirectory(): string {
  return process.env.GENERATED_DATA_DIR
    ? path.resolve(process.env.GENERATED_DATA_DIR)
    : path.resolve(process.cwd(), "../generated");
}

function sampleAllowed(): boolean {
  return process.env.ALLOW_SAMPLE_DATA === "true" || process.env.NODE_ENV !== "production";
}

async function readJson<T>(filename: string): Promise<T> {
  const filePath = path.join(/*turbopackIgnore: true*/ generatedDirectory(), filename);
  const contents = await fs.readFile(filePath, "utf8");
  return JSON.parse(contents) as T;
}

async function readWithFallback<T>(filename: string, fallback: T): Promise<T> {
  try {
    return await readJson<T>(filename);
  } catch (error) {
    if (sampleAllowed()) return fallback;

    const reason = error instanceof Error ? error.message : "erro desconhecido";
    throw new Error(
      `Dados gerados indisponíveis em ${generatedDirectory()}/${filename}. ` +
        `Execute a pipeline de analytics antes de iniciar em produção. Motivo: ${reason}`,
    );
  }
}

export async function getOpportunities(): Promise<Opportunity[]> {
  return readWithFallback<Opportunity[]>("opportunities.json", SAMPLE_OPPORTUNITIES);
}

export async function getDashboardFile(): Promise<DashboardFile> {
  return readWithFallback<DashboardFile>("dashboard.json", {});
}

export async function getModelReport(): Promise<ModelReport> {
  return readWithFallback<ModelReport>("model-report.json", SAMPLE_MODEL_REPORT);
}

export async function getDataQualityReport(): Promise<DataQualityReport> {
  return readWithFallback<DataQualityReport>("data-quality.json", SAMPLE_DATA_QUALITY);
}

export async function getDataStatus(): Promise<DataStatus> {
  const checks = await Promise.all(
    EXPECTED_FILES.map(async (filename) => {
      try {
        await fs.access(
          path.join(/*turbopackIgnore: true*/ generatedDirectory(), filename),
        );
        return [filename, true] as const;
      } catch {
        return [filename, false] as const;
      }
    }),
  );

  const availableFiles = checks.filter(([, available]) => available).map(([filename]) => filename);
  const missingFiles = checks.filter(([, available]) => !available).map(([filename]) => filename);

  return {
    source: missingFiles.length === 0 ? "generated" : sampleAllowed() ? "sample" : "unavailable",
    directory: generatedDirectory(),
    availableFiles,
    missingFiles,
    sampleAllowed: sampleAllowed(),
  };
}
