import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// ── Types ──────────────────────────────────────────────────────────
interface Ticket {
  id: number;
  subject: string;
  type: string;
  priority: string;
  channel: string;
  status: string;
  resolutionDurationHours: number | null;
  csatRating: number | null;
}

type Scenario = "acelerar" | "desacelerar" | "redirecionar" | "quarentena" | "manter" | "liberar";

interface PairDiagnostic {
  channel: string;
  subject: string;
  scenario: Scenario;
  rPair: number | null;
  totalTickets: number;
  closedWithCsat: number;
  avgDuration: number;
  avgCsat: number;
  bestChannelForSubject: string | null;
  bestChannelCsat: number | null;
  redirectTo: string | null;
  redirectViable: boolean;
}

export interface AutomationCandidate {
  id: number;
  name: string;
  targetScenario: string;
  description: string;
  pairCount: number;
  totalTickets: number;
  totalHours: number;
  projectedCsatGain: number;
  projectedHoursSaved: number;
  feasibility: number; // 1=easy … 5=hard (months)
  impactScore: number; // projectedCsatGain * totalTickets / feasibility
  details: PairDetail[];
}

interface PairDetail {
  channel: string;
  subject: string;
  tickets: number;
  hours: number;
  avgCsat: number;
  projectedCsat: number;
  action: string;
}

export interface SimulationRow {
  scenario: string;
  beforeHours: number;
  afterHours: number;
  beforeCsat: number;
  afterCsat: number;
  deltaHours: number;
  deltaCsat: number;
}

// ── CSV parsing (same as tickets/route.ts) ─────────────────────────
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"' && line[i + 1] === '"') { current += '"'; i++; }
      else if (char === '"') inQuotes = false;
      else current += char;
    } else {
      if (char === '"') inQuotes = true;
      else if (char === ",") { result.push(current.trim()); current = ""; }
      else current += char;
    }
  }
  result.push(current.trim());
  return result;
}

let cached: Ticket[] | null = null;

function loadTickets(): Ticket[] {
  if (cached) return cached;
  const csvPath = path.join(process.cwd(), "data", "customer_support_tickets.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const lines = content.split("\n");
  const headers = parseCSVLine(lines[0]);
  const tickets: Ticket[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const values = parseCSVLine(line);
    if (values.length !== headers.length) continue;
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => { row[h] = values[idx]; });

    const status = row["Ticket Status"];
    const frt = row["First Response Time"] || null;
    const ttr = row["Time to Resolution"] || null;
    let dur: number | null = null;
    if (status === "Closed" && frt && ttr) {
      const d = Math.abs(new Date(ttr).getTime() - new Date(frt).getTime()) / 3600000;
      if (!isNaN(d)) dur = d;
    }
    const csat = parseFloat(row["Customer Satisfaction Rating"]);
    const csatRating = isNaN(csat) ? null : csat;

    tickets.push({
      id: parseInt(row["Ticket ID"]),
      subject: row["Ticket Subject"],
      type: row["Ticket Type"],
      priority: row["Ticket Priority"],
      channel: row["Ticket Channel"],
      status: row["Ticket Status"],
      resolutionDurationHours: dur,
      csatRating,
    });
  }
  cached = tickets;
  return tickets;
}

// ── Helpers ────────────────────────────────────────────────────────
function avg(arr: number[]): number {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

function pearsonR(xs: number[], ys: number[]): number | null {
  const n = xs.length;
  if (n < 3) return null;
  const mx = avg(xs);
  const my = avg(ys);
  let num = 0, dx2 = 0, dy2 = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx;
    const dy = ys[i] - my;
    num += dx * dy;
    dx2 += dx * dx;
    dy2 += dy * dy;
  }
  const denom = Math.sqrt(dx2 * dy2);
  return denom === 0 ? null : Math.round((num / denom) * 1000) / 1000;
}

const REDIRECT_VIABLE: Record<string, Record<string, boolean>> = {
  "Email": { "Phone": true, "Chat": true, "Social media": false },
  "Chat": { "Phone": true, "Email": true, "Social media": false },
  "Phone": { "Email": true, "Chat": true, "Social media": false },
  "Social media": { "Email": true, "Phone": true, "Chat": false },
};

