"use client";

import { useEffect, useMemo, useState } from "react";

import { TicketFilters } from "@/components/TicketFilters";
import { TicketTable } from "@/components/TicketTable";
import type { Ticket, TicketPriority, TicketStatus } from "@/lib/types";

export default function AdminTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | "all">("all");

  useEffect(() => {
    let active = true;

    fetch("/api/tickets")
      .then(async (response) => {
        const payload = (await response.json()) as { items?: Ticket[] };
        if (active) {
          setTickets(payload.items ?? []);
        }
      })
      .catch(() => {
        if (active) {
          setTickets([]);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return tickets.filter((ticket) => {
      const byStatus = statusFilter === "all" || ticket.status === statusFilter;
      const byPriority = priorityFilter === "all" || ticket.priority === priorityFilter;
      return byStatus && byPriority;
    });
  }, [tickets, statusFilter, priorityFilter]);

  async function updateTicket(id: number, status: TicketStatus, priority: TicketPriority) {
    await fetch("/api/tickets", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, status, priority }),
    });

    const response = await fetch("/api/tickets");
    const payload = (await response.json()) as { items?: Ticket[] };
    setTickets(payload.items ?? []);
  }

  return (
    <>
      <header className="admin-header">
        <nav style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
          <span style={{ color: "var(--ad-text-dim)" }}>Painel</span>
          <span style={{ color: "var(--ad-text-dim)" }}>/</span>
          <span style={{ color: "var(--ad-text)", fontWeight: 500 }}>Tickets</span>
        </nav>
        <a
          href="/admin/kb"
          style={{
            padding: "0.5rem 1rem", borderRadius: 8, fontWeight: 500, fontSize: "0.875rem",
            border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
            color: "var(--ad-text)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "0.375rem",
          }}
        >
          📚 Base de Conhecimento
        </a>
      </header>

      <div className="admin-content">
        <div style={{ marginBottom: "1.75rem" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.03em", color: "var(--ad-text)", lineHeight: 1.15 }}>Gestão de Tickets</h1>
          <p style={{ margin: "0.375rem 0 0", fontSize: "0.9375rem", color: "var(--ad-text-muted)" }}>
            Visualize, filtre e atualize o status dos tickets de suporte
          </p>
        </div>

        <TicketFilters
          status={statusFilter}
          priority={priorityFilter}
          onStatusChange={setStatusFilter}
          onPriorityChange={setPriorityFilter}
          theme="admin"
        />

        <div style={{ marginTop: "1rem" }}>
          <TicketTable tickets={filtered} isAdminView onUpdate={updateTicket} theme="admin" />
        </div>
      </div>
    </>
  );
}
