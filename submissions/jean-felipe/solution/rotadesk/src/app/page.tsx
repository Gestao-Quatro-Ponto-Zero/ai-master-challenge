"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DashboardMetrics } from "@/lib/types";
import { SCENARIO_LABELS, STATUS_LABELS } from "@/lib/types";
import { formatDateTime, formatPercent } from "@/lib/utils";

const COLORS = ["#2563eb", "#16a34a", "#ca8a04", "#dc2626", "#9333ea", "#0891b2", "#ea580c", "#64748b"];

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/metrics")
      .then((r) => r.json())
      .then((data) => {
        if (data.error) setError(data.error);
        else setMetrics(data);
      })
      .catch(() => setError("Falha ao carregar métricas"))
      .finally(() => setLoading(false));
  }, []);

  const scenarioData = metrics
    ? Object.entries(metrics.by_scenario).map(([key, value]) => ({
        name: SCENARIO_LABELS[key as keyof typeof SCENARIO_LABELS] ?? key,
        value,
      }))
    : [];

  const channelData = metrics
    ? Object.entries(metrics.by_channel).map(([name, value]) => ({ name, value }))
    : [];

  const statusData = metrics
    ? Object.entries(metrics.by_status).map(([key, value]) => ({
        name: STATUS_LABELS[key as keyof typeof STATUS_LABELS] ?? key,
        value,
      }))
    : [];

  return (
    <DashboardLayout title="Dashboard">
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}. Configure o Supabase em `.env.local` e rode a migration.
        </div>
      )}

      {loading ? (
        <p className="text-muted-foreground">Carregando métricas...</p>
      ) : metrics ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <MetricCard title="Em aberto" value={metrics.open} />
            <MetricCard title="Em andamento" value={metrics.in_progress} />
            <MetricCard title="Aguardando humano" value={metrics.waiting_human} />
            <MetricCard title="Resolvidos por IA" value={metrics.auto_resolved_ia} />
            <MetricCard title="Resolvidos (total)" value={metrics.resolved_total} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Cenários de automação</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={scenarioData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                      {scenarioData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tickets por canal</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={channelData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Por status</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#16a34a" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Conversas por hora</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metrics.tickets_per_hour}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#9333ea" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Últimos tickets atendidos</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Hora</th>
                    <th className="pb-2 pr-4">Canal</th>
                    <th className="pb-2 pr-4">Cliente</th>
                    <th className="pb-2 pr-4">Classificação</th>
                    <th className="pb-2 pr-4">Cenário</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2">Confiança</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.recent_tickets.map((t) => (
                    <tr key={t.id} className="border-b border-border/60">
                      <td className="py-3 pr-4">{formatDateTime(t.created_at)}</td>
                      <td className="py-3 pr-4">{t.channel}</td>
                      <td className="py-3 pr-4">{t.customer_name}</td>
                      <td className="py-3 pr-4">{t.topic_group_llm ?? t.topic_group ?? "—"}</td>
                      <td className="py-3 pr-4">
                        <Badge>
                          {t.scenario
                            ? SCENARIO_LABELS[t.scenario]
                            : "—"}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4">{STATUS_LABELS[t.status]}</td>
                      <td className="py-3">{formatPercent(t.confidence)}</td>
                    </tr>
                  ))}
                  {metrics.recent_tickets.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        Nenhum ticket ainda. Use o Simulador para criar chamados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </DashboardLayout>
  );
}

function MetricCard({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="mt-1 text-3xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
