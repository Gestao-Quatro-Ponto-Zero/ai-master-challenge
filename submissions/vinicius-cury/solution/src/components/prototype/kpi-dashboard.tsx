"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  CheckCircle,
  ArrowUpRight,
  ShieldCheck,
  Clock,
  Timer,
  Star,
  Shield,
  Inbox,
  TrendingUp,
  PhoneCall,
  DollarSign,
  Gauge,
  RotateCcw,
  Users,
  Zap,
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────

export interface KPIData {
  resolution_rate: number;
  escalation_rate: number;
  deflection_rate: number;
  avg_first_response_time_seconds: number;
  avg_time_to_resolution_seconds: number;
  avg_csat: number | null;
  csat_count: number;
  sla_compliance_rate: number;
  current_queue_depth: number;
  total: number;
  // New computed KPIs
  fcr_rate: number;
  avg_handle_time_seconds: number;
  cost_per_ticket: number;
  avg_ces: number;
  reopen_rate: number;
  operator_utilization: number;
}

interface KPIDashboardProps {
  data: KPIData;
}

// ─── Color helpers ──────────────────────────────────────────────────

type ColorLevel = "green" | "yellow" | "red";

const COLOR_CLASSES: Record<ColorLevel, string> = {
  green: "text-emerald-600 dark:text-emerald-400",
  yellow: "text-amber-600 dark:text-amber-400",
  red: "text-red-600 dark:text-red-400",
};

const BG_CLASSES: Record<ColorLevel, string> = {
  green: "bg-emerald-100 dark:bg-emerald-900/30",
  yellow: "bg-amber-100 dark:bg-amber-900/30",
  red: "bg-red-100 dark:bg-red-900/30",
};

const DOT_CLASSES: Record<ColorLevel, string> = {
  green: "bg-emerald-500",
  yellow: "bg-amber-500",
  red: "bg-red-500",
};

// ─── Format helpers ─────────────────────────────────────────────────

