import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getOperatorTier, shouldAutoEscalate, escalateTicket } from "@/lib/prototype/escalation";
import type { Scenario } from "@/lib/routing/engine";

// Priority order for scenario-based sorting
const SCENARIO_PRIORITY: Record<string, number> = {
  acelerar: 0,
  quarentena: 1,
  desacelerar: 2,
  redirecionar: 3,
  manter: 4,
  liberar: 5,
};

// ─── GET: List conversations needing operator attention ──────────────

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const scenarioFilter = searchParams.get("scenario");
  const sort = searchParams.get("sort") || "priority";
  const operatorId = searchParams.get("operator_id");

  const supabase = await createClient();

  // ─── SLA Auto-Escalation Check ─────────────────────────────────────
  // Run on every queue view to escalate tickets approaching SLA deadline
  try {
    const { data: slaConversations } = await supabase
      .from("conversations")
      .select("id, created_at, sla_deadline, assigned_operator_id, escalation_tier, status")
      .in("status", ["escalated", "waiting_operator", "in_progress"])
      .not("sla_deadline", "is", null);

    if (slaConversations) {
      for (const conv of slaConversations) {
        const needsEscalation = await shouldAutoEscalate(
          conv as Record<string, unknown>,
          supabase
        );
        if (!needsEscalation) continue;

        const opId = conv.assigned_operator_id as string | null;
        if (!opId) continue;

        const currentTier = (conv.escalation_tier as number) || 1;
        if (currentTier >= 3) continue;

        await escalateTicket(conv.id, opId, supabase);
      }
    }
  } catch {
    // SLA check is best-effort — don't block queue loading
  }

  // If operator_id is provided, fetch operator to determine tier-based filtering
  let operatorLevel: string | null = null;
  let operatorSpecialties: string[] = [];
  if (operatorId) {
    const { data: operator } = await supabase
      .from("operators")
      .select("level, specialties")
      .eq("id", operatorId)
      .single();
    if (operator) {
      operatorLevel = (operator.level as string) || "junior";
      operatorSpecialties = (operator.specialties as string[]) || [];
    }
  }

  // Fetch conversations in operator-relevant statuses
  let query = supabase
    .from("conversations")
    .select("*")
    .in("status", ["escalated", "waiting_operator", "in_progress"]);

  if (scenarioFilter) {
    query = query.eq("scenario", scenarioFilter);
  }

  const { data: conversations, error } = await query;

  if (error) {
    return NextResponse.json(
      { error: "Erro ao carregar fila", details: error.message },
      { status: 500 }
    );
  }

  if (!conversations || conversations.length === 0) {
    return NextResponse.json({ queue: [] });
  }

  // Filter by operator tier if operator_id was provided
  let filteredConversations = conversations;
  if (operatorLevel) {
    const operatorTier = getOperatorTier(operatorLevel);

    filteredConversations = conversations.filter((conv) => {
      const ticketTier = (conv.escalation_tier as number) || 1;

      if (operatorTier === 1) {
        // Junior: sees unescalated tickets (tier 1) matching their specialties
        if (ticketTier > 1) return false;
        // Already assigned to someone else in_progress → skip
        if (conv.status === "in_progress" && conv.assigned_operator_id !== operatorId) return false;
        return true;
      }

      if (operatorTier === 2) {
        // Senior: sees tier 2 escalated tickets OR unhandled tier 1 past 80% SLA
        if (conv.status === "in_progress" && conv.assigned_operator_id !== operatorId) return false;
        if (ticketTier === 2) return true;
        // Check if tier 1 ticket is past 80% SLA
        if (ticketTier === 1 && conv.sla_deadline) {
          const now = Date.now();
          const deadline = new Date(conv.sla_deadline as string).getTime();
          const createdAt = new Date(conv.created_at as string).getTime();
          const totalSla = deadline - createdAt;
          const pctUsed = totalSla > 0 ? 1 - (deadline - now) / totalSla : 1;
          if (pctUsed >= 0.8) return true;
        }
        return false;
      }

      if (operatorTier === 3) {
        // Lead: sees tier 3 tickets OR any critical SLA breach (expired)
        if (conv.status === "in_progress" && conv.assigned_operator_id !== operatorId) return false;
        if (ticketTier === 3) return true;
        // Any SLA breach
        if (conv.sla_deadline) {
          const now = Date.now();
          const deadline = new Date(conv.sla_deadline as string).getTime();
          if (deadline <= now) return true; // expired
        }
        return false;
      }

      return true;
    });
  }

  // Fetch latest message for each conversation
  const conversationIds = filteredConversations.map((c) => c.id);
  const { data: latestMessages } = await supabase
    .from("messages")
    .select("conversation_id, content, role, created_at")
    .in("conversation_id", conversationIds)
    .order("created_at", { ascending: false });

  // Build a map of latest message per conversation
  const latestMessageMap: Record<
    string,
    { content: string; role: string; created_at: string }
  > = {};
  if (latestMessages) {
    for (const msg of latestMessages) {
      if (!latestMessageMap[msg.conversation_id]) {
        latestMessageMap[msg.conversation_id] = msg;
      }
    }
  }

  // Build queue items
  const now = new Date();
  const queue = filteredConversations.map((conv) => {
    const latestMsg = latestMessageMap[conv.id];
    const createdAt = new Date(conv.created_at);
    const timeInQueueMs = now.getTime() - createdAt.getTime();

    // SLA status
    let slaStatus: "green" | "yellow" | "red" | "expired" = "green";
    let slaRemainingMs: number | null = null;
    if (conv.sla_deadline) {
      const deadline = new Date(conv.sla_deadline);
      slaRemainingMs = deadline.getTime() - now.getTime();
      const totalSlaMs = deadline.getTime() - createdAt.getTime();
      const pctRemaining = totalSlaMs > 0 ? slaRemainingMs / totalSlaMs : 0;

      if (slaRemainingMs <= 0) slaStatus = "expired";
      else if (pctRemaining < 0.25) slaStatus = "red";
      else if (pctRemaining < 0.5) slaStatus = "yellow";
      else slaStatus = "green";
    }

    return {
      id: conv.id,
      channel: conv.channel,
      status: conv.status,
      customer_name: conv.customer_name,
      subject_classified: conv.subject_classified,
      category_classified: conv.category_classified,
      scenario: conv.scenario as Scenario | null,
      confidence: conv.confidence,
      assigned_operator_id: conv.assigned_operator_id,
      summary: conv.summary,
      turn_count: conv.turn_count,
      escalation_tier: conv.escalation_tier || 1,
      escalated_from_operator: conv.escalated_from_operator || null,
      sla_deadline: conv.sla_deadline,
      sla_status: slaStatus,
      sla_remaining_ms: slaRemainingMs,
      created_at: conv.created_at,
      updated_at: conv.updated_at,
      time_in_queue_ms: timeInQueueMs,
      latest_message: latestMsg
        ? {
            content:
              latestMsg.content.length > 100
                ? latestMsg.content.slice(0, 100) + "..."
                : latestMsg.content,
            role: latestMsg.role,
            created_at: latestMsg.created_at,
          }
        : null,
    };
  });

  // Sort
  if (sort === "priority") {
    queue.sort((a, b) => {
      const pa = SCENARIO_PRIORITY[a.scenario || "liberar"] ?? 5;
      const pb = SCENARIO_PRIORITY[b.scenario || "liberar"] ?? 5;
      if (pa !== pb) return pa - pb;
      // Within same priority, oldest first
      return (
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    });
  } else {
    // Sort by time (oldest first)
    queue.sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }

  return NextResponse.json({ queue });
}
