import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface Ticket {
  channel: string;
  subject: string;
  priority: string;
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

    tickets.push({
      channel: row["Ticket Channel"],
      subject: row["Ticket Subject"],
      priority: row["Ticket Priority"],
      status,
      resolutionDurationHours: dur,
      csatRating: isNaN(csat) ? null : csat,
    });
  }
  cached = tickets;
  return tickets;
}

function avg(arr: number[]): number {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

// Simple linear regression: y = slope * x + intercept
function linearRegression(points: { x: number; y: number }[]) {
  const n = points.length;
  if (n < 2) return { slope: 0, intercept: 0, r2: 0 };

  const sumX = points.reduce((s, p) => s + p.x, 0);
  const sumY = points.reduce((s, p) => s + p.y, 0);
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0);
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0);
  const sumY2 = points.reduce((s, p) => s + p.y * p.y, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // R²
  const meanY = sumY / n;
  const ssRes = points.reduce((s, p) => s + (p.y - (slope * p.x + intercept)) ** 2, 0);
  const ssTot = points.reduce((s, p) => s + (p.y - meanY) ** 2, 0);
  const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;

  return { slope: Math.round(slope * 10000) / 10000, intercept: Math.round(intercept * 100) / 100, r2: Math.round(r2 * 1000) / 1000 };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const groupBy = searchParams.get("groupBy") || "channelSubject";
  const tickets = loadTickets();

  // Group by selected dimension
  const groups: Record<string, Ticket[]> = {};
  tickets.forEach((t) => {
    let key: string;
    switch (groupBy) {
      case "channelPriority":
        key = `${t.channel} | ${t.priority}`;
        break;
      case "prioritySubject":
        key = `${t.priority} | ${t.subject}`;
        break;
      default:
        key = `${t.channel} | ${t.subject}`;
    }
    if (!groups[key]) groups[key] = [];
    groups[key].push(t);
  });

  // Compute stats per group
  const groupStats = Object.entries(groups).map(([name, items]) => {
    const durations = items.map((t) => t.resolutionDurationHours).filter((d): d is number => d !== null);
    const csats = items.map((t) => t.csatRating).filter((c): c is number => c !== null);
    const unsatisfied = items.filter((t) => t.csatRating !== null && t.csatRating <= 2).length;
    const totalWithCsat = csats.length;
    const dissatisfactionRate = totalWithCsat > 0 ? unsatisfied / totalWithCsat : 0;
    const avgDur = avg(durations);

    return {
      name,
      dim1: name.split(" | ")[0],
      dim2: name.split(" | ")[1],
      totalTickets: items.length,
      avgDuration: Math.round(avgDur * 100) / 100,
      avgCsat: Math.round(avg(csats) * 100) / 100,
      dissatisfactionRate: Math.round(dissatisfactionRate * 1000) / 10,
      riscoOperacional: Math.round(items.length * dissatisfactionRate * Math.abs(avgDur) * 100) / 100,
    };
  });

  // Sort by risco and take worst 25%
  groupStats.sort((a, b) => b.riscoOperacional - a.riscoOperacional);
  const worst25pct = groupStats.slice(0, Math.ceil(groupStats.length * 0.25));
  const rest = groupStats.slice(Math.ceil(groupStats.length * 0.25));

  // Regression on ALL points
  const allPoints = groupStats
    .filter((g) => g.avgDuration > 0 && g.avgCsat > 0)
    .map((g) => ({ x: g.avgDuration, y: g.avgCsat }));
  const regression = linearRegression(allPoints);

  // Regression line endpoints
  const allDurations = groupStats.map((g) => g.avgDuration).filter((d) => d > 0);
  const minX = allDurations.length ? Math.min(...allDurations) : 0;
  const maxX = allDurations.length ? Math.max(...allDurations) : 10;

  // Goal zone: low duration, high CSAT
  // Compute overall averages for reference
  const allGroupDurations = groupStats.map((g) => g.avgDuration).filter((d) => d > 0);
  const allGroupCsats = groupStats.map((g) => g.avgCsat).filter((c) => c > 0);
  const overallAvgDur = avg(allGroupDurations);
  const overallAvgCsat = avg(allGroupCsats);

  return NextResponse.json({
    worst25pct,
    rest,
    regression: {
      ...regression,
      lineStart: { x: minX, y: regression.slope * minX + regression.intercept },
      lineEnd: { x: maxX, y: regression.slope * maxX + regression.intercept },
    },
    goal: {
      maxDuration: Math.round(overallAvgDur * 0.5 * 100) / 100, // target: half the avg duration
      minCsat: 4, // target: CSAT ≥ 4
    },
    overall: {
      avgDuration: Math.round(overallAvgDur * 100) / 100,
      avgCsat: Math.round(overallAvgCsat * 100) / 100,
    },
  });
}
