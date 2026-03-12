"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DiagnosticoData } from "@/types";
import { Activity, Loader2, DollarSign, Clock, ThumbsUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from "recharts";

const CHANNEL_COLORS = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444", "#22c55e"];

type ChartPoint = {
  nome: string;
  valor: number;
};

function dictToChartData(dict: Record<string, number>): ChartPoint[] {
  return Object.entries(dict).map(([k, v]) => ({ nome: k, valor: +v.toFixed(2) }));
}

export default function DiagnosticoOperacional() {
  const [data, setData] = useState<DiagnosticoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"canal" | "tipo" | "prioridade">("canal");

  useEffect(() => {
    api.diagnostico().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  if (!data) return <div className="card text-center py-12 text-gray-400">Erro ao carregar dados do diagnóstico.</div>;

  const tempoMap = { canal: data.tempo_por_canal, tipo: data.tempo_por_tipo, prioridade: data.tempo_por_prioridade };
  const satMap: Record<string, Record<string, number>> = { canal: data.satisfacao_por_canal, prioridade: data.satisfacao_por_prioridade };
  const tempoData = dictToChartData(tempoMap[tab]);
  const tabLabels = { canal: "Canal", tipo: "Tipo", prioridade: "Prioridade" };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><Activity className="w-6 h-6 text-blue-600" /> Diagnóstico Operacional</h1>
        <p className="text-sm text-gray-500 mt-1">Análise baseada no Dataset 1 — Customer Support Tickets</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="kpi"><p className="kpi-label">Total Tickets</p><p className="kpi-value">{data.total_tickets.toLocaleString()}</p></div>
        <div className="kpi"><p className="kpi-label">Fechados</p><p className="kpi-value">{data.tickets_fechados.toLocaleString()}</p></div>
        <div className="kpi"><p className="kpi-label flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5" /> Satisfação Média</p><p className="kpi-value">{data.satisfacao_media.toFixed(2)}/5</p></div>
        <div className="kpi"><p className="kpi-label flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Tempo Médio</p><p className="kpi-value">{data.tempo_medio_resolucao_horas.toFixed(1)}h</p></div>
      </div>

      {/* Tempo de Resolução */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Gargalos: Tempo Médio de Resolução</h3>
          <div className="flex gap-2">
            {(["canal", "tipo", "prioridade"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${tab === t ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`}>
                Por {tabLabels[t]}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={tempoData.sort((a, b) => b.valor - a.valor)}>
            <XAxis dataKey="nome" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: "Horas", angle: -90, position: "insideLeft", style: { fontSize: 11 } }} />
            <Tooltip formatter={(v: number) => [`${v.toFixed(1)}h`, "Tempo Médio"]} />
            <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
              {tempoData.map((_, i) => <Cell key={i} fill={CHANNEL_COLORS[i % CHANNEL_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Satisfação */}
      <div className="grid grid-cols-2 gap-6">
        {(["canal", "prioridade"] as const).map((key) => (
          <div key={key} className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Satisfação por {tabLabels[key]}</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dictToChartData(satMap[key]).sort((a, b) => a.valor - b.valor)} layout="vertical">
                <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 11 }} />
                <YAxis dataKey="nome" type="category" tick={{ fontSize: 11 }} width={100} />
                <Tooltip formatter={(v: number) => [`${v.toFixed(2)}/5`, "Satisfação"]} />
                <Bar dataKey="valor" radius={[0, 6, 6, 0]}>
                  {dictToChartData(satMap[key]).map((_, i) => <Cell key={i} fill={CHANNEL_COLORS[i % CHANNEL_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {/* Distribuição */}
      <div className="grid grid-cols-2 gap-6">
        {([["distribuicao_tipo", "Por Tipo de Ticket"], ["distribuicao_prioridade", "Por Prioridade"]] as const).map(([key, title]) => (
          <div key={key} className="card">
            <h3 className="font-semibold text-gray-900 mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={Object.entries(data[key]).map(([k, v]) => ({ name: k, value: v }))}
                  cx="50%" cy="50%" innerRadius={45} outerRadius={90} paddingAngle={2} dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {Object.keys(data[key]).map((_, i) => <Cell key={i} fill={CHANNEL_COLORS[i % CHANNEL_COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {/* Desperdício */}
      <div className="bg-gradient-to-r from-blue-50 to-emerald-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><DollarSign className="w-5 h-5 text-emerald-600" /> Quantificação de Desperdício</h3>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase">Tickets Automatizáveis / Ano</p>
            <p className="text-3xl font-bold text-gray-900">{data.desperdicio.tickets_automatizaveis_ano.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase">Horas Economizadas / Ano</p>
            <p className="text-3xl font-bold text-blue-600">{data.desperdicio.horas_economizadas_ano.toLocaleString(undefined, { maximumFractionDigits: 0 })}h</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase">Economia Estimada / Ano</p>
            <p className="text-3xl font-bold text-emerald-600">R$ {data.desperdicio.economia_estimada_ano.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-4">Estimativa: 30.000 tickets/ano, ~28% automatizáveis com LLM + RAG (Low 85% + Medium simples 55%), custo R$30/h por agente.</p>
      </div>
    </div>
  );
}