// ── Diagnostic classification (inline from diagnostic/route.ts) ───
function classifyPairs(tickets: Ticket[]): PairDiagnostic[] {
  const channels = [...new Set(tickets.map((t) => t.channel))].sort();
  const subjects = [...new Set(tickets.map((t) => t.subject))].sort();

  // Subject-level r
  const subjectR: Record<string, number | null> = {};
  subjects.forEach((sub) => {
    const st = tickets.filter(
      (t) => t.subject === sub && t.resolutionDurationHours !== null && t.csatRating !== null
    );
    subjectR[sub] = st.length >= 3
      ? pearsonR(st.map((t) => t.resolutionDurationHours!), st.map((t) => t.csatRating!))
      : null;
  });

  // Per-subject channel CSAT ranking
  const subjectChannelCsat: Record<string, { channel: string; avgCsat: number }[]> = {};
  subjects.forEach((sub) => {
    const channelStats = channels.map((ch) => {
      const pt = tickets.filter(
        (t) => t.channel === ch && t.subject === sub &&
          t.resolutionDurationHours !== null && t.csatRating !== null
      );
      return {
        channel: ch,
        avgCsat: pt.length >= 3 ? Math.round(avg(pt.map((t) => t.csatRating!)) * 100) / 100 : -1,
      };
    }).filter((c) => c.avgCsat >= 0);
    subjectChannelCsat[sub] = channelStats.sort((a, b) => b.avgCsat - a.avgCsat);
  });

  // Pair-level classification
  const pairs: PairDiagnostic[] = [];

  channels.forEach((ch) => {
    subjects.forEach((sub) => {
      const pairTickets = tickets.filter(
        (t) => t.channel === ch && t.subject === sub &&
          t.resolutionDurationHours !== null && t.csatRating !== null
      );
      if (pairTickets.length < 3) return;

      const durations = pairTickets.map((t) => t.resolutionDurationHours!);
      const csats = pairTickets.map((t) => t.csatRating!);
      const rPair = pearsonR(durations, csats);
      const totalAll = tickets.filter((t) => t.channel === ch && t.subject === sub).length;
      const pairCsat = Math.round(avg(csats) * 100) / 100;
      const pairDuration = Math.round(avg(durations) * 100) / 100;

      const channelStats = subjectChannelCsat[sub] || [];
      const bestChannel = channelStats.length > 0 ? channelStats[0] : null;

      let scenario: Scenario;
      let redirectTo: string | null = null;
      let redirectViable = false;

      if (rPair !== null && rPair < -0.3) {
        scenario = "acelerar";
      } else if (rPair !== null && rPair > 0.3) {
        scenario = "desacelerar";
      } else {
        const csatGap = bestChannel ? bestChannel.avgCsat - pairCsat : 0;
        if (csatGap > 0.5 && bestChannel && bestChannel.channel !== ch) {
          const viableTarget = channelStats.find((c) =>
            c.channel !== ch &&
            c.avgCsat > pairCsat + 0.3 &&
            REDIRECT_VIABLE[ch]?.[c.channel] === true
          );
          if (viableTarget) {
            scenario = "redirecionar";
            redirectTo = viableTarget.channel;
            redirectViable = true;
          } else {
            scenario = "quarentena";
          }
        } else if (pairCsat >= 3.5) {
          scenario = "manter";
        } else {
          const allBad = channelStats.every((c) => c.avgCsat < 3.0);
          if (allBad && pairCsat < 3.0) {
            scenario = "quarentena";
          } else {
            scenario = "liberar";
          }
        }
      }

      pairs.push({
        channel: ch,
        subject: sub,
        scenario,
        rPair,
        totalTickets: totalAll,
        closedWithCsat: pairTickets.length,
        avgDuration: pairDuration,
        avgCsat: pairCsat,
        bestChannelForSubject: bestChannel?.channel || null,
        bestChannelCsat: bestChannel?.avgCsat || null,
        redirectTo,
        redirectViable,
      });
    });
  });

  return pairs;
}

