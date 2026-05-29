"use client";

import type { Ticket, TicketPriority, TicketStatus } from "@/lib/types";
import { categoryLabel, priorityLabel, statusLabel } from "@/lib/labels";

type TicketTableProps = {
  tickets: Ticket[];
  isAdminView?: boolean;
  onUpdate?: (id: number, status: TicketStatus, priority: TicketPriority) => Promise<void>;
  theme?: "default" | "admin";
};

const STATUS_OPTIONS: TicketStatus[] = ["open", "pending", "resolved", "deflected"];
const PRIORITY_OPTIONS: TicketPriority[] = ["low", "medium", "high", "critical"];

export function TicketTable({
  tickets,
  isAdminView = false,
  onUpdate,
  theme = "default",
}: TicketTableProps) {
  const isAdminTheme = theme === "admin";

  if (tickets.length === 0) {
    return (
      <div
        className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600"
        style={
          isAdminTheme
            ? {
                borderColor: "var(--ad-border)",
                background: "var(--ad-surface)",
                color: "var(--ad-text-muted)",
                boxShadow: "var(--ad-shadow)",
              }
            : undefined
        }
      >
        Nenhum ticket encontrado com os filtros atuais.
      </div>
    );
  }

  return (
    <div
      className="overflow-x-auto rounded-xl border border-slate-200 bg-white"
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
      <table className="min-w-full text-left text-sm">
        <thead
          className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500"
          style={
            isAdminTheme
              ? {
                  borderColor: "var(--ad-border)",
                  background: "var(--ad-bg)",
                  color: "var(--ad-text-muted)",
                }
              : undefined
          }
        >
          <tr>
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3">Categoria</th>
            <th className="px-4 py-3">Prioridade</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Texto</th>
            <th className="px-4 py-3">Criado em</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr
              key={ticket.id}
              className="border-b border-slate-100 align-top"
              style={isAdminTheme ? { borderColor: "var(--ad-border)", color: "var(--ad-text)" } : undefined}
            >
              <td className="px-4 py-3 font-semibold text-[hsl(var(--accent))]">#{ticket.id}</td>
              <td className="px-4 py-3">{categoryLabel(ticket.category)}</td>
              <td className="px-4 py-3">
                {isAdminView && onUpdate ? (
                  <select
                    value={ticket.priority}
                    onChange={(event) =>
                      onUpdate(ticket.id, ticket.status, event.target.value as TicketPriority)
                    }
                    className="rounded border border-slate-300 bg-white px-2 py-1 text-xs"
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
                    {PRIORITY_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {priorityLabel(option)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span>{priorityLabel(ticket.priority)}</span>
                )}
              </td>
              <td className="px-4 py-3">
                {isAdminView && onUpdate ? (
                  <select
                    value={ticket.status}
                    onChange={(event) =>
                      onUpdate(ticket.id, event.target.value as TicketStatus, ticket.priority)
                    }
                    className="rounded border border-slate-300 bg-white px-2 py-1 text-xs"
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
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {statusLabel(option)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span>{statusLabel(ticket.status)}</span>
                )}
              </td>
              <td
                className="max-w-md px-4 py-3 text-slate-700"
                style={isAdminTheme ? { color: "var(--ad-text)" } : undefined}
              >
                {ticket.raw_text}
              </td>
              <td
                className="px-4 py-3 text-slate-500"
                style={isAdminTheme ? { color: "var(--ad-text-muted)" } : undefined}
              >
                {new Date(ticket.created_at).toLocaleString("pt-BR")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
