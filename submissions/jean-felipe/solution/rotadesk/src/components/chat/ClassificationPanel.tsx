"use client";

import { Badge } from "@/components/ui/badge";
import type { Ticket } from "@/lib/types";
import { SCENARIO_LABELS, STATUS_LABELS } from "@/lib/types";
import { normalizePtBr } from "@/lib/pt-br";
import { formatPercent } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

interface ClassificationPanelProps {
  ticket: Ticket | null;
  turn: number;
}

const PIPELINE_STEPS = [
  { key: "received", label: "Chamado recebido" },
  { key: "classified", label: "Classificação ML" },
  { key: "routed", label: "Roteamento" },
  { key: "response", label: "Resposta enviada" },
] as const;

function stepState(
  key: (typeof PIPELINE_STEPS)[number]["key"],
  ticket: Ticket | null
): "done" | "active" | "pending" {
  if (!ticket) return "pending";
  switch (key) {
    case "received":
      return "done";
    case "classified":
      return ticket.topic_group ? "done" : "active";
    case "routed":
      if (!ticket.topic_group) return "pending";
      return ticket.scenario ? "done" : "active";
    case "response":
      if (!ticket.scenario) return "pending";
      return ticket.first_response_at ? "done" : "active";
    default:
      return "pending";
  }
}

export function ClassificationPanel({ ticket, turn }: ClassificationPanelProps) {
  return (
    <aside className="flex h-full flex-col rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold">Triagem em tempo real</h3>
        <Badge className="bg-muted text-foreground">Turno: {turn}</Badge>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {!ticket ? (
          <p className="text-sm text-muted-foreground">
            Envie uma mensagem para iniciar a triagem automática.
          </p>
        ) : (
          <>
            <ol className="space-y-3">
              {PIPELINE_STEPS.map((step) => {
                const state = stepState(step.key, ticket);
                return (
                  <li key={step.key} className="flex items-start gap-2.5">
                    {state === "done" ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                    ) : state === "active" ? (
                      <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-blue-600" />
                    ) : (
                      <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground/40" />
                    )}
                    <span
                      className={
                        state === "pending"
                          ? "text-sm text-muted-foreground"
                          : "text-sm font-medium"
                      }
                    >
                      {step.label}
                    </span>
                  </li>
                );
              })}
            </ol>

            <div className="space-y-2 rounded-lg bg-muted/50 p-3 text-sm">
              <Row label="Tópico" value={ticket.topic_group_llm ?? ticket.topic_group ?? "—"} />
              <Row label="Confiança" value={formatPercent(ticket.confidence)} />
              <Row
                label="Cenário"
                value={ticket.scenario ? SCENARIO_LABELS[ticket.scenario] : "—"}
              />
              <Row label="Fila" value={ticket.queue_slug ?? "—"} />
              <Row label="Status" value={STATUS_LABELS[ticket.status]} />
              {ticket.human_required_reason && (
                <p className="mt-2 text-xs text-amber-700">
                  {normalizePtBr(ticket.human_required_reason)}
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </aside>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
