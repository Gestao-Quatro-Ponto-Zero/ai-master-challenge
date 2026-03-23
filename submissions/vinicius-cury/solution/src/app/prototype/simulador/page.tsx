"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/page-header";
import {
  SimulationControls,
  type SimulationConfig,
} from "@/components/prototype/simulation-controls";
import {
  MetricsPanel,
  type Metrics,
} from "@/components/prototype/metrics-panel";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity } from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────

interface RecentTicket {
  id: string;
  channel: string;
  status: string;
  customer_name: string;
  subject_classified: string | null;
  scenario: string | null;
  created_at: string;
}

const EMPTY_METRICS: Metrics = {
  queue_depth: 0,
  in_progress: 0,
  resolved: 0,
  total: 0,
  auto_resolution_rate: 0,
  scenario_distribution: [],
  channel_distribution: [],
};

const STATUS_LABELS: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  active: { label: "Ativo", variant: "outline" },
  escalated: { label: "Escalonado", variant: "destructive" },
  waiting_operator: { label: "Aguardando", variant: "secondary" },
  in_progress: { label: "Em Atendimento", variant: "default" },
  resolved: { label: "Resolvido", variant: "secondary" },
};

// ─── Page Component ─────────────────────────────────────────────────

export default function SimuladorPage() {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState<{ generated: number; total: number } | null>(null);
  const [metrics, setMetrics] = useState<Metrics>(EMPTY_METRICS);
  const [recentTickets, setRecentTickets] = useState<RecentTicket[]>([]);
  const [statusText, setStatusText] = useState("Aguardando...");

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const metricTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ─── Fetch helpers ──────────────────────────────────────────────

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch("/api/prototype/metrics");
      if (res.ok) {
        const data = await res.json();
        setMetrics({
          queue_depth: data.queue_depth,
          in_progress: data.in_progress,
          resolved: data.resolved,
          total: data.total,
          auto_resolution_rate: data.auto_resolution_rate,
          scenario_distribution: data.scenario_distribution,
          channel_distribution: data.channel_distribution,
        });
      }
    } catch {
      // Silently handle metrics fetch failures
    }
  }, []);

  const fetchRecentTickets = useCallback(async () => {
    try {
      const res = await fetch("/api/prototype/conversations");
      if (res.ok) {
        const data = await res.json();
        setRecentTickets(
          (data.conversations || []).slice(0, 50).map((c: Record<string, unknown>) => ({
            id: c.id,
            channel: c.channel,
            status: c.status,
            customer_name: c.customer_name,
            subject_classified: c.subject_classified,
            scenario: c.scenario,
            created_at: c.created_at,
          }))
        );
      }
    } catch {
      // Silently handle fetch failures
    }
  }, []);

  // ─── Initial load ─────────────────────────────────────────────

  useEffect(() => {
    fetchMetrics();
    fetchRecentTickets();
  }, [fetchMetrics, fetchRecentTickets]);

  // ─── Cleanup timers on unmount ────────────────────────────────

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      if (metricTimerRef.current) clearInterval(metricTimerRef.current);
    };
  }, []);

  // ─── Start simulation ─────────────────────────────────────────

  async function handleStart(config: SimulationConfig) {
    setIsRunning(true);
    setStatusText("Gerando tickets...");
    setProgress({ generated: 0, total: config.ticketCount });

    try {
      const startPromise = fetch("/api/prototype/simulation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      metricTimerRef.current = setInterval(() => {
        fetchMetrics();
        fetchRecentTickets();
      }, 3000);

      const res = await startPromise;

      if (res.ok) {
        const data = await res.json();
        setSimulationId(data.simulation_id);
        setProgress({
          generated: data.tickets_generated,
          total: config.ticketCount,
        });
        setStatusText("Completo!");
      } else {
        const err = await res.json();
        setStatusText(`Erro: ${err.error || "Falha na simulação"}`);
      }
    } catch {
      setStatusText("Erro de conexão");
    } finally {
      setIsRunning(false);
      if (metricTimerRef.current) {
        clearInterval(metricTimerRef.current);
        metricTimerRef.current = null;
      }
      fetchMetrics();
      fetchRecentTickets();
    }
  }

  // ─── Reset ────────────────────────────────────────────────────

  async function handleReset() {
    setStatusText("Resetando...");
    try {
      const res = await fetch("/api/prototype/simulation/reset", {
        method: "POST",
      });
      if (res.ok) {
        setSimulationId(null);
        setProgress(null);
        setMetrics(EMPTY_METRICS);
        setRecentTickets([]);
        setStatusText("Aguardando...");
      } else {
        setStatusText("Erro ao resetar");
      }
    } catch {
      setStatusText("Erro de conexão");
    }
  }

  // ─── Render ───────────────────────────────────────────────────

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Simulador de Tickets"
        description="Gere tickets de suporte a partir do dataset real e acompanhe métricas em tempo real."
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Controls */}
        <div data-walkthrough="simulation-controls">
          <SimulationControls
            onStart={handleStart}
            onReset={handleReset}
            isRunning={isRunning}
            progress={progress}
          />
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="h-4 w-4" />
          <span>{statusText}</span>
          {simulationId && (
            <span className="font-mono text-xs">
              (ID: {simulationId.slice(0, 8)}...)
            </span>
          )}
        </div>

        {/* Distribution charts */}
        {metrics.total > 0 && (
          <MetricsPanel metrics={metrics} />
        )}

        {/* Live Feed */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Feed de Tickets</CardTitle>
          </CardHeader>
          <CardContent>
            {recentTickets.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                Nenhum ticket gerado ainda. Inicie uma simulação.
              </div>
            ) : (
              <ScrollArea className="h-64">
                <div className="space-y-2">
                  {recentTickets.map((ticket) => {
                    const statusInfo = STATUS_LABELS[ticket.status] || {
                      label: ticket.status,
                      variant: "outline" as const,
                    };
                    return (
                      <div
                        key={ticket.id}
                        className="flex items-center justify-between rounded-md border p-3 text-sm"
                      >
                        <div className="flex items-center gap-3 overflow-hidden">
                          <div className="min-w-0">
                            <p className="truncate font-medium">
                              {ticket.subject_classified || "Classificando..."}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {ticket.customer_name} · {ticket.channel}
                            </p>
                          </div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          {ticket.scenario && (
                            <ScenarioBadge scenario={ticket.scenario} />
                          )}
                          <Badge variant={statusInfo.variant}>
                            {statusInfo.label}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
