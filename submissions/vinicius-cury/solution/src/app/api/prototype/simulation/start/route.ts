import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";
import { findBestOperator } from "@/lib/prototype/escalation";
import fs from "fs";
import path from "path";

// ─── Input Validation ────────────────────────────────────────────────

const StartSimulationInput = z.object({
  ticketCount: z.number().int().min(1).max(100),
  channelDistribution: z.record(z.string(), z.number()),
  subjectFocus: z.array(z.string()).optional(),
  arrivalPattern: z.enum(["burst", "steady", "random"]),
  ticketsPerMinute: z.number().optional(),
  timeSpread: z.boolean().optional(),
});

// ─── Time Spread Distribution ──────────────────────────────────────

/**
 * Generates a backdated timestamp based on ticket index within total count.
 * Distribution: 15% 3-4h ago, 25% 1-2h ago, 30% 30-60min ago, 30% 0-15min ago
 */
function getBackdatedTimestamp(index: number, total: number): Date {
  const ratio = index / total;
  const now = Date.now();
  let minutesAgo: number;

  if (ratio < 0.15) {
    // First 15%: 180-240 min ago
    minutesAgo = 180 + Math.random() * 60;
  } else if (ratio < 0.40) {
    // Next 25%: 60-120 min ago
    minutesAgo = 60 + Math.random() * 60;
  } else if (ratio < 0.70) {
    // Next 30%: 30-60 min ago
    minutesAgo = 30 + Math.random() * 30;
  } else {
    // Last 30%: 0-15 min ago
    minutesAgo = Math.random() * 15;
  }

  return new Date(now - minutesAgo * 60 * 1000);
}

/**
 * Determines status for a ticket based on its index.
 * Distribution: 30% resolved, 15% in_progress, 40% escalated, 15% active
 */
function getTicketStatus(index: number, total: number): string {
  const ratio = index / total;
  if (ratio < 0.30) return "resolved";
  if (ratio < 0.45) return "in_progress";
  if (ratio < 0.85) return "escalated";
  return "active";
}

// ─── SLA deadlines by scenario (in minutes) ──────────────────────────

const SLA_MINUTES: Record<string, number> = {
  acelerar: 30,
  quarentena: 60,
  desacelerar: 240,
  redirecionar: 120,
  manter: 480,
  liberar: 1440,
};

// ─── CSV Parsing ────────────────────────────────────────────────────

interface CSVTicket {
  ticketId: string;
  customerName: string;
  subject: string;
  type: string;
  priority: string;
  channel: string;
  description: string;
}

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

let csvCache: CSVTicket[] | null = null;

function loadCSVTickets(): CSVTicket[] {
  if (csvCache) return csvCache;
  const csvPath = path.join(process.cwd(), "data", "customer_support_tickets.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const lines = content.split("\n");
  const headers = parseCSVLine(lines[0]);
  const tickets: CSVTicket[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const values = parseCSVLine(line);
    if (values.length !== headers.length) continue;
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h] = values[idx];
    });

    const desc = row["Ticket Description"] || "";
    if (!desc || desc.length < 10) continue;

    tickets.push({
      ticketId: row["Ticket ID"],
      customerName: row["Customer Name"] || "Cliente",
      subject: row["Ticket Subject"],
      type: row["Ticket Type"],
      priority: row["Ticket Priority"],
      channel: row["Ticket Channel"],
      description: desc,
    });
  }
  csvCache = tickets;
  return tickets;
}

// ─── Sampling ───────────────────────────────────────────────────────

function sampleTickets(
  count: number,
  channelDistribution: Record<string, number>,
  subjectFocus?: string[]
): CSVTicket[] {
  const allTickets = loadCSVTickets();

  // Filter by subject focus if provided
  let pool = subjectFocus?.length
    ? allTickets.filter((t) => subjectFocus.includes(t.subject))
    : allTickets;

  if (pool.length === 0) pool = allTickets;

  // Compute per-channel counts
  const channels = Object.keys(channelDistribution);
  const totalPct = Object.values(channelDistribution).reduce((a, b) => a + b, 0);
  const channelCounts: Record<string, number> = {};
  let assigned = 0;
  channels.forEach((ch, i) => {
    if (i === channels.length - 1) {
      channelCounts[ch] = count - assigned;
    } else {
      const n = Math.round((channelDistribution[ch] / totalPct) * count);
      channelCounts[ch] = n;
      assigned += n;
    }
  });

  const result: CSVTicket[] = [];

  for (const ch of channels) {
    const channelPool = pool.filter((t) => t.channel === ch);
    const needed = channelCounts[ch];

    if (channelPool.length === 0) {
      // Fallback: sample from full pool and override channel
      for (let i = 0; i < needed; i++) {
        const ticket = { ...pool[Math.floor(Math.random() * pool.length)] };
        ticket.channel = ch;
        result.push(ticket);
      }
    } else {
      for (let i = 0; i < needed; i++) {
        const ticket = { ...channelPool[Math.floor(Math.random() * channelPool.length)] };
        result.push(ticket);
      }
    }
  }

  return result;
}