function formatSeconds(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m < 60) return `${m}m ${s}s`;
  const h = Math.floor(m / 60);
  const rm = m % 60;
  return `${h}h ${rm}m`;
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function formatCurrency(value: number): string {
  if (value < 0.01) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

// ─── KPI Card ───────────────────────────────────────────────────────

function KPICard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: ColorLevel;
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">{title}</p>
            <p className={cn("text-2xl font-bold tracking-tight", COLOR_CLASSES[color])}>
              {value}
            </p>
          </div>
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              BG_CLASSES[color]
            )}
          >
            <Icon className={cn("h-4.5 w-4.5", COLOR_CLASSES[color])} />
          </div>
        </div>
        <div className="mt-2 flex items-center gap-1.5">
          <span className={cn("inline-block h-2 w-2 rounded-full", DOT_CLASSES[color])} />
          <span className="text-[10px] text-muted-foreground">
            {color === "green" ? "Saudável" : color === "yellow" ? "Atenção" : "Crítico"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function KPIDashboard({ data }: KPIDashboardProps) {
  const isEmpty = data.total === 0;

  if (isEmpty) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <TrendingUp className="mx-auto h-10 w-10" />
        <p className="mt-3 text-sm font-medium">
          Execute uma simulação para ver os KPIs
        </p>
        <p className="mt-1 text-xs">
          Os indicadores serão calculados automaticamente a partir dos dados da simulação.
        </p>
      </div>
    );
  }

  // ─── Color logic per KPI ──────────────────────────────────────

  const resolutionColor: ColorLevel =
    data.resolution_rate >= 80 ? "green" : data.resolution_rate >= 60 ? "yellow" : "red";

  const escalationColor: ColorLevel =
    data.escalation_rate <= 20 ? "green" : data.escalation_rate <= 40 ? "yellow" : "red";

  const deflectionColor: ColorLevel =
    data.deflection_rate >= 30 ? "green" : data.deflection_rate >= 15 ? "yellow" : "red";

  const frtColor: ColorLevel =
    data.avg_first_response_time_seconds <= 60
      ? "green"
      : data.avg_first_response_time_seconds <= 180
        ? "yellow"
        : "red";

  const ttrColor: ColorLevel =
    data.avg_time_to_resolution_seconds <= 7200
      ? "green"
      : data.avg_time_to_resolution_seconds <= 28800
        ? "yellow"
        : "red";

  const csatColor: ColorLevel =
    data.avg_csat !== null
      ? data.avg_csat >= 4.0
        ? "green"
        : data.avg_csat >= 3.0
          ? "yellow"
          : "red"
      : "yellow";

  const slaColor: ColorLevel =
    data.sla_compliance_rate >= 90
      ? "green"
      : data.sla_compliance_rate >= 75
        ? "yellow"
        : "red";

  const queueColor: ColorLevel =
    data.current_queue_depth <= 5
      ? "green"
      : data.current_queue_depth <= 15
        ? "yellow"
        : "red";

  // New KPI colors
  const fcrColor: ColorLevel =
    data.fcr_rate >= 60 ? "green" : data.fcr_rate >= 30 ? "yellow" : "red";

  const ahtColor: ColorLevel =
    data.avg_handle_time_seconds <= 600
      ? "green"
      : data.avg_handle_time_seconds <= 1800
        ? "yellow"
        : "red";

  const costColor: ColorLevel =
    data.cost_per_ticket <= 1.0
      ? "green"
      : data.cost_per_ticket <= 5.0
        ? "yellow"
        : "red";

  const cesColor: ColorLevel =
    data.avg_ces <= 2.0 ? "green" : data.avg_ces <= 3.5 ? "yellow" : "red";

  const reopenColor: ColorLevel =
    data.reopen_rate <= 5 ? "green" : data.reopen_rate <= 15 ? "yellow" : "red";

  const utilizationColor: ColorLevel =
    data.operator_utilization >= 40 && data.operator_utilization <= 80
      ? "green"
      : data.operator_utilization > 80
        ? "red"
        : "yellow";

  // ─── Render ───────────────────────────────────────────────────

  return (
    <KPITabs
      data={data}
      supportKPIs={[
        { title: "Taxa de Resolução", value: formatPercent(data.resolution_rate), icon: CheckCircle, color: resolutionColor },
        { title: "Taxa de Escalação", value: formatPercent(data.escalation_rate), icon: ArrowUpRight, color: escalationColor },
        { title: "Taxa de Deflexão", value: formatPercent(data.deflection_rate), icon: ShieldCheck, color: deflectionColor },
        { title: "Tempo Primeira Resposta", value: formatSeconds(data.avg_first_response_time_seconds), icon: Clock, color: frtColor },
        { title: "Tempo Médio Resolução", value: formatSeconds(data.avg_time_to_resolution_seconds), icon: Timer, color: ttrColor },
        { title: "CSAT Médio", value: data.avg_csat !== null ? `${data.avg_csat}/5.0` : "N/A", icon: Star, color: csatColor },
        { title: "SLA Compliance", value: formatPercent(data.sla_compliance_rate), icon: Shield, color: slaColor },
        { title: "Fila Atual", value: `${data.current_queue_depth} tickets`, icon: Inbox, color: queueColor },
      ]}
      advancedKPIs={[
        { title: "FCR (Resolução 1º Contato)", value: formatPercent(data.fcr_rate), icon: Zap, color: fcrColor },
        { title: "AHT (Tempo Médio Atendimento)", value: data.avg_handle_time_seconds > 0 ? formatSeconds(data.avg_handle_time_seconds) : "N/A", icon: PhoneCall, color: ahtColor },
        { title: "Custo Estimado por Ticket", value: formatCurrency(data.cost_per_ticket), icon: DollarSign, color: costColor },
        { title: "CES (Esforço do Cliente)", value: data.avg_ces > 0 ? `${data.avg_ces.toFixed(1)}/5.0` : "N/A", icon: Gauge, color: cesColor },
        { title: "Taxa de Reabertura", value: formatPercent(data.reopen_rate), icon: RotateCcw, color: reopenColor },
        { title: "Utilização dos Operadores", value: formatPercent(data.operator_utilization), icon: Users, color: utilizationColor },
      ]}
    />
  );
}

// ─── Tabs Component ──────────────────────────────────────────────

interface KPITabEntry {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: ColorLevel;
}

function KPITabs({
  data,
  supportKPIs,
  advancedKPIs,
}: {
  data: KPIData;
  supportKPIs: KPITabEntry[];
  advancedKPIs: KPITabEntry[];
}) {
  const [activeTab, setActiveTab] = useState<"suporte" | "avancados">("suporte");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 rounded-lg border p-1">
          <button
            onClick={() => setActiveTab("suporte")}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium transition-colors",
              activeTab === "suporte"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            Suporte
          </button>
          <button
            onClick={() => setActiveTab("avancados")}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium transition-colors",
              activeTab === "avancados"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            Avançados
          </button>
        </div>
        <span className="text-xs text-muted-foreground">
          {data.total} conversas totais
        </span>
      </div>

      {activeTab === "suporte" ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {supportKPIs.map((kpi) => (
            <KPICard key={kpi.title} {...kpi} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
          {advancedKPIs.map((kpi) => (
            <KPICard key={kpi.title} {...kpi} />
          ))}
        </div>
      )}
    </div>
  );
}
