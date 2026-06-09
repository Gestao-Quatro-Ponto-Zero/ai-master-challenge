"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TicketDetailPanel } from "@/components/kanban/TicketDetailPanel";
import type { Ticket, TicketStatus } from "@/lib/types";
import { SCENARIO_LABELS } from "@/lib/types";
import { cn, formatPercent } from "@/lib/utils";

const COLUMNS: {
  status: TicketStatus;
  label: string;
  header: string;
  column: string;
  badge: string;
  accent: string;
}[] = [
  {
    status: "open",
    label: "Aberto",
    header: "bg-slate-100 text-slate-800",
    column: "bg-slate-50/80 border-slate-200",
    badge: "bg-slate-200 text-slate-800",
    accent: "border-t-slate-400",
  },
  {
    status: "triagem",
    label: "Triagem",
    header: "bg-blue-100 text-blue-900",
    column: "bg-blue-50/60 border-blue-200",
    badge: "bg-blue-200 text-blue-900",
    accent: "border-t-blue-500",
  },
  {
    status: "pending_review",
    label: "Revisão",
    header: "bg-amber-100 text-amber-900",
    column: "bg-amber-50/60 border-amber-200",
    badge: "bg-amber-200 text-amber-900",
    accent: "border-t-amber-500",
  },
  {
    status: "human_required",
    label: "Humano",
    header: "bg-orange-100 text-orange-900",
    column: "bg-orange-50/60 border-orange-200",
    badge: "bg-orange-200 text-orange-900",
    accent: "border-t-orange-500",
  },
  {
    status: "routed",
    label: "Roteado",
    header: "bg-violet-100 text-violet-900",
    column: "bg-violet-50/60 border-violet-200",
    badge: "bg-violet-200 text-violet-900",
    accent: "border-t-violet-500",
  },
  {
    status: "pending_customer",
    label: "Aguardando cliente",
    header: "bg-cyan-100 text-cyan-900",
    column: "bg-cyan-50/60 border-cyan-200",
    badge: "bg-cyan-200 text-cyan-900",
    accent: "border-t-cyan-500",
  },
  {
    status: "closed",
    label: "Resolvido",
    header: "bg-emerald-100 text-emerald-900",
    column: "bg-emerald-50/60 border-emerald-200",
    badge: "bg-emerald-200 text-emerald-900",
    accent: "border-t-emerald-500",
  },
];

const NEXT_STATUS: Partial<Record<TicketStatus, TicketStatus>> = {
  open: "triagem",
  triagem: "routed",
  pending_review: "routed",
  human_required: "pending_customer",
  routed: "pending_customer",
  pending_customer: "closed",
};

export default function KanbanPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function load() {
    fetch("/api/tickets")
      .then((r) => r.json())
      .then((data) => Array.isArray(data) && setTickets(data));
  }

  useEffect(() => {
    load();
  }, []);

  async function moveTicket(id: string, status: TicketStatus, resolved_by?: string) {
    await fetch(`/api/tickets/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        status === "closed" && resolved_by
          ? { resolved_by }
          : { status }
      ),
    });
    load();
  }

  return (
    <DashboardLayout title="Kanban de chamados">
      <TicketDetailPanel ticketId={selectedId} onClose={() => setSelectedId(null)} />
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMNS.map((col) => {
          const items = tickets.filter((t) => t.status === col.status);
          return (
            <div
              key={col.status}
              className={cn(
                "min-w-[260px] shrink-0 rounded-xl border p-3",
                col.column
              )}
            >
              <div
                className={cn(
                  "mb-3 flex items-center justify-between rounded-lg px-3 py-2",
                  col.header
                )}
              >
                <h3 className="text-sm font-semibold">{col.label}</h3>
                <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", col.badge)}>
                  {items.length}
                </span>
              </div>
              <div className="space-y-3">
                {items.map((t) => (
                  <Card
                    key={t.id}
                    className={cn(
                      "cursor-pointer border-t-4 shadow-sm transition-shadow hover:shadow-md",
                      col.accent
                    )}
                    onClick={() => setSelectedId(t.id)}
                  >
                    <CardHeader className="p-4 pb-2">
                      <CardTitle className="text-sm">
                        #{t.ticket_number} · {t.customer_name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 p-4 pt-0 text-xs">
                      <p className="line-clamp-2 text-muted-foreground">{t.subject}</p>
                      <p>{t.channel}</p>
                      <p>{t.topic_group ?? "—"} · {formatPercent(t.confidence)}</p>
                      {t.scenario && (
                        <Badge className="text-[10px]">
                          {SCENARIO_LABELS[t.scenario]}
                        </Badge>
                      )}
                      <div className="flex flex-wrap gap-1 pt-2" onClick={(e) => e.stopPropagation()}>
                        {NEXT_STATUS[t.status] && (
                          <Button
                            variant="outline"
                            className="h-7 px-2 text-xs"
                            onClick={() => moveTicket(t.id, NEXT_STATUS[t.status]!)}
                          >
                            Avançar
                          </Button>
                        )}
                        {t.status !== "closed" && (
                          <Button
                            variant="outline"
                            className="h-7 px-2 text-xs"
                            onClick={() => moveTicket(t.id, "closed", "human")}
                          >
                            Resolver (humano)
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </DashboardLayout>
  );
}
