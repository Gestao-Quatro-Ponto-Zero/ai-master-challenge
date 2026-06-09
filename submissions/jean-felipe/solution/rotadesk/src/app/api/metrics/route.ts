import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";
import type { DashboardMetrics, Ticket } from "@/lib/types";

export async function GET() {
  try {
    const supabase = createServerClient();
    const { data: tickets, error } = await supabase
      .from("tickets")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });

    const all = (tickets ?? []) as Ticket[];

    const open = all.filter((t) => t.status === "open").length;
    const in_progress = all.filter((t) =>
      ["triagem", "routed", "pending_customer"].includes(t.status)
    ).length;
    const waiting_human = all.filter((t) =>
      ["pending_review", "human_required"].includes(t.status)
    ).length;
    const auto_resolved_ia = all.filter(
      (t) => t.status === "closed" && t.resolved_by === "auto_ia"
    ).length;
    const resolved_total = all.filter((t) => t.status === "closed").length;

    const by_scenario: Record<string, number> = {};
    const by_channel: Record<string, number> = {};
    const by_status: Record<string, number> = {};
    const hourMap: Record<string, number> = {};

    for (const t of all) {
      const sc = t.scenario ?? "sem_cenario";
      by_scenario[sc] = (by_scenario[sc] ?? 0) + 1;
      by_channel[t.channel] = (by_channel[t.channel] ?? 0) + 1;
      by_status[t.status] = (by_status[t.status] ?? 0) + 1;

      const hour = new Date(t.created_at).toLocaleString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      });
      hourMap[hour] = (hourMap[hour] ?? 0) + 1;
    }

    const tickets_per_hour = Object.entries(hourMap)
      .map(([hour, count]) => ({ hour, count }))
      .sort((a, b) => a.hour.localeCompare(b.hour));

    const metrics: DashboardMetrics = {
      open,
      in_progress,
      waiting_human,
      auto_resolved_ia,
      resolved_total,
      by_scenario,
      by_channel,
      by_status,
      tickets_per_hour,
      recent_tickets: all.slice(0, 15),
    };

    return NextResponse.json(metrics);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro" },
      { status: 500 }
    );
  }
}
