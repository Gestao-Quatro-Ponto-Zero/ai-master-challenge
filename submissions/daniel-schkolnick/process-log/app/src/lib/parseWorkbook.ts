import * as XLSX from "xlsx";
import type { Lead, RawRow } from "./types";
import {
  isInvalid, parseEmployees, parseDate, parseCloseValue,
  normalizeDealStage, getEmployeeBucket, parseSector
} from "./dataHelpers";
import { computeScores } from "./scoring";

export async function parseWorkbookFromUrl(url: string): Promise<Lead[]> {
  const resp = await fetch(url);
  const buf = await resp.arrayBuffer();
  return parseWorkbookBuffer(buf);
}

export function parseWorkbookBuffer(buf: ArrayBuffer): Lead[] {
  const wb = XLSX.read(buf, { type: "array", cellDates: true });
  const sheetName = wb.SheetNames.find(n => n.toLowerCase().includes("sales_pipeline")) || wb.SheetNames[0];
  const sheet = wb.Sheets[sheetName];
  const rows: RawRow[] = XLSX.utils.sheet_to_json(sheet, { defval: "" });

  const leads: Lead[] = rows.map(r => {
    const employees = parseEmployees(r.employees);
    const sector = parseSector(r.sector);
    const bucket = getEmployeeBucket(employees);
    const missingSector = isInvalid(r.sector);
    const missingEmployees = employees === null;
    const isIncomplete = missingSector || missingEmployees;

    const missingFields: string[] = [];
    if (missingSector) missingFields.push("setor");
    if (missingEmployees) missingFields.push("porte");

    return {
      opportunity_id: String(r.opportunity_id || "").trim(),
      sales_agent: String(r.sales_agent || "").trim(),
      manager: String(r.manager || "").trim(),
      account: String(r.account || "").trim(),
      employees,
      sector,
      product: String(r.product || "").trim(),
      deal_stage: normalizeDealStage(String(r.deal_stage || "")),
      engage_date: parseDate(r.engage_date),
      close_date: parseDate(r.close_date),
      close_value: parseCloseValue(r.close_value),
      employeeBucket: bucket,
      isIncomplete,
      missingFields,
      scoreNumeric: null,
      scoreGrade: null,
      actionStatus: "Baixa prioridade" as const,
      scoreExplanation: "",
    };
  });

  return computeScores(leads);
}
