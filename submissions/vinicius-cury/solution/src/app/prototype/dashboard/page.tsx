"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import { KPIDashboard, type KPIData } from "@/components/prototype/kpi-dashboard";
import { SLAGauge } from "@/components/prototype/sla-gauge";
import {
  Users,
  Headset,
  CheckCircle,
  TrendingUp,
  MessageSquare,
  Clock,
} from "lucide-react";
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
  LineChart,
  Line,
} from "recharts";

// ─── Types ──────────────────────────────────────────────────────────

interface Metrics {
  queue_depth: number;
  in_progress: number;
  resolved: number;
  total: number;
  auto_resolution_rate: number;
  scenario_distribution: { scenario: string; count: number }[];
  channel_distribution: { channel: string; count: number }[];
}

interface MetricsResponse extends Metrics {
  total_conversations: number;
  active_conversations: number;
  resolution_rate: number;
  escalation_rate: number;
  deflection_rate: number;
  avg_first_response_time_seconds: number;
  avg_time_to_resolution_seconds: number;
  avg_csat: number | null;
  csat_count: number;
  sla_compliance_rate: number;
  current_queue_depth: number;
  avg_queue_wait_seconds: number;
  // New computed KPIs
  fcr_rate: number;
  avg_handle_time_seconds: number;
  cost_per_ticket: number;
  avg_ces: number;
  reopen_rate: number;
  operator_utilization: number;
}

const EMPTY_KPI: KPIData = {
  resolution_rate: 0,
  escalation_rate: 0,
  deflection_rate: 0,
  avg_first_response_time_seconds: 0,
  avg_time_to_resolution_seconds: 0,
  avg_csat: null,
  csat_count: 0,
  sla_compliance_rate: 100,
  current_queue_depth: 0,
  total: 0,
  fcr_rate: 0,
  avg_handle_time_seconds: 0,
  cost_per_ticket: 0,
  avg_ces: 0,
  reopen_rate: 0,
  operator_utilization: 0,
};

interface Conversation {
  id: string;
  customer_name: string;
  channel: string;
  category_classified: string | null;
  subject_classified: string | null;
  scenario: string | null;
  status: string;
  confidence: number | null;
  created_at: string;
}

interface Operator {
  id: string;
  name: string;
  status: string;
  active_conversations: number;
  max_conversations: number;
  resolved_count: number;
}

// ─── Constants ──────────────────────────────────────────────────────

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

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  active: { label: "Ativo", color: "#3b82f6" },
  escalated: { label: "Escalonado", color: "#f97316" },
  waiting_operator: { label: "Aguardando Operador", color: "#eab308" },
  in_progress: { label: "Em Atendimento", color: "#a855f7" },
  resolved: { label: "Resolvido", color: "#22c55e" },
};

