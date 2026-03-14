"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Ticket, Severidade } from "@/types";
import { CheckCircle, Bot, UserCheck, Loader2, ArrowRight } from "lucide-react";

const SEV_STYLE: Record<Severidade, string> = { baixo: "badge-baixo", medio: "badge-medio", critico: "badge-critico" };
const SEV_LABEL: Record<Severidade, string> = { baixo: "Baixo", medio: "Médio", critico: "Crítico" };

export default function TicketsResolvidos() {
  const router = useRouter();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState<"todos" | "ia" | "humano">("todos");

  useEffect(() => {
    api.listarTickets({ status: "resolvido", limite: "200" })
      .then(setTickets)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const isAutoResolvido = (t: Ticket) => t.severidade === "baixo" && !!t.resposta_ia;
  const autoResolvidos = tickets.filter(isAutoResolvido);
  const humanoResolvidos = tickets.filter((t) => !isAutoResolvido(t));

  const exibir = filtro === "ia" ? autoResolvidos : filtro === "humano" ? humanoResolvidos : tickets;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tickets Resolvidos</h1>

      <div className="grid grid-cols-3 gap-4">
        <div className="kpi">
          <p className="kpi-label">Total Resolvidos</p>
          <p className="kpi-value">{tickets.length}</p>
        </div>
        <div className="kpi">
          <p className="kpi-label flex items-center gap-1"><Bot className="w-3.5 h-3.5" /> Resolvidos pela IA</p>
          <p className="kpi-value text-blue-600">{autoResolvidos.length}</p>
        </div>
        <div className="kpi">
          <p className="kpi-label flex items-center gap-1"><UserCheck className="w-3.5 h-3.5" /> Resolvidos por Humano</p>
          <p className="kpi-value text-orange-600">{humanoResolvidos.length}</p>
        </div>
      </div>

      <div className="flex gap-2">
        {(["todos", "ia", "humano"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filtro === f ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {{ todos: "Todos", ia: "IA Automática", humano: "Humano" }[f]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
      ) : exibir.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Nenhum ticket resolvido.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {exibir.map((t) => (
            <div key={t.id} className="card-hover flex items-center gap-4 cursor-pointer" onClick={() => router.push(`/agente/ticket/${t.id}`)}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={SEV_STYLE[t.severidade]}>{SEV_LABEL[t.severidade]}</span>
                  <span className="font-mono text-xs text-gray-400">#{t.id}</span>
                  <span className="text-sm font-semibold text-gray-800">{t.categoria}</span>
                </div>
                <p className="text-sm text-gray-600 truncate">{t.texto}</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-xs font-medium text-gray-500">
                  {isAutoResolvido(t) ? (
                    <span className="flex items-center gap-1 text-blue-600"><Bot className="w-3.5 h-3.5" /> IA</span>
                  ) : (
                    <span className="flex items-center gap-1 text-orange-600"><UserCheck className="w-3.5 h-3.5" /> {t.agente_responsavel || "Agente"}</span>
                  )}
                </p>
                <ArrowRight className="w-4 h-4 text-gray-300 mt-1 ml-auto" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
