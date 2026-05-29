"use client";

import type { TicketPriority, TicketStatus } from "@/lib/types";
import { priorityLabel, statusLabel } from "@/lib/labels";

type TicketFiltersProps = {
  status: TicketStatus | "all";
  priority: TicketPriority | "all";
  onStatusChange: (value: TicketStatus | "all") => void;
  onPriorityChange: (value: TicketPriority | "all") => void;
  theme?: "default" | "admin";
};

export function TicketFilters({
  status,
  priority,
  onStatusChange,
  onPriorityChange,
  theme = "default",
}: TicketFiltersProps) {
  const isAdminTheme = theme === "admin";

  return (
    <div
      className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2"
      style={
        isAdminTheme
          ? {
              borderColor: "var(--ad-border)",
              background: "var(--ad-surface)",
              boxShadow: "var(--ad-shadow)",
            }
          : undefined
      }
    >
      <label className="text-sm">
        <span
          className="mb-1 block text-xs uppercase tracking-wide text-slate-500"
          style={isAdminTheme ? { color: "var(--ad-text-muted)" } : undefined}
        >
          Status
        </span>
        <select
          value={status}
          onChange={(event) => onStatusChange(event.target.value as TicketStatus | "all")}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
          style={
            isAdminTheme
              ? {
                  borderColor: "var(--ad-border)",
                  background: "var(--ad-bg)",
                  color: "var(--ad-text)",
                }
              : undefined
          }
        >
          <option value="all">Todos</option>
          <option value="open">{statusLabel("open")}</option>
          <option value="pending">{statusLabel("pending")}</option>
          <option value="resolved">{statusLabel("resolved")}</option>
          <option value="deflected">{statusLabel("deflected")}</option>
        </select>
      </label>

      <label className="text-sm">
        <span
          className="mb-1 block text-xs uppercase tracking-wide text-slate-500"
          style={isAdminTheme ? { color: "var(--ad-text-muted)" } : undefined}
        >
          Prioridade
        </span>
        <select
          value={priority}
          onChange={(event) => onPriorityChange(event.target.value as TicketPriority | "all")}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
          style={
            isAdminTheme
              ? {
                  borderColor: "var(--ad-border)",
                  background: "var(--ad-bg)",
                  color: "var(--ad-text)",
                }
              : undefined
          }
        >
          <option value="all">Todas</option>
          <option value="low">{priorityLabel("low")}</option>
          <option value="medium">{priorityLabel("medium")}</option>
          <option value="high">{priorityLabel("high")}</option>
          <option value="critical">{priorityLabel("critical")}</option>
        </select>
      </label>
    </div>
  );
}