// ── Automation candidates ──────────────────────────────────────────
function buildCandidates(pairs: PairDiagnostic[]): AutomationCandidate[] {
  const candidates: AutomationCandidate[] = [];

  // --- Candidate 1: Auto-roteamento (redirecionar pairs) ---
  const redirectPairs = pairs.filter((p) => p.scenario === "redirecionar");
  const c1Details: PairDetail[] = redirectPairs.map((p) => {
    const csatGain = (p.bestChannelCsat ?? p.avgCsat) - p.avgCsat;
    return {
      channel: p.channel,
      subject: p.subject,
      tickets: p.totalTickets,
      hours: Math.round(p.avgDuration * p.totalTickets * 10) / 10,
      avgCsat: p.avgCsat,
      projectedCsat: Math.round((p.avgCsat + csatGain) * 100) / 100,
      action: `Redirecionar → ${p.redirectTo}`,
    };
  });
  const c1TotalTickets = c1Details.reduce((s, d) => s + d.tickets, 0);
  const c1TotalHours = c1Details.reduce((s, d) => s + d.hours, 0);
  // Weighted CSAT gain
  const c1CsatGain = c1TotalTickets > 0
    ? Math.round(c1Details.reduce((s, d) => s + (d.projectedCsat - d.avgCsat) * d.tickets, 0) / c1TotalTickets * 100) / 100
    : 0;

  candidates.push({
    id: 1,
    name: "Auto-Roteamento Inteligente",
    targetScenario: "redirecionar",
    description: "Roteamento automático de tickets para o canal com melhor CSAT para cada assunto. Baseado na análise de pares com redirecionamento viável.",
    pairCount: redirectPairs.length,
    totalTickets: c1TotalTickets,
    totalHours: Math.round(c1TotalHours),
    projectedCsatGain: c1CsatGain,
    projectedHoursSaved: 0, // routing doesn't save hours, it improves CSAT
    feasibility: 1,
    impactScore: 0, // computed below
    details: c1Details,
  });

  // --- Candidate 2: Fila Prioritária (acelerar pairs) ---
  const acelerarPairs = pairs.filter((p) => p.scenario === "acelerar");
  const c2Details: PairDetail[] = acelerarPairs.map((p) => {
    const reducedDuration = p.avgDuration * 0.7; // 30% reduction
    // Estimate CSAT improvement via negative r: reducing time improves CSAT
    const rAbs = Math.abs(p.rPair ?? 0);
    const csatBoost = rAbs * 0.5; // heuristic: stronger r → bigger improvement
    return {
      channel: p.channel,
      subject: p.subject,
      tickets: p.totalTickets,
      hours: Math.round(p.avgDuration * p.totalTickets * 10) / 10,
      avgCsat: p.avgCsat,
      projectedCsat: Math.round((p.avgCsat + csatBoost) * 100) / 100,
      action: `Fila rápida (−30% tempo → ${reducedDuration.toFixed(1)}h)`,
    };
  });
  const c2TotalTickets = c2Details.reduce((s, d) => s + d.tickets, 0);
  const c2TotalHours = c2Details.reduce((s, d) => s + d.hours, 0);
  const c2HoursSaved = Math.round(c2TotalHours * 0.3);
  const c2CsatGain = c2TotalTickets > 0
    ? Math.round(c2Details.reduce((s, d) => s + (d.projectedCsat - d.avgCsat) * d.tickets, 0) / c2TotalTickets * 100) / 100
    : 0;

  candidates.push({
    id: 2,
    name: "Fila Prioritária Inteligente",
    targetScenario: "acelerar",
    description: "Fila express para pares onde tempo impacta negativamente a satisfação. Redução projetada de 30% na duração via roteamento para agentes rápidos.",
    pairCount: acelerarPairs.length,
    totalTickets: c2TotalTickets,
    totalHours: Math.round(c2TotalHours),
    projectedCsatGain: c2CsatGain,
    projectedHoursSaved: c2HoursSaved,
    feasibility: 1,
    impactScore: 0,
    details: c2Details,
  });

  // --- Candidate 3: Automação Chat (liberar pairs) ---
  const liberarPairs = pairs.filter((p) => p.scenario === "liberar");
  const c3Details: PairDetail[] = liberarPairs.map((p) => {
    const hoursFreed = p.avgDuration * p.totalTickets * 0.5; // 50% handled by bot
    return {
      channel: p.channel,
      subject: p.subject,
      tickets: p.totalTickets,
      hours: Math.round(p.avgDuration * p.totalTickets * 10) / 10,
      avgCsat: p.avgCsat,
      projectedCsat: p.avgCsat, // CSAT neutral (time doesn't matter here)
      action: `Bot atende 50% (${Math.round(hoursFreed)}h liberadas)`,
    };
  });
  const c3TotalTickets = c3Details.reduce((s, d) => s + d.tickets, 0);
  const c3TotalHours = c3Details.reduce((s, d) => s + d.hours, 0);
  const c3HoursFreed = Math.round(c3TotalHours * 0.5);

  candidates.push({
    id: 3,
    name: "Automação via Chatbot",
    targetScenario: "liberar",
    description: "Chatbot para pares onde tempo não influencia satisfação e CSAT é neutro. Bot atende 50% dos tickets, liberando horas de agentes humanos para cenários mais críticos.",
    pairCount: liberarPairs.length,
    totalTickets: c3TotalTickets,
    totalHours: Math.round(c3TotalHours),
    projectedCsatGain: 0,
    projectedHoursSaved: c3HoursFreed,
    feasibility: 4,
    impactScore: 0,
    details: c3Details,
  });

  // --- Candidate 4: Roteamento Especialista (desacelerar pairs) ---
  const desacelerarPairs = pairs.filter((p) => p.scenario === "desacelerar");
  const c4Details: PairDetail[] = desacelerarPairs.map((p) => {
    const rAbs = Math.abs(p.rPair ?? 0);
    const csatBoost = rAbs * 0.3; // slower → better CSAT, agent specialization helps
    return {
      channel: p.channel,
      subject: p.subject,
      tickets: p.totalTickets,
      hours: Math.round(p.avgDuration * p.totalTickets * 10) / 10,
      avgCsat: p.avgCsat,
      projectedCsat: Math.round((p.avgCsat + csatBoost) * 100) / 100,
      action: `Agente especialista (SLA estendido)`,
    };
  });
  const c4TotalTickets = c4Details.reduce((s, d) => s + d.tickets, 0);
  const c4TotalHours = c4Details.reduce((s, d) => s + d.hours, 0);
  const c4CsatGain = c4TotalTickets > 0
    ? Math.round(c4Details.reduce((s, d) => s + (d.projectedCsat - d.avgCsat) * d.tickets, 0) / c4TotalTickets * 100) / 100
    : 0;

  candidates.push({
    id: 4,
    name: "Roteamento para Especialistas",
    targetScenario: "desacelerar",
    description: "Roteamento para agentes seniores com SLA estendido nos pares onde mais tempo = mais satisfação. Prioriza qualidade sobre velocidade.",
    pairCount: desacelerarPairs.length,
    totalTickets: c4TotalTickets,
    totalHours: Math.round(c4TotalHours),
    projectedCsatGain: c4CsatGain,
    projectedHoursSaved: 0, // actually uses more time, but that's the point
    feasibility: 2,
    impactScore: 0,
    details: c4Details,
  });

  // Compute impact scores: (csatGain * tickets + hoursSaved) / feasibility
  candidates.forEach((c) => {
    c.impactScore = Math.round(
      ((c.projectedCsatGain * c.totalTickets) + c.projectedHoursSaved) / c.feasibility * 10
    ) / 10;
  });

  return candidates;
}

