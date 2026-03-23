import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();

  // Fetch all conversations with relevant fields
  const { data: conversations, error } = await supabase
    .from("conversations")
    .select(
      "id, status, scenario, channel, created_at, resolved_at, updated_at, accepted_at, sla_deadline, csat_rating, assigned_operator_id, turn_count, escalation_tier"
    );

  if (error) {
    return NextResponse.json(
      { error: "Erro ao carregar métricas", details: error.message },
      { status: 500 }
    );
  }

  const all = conversations || [];
  const total = all.length;

  // ─── Volume ─────────────────────────────────────────────────────

  const activeConversations = all.filter(
    (c) =>
      c.status === "active" ||
      c.status === "in_progress" ||
      c.status === "escalated" ||
      c.status === "waiting_operator"
  ).length;

  // ─── Queue ──────────────────────────────────────────────────────

  const queueDepth = all.filter(
    (c) => c.status === "escalated" || c.status === "waiting_operator"
  ).length;

  const inProgress = all.filter((c) => c.status === "in_progress").length;
  const resolved = all.filter((c) => c.status === "resolved").length;
  const closed = all.filter((c) => c.status === "closed").length;

  // ─── Resolution rates ──────────────────────────────────────────

  const closedOrResolved = resolved + closed;
  const resolutionRate =
    closedOrResolved > 0
      ? Math.round((resolved / closedOrResolved) * 1000) / 10
      : 0;

  // Escalation: tickets that went to operator queue
  const escalatedTotal = all.filter(
    (c) =>
      c.status === "escalated" ||
      c.status === "in_progress" ||
      c.status === "waiting_operator"
  ).length;
  const escalationRate =
    total > 0 ? Math.round((escalatedTotal / total) * 1000) / 10 : 0;

  // Deflection: auto-resolved by bot (resolved without going through operator)
  const autoResolved = all.filter(
    (c) => c.status === "resolved" && !c.scenario
  ).length;
  const botResolved = all.filter((c) => c.status === "resolved").length;
  const deflectionRate =
    total > 0 ? Math.round((botResolved / total) * 1000) / 10 : 0;
  const autoResolutionRate =
    total > 0 ? Math.round((resolved / total) * 100) : 0;

  // ─── Scenario distribution ─────────────────────────────────────

  const scenarioCounts: Record<string, number> = {};
  for (const c of all) {
    if (c.scenario) {
      scenarioCounts[c.scenario] = (scenarioCounts[c.scenario] || 0) + 1;
    }
  }
  const scenarioDistribution = Object.entries(scenarioCounts).map(
    ([scenario, count]) => ({ scenario, count })
  );

  // ─── Channel distribution ─────────────────────────────────────

  const channelCounts: Record<string, number> = {};
  for (const c of all) {
    if (c.channel) {
      channelCounts[c.channel] = (channelCounts[c.channel] || 0) + 1;
    }
  }
  const channelDistribution = Object.entries(channelCounts).map(
    ([channel, count]) => ({ channel, count })
  );

  // ─── CSAT ──────────────────────────────────────────────────────

  const csatRatings = all
    .filter((c) => c.csat_rating !== null && c.csat_rating !== undefined)
    .map((c) => c.csat_rating as number);
  const csatCount = csatRatings.length;
  const avgCsat =
    csatCount > 0
      ? Math.round(
          (csatRatings.reduce((a, b) => a + b, 0) / csatCount) * 10
        ) / 10
      : null;

  // ─── SLA compliance ────────────────────────────────────────────

  const withSla = all.filter((c) => c.sla_deadline !== null);
  const slaCompliant = withSla.filter((c) => {
    if (c.status === "resolved" && c.resolved_at && c.sla_deadline) {
      return new Date(c.resolved_at) <= new Date(c.sla_deadline);
    }
    if (c.sla_deadline) {
      return new Date() <= new Date(c.sla_deadline);
    }
    return true;
  });
  const slaComplianceRate =
    withSla.length > 0
      ? Math.round((slaCompliant.length / withSla.length) * 1000) / 10
      : 100;

  // ─── FRT: Average first response time ──────────────────────────
  // Fetch first customer msg and first bot msg per conversation
  let avgFRT = 0;
  const convIds = all.map((c) => c.id);

  if (convIds.length > 0) {
    const { data: msgData } = await supabase
      .from("messages")
      .select("conversation_id, role, created_at")
      .in("conversation_id", convIds.slice(0, 200))
      .in("role", ["customer", "assistant"])
      .order("created_at", { ascending: true });

    if (msgData && msgData.length > 0) {
      // Group by conversation
      const convMessages: Record<
        string,
        { customer_first?: string; assistant_first?: string }
      > = {};
      for (const msg of msgData) {
        const cid = msg.conversation_id;
        if (!convMessages[cid]) convMessages[cid] = {};
        if (msg.role === "customer" && !convMessages[cid].customer_first) {
          convMessages[cid].customer_first = msg.created_at;
        }
        if (msg.role === "assistant" && !convMessages[cid].assistant_first) {
          convMessages[cid].assistant_first = msg.created_at;
        }
      }

      // Calculate FRT for each conversation that has both
      let totalFRT = 0;
      let frtCount = 0;
      for (const cid of Object.keys(convMessages)) {
        const cm = convMessages[cid];
        if (cm.customer_first && cm.assistant_first) {
          const diff =
            (new Date(cm.assistant_first).getTime() -
              new Date(cm.customer_first).getTime()) /
            1000;
          if (diff >= 0) {
            totalFRT += diff;
            frtCount++;
          }
        }
      }
      if (frtCount > 0) {
        avgFRT = Math.round(totalFRT / frtCount);
      }
    }
  }

  // ─── TTR: Average time to resolution ───────────────────────────

  let avgTTR = 0;
  const resolvedConvs = all.filter(
    (c) => c.status === "resolved" && c.resolved_at
  );
  if (resolvedConvs.length > 0) {
    const totalTTR = resolvedConvs.reduce((sum, c) => {
      const created = new Date(c.created_at).getTime();
      const resolvedAt = new Date(c.resolved_at!).getTime();
      return sum + (resolvedAt - created) / 1000;
    }, 0);
    avgTTR = Math.round(totalTTR / resolvedConvs.length);
  }

  // ─── Queue wait time ───────────────────────────────────────────

  let avgQueueWait = 0;
  const queueConvs = all.filter(
    (c) => c.status === "escalated" || c.status === "waiting_operator"
  );
  if (queueConvs.length > 0) {
    const totalWait = queueConvs.reduce((sum, c) => {
      const created = new Date(c.created_at).getTime();
      return sum + (Date.now() - created) / 1000;
    }, 0);
    avgQueueWait = Math.round(totalWait / queueConvs.length);
  }

  // ─── FCR (First Contact Resolution) ────────────────────────────
  // Tickets resolved by the chatbot without operator escalation
  const resolvedAll = all.filter((c) => c.status === "resolved");
  const autoResolvedFCR = resolvedAll.filter(
    (c) => !c.assigned_operator_id
  ).length;
  const fcrRate =
    resolvedAll.length > 0
      ? Math.round((autoResolvedFCR / resolvedAll.length) * 1000) / 10
      : 0;

  // ─── AHT (Average Handle Time) ───────────────────────────────
  // Time between operator accepting (accepted_at) and resolving (resolved_at).
  const operatorResolved = all.filter(
    (c) =>
      c.status === "resolved" &&
      c.assigned_operator_id &&
      c.resolved_at &&
      c.accepted_at
  );
  let avgAHT = 0;
  if (operatorResolved.length > 0) {
    const totalAHT = operatorResolved.reduce((sum, c) => {
      const accepted = new Date(c.accepted_at!).getTime();
      const resolvedTime = new Date(c.resolved_at!).getTime();
      const diff = (resolvedTime - accepted) / 1000;
      return sum + (diff > 0 ? diff : 0);
    }, 0);
    avgAHT = Math.round(totalAHT / operatorResolved.length);
  }

  // ─── Custo Estimado por Ticket ────────────────────────────────
  // OpenAI API call ≈ $0.002 (gpt-4o-mini), embedding ≈ $0.0001
  // ~3 API calls per conversation (classify + sub-classify + response) + 1 embedding
  // Operator time at $15/hour
  const COST_PER_API_CALL = 0.002;
  const COST_PER_EMBEDDING = 0.0001;
  const OPERATOR_HOURLY_RATE = 15;
  const API_CALLS_PER_CONV = 3;

  const totalApiCost = total * (API_CALLS_PER_CONV * COST_PER_API_CALL + COST_PER_EMBEDDING);
  const totalOperatorHours = avgAHT > 0 ? (operatorResolved.length * avgAHT) / 3600 : 0;
  const totalOperatorCost = totalOperatorHours * OPERATOR_HOURLY_RATE;
  const costPerTicket =
    total > 0
      ? Math.round(((totalApiCost + totalOperatorCost) / total) * 10000) / 10000
      : 0;

  // ─── CES (Customer Effort Score) proxy ────────────────────────
  // turn_count + (escalated ? 2 : 0). Normalize to 1-5 scale.
  const resolvedWithTurns = resolvedAll.filter((c) => c.turn_count !== null);
  let avgCES = 0;
  if (resolvedWithTurns.length > 0) {
    const rawScores = resolvedWithTurns.map((c) => {
      let score = c.turn_count ?? 0;
      if (c.assigned_operator_id) score += 2; // escalated
      return score;
    });
    const avgRaw = rawScores.reduce((a, b) => a + b, 0) / rawScores.length;
    // Normalize: 0 turns → 1.0 (best), 10+ turns → 5.0 (worst)
    avgCES = Math.min(5, Math.max(1, Math.round((1 + (avgRaw / 10) * 4) * 10) / 10));
  }

  // ─── Taxa de Reabertura ───────────────────────────────────────
  // Check for customer messages sent after conversation was resolved
  let reopenRate = 0;
  if (resolvedAll.length > 0 && convIds.length > 0) {
    const resolvedIds = resolvedAll.map((c) => c.id);
    const { data: postResolveMessages } = await supabase
      .from("messages")
      .select("conversation_id")
      .in("conversation_id", resolvedIds.slice(0, 200))
      .eq("role", "customer");

    if (postResolveMessages) {
      // Check if any customer message was sent after resolved_at
      const resolvedMap = new Map(
        resolvedAll.map((c) => [c.id, c.resolved_at])
      );
      // We already have message timestamps from the FRT query; for reopens we need a separate check
      const { data: postMsgs } = await supabase
        .from("messages")
        .select("conversation_id, created_at")
        .in("conversation_id", resolvedIds.slice(0, 200))
        .eq("role", "customer")
        .order("created_at", { ascending: false });

      if (postMsgs) {
        const reopenedSet = new Set<string>();
        for (const msg of postMsgs) {
          const resolvedAt = resolvedMap.get(msg.conversation_id);
          if (
            resolvedAt &&
            new Date(msg.created_at).getTime() >
              new Date(resolvedAt).getTime()
          ) {
            reopenedSet.add(msg.conversation_id);
          }
        }
        reopenRate =
          Math.round((reopenedSet.size / resolvedAll.length) * 1000) / 10;
      }
    }
  }

  // ─── Utilização dos Operadores ────────────────────────────────
  const { data: operatorsData } = await supabase
    .from("operators")
    .select("id, active_tickets, max_capacity, status");

  let avgOperatorUtilization = 0;
  if (operatorsData && operatorsData.length > 0) {
    const onlineOps = operatorsData.filter(
      (op) => op.status === "available" || op.status === "busy"
    );
    if (onlineOps.length > 0) {
      const totalUtil = onlineOps.reduce((sum, op) => {
        const cap = op.max_capacity || 5;
        return sum + (op.active_tickets || 0) / cap;
      }, 0);
      avgOperatorUtilization =
        Math.round((totalUtil / onlineOps.length) * 1000) / 10;
    }
  }

  // ─── Response ──────────────────────────────────────────────────

  return NextResponse.json({
    // New KPI fields
    total_conversations: total,
    active_conversations: activeConversations,
    resolution_rate: resolutionRate,
    escalation_rate: escalationRate,
    deflection_rate: deflectionRate,
    avg_first_response_time_seconds: avgFRT,
    avg_time_to_resolution_seconds: avgTTR,
    avg_csat: avgCsat,
    csat_count: csatCount,
    sla_compliance_rate: slaComplianceRate,
    current_queue_depth: queueDepth,
    avg_queue_wait_seconds: avgQueueWait,

    // New computed KPIs
    fcr_rate: fcrRate,
    avg_handle_time_seconds: avgAHT,
    cost_per_ticket: costPerTicket,
    avg_ces: avgCES,
    reopen_rate: reopenRate,
    operator_utilization: avgOperatorUtilization,

    // Legacy fields (backward compatibility with MetricsPanel)
    queue_depth: queueDepth,
    in_progress: inProgress,
    resolved,
    total,
    auto_resolution_rate: autoResolutionRate,
    scenario_distribution: scenarioDistribution,
    channel_distribution: channelDistribution,
  });
}