// ─── Main Handler ───────────────────────────────────────────────────

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const parsed = StartSimulationInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { ticketCount, channelDistribution, subjectFocus, arrivalPattern, timeSpread } = parsed.data;
  const supabase = await createClient();

  // Create simulation run record
  const { data: simRun, error: simError } = await supabase
    .from("simulation_runs")
    .insert({
      config: { ticketCount, channelDistribution, subjectFocus, arrivalPattern, timeSpread },
      status: "running",
      tickets_generated: 0,
      tickets_classified: 0,
      tickets_resolved: 0,
    })
    .select()
    .single();

  if (simError || !simRun) {
    return NextResponse.json(
      { error: "Erro ao criar simulação", details: simError?.message },
      { status: 500 }
    );
  }

  const simulationId = simRun.id;

  // Sample tickets from CSV
  const sampledTickets = sampleTickets(ticketCount, channelDistribution, subjectFocus);

  // Determine base URL for internal API calls
  const baseUrl =
    process.env.NEXT_PUBLIC_SITE_URL ||
    (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");

  // Process tickets in batches of 4
  const BATCH_SIZE = 4;
  let totalGenerated = 0;
  let totalClassified = 0;
  let totalResolved = 0;

  for (let batchStart = 0; batchStart < sampledTickets.length; batchStart += BATCH_SIZE) {
    // Check if simulation was cancelled
    const { data: currentRun } = await supabase
      .from("simulation_runs")
      .select("status")
      .eq("id", simulationId)
      .single();

    if (currentRun?.status === "cancelled") break;

    const batch = sampledTickets.slice(batchStart, batchStart + BATCH_SIZE);

    const batchResults = await Promise.all(
      batch.map(async (ticket, batchIdx) => {
        try {
          const globalIdx = batchStart + batchIdx;

          // Compute backdated timestamp if timeSpread is enabled
          const createdAt = timeSpread
            ? getBackdatedTimestamp(globalIdx, sampledTickets.length)
            : new Date();

          // Determine target status when timeSpread is enabled
          const targetStatus = timeSpread
            ? getTicketStatus(globalIdx, sampledTickets.length)
            : null;

          // 1. Create conversation with optional backdated timestamp
          const insertData: Record<string, unknown> = {
            channel: ticket.channel,
            customer_name: ticket.customerName,
            status: "active",
            turn_count: 0,
            identity_state: "support",
          };
          if (timeSpread) {
            insertData.created_at = createdAt.toISOString();
            insertData.updated_at = createdAt.toISOString();
          }

          const { data: conv, error: convError } = await supabase
            .from("conversations")
            .insert(insertData)
            .select()
            .single();

          if (convError || !conv) return { generated: false, classified: false, resolved: false };

          // 2. Insert customer message with same timestamp
          const msgInsert: Record<string, unknown> = {
            conversation_id: conv.id,
            role: "customer",
            content: ticket.description,
          };
          if (timeSpread) {
            msgInsert.created_at = createdAt.toISOString();
          }
          await supabase.from("messages").insert(msgInsert);

          // 3. Classify ticket
          let classResult: {
            category: string;
            subject: string;
            scenario: string;
            confidence: number;
            kb_suggestion: { title: string; content: string } | null;
          } | null = null;

          try {
            const classRes = await fetch(`${baseUrl}/api/prototype/classify`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                text: ticket.description,
                channel: ticket.channel,
              }),
            });

            if (classRes.ok) {
              classResult = await classRes.json();
            }
          } catch {
            // Classification failed — use fallback
          }

          if (!classResult) {
            classResult = {
              category: "Software",
              subject: ticket.subject,
              scenario: "manter",
              confidence: 0,
              kb_suggestion: null,
            };
          }

          // 4. Compute SLA deadline relative to created_at (not now())
          const scenario = classResult.scenario || "manter";
          const slaMinutes = SLA_MINUTES[scenario] || 480;
          const slaDeadline = new Date(createdAt.getTime() + slaMinutes * 60 * 1000).toISOString();

          // 5. Determine outcome based on timeSpread status or default logic
          const effectiveStatus = targetStatus || (
            classResult.kb_suggestion !== null && Math.random() < 0.5 ? "resolved" : "escalated"
          );

          if (effectiveStatus === "resolved") {
            const kbTitle = classResult.kb_suggestion?.title || `Resolução: ${classResult.subject}`;
            const resolvedAt = timeSpread
              ? new Date(createdAt.getTime() + (5 + Math.random() * 20) * 60 * 1000)
              : new Date();

            await supabase.from("messages").insert({
              conversation_id: conv.id,
              role: "assistant",
              content: `Resolução automática via base de conhecimento: ${kbTitle}`,
              metadata: { type: "auto_resolution", kb_title: kbTitle },
              ...(timeSpread ? { created_at: new Date(createdAt.getTime() + 2 * 60 * 1000).toISOString() } : {}),
            });

            await supabase
              .from("conversations")
              .update({
                status: "resolved",
                subject_classified: classResult.subject,
                category_classified: classResult.category,
                scenario,
                confidence: classResult.confidence,
                sla_deadline: slaDeadline,
                resolved_at: resolvedAt.toISOString(),
                updated_at: resolvedAt.toISOString(),
              })
              .eq("id", conv.id);

            return { generated: true, classified: true, resolved: true };
          } else if (effectiveStatus === "in_progress") {
            // In-progress: classified + assigned to operator (will be assigned after main loop)
            await supabase
              .from("conversations")
              .update({
                status: "in_progress",
                subject_classified: classResult.subject,
                category_classified: classResult.category,
                scenario,
                confidence: classResult.confidence,
                sla_deadline: slaDeadline,
                summary: `${classResult.category} — ${classResult.subject}`,
                updated_at: new Date().toISOString(),
              })
              .eq("id", conv.id);

            return { generated: true, classified: true, resolved: false };
          } else if (effectiveStatus === "active") {
            // Active: still in chat, classified but no resolution yet
            await supabase
              .from("conversations")
              .update({
                status: "active",
                subject_classified: classResult.subject,
                category_classified: classResult.category,
                scenario,
                confidence: classResult.confidence,
                sla_deadline: slaDeadline,
                updated_at: new Date().toISOString(),
              })
              .eq("id", conv.id);

            return { generated: true, classified: true, resolved: false };
          } else {
            // Escalated (default)
            await supabase.from("messages").insert({
              conversation_id: conv.id,
              role: "system",
              content: "Ticket escalonado para fila de operadores.",
              metadata: { type: "escalation" },
              ...(timeSpread ? { created_at: new Date(createdAt.getTime() + 2 * 60 * 1000).toISOString() } : {}),
            });

            await supabase
              .from("conversations")
              .update({
                status: "escalated",
                subject_classified: classResult.subject,
                category_classified: classResult.category,
                scenario,
                confidence: classResult.confidence,
                sla_deadline: slaDeadline,
                summary: `${classResult.category} — ${classResult.subject}`,
                updated_at: new Date().toISOString(),
              })
              .eq("id", conv.id);

            return { generated: true, classified: true, resolved: false };
          }
        } catch {
          return { generated: false, classified: false, resolved: false };
        }
      })
    );

    // Aggregate batch results
    for (const r of batchResults) {
      if (r.generated) totalGenerated++;
      if (r.classified) totalClassified++;
      if (r.resolved) totalResolved++;
    }

    // Update simulation progress
    await supabase
      .from("simulation_runs")
      .update({
        tickets_generated: totalGenerated,
        tickets_classified: totalClassified,
        tickets_resolved: totalResolved,
      })
      .eq("id", simulationId);
  }

  // ─── Post-loop: Assign in_progress tickets to operators via intelligent routing ─
  if (timeSpread) {
    // Get in_progress tickets without assigned operator
    const { data: inProgressConvs } = await supabase
      .from("conversations")
      .select("id, subject_classified, category_classified, scenario")
      .eq("status", "in_progress")
      .is("assigned_operator_id", null);

    if (inProgressConvs) {
      for (const conv of inProgressConvs) {
        const bestOp = await findBestOperator(
          conv.scenario as string | null,
          conv.category_classified as string | null,
          1,
          supabase
        );

        if (bestOp) {
          await supabase
            .from("conversations")
            .update({
              assigned_operator_id: bestOp.id,
              accepted_at: new Date().toISOString(),
            })
            .eq("id", conv.id);

          // Atomically increment operator active_tickets
          await supabase.rpc("increment_active_tickets", { operator_id: bestOp.id });
        }
        // If no operator found, leave in queue (status stays 'in_progress')
      }
    }

    // Also assign escalated tickets without operator
    const { data: escalatedConvs } = await supabase
      .from("conversations")
      .select("id, subject_classified, category_classified, scenario")
      .eq("status", "escalated")
      .is("assigned_operator_id", null);

    if (escalatedConvs) {
      for (const conv of escalatedConvs) {
        const bestOp = await findBestOperator(
          conv.scenario as string | null,
          conv.category_classified as string | null,
          1,
          supabase
        );

        if (bestOp) {
          await supabase
            .from("conversations")
            .update({
              assigned_operator_id: bestOp.id,
              status: "waiting_operator",
            })
            .eq("id", conv.id);

          await supabase.rpc("increment_active_tickets", { operator_id: bestOp.id });
        }
        // If no operator found, leave as escalated in queue
      }
    }
  }

  // Mark simulation as complete
  await supabase
    .from("simulation_runs")
    .update({
      status: "completed",
      tickets_generated: totalGenerated,
      tickets_classified: totalClassified,
      tickets_resolved: totalResolved,
      completed_at: new Date().toISOString(),
    })
    .eq("id", simulationId);

  return NextResponse.json({
    simulation_id: simulationId,
    status: "completed",
    tickets_generated: totalGenerated,
    tickets_classified: totalClassified,
    tickets_resolved: totalResolved,
  });
}
