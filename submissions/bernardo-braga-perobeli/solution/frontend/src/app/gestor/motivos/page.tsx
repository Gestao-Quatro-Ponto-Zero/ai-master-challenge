"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TopMotivos } from "@/types";
import { Loader2, Tag } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const SEV_COLORS: Record<string, string> = { todos: "#3b82f6", baixo: "#22c55e", medio: "#eab308", critico: "#ef4444" };

export default function MotivosPorNivel() {
  const [data, setData] = useState<TopMotivos | null>(null);
  const [periodo, setPeriodo] = useState("dia");
  const [severidade, setSeveridade] = useState("todos");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.topMotivos(periodo, severidade).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [periodo, severidade]);

  const periodos = [
    { value: "dia", label: "Hoje" },
    { value: "semana", label: "Última Semana" },
    { value: "mes", label: "Último Mês" },
  ];

  const niveis = [
    { value: "todos", label: "Todos" },
    { value: "baixo", label: "Baixo" },
    { value: "medio", label: "Médio" },
    { value: "critico", label: "Crítico" },
  ];

  const cor = SEV_COLORS[severidade] || "#3b82f6";

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><Tag className="w-6 h-6 text-blue-600" /> Principais Motivos por Nível</h1>
        <p className="text-sm text-gray-500 mt-1">Identifique quais categorias são mais recorrentes em cada nível</p>
      </div>

      <div className="flex flex-wrap gap-6">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">Período:</span>
          {periodos.map((p) => (
            <button key={p.value} onClick={() => setPeriodo(p.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${periodo === p.value ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">Nível:</span>
          {niveis.map((n) => (
            <button key={n.value} onClick={() => setSeveridade(n.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${severidade === n.value ? "text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`}
              style={severidade === n.value ? { backgroundColor: SEV_COLORS[n.value] } : {}}>
              {n.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
      ) : !data || data.motivos.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">Sem dados para os filtros selecionados.</div>
      ) : (
        <>
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">
              Top Motivos — {severidade === "todos" ? "Todos os Níveis" : severidade.toUpperCase()}
            </h3>
            <ResponsiveContainer width="100%" height={Math.max(250, data.motivos.length * 50)}>
              <BarChart data={[...data.motivos].reverse()} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="categoria" type="category" tick={{ fontSize: 12 }} width={150} />
                <Tooltip
                  formatter={(value, _name, item) => {
                    const percentual = typeof item?.payload?.percentual === "number" ? item.payload.percentual : 0;
                    return [`${value} (${percentual}%)`, "Tickets"];
                  }}
                />
                <Bar dataKey="quantidade" radius={[0, 6, 6, 0]} fill={cor}>
                  {data.motivos.map((_, i) => <Cell key={i} fill={cor} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Tabela Detalhada</h3>
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">Categoria</th>
                  <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">Tickets</th>
                  <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wide pb-3">% do Total</th>
                  <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wide pb-3 w-40">Barra</th>
                </tr>
              </thead>
              <tbody>
                {data.motivos.map((m, i) => (
                  <tr key={i} className="border-b border-gray-100 last:border-0">
                    <td className="py-3 text-sm font-medium text-gray-800">{m.categoria}</td>
                    <td className="py-3 text-sm text-right text-gray-600">{m.quantidade}</td>
                    <td className="py-3 text-sm text-right text-gray-600">{m.percentual}%</td>
                    <td className="py-3">
                      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${m.percentual}%`, backgroundColor: cor }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
