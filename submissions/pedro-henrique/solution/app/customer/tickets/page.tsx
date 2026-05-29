"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import { TicketFilters } from "@/components/TicketFilters";
import { TicketTable } from "@/components/TicketTable";
import type { Ticket, TicketCategory, TicketPriority, TicketStatus } from "@/lib/types";

type TicketListResponse = { items?: Ticket[] };
type ClassifyResponse = {
  category?: TicketCategory;
  priority?: TicketPriority;
  error?: string;
};
type CreateTicketResponse = { ticket?: Ticket; error?: string };

export default function CustomerTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | "all">("all");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [modalError, setModalError] = useState("");
  const [feedback, setFeedback] = useState("");

  async function loadTickets() {
    try {
      const response = await fetch("/api/tickets");
      const payload = (await response.json()) as TicketListResponse;
      setTickets(payload.items ?? []);
    } catch {
      setTickets([]);
    }
  }

  useEffect(() => {
    let active = true;

    fetch("/api/tickets")
      .then(async (response) => {
        const payload = (await response.json()) as TicketListResponse;
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

  function openCreateModal() {
    setIsCreateModalOpen(true);
    setModalError("");
  }

  function closeCreateModal() {
    if (creating) return;
    setIsCreateModalOpen(false);
    setDescription("");
    setModalError("");
  }

  function closeCreateModalForced() {
    setIsCreateModalOpen(false);
    setDescription("");
    setModalError("");
  }

  async function handleCreateTicket(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const rawText = description.trim();

    if (!rawText) {
      setModalError("Descreva o problema para criar o ticket.");
      return;
    }

    setCreating(true);
    setModalError("");

    try {
      const classifyResponse = await fetch("/api/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText }),
      });
      const classifyPayload = (await classifyResponse.json()) as ClassifyResponse;
      if (!classifyResponse.ok) {
        throw new Error(classifyPayload.error ?? "Não foi possível classificar o ticket.");
      }

      const createResponse = await fetch("/api/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: "text",
          raw_text: rawText,
          category: classifyPayload.category,
          priority: classifyPayload.priority,
        }),
      });
      const createPayload = (await createResponse.json()) as CreateTicketResponse;
      if (!createResponse.ok || !createPayload.ticket) {
        throw new Error(createPayload.error ?? "Não foi possível criar o ticket.");
      }

      setFeedback(`Ticket #${createPayload.ticket.id} criado com sucesso.`);
      closeCreateModalForced();
      await loadTickets();
    } catch (error) {
      setModalError(error instanceof Error ? error.message : "Erro inesperado ao criar ticket.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="page">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <Image src="/logo-g4.png" alt="Logo G4" width={18} height={18} />
            <p className="text-xs uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Cliente</p>
          </div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--primary))]">Meus tickets</h1>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={openCreateModal}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 hover:bg-slate-50"
          >
            Novo ticket
          </button>
          <a
            href="/api/auth/demo?logout=1"
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 hover:bg-slate-50"
          >
            Sair
          </a>
        </div>
      </header>

      {feedback && (
        <p className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {feedback}
        </p>
      )}

      <TicketFilters
        status={statusFilter}
        priority={priorityFilter}
        onStatusChange={setStatusFilter}
        onPriorityChange={setPriorityFilter}
      />

      <div className="mt-4">
        <TicketTable tickets={filtered} />
      </div>

      {isCreateModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-4"
          onClick={closeCreateModal}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Criar novo ticket"
            className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-5 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">Criar novo ticket</h2>
              <button
                type="button"
                onClick={closeCreateModal}
                className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                aria-label="Fechar modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-3">
              <label className="block text-sm font-medium text-slate-700" htmlFor="ticket-desc">
                Descrição do problema
              </label>
              <textarea
                id="ticket-desc"
                rows={5}
                maxLength={2000}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Descreva seu problema com contexto, erro e impacto."
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-slate-400"
              />

              {modalError && <p className="text-sm text-red-600">{modalError}</p>}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeCreateModal}
                  disabled={creating}
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg border border-[hsl(var(--primary))] bg-[hsl(var(--primary))] px-3 py-2 text-sm font-semibold text-white hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {creating ? "Criando..." : "Criar ticket"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
