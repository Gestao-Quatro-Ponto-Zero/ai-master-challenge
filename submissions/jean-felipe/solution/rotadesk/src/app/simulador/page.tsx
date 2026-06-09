"use client";

import { useState } from "react";
import {
  Activity,
  Loader2,
  Mail,
  MessageSquare,
  Phone,
  Play,
  RotateCcw,
  Share2,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import simulationSamples from "@/data/simulation-samples.json";
import { pickRandomChannel, pickSamples } from "@/lib/simulation";
import type { Ticket, TicketChannel } from "@/lib/types";
import { SCENARIO_LABELS, STATUS_LABELS } from "@/lib/types";
import { cn, formatDateTime, formatPercent } from "@/lib/utils";

type SimStatus = "idle" | "running" | "done" | "error";

const CHANNEL_ICONS: Record<TicketChannel, typeof MessageSquare> = {
  Chat: MessageSquare,
  Email: Mail,
  Phone: Phone,
  "Social media": Share2,
};

export default function SimuladorPage() {
  const [quantity, setQuantity] = useState(5);
  const [status, setStatus] = useState<SimStatus>("idle");
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [feed, setFeed] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);

  const running = status === "running";

  async function startSimulation() {
    if (quantity === 0) return;

    setStatus("running");
    setError(null);
    setFeed([]);
    setProgress({ current: 0, total: quantity });

    const pool = simulationSamples as typeof simulationSamples;
    const payloads = pickSamples(pool, quantity).map((sample) => ({
      ...sample,
      channel: pickRandomChannel(),
    }));

    const created: Ticket[] = [];

    try {
      for (let i = 0; i < payloads.length; i++) {
        const p = payloads[i];
        const res = await fetch("/api/tickets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(p),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error ?? "Falha ao criar ticket");

        created.unshift(data);
        setFeed([...created]);
        setProgress({ current: i + 1, total: quantity });
      }
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro na simulação");
      setStatus("error");
    }
  }

  async function resetData() {
    if (!confirm("Apagar todos os tickets gerados? Esta ação não pode ser desfeita.")) return;
    setStatus("running");
    setError(null);
    try {
      const res = await fetch("/api/simulate/reset", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Falha ao resetar");
      setFeed([]);
      setProgress({ current: 0, total: 0 });
      setStatus("idle");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao resetar");
      setStatus("error");
    }
  }

  const statusLabel =
    status === "idle"
      ? "Aguardando início..."
      : status === "running"
        ? progress.total > 0
          ? `Processando ${progress.current}/${progress.total} chamados...`
          : "Resetando dados..."
        : status === "done"
          ? `${feed.length} tickets gerados com sucesso.`
          : "Simulação interrompida.";

  return (
    <DashboardLayout title="Simulador de tickets">
      <div className="mx-auto max-w-4xl space-y-6">
        <p className="text-sm text-muted-foreground">
          Gere chamados a partir do dataset DS1. Os canais são atribuídos aleatoriamente a cada
          ticket.
        </p>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Configuração da simulação</CardTitle>
            <p className="text-sm text-muted-foreground">
              Escolha quantos tickets deseja gerar (0 a 30).
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium">Quantidade de tickets</p>
                <span className="text-2xl font-bold tabular-nums">{quantity}</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                step={1}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                disabled={running}
                className="h-2 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary disabled:opacity-50"
              />
              <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>30</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <Button
                onClick={startSimulation}
                disabled={running || quantity === 0}
                className="min-w-[200px] gap-2"
              >
                {running && progress.total > 0 ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Iniciar simulação
              </Button>
              <Button
                variant="outline"
                onClick={resetData}
                disabled={running}
                className="gap-2 border-red-300 text-red-600 hover:bg-red-50"
              >
                <RotateCcw className="h-4 w-4" />
                Limpar tickets
              </Button>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}
          </CardContent>
        </Card>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity
            className={cn("h-4 w-4", running && "animate-pulse text-emerald-600")}
          />
          <span>{statusLabel}</span>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Feed de tickets</CardTitle>
          </CardHeader>
          <CardContent>
            {feed.length === 0 ? (
              <p className="py-16 text-center text-sm text-muted-foreground">
                Nenhum ticket gerado ainda. Ajuste a quantidade e inicie a simulação.
              </p>
            ) : (
              <ul className="max-h-[480px] space-y-3 overflow-y-auto pr-1">
                {feed.map((t) => (
                  <TicketFeedItem key={t.id} ticket={t} />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

function TicketFeedItem({ ticket }: { ticket: Ticket }) {
  const Icon = CHANNEL_ICONS[ticket.channel] ?? MessageSquare;

  return (
    <li className="flex gap-3 rounded-xl border border-border bg-muted/20 p-4 transition-colors hover:bg-muted/40">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold">#{ticket.ticket_number}</span>
          <Badge>{ticket.channel}</Badge>
          {ticket.scenario && (
            <Badge className="bg-blue-50 text-blue-800">
              {SCENARIO_LABELS[ticket.scenario]}
            </Badge>
          )}
          <span className="ml-auto text-xs text-muted-foreground">
            {formatDateTime(ticket.created_at)}
          </span>
        </div>
        <p className="truncate text-sm font-medium">{ticket.subject}</p>
        <p className="line-clamp-2 text-xs text-muted-foreground">{ticket.description}</p>
        <div className="flex flex-wrap gap-3 pt-1 text-xs text-muted-foreground">
          <span>{ticket.customer_name}</span>
          <span>{STATUS_LABELS[ticket.status]}</span>
          <span>{ticket.topic_group ?? "—"}</span>
          <span>Confiança: {formatPercent(ticket.confidence)}</span>
        </div>
      </div>
    </li>
  );
}
