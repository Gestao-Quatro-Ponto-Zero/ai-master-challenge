import fs from "fs";
import path from "path";

// ─── Types ───────────────────────────────────────────────────────────

export type Scenario =
  | "acelerar"
  | "desacelerar"
  | "redirecionar"
  | "quarentena"
  | "manter"
  | "liberar";

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

export interface PairDiagnostic {
  channel: string;
  subject: string;
  scenario: Scenario;
  rPair: number | null;
  rSubject: number | null;
  divergence: string | null;
  totalTickets: number;
  closedWithCsat: number;
  avgDuration: number;
  avgCsat: number;
  impact: number;
  bestChannelForSubject: string | null;
  bestChannelCsat: number | null;
  redirectTo: string | null;
  redirectViable: boolean;
}

export interface RoutingResult {
  pairs: PairDiagnostic[];
  routingMatrix: Record<string, Record<string, Scenario | null>>;
  channels: string[];
  subjects: string[];
}

// ─── Constants ───────────────────────────────────────────────────────

// Redirection viability matrix
// Social media as origin = NOT viable (can't pull to other channels)
// Anything → Social media = NOT viable
export const REDIRECT_VIABLE: Record<string, Record<string, boolean>> = {
  Email: { Phone: true, Chat: true, "Social media": false },
  Chat: { Phone: true, Email: true, "Social media": false },
  Phone: { Email: true, Chat: true, "Social media": false },
  "Social media": { Email: true, Phone: true, Chat: false },
};

// ─── Helpers ─────────────────────────────────────────────────────────

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (char === '"') inQuotes = false;
      else current += char;
    } else {
      if (char === '"') inQuotes = true;
      else if (char === ",") {
        result.push(current.trim());
        current = "";
      } else current += char;
    }
  }
  result.push(current.trim());
  return result;
}

let cached: Ticket[] | null = null;

