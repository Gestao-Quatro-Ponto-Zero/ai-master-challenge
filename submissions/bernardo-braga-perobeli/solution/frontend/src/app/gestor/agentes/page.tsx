"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agente, StatusAgente } from "@/types";
import { Users, Loader2, Wifi, WifiOff, Clock } from "lucide-react";

const STATUS_STYLE: Record<StatusAgente, { bg: string; text: string; dot: string; label: string }> = {
  online: { bg: "bg-green-50", text: "text-green-700", dot: "bg-green-500", label: "Online" },
  offline: { bg: "bg-gray-50", text: "text-gray-500", dot: "bg-gray-400", label: "Offline" },
  ocupado: { bg: "bg-orange-50", text: "text-orange-700", dot: "bg-orange-500", label: "Ocupado" },
};

export default function AgentesOnline() {
  const [agentes, setAgentes] = useState<Agente[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.agentesOnline().then(setAgentes).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const online = agentes.filter((a) => a.status === "online").length;
  const ocupados = agentes.filter((a) => a.status === "ocupado").length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><Users className="w-6 h-6 text-blue-600" /> Agentes Online</h1>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
      ) : agentes.length === 0 ? (
        <div className="card text-center py-16">
          <WifiOff className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">Nenhum agente online no momento.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="kpi"><p className="kpi-label">Agentes Ativos</p><p className="kpi-value">{agentes.length}</p></div>
            <div className="kpi"><p className="kpi-label flex items-center gap-1"><Wifi className="w-3.5 h-3.5 text-green-500" /> Online</p><p className="kpi-value text-green-600">{online}</p></div>
            <div className="kpi"><p className="kpi-label flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-orange-500" /> Ocupados</p><p className="kpi-value text-orange-600">{ocupados}</p></div>
          </div>

          <div className="space-y-3">
            {agentes.map((a) => {
              const s = STATUS_STYLE[a.status];
              return (
                <div key={a.nome} className="card-hover flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold text-white shrink-0">
                    {a.nome.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{a.nome}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className={`w-2 h-2 rounded-full ${s.dot}`} />
                      <span className={`text-xs font-medium ${s.text}`}>{s.label}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-900">{a.tickets_atribuidos}</p>
                    <p className="text-xs text-gray-400">tickets atribuídos</p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
