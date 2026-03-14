"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Metricas } from "@/types";
import { Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const SEV_COLORS: Record<string, string> = { baixo: "#22c55e", medio: "#eab308", critico: "#ef4444" };
const STATUS_COLORS = ["#3b82f6", "#f59e0b", "#22c55e", "#ef4444"];

export default function DashboardMetricas() {
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [periodo, setPeriodo] = useState("dia");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.metricas(periodo).then(setMetricas).catch(() => {}).finally(() => setLoading(false));
  }, [periodo]);

  const periodos = [
    { value: "dia", label: "Hoje" },
    { value: "semana", label: "Última Semana" },
    { value: "mes", label: "Último Mês" },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard de Métricas</h1>
        <div className="flex gap-2">
          {periodos.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriodo(p.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                periodo === p.value ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
      ) : !metricas ? (
        <div className="card text-center py-12 text-gray-400">Sem dados disponíveis.</div>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-4">
            <div className="kpi"><p className="kpi-label">Total de Tickets</p><p className="kpi-value">{metricas.total_tickets}</p></div>
            <div className="kpi">
              <p className="kpi-label">Tempo Médio Resolução</p>
              <p className="kpi-value">{metricas.tempo_medio_resolucao_horas ? `${metricas.tempo_medio_resolucao_horas.toFixed(1)}h` : "N/A"}</p>
            </div>
            <div className="kpi"><p className="kpi-label">Resolvidos pela IA</p><p className="kpi-value text-blue-600">{metricas.auto_resolvidos}</p></div>
            <div className="kpi"><p className="kpi-label">% Auto-resolução</p><p className="kpi-value text-emerald-600">{metricas.pct_auto_resolvidos.toFixed(1)}%</p></div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Tickets por Severidade</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(metricas.por_severidade).map(([k, v]) => ({ nome: k.charAt(0).toUpperCase() + k.slice(1), valor: v, fill: SEV_COLORS[k] || "#94a3b8" }))}>
                  <XAxis dataKey="nome" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
                    {Object.entries(metricas.por_severidade).map(([k]) => (
                      <Cell key={k} fill={SEV_COLORS[k] || "#94a3b8"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Tickets por Status</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(metricas.por_status).map(([k, v]) => ({ name: k.replace("_", " "), value: v }))}
                    cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {Object.keys(metricas.por_status).map((_, i) => (
                      <Cell key={i} fill={STATUS_COLORS[i % STATUS_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
