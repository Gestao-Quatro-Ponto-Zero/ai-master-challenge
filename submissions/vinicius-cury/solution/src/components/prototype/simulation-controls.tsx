"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, RotateCcw, Loader2 } from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────

export interface SimulationConfig {
  ticketCount: number;
  channelDistribution: Record<string, number>;
  arrivalPattern: "burst" | "steady";
}

interface SimulationControlsProps {
  onStart: (config: SimulationConfig) => void;
  onReset: () => void;
  isRunning: boolean;
  progress: { generated: number; total: number } | null;
}

// ─── Presets ────────────────────────────────────────────────────────

const TICKET_COUNTS = [1, 5, 10, 20, 50];

const CHANNEL_PRESETS: Record<string, { label: string; distribution: Record<string, number> }> = {
  uniform: {
    label: "Uniforme",
    distribution: { Email: 25, Chat: 25, Phone: 25, "Social media": 25 },
  },
  chat_first: {
    label: "Chat-first",
    distribution: { Chat: 60, Email: 20, Phone: 10, "Social media": 10 },
  },
  realistic: {
    label: "Realista",
    distribution: { Email: 35, Chat: 25, Phone: 25, "Social media": 15 },
  },
};

const ARRIVAL_PATTERNS: { value: "burst" | "steady"; label: string }[] = [
  { value: "burst", label: "Todos de uma vez" },
  { value: "steady", label: "Fluxo constante" },
];

// ─── Component ──────────────────────────────────────────────────────

export function SimulationControls({
  onStart,
  onReset,
  isRunning,
  progress,
}: SimulationControlsProps) {
  const [ticketCount, setTicketCount] = useState(5);
  const [channelPreset, setChannelPreset] = useState("realistic");
  const [arrivalPattern, setArrivalPattern] = useState<"burst" | "steady">("burst");

  function handleStart() {
    const preset = CHANNEL_PRESETS[channelPreset];
    onStart({
      ticketCount,
      channelDistribution: preset.distribution,
      arrivalPattern,
    });
  }

  function handleReset() {
    const confirmed = window.confirm(
      "Tem certeza? Isso irá apagar todas as conversas, mensagens e simulações do protótipo. Os dados de análise não serão afetados."
    );
    if (confirmed) onReset();
  }

  const progressPct =
    progress && progress.total > 0
      ? Math.round((progress.generated / progress.total) * 100)
      : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Controles da Simulação</CardTitle>
        <CardDescription>
          Configure e inicie uma simulação de tickets de suporte
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Ticket count */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Quantidade de tickets</label>
          <div className="flex flex-wrap gap-2">
            {TICKET_COUNTS.map((n) => (
              <Button
                key={n}
                variant={ticketCount === n ? "default" : "outline"}
                size="sm"
                disabled={isRunning}
                onClick={() => setTicketCount(n)}
              >
                {n}
              </Button>
            ))}
          </div>
        </div>

        {/* Channel distribution */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Distribuição de canais</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(CHANNEL_PRESETS).map(([key, preset]) => (
              <Button
                key={key}
                variant={channelPreset === key ? "default" : "outline"}
                size="sm"
                disabled={isRunning}
                onClick={() => setChannelPreset(key)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            {Object.entries(CHANNEL_PRESETS[channelPreset].distribution)
              .map(([ch, pct]) => `${ch}: ${pct}%`)
              .join(" · ")}
          </p>
        </div>

        {/* Arrival pattern */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Padrão de chegada</label>
          <div className="flex flex-wrap gap-2">
            {ARRIVAL_PATTERNS.map((p) => (
              <Button
                key={p.value}
                variant={arrivalPattern === p.value ? "default" : "outline"}
                size="sm"
                disabled={isRunning}
                onClick={() => setArrivalPattern(p.value)}
              >
                {p.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Progress bar */}
        {isRunning && progress && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {progress.generated < progress.total
                  ? "Gerando e classificando tickets..."
                  : "Completo!"}
              </span>
              <span className="font-medium">
                {progress.generated} / {progress.total}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <Button
            onClick={handleStart}
            disabled={isRunning}
            className="flex-1"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processando...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Iniciar Simulação
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={isRunning}
            className="text-destructive hover:text-destructive"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Resetar Dados
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
