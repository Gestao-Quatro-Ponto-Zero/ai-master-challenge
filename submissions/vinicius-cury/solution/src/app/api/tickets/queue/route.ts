import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

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

type Scenario = "acelerar" | "desacelerar" | "redirecionar" | "quarentena" | "manter" | "liberar";

const SCENARIO_PRIORITY: Record<Scenario, number> = {
  acelerar: 1,
  quarentena: 2,
  redirecionar: 3,
  desacelerar: 4,
  manter: 5,
  liberar: 6,
};

const SCENARIO_ACTIONS: Record<Scenario, string> = {
  acelerar: "Agentes rápidos",
  desacelerar: "Agentes especializados",
  redirecionar: "Migrar canal",
  quarentena: "Investigar causa raiz",
  manter: "Manter canal atual",
  liberar: "Deprioritizar",
};

interface QueueItem {
  position: number;
  ticketId: number;
  channel: string;
  subject: string;
  priority: string;
  scenario: Scenario;
  action: string;
  redirectTo: string | null;
  scenarioPriority: number;
}

export async function GET() {
  const tickets = loadTickets();
  const channels = [...new Set(tickets.map((t) => t.channel))].sort();
  const subjects = [...new Set(tickets.map((t) => t.subject))].sort();

  // Build subject-level r
  const subjectR: Record<string, number | null> = {};
  subjects.forEach((sub) => {
    const subTickets = tickets.filter(
      (t) => t.subject === sub && t.resolutionDurationHours !== null && t.csatRating !== null
    );
    subjectR[sub] = subTickets.length >= 3
      ? pearsonR(subTickets.map((t) => t.resolutionDurationHours!), subTickets.map((t) => t.csatRating!))
      : null;
  });

  // Per-subject channel CSAT ranking
  const subjectChannelCsat: Record<string, { channel: string; avgCsat: number }[]> = {};
  subjects.forEach((sub) => {
    const channelStats = channels.map((ch) => {
      const pairTickets = tickets.filter(
        (t) => t.channel === ch && t.subject === sub &&
          t.resolutionDurationHours !== null && t.csatRating !== null
      );
      return {
        channel: ch,
        avgCsat: pairTickets.length >= 3
          ? Math.round(avg(pairTickets.map((t) => t.csatRating!)) * 100) / 100
          : -1,
      };
    }).filter((c) => c.avgCsat >= 0);
    subjectChannelCsat[sub] = channelStats.sort((a, b) => b.avgCsat - a.avgCsat);
  });

  // Classify a single channel+subject pair
  function classifyPair(ch: string, sub: string): { scenario: Scenario; redirectTo: string | null } {
    const pairTickets = tickets.filter(
      (t) => t.channel === ch && t.subject === sub &&
        t.resolutionDurationHours !== null && t.csatRating !== null
    );

    if (pairTickets.length < 3) return { scenario: "manter", redirectTo: null };

    const durations = pairTickets.map((t) => t.resolutionDurationHours!);
    const csats = pairTickets.map((t) => t.csatRating!);
    const rPair = pearsonR(durations, csats);
    const pairCsat = Math.round(avg(csats) * 100) / 100;

    const channelStats = subjectChannelCsat[sub] || [];
    const bestChannel = channelStats.length > 0 ? channelStats[0] : null;

    if (rPair !== null && rPair < -0.3) return { scenario: "acelerar", redirectTo: null };
    if (rPair !== null && rPair > 0.3) return { scenario: "desacelerar", redirectTo: null };

    const csatGap = bestChannel ? bestChannel.avgCsat - pairCsat : 0;

    if (csatGap > 0.5 && bestChannel && bestChannel.channel !== ch) {
      const viableTarget = channelStats.find((c) =>
        c.channel !== ch &&
        c.avgCsat > pairCsat + 0.3 &&
        REDIRECT_VIABLE[ch]?.[c.channel] === true
      );
      if (viableTarget) return { scenario: "redirecionar", redirectTo: viableTarget.channel };
      return { scenario: "quarentena", redirectTo: null };
    }

    if (pairCsat >= 3.5) return { scenario: "manter", redirectTo: null };

    const allBad = channelStats.every((c) => c.avgCsat < 3.0);
    if (allBad && pairCsat < 3.0) return { scenario: "quarentena", redirectTo: null };

    return { scenario: "liberar", redirectTo: null };
  }

  // Pick 20 random closed tickets
  const closedTickets = tickets.filter((t) => t.status === "Closed");
  const shuffled = closedTickets.sort(() => Math.random() - 0.5);
  const sample = shuffled.slice(0, 20);

  // Classify each
  const queue: QueueItem[] = sample.map((t) => {
    const { scenario, redirectTo } = classifyPair(t.channel, t.subject);
    return {
      position: 0,
      ticketId: t.id,
      channel: t.channel,
      subject: t.subject,
      priority: t.priority,
      scenario,
      action: SCENARIO_ACTIONS[scenario],
      redirectTo,
      scenarioPriority: SCENARIO_PRIORITY[scenario],
    };
  });

  // Sort by scenario priority
  queue.sort((a, b) => a.scenarioPriority - b.scenarioPriority);
  queue.forEach((item, i) => { item.position = i + 1; });

  return NextResponse.json({ queue });
}
