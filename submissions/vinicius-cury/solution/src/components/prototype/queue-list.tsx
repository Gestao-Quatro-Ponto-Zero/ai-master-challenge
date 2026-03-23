"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import Link from "next/link";
import {
  Mail,
  Phone,
  MessageSquare,
  Share2,
  Clock,
  ArrowUpDown,
  Inbox,
  ArrowUpCircle,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

export interface QueueItem {
  id: string;
  channel: string;
  status: string;
  customer_name: string | null;
  subject_classified: string | null;
  category_classified: string | null;
  scenario: string | null;
  confidence: number | null;
  assigned_operator_id: string | null;
  summary: string | null;
  turn_count: number | null;
  escalation_tier?: number;
  escalated_from_operator?: string | null;
  sla_deadline: string | null;
  sla_status: "green" | "yellow" | "red" | "expired";
  sla_remaining_ms: number | null;
  created_at: string;
  updated_at: string;
  time_in_queue_ms: number;
  latest_message: {
    content: string;
    role: string;
    created_at: string;
  } | null;
}

interface QueueListProps {
  queue: QueueItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  isLoading: boolean;
}

// ─── Constants ───────────────────────────────────────────────────────

const SCENARIO_FILTERS = [
  { key: null, label: "Todos" },
  { key: "acelerar", label: "Acelerar" },
  { key: "quarentena", label: "Quarentena" },
  { key: "desacelerar", label: "Desacelerar" },
  { key: "redirecionar", label: "Redirecionar" },
  { key: "manter", label: "Manter" },
  { key: "liberar", label: "Liberar" },
] as const;

// ─── Helpers ─────────────────────────────────────────────────────────

function getChannelIcon(channel: string) {
  switch (channel?.toLowerCase()) {
    case "email":
      return <Mail className="h-3.5 w-3.5" />;
    case "phone":
    case "telefone":
      return <Phone className="h-3.5 w-3.5" />;
    case "chat":
      return <MessageSquare className="h-3.5 w-3.5" />;
    case "social media":
    case "social":
      return <Share2 className="h-3.5 w-3.5" />;
    default:
      return <MessageSquare className="h-3.5 w-3.5" />;
  }
}

function formatTimeAgo(ms: number): string {
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours}h`;
  const days = Math.floor(hours / 24);
  return `há ${days}d`;
}

function getSlaColorClass(status: "green" | "yellow" | "red" | "expired") {
  switch (status) {
    case "green":
      return "bg-green-500";
    case "yellow":
      return "bg-yellow-500";
    case "red":
      return "bg-red-500";
    case "expired":
      return "bg-red-500 animate-pulse";
  }
}

// ─── Queue Item ──────────────────────────────────────────────────────

function QueueItemCard({
  item,
  isSelected,
  onClick,
  isNew,
}: {
  item: QueueItem;
  isSelected: boolean;
  onClick: () => void;
  isNew: boolean;
}) {
  const truncatedId = item.id.slice(0, 8);

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full rounded-lg border p-3 text-left transition-all hover:bg-muted/50 animate-in fade-in slide-in-from-left-2 duration-300",
        isSelected && "border-primary bg-primary/5 shadow-sm",
        isNew && "border-l-4 border-l-blue-500"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {/* Top row: ID + scenario */}
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-muted-foreground">
              #{truncatedId}
            </span>
            {item.scenario && <ScenarioBadge scenario={item.scenario} />}
            {isNew && (
              <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                Novo
              </span>
            )}
          </div>

          {/* Subject */}
          <p className="mt-1 truncate text-sm font-medium">
            {item.subject_classified || item.customer_name || "Sem assunto"}
          </p>

          {/* Escalation info */}
          {item.escalation_tier && item.escalation_tier > 1 && (
            <div className="mt-0.5 flex items-center gap-1">
              <ArrowUpCircle className="h-3 w-3 text-orange-500" />
              <span className="text-[10px] font-medium text-orange-600">
                Tier {item.escalation_tier}
              </span>
              {item.escalated_from_operator && (
                <span className="text-[10px] text-muted-foreground">
                  — Escalado
                </span>
              )}
            </div>
          )}

          {/* Latest message preview */}
          {item.latest_message && (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {item.latest_message.content}
            </p>
          )}
        </div>

        {/* Right side: channel + time + SLA */}
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1 text-muted-foreground">
            {getChannelIcon(item.channel)}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">
              {formatTimeAgo(item.time_in_queue_ms)}
            </span>
          </div>
          {/* SLA indicator */}
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              getSlaColorClass(item.sla_status)
            )}
            title={
              item.sla_status === "expired"
                ? "SLA expirado"
                : `SLA: ${item.sla_status}`
            }
          />
        </div>
      </div>
    </button>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function QueueList({
  queue,
  selectedId,
  onSelect,
  isLoading,
}: QueueListProps) {
  const [scenarioFilter, setScenarioFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"priority" | "time">("priority");

  // Filter by scenario
  const filtered = scenarioFilter
    ? queue.filter((item) => item.scenario === scenarioFilter)
    : queue;

  // Track items that arrived recently (less than 30 seconds in queue)
  const newItemIds = new Set(
    queue.filter((item) => item.time_in_queue_ms < 30000).map((item) => item.id)
  );

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="border-b pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            Fila ({filtered.length})
          </CardTitle>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() =>
              setSortBy(sortBy === "priority" ? "time" : "priority")
            }
            title={
              sortBy === "priority"
                ? "Ordenar por tempo"
                : "Ordenar por prioridade"
            }
          >
            <ArrowUpDown className="h-3.5 w-3.5" />
          </Button>
        </div>
        {/* Scenario filter buttons */}
        <div className="flex flex-wrap gap-1 pt-2">
          {SCENARIO_FILTERS.map((f) => (
            <button
              key={f.key ?? "all"}
              onClick={() => setScenarioFilter(f.key)}
              className={cn(
                "rounded-full border px-2 py-0.5 text-[10px] font-medium transition-colors",
                scenarioFilter === f.key
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-muted-foreground hover:bg-muted"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[calc(100vh-16rem)]">
          {isLoading && filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="mt-2 text-sm">Carregando fila...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Inbox className="h-10 w-10" />
              <p className="mt-2 text-sm">Nenhum ticket na fila</p>
              <Link
                href="/prototype/simulador"
                className="mt-2 text-xs text-primary underline hover:no-underline"
              >
                Use o Simulador para gerar tickets
              </Link>
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {filtered.map((item) => (
                <QueueItemCard
                  key={item.id}
                  item={item}
                  isSelected={selectedId === item.id}
                  onClick={() => onSelect(item.id)}
                  isNew={newItemIds.has(item.id)}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