// ── Before/After simulation ────────────────────────────────────────
function buildSimulation(pairs: PairDiagnostic[], candidates: AutomationCandidate[]): {
  simulation: SimulationRow[];
  totals: { beforeHours: number; afterHours: number; beforeCsat: number; afterCsat: number };
} {
  const scenarioOrder: Scenario[] = ["acelerar", "desacelerar", "redirecionar", "quarentena", "manter", "liberar"];
  const scenarioLabels: Record<Scenario, string> = {
    acelerar: "Acelerar",
    desacelerar: "Desacelerar",
    redirecionar: "Redirecionar",
    quarentena: "Quarentena",
    manter: "Manter",
    liberar: "Liberar",
  };

  // Hours freed from liberar (50% by bot)
  const liberarCandidate = candidates.find((c) => c.id === 3);
  const hoursFreed = liberarCandidate?.projectedHoursSaved ?? 0;

  // Reallocate 50% of freed hours to acelerar + quarentena
  const reallocateTotal = hoursFreed * 0.5;
  const acelerarPairs = pairs.filter((p) => p.scenario === "acelerar");
  const quarentenaPairs = pairs.filter((p) => p.scenario === "quarentena");
  const acelerarHours = acelerarPairs.reduce((s, p) => s + p.avgDuration * p.totalTickets, 0);
  const quarentenaHours = quarentenaPairs.reduce((s, p) => s + p.avgDuration * p.totalTickets, 0);
  const totalTarget = acelerarHours + quarentenaHours;
  const acelerarShare = totalTarget > 0 ? acelerarHours / totalTarget : 0.5;

  const simulation: SimulationRow[] = scenarioOrder.map((scenario) => {
    const sPairs = pairs.filter((p) => p.scenario === scenario);
    const beforeHours = Math.round(sPairs.reduce((s, p) => s + p.avgDuration * p.totalTickets, 0));
    const totalTickets = sPairs.reduce((s, p) => s + p.totalTickets, 0);
    const beforeCsat = totalTickets > 0
      ? Math.round(sPairs.reduce((s, p) => s + p.avgCsat * p.totalTickets, 0) / totalTickets * 100) / 100
      : 0;

    let afterHours = beforeHours;
    let afterCsat = beforeCsat;

    switch (scenario) {
      case "acelerar":
        afterHours = Math.round(beforeHours * 0.7 + reallocateTotal * acelerarShare); // 30% faster + extra agents
        afterCsat = Math.round((beforeCsat + (candidates.find((c) => c.id === 2)?.projectedCsatGain ?? 0)) * 100) / 100;
        break;
      case "desacelerar":
        afterHours = Math.round(beforeHours * 1.1); // 10% more time = better quality
        afterCsat = Math.round((beforeCsat + (candidates.find((c) => c.id === 4)?.projectedCsatGain ?? 0)) * 100) / 100;
        break;
      case "redirecionar":
        afterHours = beforeHours; // same hours, different channel
        afterCsat = Math.round((beforeCsat + (candidates.find((c) => c.id === 1)?.projectedCsatGain ?? 0)) * 100) / 100;
        break;
      case "quarentena":
        afterHours = Math.round(beforeHours + reallocateTotal * (1 - acelerarShare)); // extra agents for investigation
        afterCsat = Math.round((beforeCsat + 0.15) * 100) / 100; // modest improvement from investigation
        break;
      case "manter":
        // no change
        break;
      case "liberar":
        afterHours = Math.round(beforeHours * 0.5); // 50% handled by bot
        afterCsat = beforeCsat; // neutral
        break;
    }

    return {
      scenario: scenarioLabels[scenario],
      beforeHours,
      afterHours,
      beforeCsat,
      afterCsat,
      deltaHours: afterHours - beforeHours,
      deltaCsat: Math.round((afterCsat - beforeCsat) * 100) / 100,
    };
  });

  const totals = {
    beforeHours: simulation.reduce((s, r) => s + r.beforeHours, 0),
    afterHours: simulation.reduce((s, r) => s + r.afterHours, 0),
    beforeCsat: 0,
    afterCsat: 0,
  };

  // Weighted average CSAT
  const totalTickets = pairs.reduce((s, p) => s + p.totalTickets, 0);
  totals.beforeCsat = totalTickets > 0
    ? Math.round(pairs.reduce((s, p) => s + p.avgCsat * p.totalTickets, 0) / totalTickets * 100) / 100
    : 0;

  // After CSAT: weighted by scenario simulation
  const scenarioPairTickets = scenarioOrder.map((sc) => {
    const sp = pairs.filter((p) => p.scenario === sc);
    return sp.reduce((s, p) => s + p.totalTickets, 0);
  });
  const afterCsatWeighted = simulation.reduce((s, r, i) => s + r.afterCsat * scenarioPairTickets[i], 0);
  const totalSimTickets = scenarioPairTickets.reduce((s, t) => s + t, 0);
  totals.afterCsat = totalSimTickets > 0 ? Math.round(afterCsatWeighted / totalSimTickets * 100) / 100 : 0;

  return { simulation, totals };
}

// ── Scenario hours summary ─────────────────────────────────────────
function scenarioHours(pairs: PairDiagnostic[]): Record<string, number> {
  const result: Record<string, number> = {};
  const scenarios: Scenario[] = ["acelerar", "desacelerar", "redirecionar", "quarentena", "manter", "liberar"];
  scenarios.forEach((s) => {
    const sp = pairs.filter((p) => p.scenario === s);
    result[s] = Math.round(sp.reduce((sum, p) => sum + p.avgDuration * p.totalTickets, 0));
  });
  return result;
}

// ── GET handler ────────────────────────────────────────────────────
export async function GET() {
  const tickets = loadTickets();
  const pairs = classifyPairs(tickets);
  const candidates = buildCandidates(pairs);
  const { simulation, totals } = buildSimulation(pairs, candidates);
  const hours = scenarioHours(pairs);

  return NextResponse.json({
    candidates,
    simulation,
    totals,
    scenarioHours: hours,
    pairCount: pairs.length,
    totalTickets: pairs.reduce((s, p) => s + p.totalTickets, 0),
  });
}