// ─── Dashboard Page ─────────────────────────────────────────────────

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [kpiData, setKpiData] = useState<KPIData>(EMPTY_KPI);
  const [slaRate, setSlaRate] = useState(100);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [operators, setOperators] = useState<Operator[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const router = useRouter();

  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, convsRes, opsRes] = await Promise.all([
        fetch("/api/prototype/metrics"),
        fetch("/api/prototype/conversations"),
        fetch("/api/prototype/operators"),
      ]);

      if (metricsRes.ok) {
        const data: MetricsResponse = await metricsRes.json();
        setMetrics(data);
        setKpiData({
          resolution_rate: data.resolution_rate,
          escalation_rate: data.escalation_rate,
          deflection_rate: data.deflection_rate,
          avg_first_response_time_seconds: data.avg_first_response_time_seconds,
          avg_time_to_resolution_seconds: data.avg_time_to_resolution_seconds,
          avg_csat: data.avg_csat,
          csat_count: data.csat_count,
          sla_compliance_rate: data.sla_compliance_rate,
          current_queue_depth: data.current_queue_depth,
          total: data.total,
          fcr_rate: data.fcr_rate,
          avg_handle_time_seconds: data.avg_handle_time_seconds,
          cost_per_ticket: data.cost_per_ticket,
          avg_ces: data.avg_ces,
          reopen_rate: data.reopen_rate,
          operator_utilization: data.operator_utilization,
        });
        setSlaRate(data.sla_compliance_rate);
      }

      if (convsRes.ok) {
        const data = await convsRes.json();
        setConversations(data.conversations || []);
      }

      if (opsRes.ok) {
        const data = await opsRes.json();
        setOperators(data.operators || []);
      }

      setError(null);
    } catch {
      setError("Erro ao carregar dados do dashboard.");
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ─── Derived data ─────────────────────────────────────────────────

  // Filter conversations by date range
  const filteredConversations = conversations.filter((c) => {
    if (!dateFrom && !dateTo) return true;
    const d = c.created_at.slice(0, 10); // YYYY-MM-DD
    if (dateFrom && d < dateFrom) return false;
    if (dateTo && d > dateTo) return false;
    return true;
  });

  const scenarioData = (metrics?.scenario_distribution || []).map((d) => ({
    name: SCENARIO_LABELS_PT[d.scenario] || d.scenario,
    value: d.count,
    color: SCENARIO_CHART_COLORS[d.scenario] || "#94a3b8",
  }));

  const channelData = (metrics?.channel_distribution || []).map((d) => ({
    name: d.channel,
    tickets: d.count,
    fill: CHANNEL_COLORS[d.channel] || "#94a3b8",
  }));

  // Status distribution
  const statusCounts: Record<string, number> = {};
  for (const c of filteredConversations) {
    statusCounts[c.status] = (statusCounts[c.status] || 0) + 1;
  }
  const statusData = Object.entries(statusCounts).map(([status, count]) => ({
    name: STATUS_CONFIG[status]?.label || status,
    value: count,
    fill: STATUS_CONFIG[status]?.color || "#94a3b8",
  }));

  // Timeline: conversations created per hour
  const hourCounts: Record<string, number> = {};
  for (const c of filteredConversations) {
    const date = new Date(c.created_at);
    const hourKey = `${date.getHours().toString().padStart(2, "0")}:00`;
    hourCounts[hourKey] = (hourCounts[hourKey] || 0) + 1;
  }
  const timelineData = Object.entries(hourCounts)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, count]) => ({ hour, conversas: count }));

  // Recent conversations (last 50)
  const recentConversations = filteredConversations.slice(0, 50);

  // ─── Render ───────────────────────────────────────────────────────

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center justify-between border-b bg-background px-6 py-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Dashboard do Protótipo
          </h1>
          <p className="text-sm text-muted-foreground">
            Visão agregada de todas as conversas, operadores e métricas do
            protótipo.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">De</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-9 w-[140px] rounded-md border border-input bg-transparent px-2 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Até</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-9 w-[140px] rounded-md border border-input bg-transparent px-2 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
          {(dateFrom || dateTo) && (
            <button
              onClick={() => { setDateFrom(""); setDateTo(""); }}
              className="mt-4 text-xs text-muted-foreground hover:text-foreground underline"
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex-1 space-y-6 overflow-y-auto p-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <KPICard
            title="Total de Conversas"
            value={metrics?.total ?? 0}
            icon={MessageSquare}
          />
          <KPICard
            title="Na Fila"
            value={metrics?.queue_depth ?? 0}
            icon={Clock}
          />
          <KPICard
            title="Em Atendimento"
            value={metrics?.in_progress ?? 0}
            icon={Headset}
          />
          <KPICard
            title="Resolvidos"
            value={metrics?.resolved ?? 0}
            icon={CheckCircle}
          />
          <KPICard
            title="Resolucao Automatica"
            value={metrics?.auto_resolution_rate ?? 0}
            icon={TrendingUp}
            suffix="%"
          />
        </div>

        {/* KPI Dashboard (8 detailed KPIs) */}
        <KPIDashboard data={kpiData} />

        {/* SLA Gauge */}
        {metrics && metrics.total > 0 && (
          <div className="grid gap-4 md:grid-cols-3">
            <SLAGauge complianceRate={slaRate} />
            <div className="md:col-span-2" />
          </div>
        )}

        {/* Charts Row 1: Scenario + Channel */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Scenario Donut */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Distribuicao por Cenario
              </CardTitle>
            </CardHeader>
            <CardContent>
              {scenarioData.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={scenarioData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      dataKey="value"
                      paddingAngle={2}
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {scenarioData.map((entry, index) => (
                        <Cell key={`sc-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Channel Bar */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Distribuicao por Canal
              </CardTitle>
            </CardHeader>
            <CardContent>
              {channelData.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={channelData}>
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="tickets"
                      name="Tickets"
                      radius={[4, 4, 0, 0]}
                    >
                      {channelData.map((entry, index) => (
                        <Cell key={`ch-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2: Status + Timeline */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Status Horizontal Bar */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Distribuicao por Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              {statusData.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={statusData} layout="vertical">
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={{ fontSize: 12 }}
                      width={140}
                    />
                    <Tooltip />
                    <Bar dataKey="value" name="Conversas" radius={[0, 4, 4, 0]}>
                      {statusData.map((entry, index) => (
                        <Cell key={`st-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Conversas por Hora
              </CardTitle>
            </CardHeader>
            <CardContent>
              {timelineData.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={timelineData}>
                    <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="conversas"
                      name="Conversas"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Operator Summary */}
        {operators.length > 0 && (
          <div>
            <h2 className="mb-3 text-lg font-semibold">Operadores</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
              {operators.map((op) => (
                <Card key={op.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <Users className="h-4 w-4 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold">
                          {op.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {op.active_conversations}/{op.max_conversations} ativos
                          {" | "}
                          {op.resolved_count ?? 0} resolvidos
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Recent Tickets Table */}
        <div>
          <h2 className="mb-3 text-lg font-semibold">Conversas Recentes</h2>
          <Card>
            <CardContent className="p-0">
              <div className="max-h-[480px] overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 border-b bg-muted/50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">
                        Cliente
                      </th>
                      <th className="px-4 py-2 text-left font-medium">
                        Canal
                      </th>
                      <th className="px-4 py-2 text-left font-medium">
                        Classificação
                      </th>
                      <th className="px-4 py-2 text-left font-medium">
                        Cenário
                      </th>
                      <th className="px-4 py-2 text-left font-medium">
                        Status
                      </th>
                      <th className="px-4 py-2 text-right font-medium">
                        Confiança
                      </th>
                      <th className="px-4 py-2 text-right font-medium">
                        Criado
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {recentConversations.length === 0 ? (
                      <tr>
                        <td
                          colSpan={7}
                          className="px-4 py-8 text-center text-muted-foreground"
                        >
                          Nenhuma conversa registrada ainda.
                        </td>
                      </tr>
                    ) : (
                      recentConversations.map((c) => (
                        <tr
                          key={c.id}
                          className="cursor-pointer transition-colors hover:bg-muted/50"
                          onClick={() =>
                            router.push(
                              `/prototype/operador?conversation=${c.id}`
                            )
                          }
                        >
                          <td className="px-4 py-2 font-medium">
                            {c.customer_name || "—"}
                          </td>
                          <td className="px-4 py-2">{c.channel || "—"}</td>
                          <td className="px-4 py-2">
                            {c.category_classified ? (
                              <div>
                                <span>{c.category_classified}</span>
                                {c.subject_classified && (
                                  <span className="ml-1 text-xs text-muted-foreground">
                                    / {c.subject_classified}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-xs text-muted-foreground">Aguardando</span>
                            )}
                          </td>
                          <td className="px-4 py-2">
                            {c.scenario ? (
                              <ScenarioBadge scenario={c.scenario} />
                            ) : (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </td>
                          <td className="px-4 py-2">
                            <span
                              className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                              style={{
                                backgroundColor:
                                  (STATUS_CONFIG[c.status]?.color || "#94a3b8") +
                                  "20",
                                color:
                                  STATUS_CONFIG[c.status]?.color || "#94a3b8",
                              }}
                            >
                              {STATUS_CONFIG[c.status]?.label || c.status}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right">
                            {c.confidence != null
                              ? `${Math.round(c.confidence * 100)}%`
                              : "—"}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-right text-muted-foreground">
                            {new Date(c.created_at).toLocaleTimeString("pt-BR", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ─── Helper Components ──────────────────────────────────────────────

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

function EmptyChart() {
  return (
    <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
      Sem dados ainda
    </div>
  );
}
