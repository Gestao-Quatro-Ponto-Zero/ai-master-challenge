import { NextRequest, NextResponse } from "next/server";
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

const SCENARIO_ACTIONS: Record<Scenario, string> = {
  acelerar: "Rotear para agentes rápidos — resolver o mais rápido possível.",
  desacelerar: "Rotear para agentes especializados — dar mais tempo e atenção.",
  redirecionar: "Migrar para canal com melhor desempenho para este assunto.",
  quarentena: "Investigar causa raiz — CSAT ruim sem alternativa viável.",
  manter: "Manter no canal atual — desempenho satisfatório.",
  liberar: "Deprioritizar — liberar recursos para pares mais críticos.",
};

interface RoutingResult {
  scenario: Scenario;
  action: string;
  redirectTo: string | null;
  rPair: number | null;
  avgCsat: number;
  avgDuration: number;
  totalTickets: number;
  explanation: string;
}

function buildRoutingMatrix(tickets: Ticket[]) {
  const channels = [...new Set(tickets.map((t) => t.channel))].sort();
  const subjects = [...new Set(tickets.map((t) => t.subject))].sort();

  // Subject-level r
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

  // Build matrix
  const matrix: Record<string, Record<string, RoutingResult>> = {};

  channels.forEach((ch) => {
    matrix[ch] = {};
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

      matrix[ch][sub] = {
        scenario,
        action: SCENARIO_ACTIONS[scenario],
        redirectTo,
        rPair,
        avgCsat: pairCsat,
        avgDuration: pairDuration,
        totalTickets: totalAll,
        explanation: buildExplanation(scenario, ch, sub, rPair, pairCsat, pairDuration, totalAll, redirectTo, bestChannel),
      };
    });
  });

  return matrix;
}

function buildExplanation(
  scenario: Scenario, channel: string, subject: string,
  rPair: number | null, avgCsat: number, avgDuration: number,
  totalTickets: number, redirectTo: string | null,
  bestChannel: { channel: string; avgCsat: number } | null,
): string {
  const base = `Analisamos ${totalTickets} tickets de "${subject}" no canal ${channel}. `;
  const csatStr = `CSAT médio: ${avgCsat.toFixed(2)}, duração média: ${avgDuration.toFixed(1)}h. `;

  switch (scenario) {
    case "acelerar":
      return base + csatStr +
        `A correlação entre tempo e satisfação é negativa (r=${rPair?.toFixed(3)}), indicando que quanto mais tempo o ticket leva, menor a satisfação do cliente. Recomendação: priorizar resolução rápida com agentes experientes.`;
    case "desacelerar":
      return base + csatStr +
        `A correlação entre tempo e satisfação é positiva (r=${rPair?.toFixed(3)}), indicando que tickets que recebem mais atenção e tempo geram maior satisfação. Recomendação: rotear para agentes especializados que possam dedicar mais tempo.`;
    case "redirecionar":
      return base + csatStr +
        `O tempo de resolução não é o fator principal, mas o canal ${channel} tem CSAT inferior ao canal ${redirectTo} (CSAT ${bestChannel?.avgCsat.toFixed(2)}). Recomendação: migrar estes tickets para ${redirectTo} onde o desempenho é comprovadamente melhor.`;
    case "quarentena":
      return base + csatStr +
        `O CSAT está abaixo do aceitável e não há canal alternativo viável com melhor desempenho. Este par precisa de investigação da causa raiz — o problema pode estar no processo, no treinamento, ou na natureza do assunto.`;
    case "manter":
      return base + csatStr +
        `O canal ${channel} apresenta bom desempenho para "${subject}" — CSAT satisfatório e sem indicação de que mudanças trariam melhoria significativa. Manter operação atual.`;
    case "liberar":
      return base + csatStr +
        `Tempo não influencia satisfação e o CSAT é neutro. Este par não é crítico — recursos podem ser realocados para pares com maior impacto operacional.`;
  }
}

let routingMatrix: Record<string, Record<string, RoutingResult>> | null = null;

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { channel, subject, description } = body as {
    channel: string;
    subject: string;
    description: string;
  };

  if (!channel || !subject) {
    return NextResponse.json({ error: "Canal e assunto são obrigatórios." }, { status: 400 });
  }

  const tickets = loadTickets();
  if (!routingMatrix) {
    routingMatrix = buildRoutingMatrix(tickets);
  }

  const result = routingMatrix[channel]?.[subject];

  if (!result) {
    return NextResponse.json({
      scenario: "manter" as Scenario,
      action: SCENARIO_ACTIONS["manter"],
      redirectTo: null,
      rPair: null,
      avgCsat: 0,
      avgDuration: 0,
      totalTickets: 0,
      explanation: `Não há dados suficientes para o par "${channel}" × "${subject}". Sem histórico suficiente (mínimo 3 tickets com CSAT e duração), o sistema mantém o ticket no canal atual por precaução. Descrição recebida: "${description?.slice(0, 100) || "(vazia)"}"`,
    });
  }

  return NextResponse.json({
    ...result,
    explanation: result.explanation + (description ? ` Contexto adicional do ticket: "${description.slice(0, 200)}"` : ""),
  });
}
