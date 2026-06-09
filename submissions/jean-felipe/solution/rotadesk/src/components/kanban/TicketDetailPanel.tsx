"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Wand2, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { normalizePtBr } from "@/lib/pt-br";
import type { Ticket, TicketMessage } from "@/lib/types";
import { SCENARIO_LABELS, STATUS_LABELS } from "@/lib/types";
import { cn, formatDateTime, formatPercent } from "@/lib/utils";

interface TicketDetail extends Ticket {
  ticket_messages?: TicketMessage[];
}

interface TicketDetailPanelProps {
  ticketId: string | null;
  onClose: () => void;
}

export function TicketDetailPanel({ ticketId, onClose }: TicketDetailPanelProps) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [draft, setDraft] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticketId) {
      setTicket(null);
      setDraft(null);
      setDraftError(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    setDraft(null);
    setDraftError(null);

    fetch(`/api/tickets/${ticketId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setTicket(data);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Erro ao carregar ticket"))
      .finally(() => setLoading(false));
  }, [ticketId]);

  async function generateDraft() {
    if (!ticketId) return;
    setDraftLoading(true);
    setDraftError(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: ticketId, mode: "draft" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Falha ao gerar rascunho");
      setDraft(data.content ?? null);
    } catch (e) {
      setDraftError(e instanceof Error ? e.message : "Erro ao gerar rascunho");
    } finally {
      setDraftLoading(false);
    }
  }

  if (!ticketId) return null;

  const messages = (ticket?.ticket_messages ?? []).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-40 bg-black/30"
        aria-label="Fechar detalhes"
        onClick={onClose}
      />
      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col border-l border-border bg-card shadow-xl">
        <header className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <p className="text-xs text-muted-foreground">Detalhes do chamado</p>
            <h2 className="text-lg font-semibold">
              {ticket ? `#${ticket.ticket_number} · ${ticket.customer_name}` : "Carregando..."}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-muted"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Carregando detalhes...
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          {ticket && !loading && (
            <div className="space-y-6">
              <section className="space-y-2">
                <h3 className="text-sm font-semibold">Sobre o chamado</h3>
                <p className="text-sm font-medium">{ticket.subject}</p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {ticket.description}
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <Badge>{ticket.channel}</Badge>
                  <Badge>{ticket.ticket_type}</Badge>
                  <Badge>{ticket.ticket_priority}</Badge>
                </div>
              </section>

              <section className="space-y-2 rounded-xl bg-muted/40 p-4">
                <h3 className="text-sm font-semibold">Como está sendo tratado</h3>
                <DetailRow label="Status" value={STATUS_LABELS[ticket.status]} />
                <DetailRow
                  label="Cenário"
                  value={ticket.scenario ? SCENARIO_LABELS[ticket.scenario] : "—"}
                />
                <DetailRow
                  label="Classificação"
                  value={ticket.topic_group_llm ?? ticket.topic_group ?? "—"}
                />
                <DetailRow label="Confiança" value={formatPercent(ticket.confidence)} />
                <DetailRow label="Fila" value={ticket.queue_slug ?? "—"} />
                {ticket.human_required_reason && (
                  <p className="text-xs text-amber-800">
                    {normalizePtBr(ticket.human_required_reason)}
                  </p>
                )}
                {ticket.ack_message && (
                  <div className="mt-2 rounded-lg border border-dashed border-border bg-card p-3 text-xs">
                    <p className="mb-1 font-medium text-muted-foreground">Confirmação enviada</p>
                    <p>{normalizePtBr(ticket.ack_message)}</p>
                  </div>
                )}
                {ticket.resolved_by && (
                  <DetailRow
                    label="Resolução"
                    value={ticket.resolved_by === "auto_ia" ? "Automática (IA)" : "Humana"}
                  />
                )}
              </section>

              <section className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Wand2 className="h-4 w-4 text-blue-600" />
                    <h3 className="text-sm font-semibold">Rascunho sugerido (RAG)</h3>
                  </div>
                  <Button
                    variant="outline"
                    className="h-8 gap-1.5 px-3 text-xs"
                    onClick={generateDraft}
                    disabled={draftLoading}
                  >
                    {draftLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Wand2 className="h-3.5 w-3.5" />
                    )}
                    {draft ? "Regenerar" : "Gerar rascunho"}
                  </Button>
                </div>
                {draftLoading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Gerando sugestão com IA...
                  </div>
                )}
                {!draftLoading && draft && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50/80 p-3 text-sm text-blue-900 whitespace-pre-wrap">
                    {normalizePtBr(draft)}
                  </div>
                )}
                {!draftLoading && !draft && !draftError && (
                  <p className="text-sm text-muted-foreground">
                    Clique em &quot;Gerar rascunho&quot; para obter uma sugestão de resposta com IA.
                  </p>
                )}
                {draftError && <p className="text-sm text-red-600">{draftError}</p>}
              </section>

              {messages.length > 0 && (
                <section className="space-y-2">
                  <h3 className="text-sm font-semibold">Histórico de mensagens</h3>
                  <ul className="space-y-2">
                    {messages.map((m) => (
                      <li
                        key={m.id}
                        className={cn(
                          "rounded-lg p-3 text-xs",
                          m.role === "customer"
                            ? "bg-primary/5"
                            : m.role === "agent"
                              ? "bg-muted"
                              : "border border-dashed text-muted-foreground"
                        )}
                      >
                        <p className="mb-1 font-medium">
                          {m.role === "customer"
                            ? "Cliente"
                            : m.role === "agent"
                              ? "RotaDesk"
                              : "Sistema"}{" "}
                          · {formatDateTime(m.created_at)}
                        </p>
                        <p className="whitespace-pre-wrap">{normalizePtBr(m.content)}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </div>

        {ticket && (
          <footer className="border-t border-border px-5 py-4">
            <Link
              href={`/chat?ticket=${ticket.id}`}
              className="inline-flex w-full items-center justify-center rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              Abrir no atendimento
            </Link>
          </footer>
        )}
      </aside>
    </>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
