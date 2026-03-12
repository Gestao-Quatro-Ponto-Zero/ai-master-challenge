"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Alerta, Severidade } from "@/types";
import { Bell, Loader2, CheckCircle, AlertTriangle, Settings } from "lucide-react";

const SEV_BG: Record<Severidade, string> = { baixo: "bg-green-50 border-green-200", medio: "bg-yellow-50 border-yellow-200", critico: "bg-red-50 border-red-200" };
const SEV_TEXT: Record<Severidade, string> = { baixo: "text-green-800", medio: "text-yellow-800", critico: "text-red-800" };
const SEV_ICON_COLOR: Record<Severidade, string> = { baixo: "text-green-600", medio: "text-yellow-600", critico: "text-red-600" };

export default function PainelAlertas() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState(true);
  const [apenasAtivos, setApenasAtivos] = useState(false);

  useEffect(() => {
    let mounted = true;

    const carregar = async (showLoading = false) => {
      if (showLoading) setLoading(true);
      try {
        const data = await api.alertas(apenasAtivos);
        if (mounted) setAlertas(data);
      } catch {
        // noop
      } finally {
        if (showLoading && mounted) setLoading(false);
      }
    };

    carregar(true);
    const interval = setInterval(() => carregar(false), 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [apenasAtivos]);

  const ativos = alertas.filter((a) => !a.reconhecido);
  const historico = alertas.filter((a) => a.reconhecido);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><Bell className="w-6 h-6 text-blue-600" /> Painel de Alertas</h1>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-400">Atualiza a cada 10s</span>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input type="checkbox" checked={apenasAtivos} onChange={(e) => setApenasAtivos(e.target.checked)} className="rounded border-gray-300" />
            Apenas ativos
          </label>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
      ) : alertas.length === 0 ? (
        <div className="card text-center py-16">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-400" />
          <p className="text-lg font-medium text-gray-700">Nenhum alerta no momento</p>
          <p className="text-sm text-gray-400 mt-1">Tudo sob controle.</p>
        </div>
      ) : (
        <>
          {ativos.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" /> Alertas Ativos ({ativos.length})
              </h2>
              {ativos.map((a) => (
                <div key={a.id} className={`border rounded-xl p-5 ${SEV_BG[a.severidade]}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className={`w-5 h-5 mt-0.5 ${SEV_ICON_COLOR[a.severidade]}`} />
                      <div>
                        <p className={`font-semibold ${SEV_TEXT[a.severidade]}`}>{a.tipo.toUpperCase().replace("_", " ")}</p>
                        <p className={`text-sm mt-1 ${SEV_TEXT[a.severidade]}`}>{a.mensagem}</p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 shrink-0">{a.disparado_em.slice(0, 19).replace("T", " ")}</span>
                  </div>
                  <div className="flex gap-4 mt-3 text-xs text-gray-500">
                    <span>Contagem: <strong>{a.contagem}</strong></span>
                    <span>Limite: <strong>{a.limite}</strong></span>
                    <span>ID: {a.id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {historico.length > 0 && !apenasAtivos && (
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Histórico ({historico.length})</h2>
              {historico.map((a) => (
                <div key={a.id} className="card py-3 text-sm text-gray-500">
                  <span className="text-xs text-gray-400 mr-2">[{a.disparado_em.slice(0, 19).replace("T", " ")}]</span>
                  {a.tipo} — {a.mensagem}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-4 h-4 text-gray-400" />
          <h3 className="font-semibold text-gray-900">Configuração de Limites</h3>
        </div>
        <p className="text-xs text-gray-500 mb-4">Limites que disparam alertas quando ultrapassados em um dia.</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500">Tickets MÉDIOS / dia</label>
            <input type="number" value={50} disabled className="input bg-gray-50 mt-1" />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Tickets CRÍTICOS / dia</label>
            <input type="number" value={10} disabled className="input bg-gray-50 mt-1" />
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-3">Configuráveis no backend (config.py)</p>
      </div>
    </div>
  );
}
