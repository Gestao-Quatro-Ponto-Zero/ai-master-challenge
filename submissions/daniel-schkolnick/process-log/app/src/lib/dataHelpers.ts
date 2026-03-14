import type { DealStage, EmployeeBucket } from "./types";

const INVALID_VALUES = new Set(["", "#REF!", "#N/A", "null", "undefined", "NaN"]);

export function isInvalid(value: any): boolean {
  if (value === null || value === undefined) return true;
  const str = String(value).trim();
  return str === "" || INVALID_VALUES.has(str);
}

export function parseEmployees(value: any): number | null {
  if (isInvalid(value)) return null;
  const n = Number(value);
  return isNaN(n) || n < 0 ? null : Math.round(n);
}

export function parseDate(value: any): Date | null {
  if (isInvalid(value)) return null;
  // Handle Excel serial dates
  if (typeof value === "number") {
    const d = new Date((value - 25569) * 86400 * 1000);
    return isNaN(d.getTime()) ? null : d;
  }
  const d = new Date(value);
  return isNaN(d.getTime()) ? null : d;
}

export function parseCloseValue(value: any): number {
  if (isInvalid(value)) return 0;
  const n = Number(value);
  return isNaN(n) ? 0 : n;
}

export function normalizeDealStage(raw: string): DealStage {
  const lower = (raw || "").trim().toLowerCase();
  if (lower === "won") return "Won";
  if (lower === "lost") return "Lost";
  if (lower === "engaging") return "Engaging";
  if (lower === "prospecting") return "Prospecting";
  console.warn(`Unknown deal_stage "${raw}", defaulting to Prospecting`);
  return "Prospecting";
}

export function getEmployeeBucket(employees: number | null): EmployeeBucket | null {
  if (employees === null) return null;
  if (employees <= 250) return "0-250";
  if (employees <= 1000) return "251-1000";
  if (employees <= 5000) return "1001-5000";
  return "5001+";
}

export function parseSector(value: any): string | null {
  if (isInvalid(value)) return null;
  return String(value).trim();
}

export function daysBetween(a: Date, b: Date): number {
  return Math.abs(Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24)));
}
