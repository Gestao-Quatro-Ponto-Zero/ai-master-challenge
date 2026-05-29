import { readFile } from "node:fs/promises";
import path from "node:path";

import { NextRequest } from "next/server";

import { getDemoUser, isAdmin } from "@/lib/auth";
import { fail, ok } from "@/lib/api";
import { getDeflectionMetrics } from "@/lib/mock-db";

export async function GET(request: NextRequest) {
  const user = getDemoUser(request);

  if (!user) {
    return fail("Não autenticado", 401);
  }

  if (!isAdmin(user)) {
    return fail("Acesso permitido apenas para admin", 403);
  }

  const filePath = path.join(process.cwd(), "public", "insights.json");

  try {
    const data = await readFile(filePath, "utf-8");
    const parsed = JSON.parse(data) as Record<string, unknown>;
    const runtimeMetrics = getDeflectionMetrics();
    const persistedDeflection =
      (parsed.deflection_metrics as Record<string, unknown> | undefined) ?? {};

    return ok({
      ...parsed,
      deflection_metrics: {
        ...persistedDeflection,
        ...runtimeMetrics,
      },
    });
  } catch {
    return ok({
      generated_at: new Date().toISOString(),
      data_source: "runtime_fallback",
      ticket_status_summary: {
        total_tickets: 0,
        open_tickets: 0,
        pending_tickets: 0,
        closed_tickets: 0,
        resolved_tickets: 0,
        resolved_definition: "tickets fechados com CSAT >= 4",
      },
      channel_bottlenecks: [],
      ticket_type_analysis: [],
      customer_satisfaction: {
        positive_count: 0,
        neutral_count: 0,
        negative_count: 0,
        positive_pct: 0,
        neutral_pct: 0,
        negative_pct: 0,
        sample_size: 0,
      },
      calculation_rationale: [],
      flow_bottlenecks: [],
      csat_drivers: [],
      waste_estimation: {
        recoverable_hours: 0,
        recoverable_brl: 0,
      },
      automation_patterns: [],
      deflection_metrics: getDeflectionMetrics(),
    });
  }
}
