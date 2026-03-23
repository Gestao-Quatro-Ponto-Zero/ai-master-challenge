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
  ticketDate: string | null; // YYYY-MM-DD from First Response Time
  resolutionDurationHours: number | null;
  csatRating: number | null;
  csatSegment: string | null;
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
    // Only compute resolution duration for Closed tickets that have both timestamps
    if (status === "Closed" && frt && ttr) {
      const d = Math.abs(new Date(ttr).getTime() - new Date(frt).getTime()) / 3600000;
      if (!isNaN(d)) dur = d;
    }
    const csat = parseFloat(row["Customer Satisfaction Rating"]);
    const csatRating = isNaN(csat) ? null : csat;
    let csatSegment: string | null = null;
    if (csatRating !== null) {
      if (csatRating >= 4) csatSegment = "Satisfeito";
      else if (csatRating === 3) csatSegment = "Neutro";
      else csatSegment = "Insatisfeito";
    }

    // Extract date from First Response Time (YYYY-MM-DD)
    const frtStr = row["First Response Time"] || "";
    const dateMatch = frtStr.match(/^\d{4}-\d{2}-\d{2}/);
    const ticketDate = dateMatch ? dateMatch[0] : null;

    tickets.push({
      id: parseInt(row["Ticket ID"]),
      subject: row["Ticket Subject"],
      type: row["Ticket Type"],
      priority: row["Ticket Priority"],
      channel: row["Ticket Channel"],
      status: row["Ticket Status"],
      ticketDate,
      resolutionDurationHours: dur,
      csatRating,
      csatSegment,
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

function median(arr: number[]): number {
  if (!arr.length) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function groupBy<T>(arr: T[], key: (item: T) => string) {
  const map: Record<string, T[]> = {};
  arr.forEach((item) => {
    const k = key(item);
    if (!map[k]) map[k] = [];
    map[k].push(item);
  });
  return map;
}

const PRIORITY_WEIGHT: Record<string, number> = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1,
};

function computeGroupStats(tickets: Ticket[], groupKey: (t: Ticket) => string) {
  const groups = groupBy(tickets, groupKey);
  return Object.entries(groups)
    .map(([name, items]) => {
      const durations = items
        .map((t) => t.resolutionDurationHours)
        .filter((d): d is number => d !== null);
      const csats = items
        .map((t) => t.csatRating)
        .filter((c): c is number => c !== null);
      const satisfied = items.filter((t) => t.csatSegment === "Satisfeito").length;
      const neutral = items.filter((t) => t.csatSegment === "Neutro").length;
      const unsatisfied = items.filter((t) => t.csatSegment === "Insatisfeito").length;

      const totalWithCsat = satisfied + neutral + unsatisfied;
      const dissatisfactionRate = totalWithCsat > 0 ? unsatisfied / totalWithCsat : 0;
      const avgDur = avg(durations);
      const avgPriorityWeight = avg(items.map((t) => PRIORITY_WEIGHT[t.priority] || 1));

      // Score B: volume × dissatisfaction_rate × avg_duration
      const riscoOperacional = Math.round(
        items.length * dissatisfactionRate * Math.abs(avgDur) * 100
      ) / 100;

      // Score B by Priority: volume × dissatisfaction_rate × avg_duration × priority_weight
      const riscoPrioridade = Math.round(
        items.length * dissatisfactionRate * Math.abs(avgDur) * avgPriorityWeight * 100
      ) / 100;

      return {
        name,
        totalTickets: items.length,
        closedTickets: durations.length,
        avgResolutionHours: Math.round(avgDur * 100) / 100,
        medianResolutionHours: Math.round(median(durations) * 100) / 100,
        avgCsat: Math.round(avg(csats) * 100) / 100,
        medianCsat: Math.round(median(csats) * 100) / 100,
        satisfied,
        neutral,
        unsatisfied,
        dissatisfactionRate: Math.round(dissatisfactionRate * 1000) / 10,
        avgPriorityWeight: Math.round(avgPriorityWeight * 100) / 100,
        riscoOperacional,
        riscoPrioridade,
      };
    })
    .sort((a, b) => b.riscoOperacional - a.riscoOperacional);
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  let tickets = loadTickets();

  // Apply filters
  const channel = searchParams.get("channel");
  const priority = searchParams.get("priority");
  const type = searchParams.get("type");
  const subject = searchParams.get("subject");
  const status = searchParams.get("status");
  const csatSegment = searchParams.get("csatSegment");
  const dateFrom = searchParams.get("dateFrom");
  const dateTo = searchParams.get("dateTo");

  if (channel) tickets = tickets.filter((t) => t.channel === channel);
  if (priority) tickets = tickets.filter((t) => t.priority === priority);
  if (type) tickets = tickets.filter((t) => t.type === type);
  if (subject) tickets = tickets.filter((t) => t.subject === subject);
  if (status) tickets = tickets.filter((t) => t.status === status);
  if (csatSegment) tickets = tickets.filter((t) => t.csatSegment === csatSegment);
  if (dateFrom) tickets = tickets.filter((t) => t.ticketDate && t.ticketDate >= dateFrom);
  if (dateTo) tickets = tickets.filter((t) => t.ticketDate && t.ticketDate <= dateTo);

  const durations = tickets
    .map((t) => t.resolutionDurationHours)
    .filter((d): d is number => d !== null);
  const csats = tickets
    .map((t) => t.csatRating)
    .filter((c): c is number => c !== null);

  const stats = {
    totals: {
      tickets: tickets.length,
      closed: tickets.filter((t) => t.status === "Closed").length,
      open: tickets.filter((t) => t.status === "Open").length,
      pending: tickets.filter((t) => t.status === "Pending Customer Response").length,
      avgResolutionHours: Math.round(avg(durations) * 100) / 100,
      medianResolutionHours: Math.round(median(durations) * 100) / 100,
      avgCsat: Math.round(avg(csats) * 100) / 100,
      satisfied: tickets.filter((t) => t.csatSegment === "Satisfeito").length,
      neutral: tickets.filter((t) => t.csatSegment === "Neutro").length,
      unsatisfied: tickets.filter((t) => t.csatSegment === "Insatisfeito").length,
    },
    byChannel: computeGroupStats(tickets, (t) => t.channel),
    bySubject: computeGroupStats(tickets, (t) => t.subject),
    byPriority: computeGroupStats(tickets, (t) => t.priority),
    byType: computeGroupStats(tickets, (t) => t.type),
    byChannelSubject: computeGroupStats(tickets, (t) => `${t.channel} | ${t.subject}`),
    byChannelPriority: computeGroupStats(tickets, (t) => `${t.channel} | ${t.priority}`),
    byPrioritySubject: computeGroupStats(tickets, (t) => `${t.priority} | ${t.subject}`),
    durationVsCsat: (() => {
      const buckets = ["0-2h", "2-5h", "5-10h", "10-15h", "15-24h"];
      const csatValues = [1, 2, 3, 4, 5];
      const matrix: Record<string, Record<number, number>> = {};
      buckets.forEach((b) => { matrix[b] = {}; csatValues.forEach((c) => { matrix[b][c] = 0; }); });

      tickets.forEach((t) => {
        if (t.resolutionDurationHours === null || t.csatRating === null) return;
        const d = t.resolutionDurationHours;
        let bucket: string;
        if (d < 2) bucket = "0-2h";
        else if (d < 5) bucket = "2-5h";
        else if (d < 10) bucket = "5-10h";
        else if (d < 15) bucket = "10-15h";
        else bucket = "15-24h";
        matrix[bucket][t.csatRating] = (matrix[bucket][t.csatRating] || 0) + 1;
      });

      return { buckets, csatValues, matrix };
    })(),
    correlationBySubject: (() => {
      // Per Subject: Pearson r between duration and CSAT (across all channels)
      const subjects = [...new Set(tickets.map((t) => t.subject))].sort();
      const results = subjects.map((sub) => {
        const pairs = tickets.filter(
          (t) => t.subject === sub && t.resolutionDurationHours !== null && t.csatRating !== null
        );
        const r = pairs.length >= 3
          ? pearsonR(
              pairs.map((t) => t.resolutionDurationHours!),
              pairs.map((t) => t.csatRating!)
            )
          : null;
        const csats = pairs.map((t) => t.csatRating!);
        const durations = pairs.map((t) => t.resolutionDurationHours!);
        const totalTickets = tickets.filter((t) => t.subject === sub).length;
        const closedWithCsat = pairs.length;
        return {
          subject: sub,
          totalTickets,
          closedWithCsat,
          avgCsat: csats.length ? Math.round(avg(csats) * 100) / 100 : null,
          avgDuration: durations.length ? Math.round(avg(durations) * 100) / 100 : null,
          correlation: r,
          impact: r !== null ? Math.round(r * totalTickets * 10) / 10 : 0,
        };
      });
      return results;
    })(),
    correlationDurationCsat: (() => {
      // Per Channel × Subject: Pearson r between duration and CSAT
      const channels = [...new Set(tickets.map((t) => t.channel))].sort();
      const subjects = [...new Set(tickets.map((t) => t.subject))].sort();
      const matrix: Record<string, Record<string, number | null>> = {};

      channels.forEach((ch) => {
        matrix[ch] = {};
        subjects.forEach((sub) => {
          const pairs = tickets.filter(
            (t) => t.channel === ch && t.subject === sub && t.resolutionDurationHours !== null && t.csatRating !== null
          );
          if (pairs.length < 3) {
            matrix[ch][sub] = null;
          } else {
            matrix[ch][sub] = pearsonR(
              pairs.map((t) => t.resolutionDurationHours!),
              pairs.map((t) => t.csatRating!)
            );
          }
        });
      });

      return { channels, subjects, matrix };
    })(),
    filterOptions: {
      channels: [...new Set(tickets.map((t) => t.channel))].sort(),
      priorities: ["Critical", "High", "Medium", "Low"],
      types: [...new Set(tickets.map((t) => t.type))].sort(),
      subjects: [...new Set(tickets.map((t) => t.subject))].sort(),
      statuses: [...new Set(tickets.map((t) => t.status))].sort(),
      csatSegments: ["Satisfeito", "Neutro", "Insatisfeito"],
      dates: [...new Set(tickets.map((t) => t.ticketDate).filter(Boolean) as string[])].sort(),
    },
  };

  return NextResponse.json(stats);
}
