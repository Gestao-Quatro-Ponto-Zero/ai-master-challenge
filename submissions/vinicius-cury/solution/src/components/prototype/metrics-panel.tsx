"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Users, Headset, CheckCircle, TrendingUp } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ─── Types ──────────────────────────────────────────────────────────

export interface Metrics {
  queue_depth: number;
  in_progress: number;
  resolved: number;
  total: number;
  auto_resolution_rate: number;
  scenario_distribution: { scenario: string; count: number }[];
  channel_distribution: { channel: string; count: number }[];
}

interface MetricsPanelProps {
  metrics: Metrics;
}

// ─── Scenario Colors ────────────────────────────────────────────────

const SCENARIO_CHART_COLORS: Record<string, string> = {
  acelerar: "#ef4444",
  desacelerar: "#3b82f6",
  redirecionar: "#eab308",
  quarentena: "#6b7280",
  manter: "#22c55e",
  liberar: "#10b981",
};

const SCENARIO_LABELS_PT: Record<string, string> = {
  acelerar: "Acelerar",
  desacelerar: "Desacelerar",
  redirecionar: "Redirecionar",
  quarentena: "Quarentena",
  manter: "Manter",
  liberar: "Liberar",
};

const CHANNEL_COLORS: Record<string, string> = {
  Email: "#3b82f6",
  Chat: "#22c55e",
  Phone: "#a855f7",
  "Social media": "#f97316",
};

// ─── KPI Card ───────────────────────────────────────────────────────

function KPICard({
  title,
  value,
  icon: Icon,
  suffix,
}: {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  suffix?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">
            {value}
            {suffix}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Component ──────────────────────────────────────────────────────

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  const isEmpty = metrics.total === 0;

  if (isEmpty) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <TrendingUp className="mx-auto h-10 w-10" />
        <p className="mt-3 text-sm font-medium">
          Execute uma simulação para ver as métricas
        </p>
        <p className="mt-1 text-xs">
          Use os controles acima para gerar tickets e acompanhar os resultados
          em tempo real.
        </p>
      </div>
    );
  }

  const scenarioData = metrics.scenario_distribution.map((d) => ({
    name: SCENARIO_LABELS_PT[d.scenario] || d.scenario,
    value: d.count,
    color: SCENARIO_CHART_COLORS[d.scenario] || "#94a3b8",
  }));

  const channelData = metrics.channel_distribution.map((d) => ({
    name: d.channel,
    tickets: d.count,
    fill: CHANNEL_COLORS[d.channel] || "#94a3b8",
  }));

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard title="Na Fila" value={metrics.queue_depth} icon={Users} />
        <KPICard title="Em Atendimento" value={metrics.in_progress} icon={Headset} />
        <KPICard title="Resolvidos" value={metrics.resolved} icon={CheckCircle} />
        <KPICard
          title="Taxa de Deflexão"
          value={metrics.auto_resolution_rate}
          icon={TrendingUp}
          suffix="%"
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Scenario Pie Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Distribuição por Cenário</CardTitle>
          </CardHeader>
          <CardContent>
            {scenarioData.length === 0 ? (
              <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Sem dados ainda
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={scenarioData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                    paddingAngle={2}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {scenarioData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Channel Bar Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Distribuição por Canal</CardTitle>
          </CardHeader>
          <CardContent>
            {channelData.length === 0 ? (
              <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Sem dados ainda
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={channelData}>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="tickets" name="Tickets" radius={[4, 4, 0, 0]}>
                    {channelData.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