function loadTickets(): Ticket[] {
  if (cached) return cached;
  const csvPath = path.join(
    process.cwd(),
    "data",
    "customer_support_tickets.csv"
  );
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
    headers.forEach((h, idx) => {
      row[h] = values[idx];
    });

    const status = row["Ticket Status"];
    const frt = row["First Response Time"] || null;
    const ttr = row["Time to Resolution"] || null;
    let dur: number | null = null;
    if (status === "Closed" && frt && ttr) {
      const d =
        Math.abs(new Date(ttr).getTime() - new Date(frt).getTime()) / 3600000;
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

export function pearsonR(xs: number[], ys: number[]): number | null {
  const n = xs.length;
  if (n < 3) return null;
  const mx = avg(xs);
  const my = avg(ys);
  let num = 0,
    dx2 = 0,
    dy2 = 0;
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

// ─── Core Routing Logic ─────────────────────────────────────────────

function computeRouting(): RoutingResult {
  const tickets = loadTickets();

  const channels = [...new Set(tickets.map((t) => t.channel))].sort();
  const subjects = [...new Set(tickets.map((t) => t.subject))].sort();

  // Layer 1: Subject-level r
  const subjectR: Record<string, number | null> = {};
  subjects.forEach((sub) => {
    const subTickets = tickets.filter(
      (t) =>
        t.subject === sub &&
        t.resolutionDurationHours !== null &&
        t.csatRating !== null
    );
    subjectR[sub] =
      subTickets.length >= 3
        ? pearsonR(
            subTickets.map((t) => t.resolutionDurationHours!),
            subTickets.map((t) => t.csatRating!)
          )
        : null;
  });

  // Per-subject: channel CSAT ranking
  const subjectChannelCsat: Record<
    string,
    { channel: string; avgCsat: number }[]
  > = {};
  subjects.forEach((sub) => {
    const channelStats = channels
      .map((ch) => {
        const pairTickets = tickets.filter(
          (t) =>
            t.channel === ch &&
            t.subject === sub &&
            t.resolutionDurationHours !== null &&
            t.csatRating !== null
        );
        return {
          channel: ch,
          avgCsat:
            pairTickets.length >= 3
              ? Math.round(avg(pairTickets.map((t) => t.csatRating!)) * 100) /
                100
              : -1,
        };
      })
      .filter((c) => c.avgCsat >= 0);
    subjectChannelCsat[sub] = channelStats.sort(
      (a, b) => b.avgCsat - a.avgCsat
    );
  });

  // Layer 2: Pair-level classification
  const pairs: PairDiagnostic[] = [];

  channels.forEach((ch) => {
    subjects.forEach((sub) => {
      const pairTickets = tickets.filter(
        (t) =>
          t.channel === ch &&
          t.subject === sub &&
          t.resolutionDurationHours !== null &&
          t.csatRating !== null
      );

      if (pairTickets.length < 3) return;

      const durations = pairTickets.map((t) => t.resolutionDurationHours!);
      const csats = pairTickets.map((t) => t.csatRating!);
      const rPair = pearsonR(durations, csats);
      const rSub = subjectR[sub];
      const totalAll = tickets.filter(
        (t) => t.channel === ch && t.subject === sub
      ).length;
      const pairCsat = Math.round(avg(csats) * 100) / 100;
      const pairDuration = Math.round(avg(durations) * 100) / 100;

      // Divergence detection
      let divergence: string | null = null;
      if (rSub !== null && rPair !== null) {
        if (rSub < -0.1 && rPair > 0.3)
          divergence =
            "Assunto sensível ao tempo, mas NESTE canal tempo ajuda";
        else if (rSub > 0.1 && rPair < -0.3)
          divergence =
            "Assunto se beneficia de tempo, mas NESTE canal tempo prejudica";
        else if (Math.abs(rSub) < 0.1 && Math.abs(rPair) > 0.3)
          divergence =
            "No agregado tempo neutro, mas neste par há correlação forte";
      }

      // Best channel for this subject
      const channelStats = subjectChannelCsat[sub] || [];
      const bestChannel = channelStats.length > 0 ? channelStats[0] : null;

      // === DECISION TREE ===
      let scenario: Scenario;
      let redirectTo: string | null = null;
      let redirectViable = false;

      // STEP 1: r(time, CSAT) of the pair
      if (rPair !== null && rPair < -0.3) {
        scenario = "acelerar";
      } else if (rPair !== null && rPair > 0.3) {
        scenario = "desacelerar";
      } else {
        // |r| <= 0.3: Time is NOT a strong factor. Go to Step 2.
        const csatGap = bestChannel ? bestChannel.avgCsat - pairCsat : 0;

        if (csatGap > 0.5 && bestChannel && bestChannel.channel !== ch) {
          // STEP 3: Is redirection viable?
          const viableTarget = channelStats.find(
            (c) =>
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
        rSubject: rSub,
        divergence,
        totalTickets: totalAll,
        closedWithCsat: pairTickets.length,
        avgDuration: pairDuration,
        avgCsat: pairCsat,
        impact: rPair !== null ? Math.round(rPair * totalAll * 10) / 10 : 0,
        bestChannelForSubject: bestChannel?.channel || null,
        bestChannelCsat: bestChannel?.avgCsat || null,
        redirectTo,
        redirectViable,
      });
    });
  });

  pairs.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  // Build routing matrix
  const routingMatrix: Record<string, Record<string, Scenario | null>> = {};
  channels.forEach((ch) => {
    routingMatrix[ch] = {};
    subjects.forEach((sub) => {
      const pair = pairs.find((p) => p.channel === ch && p.subject === sub);
      routingMatrix[ch][sub] = pair?.scenario || null;
    });
  });

  return { pairs, routingMatrix, channels, subjects };
}

// ─── Public API ──────────────────────────────────────────────────────

let routingCache: RoutingResult | null = null;

/** Returns the full routing matrix computed from CSV data */
export function getRoutingMatrix(): RoutingResult {
  if (!routingCache) {
    routingCache = computeRouting();
  }
  return routingCache;
}

/** Returns the scenario for a specific (channel, subject) pair */
export function getScenarioForPair(
  channel: string,
  subject: string
): PairDiagnostic | null {
  const { pairs } = getRoutingMatrix();
  return (
    pairs.find((p) => p.channel === channel && p.subject === subject) || null
  );
}

/** Clears the routing cache (useful for testing) */
export function clearRoutingCache(): void {
  routingCache = null;
  cached = null;
}
