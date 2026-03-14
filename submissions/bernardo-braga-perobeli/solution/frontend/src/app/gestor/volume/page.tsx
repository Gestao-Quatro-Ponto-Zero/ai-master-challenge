"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Metricas } from "@/types";
import { Loader2, TrendingUp, Bot, UserCheck } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis } from "recharts";

const SEV_COLORS: Record<string, string> = { baixo: "#22c55e", medio: "#eab308", critico: "#ef4444" };

export default function VolumePorNivel() {
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
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><TrendingUp className="w-6 h-6 text-blue-600" /> Volume por Nível</h1>
        <div className="flex gap-2">
          {periodos.map((p) => (
            <button key={p.value} onClick={() => setPeriodo(p.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${periodo === p.value ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
      ) : !metricas || metricas.total_tickets === 0 ? (
        <div className="card text-center py-12 text-gray-400">Sem dados para o período selecionado.</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4">
            {(["baixo", "medio", "critico"] as const).map((nivel) => {
              const qtd = metricas.por_severidade[nivel] || 0;
              const pct = metricas.total_tickets > 0 ? (qtd / metricas.total_tickets * 100) : 0;
              const labels = { baixo: "Baixo", medio: "Médio", critico: "Crítico" };
              return (
                <div key={nivel} className="card">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: SEV_COLORS[nivel] }} />
                    <p className="text-sm font-medium text-gray-500">{labels[nivel]}</p>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{qtd}</p>
                  <p className="text-sm text-gray-400">{pct.toFixed(1)}% do total</p>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Distribuição por Nível</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(metricas.por_severidade).map(([k, v]) => ({ name: k.toUpperCase(), value: v }))}
                    cx="50%" cy="50%" innerRadius={50} outerRadius={100} paddingAngle={3} dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {Object.entries(metricas.por_severidade).map(([k]) => (
                      <Cell key={k} fill={SEV_COLORS[k] || "#94a3b8"} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Resolução: IA vs Humano</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  { nome: "IA Automática", valor: metricas.auto_resolvidos, fill: "#3b82f6" },
                  { nome: "Humano", valor: metricas.total_tickets - metricas.auto_resolvidos, fill: "#f97316" },
                ]}>
                  <XAxis dataKey="nome" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
                    <Cell fill="#3b82f6" />
                    <Cell fill="#f97316" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
