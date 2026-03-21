import type { Lead, ScoreGrade, ActionStatus } from "./types";
import { daysBetween } from "./dataHelpers";

interface GroupMetrics {
  winRate: number | null;
  avgTime: number | null;
}

function computeGroupMetrics(leads: Lead[], groupKey: (l: Lead) => string | null): Map<string, GroupMetrics> {
  const groups = new Map<string, { won: number; lost: number; totalDays: number; daysCount: number }>();

  for (const l of leads) {
    if (l.deal_stage !== "Won" && l.deal_stage !== "Lost") continue;
    const key = groupKey(l);
    if (!key) continue;
    let g = groups.get(key);
    if (!g) { g = { won: 0, lost: 0, totalDays: 0, daysCount: 0 }; groups.set(key, g); }
    if (l.deal_stage === "Won") g.won++;
    else g.lost++;
    if (l.engage_date && l.close_date) {
      g.totalDays += daysBetween(l.engage_date, l.close_date);
      g.daysCount++;
    }
  }

  const result = new Map<string, GroupMetrics>();
  for (const [key, g] of groups) {
    const total = g.won + g.lost;
    result.set(key, {
      winRate: total > 0 ? g.won / total : null,
      avgTime: g.daysCount > 0 ? g.totalDays / g.daysCount : null,
    });
  }
  return result;
}

function normalizeValue(
  value: number | null,
  metricsMap: Map<string, GroupMetrics>,
  field: "winRate" | "avgTime",
  higherIsBetter: boolean
): number {
  if (value === null) return 50;
  const allValues = Array.from(metricsMap.values()).map(m => m[field]).filter((v): v is number => v !== null);
  if (allValues.length === 0) return 50;
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  if (max === min) return 50;
  return higherIsBetter
    ? ((value - min) / (max - min)) * 100
    : ((max - value) / (max - min)) * 100;
}

function getActionStatus(lead: Lead): ActionStatus {
  if (lead.deal_stage === "Won") return "Ganho";
  if (lead.deal_stage === "Lost") return "Perdido";
  if (lead.isIncomplete) return "Corrigir cadastro";
  if (lead.scoreGrade === "A" || lead.scoreGrade === "B") return "Foco agora";
  if (lead.scoreGrade === "C") return "Foco depois";
  return "Baixa prioridade";
}

function getScoreExplanation(lead: Lead, sectorMetrics: Map<string, GroupMetrics>, bucketMetrics: Map<string, GroupMetrics>): string {
  if (lead.isIncomplete) {
    return "Não classificado por falta de dados obrigatórios";
  }
  if (!lead.scoreGrade) return "";

  const sm = sectorMetrics.get(lead.sector!);
  const bm = bucketMetrics.get(lead.employeeBucket!);

  const sectorWinHigh = sm && sm.winRate !== null && sm.winRate > 0.5;
  const sectorTimeLow = sm && sm.avgTime !== null && sm.avgTime < 60;
  const bucketWinHigh = bm && bm.winRate !== null && bm.winRate > 0.5;
  const bucketTimeLow = bm && bm.avgTime !== null && bm.avgTime < 60;

  if (lead.scoreGrade === "A") {
    return "Alta atratividade estrutural: segmento com boa conversão e porte com fechamento rápido";
  }
  if (lead.scoreGrade === "B") {
    if (sectorWinHigh && !bucketTimeLow) return "Boa atratividade: segmento competitivo, porte com fechamento moderado";
    if (bucketWinHigh && !sectorTimeLow) return "Boa atratividade: porte competitivo, segmento com fechamento moderado";
    return "Boa atratividade estrutural: métricas acima da média em segmento e porte";
  }
  if (lead.scoreGrade === "C") {
    return "Atratividade média: porte ou segmento com eficiência moderada";
  }
  return "Baixa atratividade estrutural: segmento e porte com menor eficiência histórica";
}

export function computeScores(leads: Lead[]): Lead[] {
  const sectorMetrics = computeGroupMetrics(leads, l => l.sector);
  const bucketMetrics = computeGroupMetrics(leads, l => l.employeeBucket);

  const completeLeads: { index: number; score: number }[] = [];
  const result = leads.map((l, i) => ({ ...l }));

  for (let i = 0; i < result.length; i++) {
    const l = result[i];
    if (l.isIncomplete) { l.scoreNumeric = null; l.scoreGrade = null; continue; }

    const sm = sectorMetrics.get(l.sector!);
    const bm = bucketMetrics.get(l.employeeBucket!);

    const v1 = normalizeValue(sm?.winRate ?? null, sectorMetrics, "winRate", true);
    const v2 = normalizeValue(sm?.avgTime ?? null, sectorMetrics, "avgTime", false);
    const v3 = normalizeValue(bm?.winRate ?? null, bucketMetrics, "winRate", true);
    const v4 = normalizeValue(bm?.avgTime ?? null, bucketMetrics, "avgTime", false);

    l.scoreNumeric = (v1 + v2 + v3 + v4) / 4;
    completeLeads.push({ index: i, score: l.scoreNumeric });
  }

  // Assign quartiles
  completeLeads.sort((a, b) => b.score - a.score);
  const n = completeLeads.length;
  for (let rank = 0; rank < n; rank++) {
    const pct = rank / n;
    let grade: ScoreGrade;
    if (pct < 0.25) grade = "A";
    else if (pct < 0.5) grade = "B";
    else if (pct < 0.75) grade = "C";
    else grade = "D";
    result[completeLeads[rank].index].scoreGrade = grade;
  }

  // Assign action status and explanation
  for (const l of result) {
    l.actionStatus = getActionStatus(l);
    l.scoreExplanation = getScoreExplanation(l, sectorMetrics, bucketMetrics);
  }

  return result;
}
