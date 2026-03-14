"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { Ticket, Severidade } from "@/types";
import { ArrowLeft, Bot, AlertTriangle, CheckCircle, ArrowUpRight, RotateCcw, Loader2, Sparkles } from "lucide-react";

const SEV_STYLE: Record<Severidade, string> = { baixo: "badge-baixo", medio: "badge-medio", critico: "badge-critico" };
const SEV_LABEL: Record<Severidade, string> = { baixo: "Baixo", medio: "Médio", critico: "Crítico" };
const STATUS_LABEL: Record<string, string> = { novo: "Novo", em_andamento: "Em Andamento", resolvido: "Resolvido", escalado: "Escalado" };

export default function DetalheTicket() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.obterTicket(id).then(setTicket).catch(() => {}).finally(() => setLoading(false));
    }
  }, [id]);

  const atualizarStatus = async (status: string) => {
    if (!ticket) return;
    const updated = await api.atualizarStatus(ticket.id, status, user?.nome);
    setTicket(updated);
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  if (!ticket) return <div className="card text-center py-12 text-gray-500">Ticket não encontrado.</div>;

  const sev = ticket.severidade;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Voltar
      </button>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Ticket #{ticket.id}</h1>
            <span className={SEV_STYLE[sev]}>{SEV_LABEL[sev]}</span>
          </div>
          <p className="text-sm text-gray-500 mt-1">{ticket.nome_cliente} • {ticket.canal} • {STATUS_LABEL[ticket.status]}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-600">{ticket.categoria}</p>
          <div className="w-24 h-2 bg-gray-200 rounded-full mt-1 overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full" style={{ width: `${ticket.confianca * 100}%` }} />
          </div>
          <p className="text-xs text-gray-400 mt-0.5">Confiança: {(ticket.confianca * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Texto Original */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Texto Original do Cliente</h3>
        <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{ticket.texto}</p>
      </div>

      {/* Resumo IA */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-blue-900">Resumo gerado pela IA</h3>
          <span className="text-[10px] text-blue-500 bg-blue-100 px-2 py-0.5 rounded-full font-medium">Automático</span>
        </div>
        <p className="text-blue-800">{ticket.resumo_ia || "Resumo não disponível."}</p>
      </div>

      {/* Soluções Sugeridas */}
      {ticket.solucoes_sugeridas && ticket.solucoes_sugeridas.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Soluções Sugeridas pela IA</h3>
            <span className="text-[10px] text-purple-500 bg-purple-100 px-2 py-0.5 rounded-full font-medium">3 sugestões</span>
          </div>
          <div className="space-y-3">
            {ticket.solucoes_sugeridas.map((sol, i) => (
              <div key={i} className="flex gap-3 items-start">
                <span className="shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">{i + 1}</span>
                <p className="text-gray-700">{sol}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resposta IA baseada no nível */}
      {sev === "baixo" && ticket.resposta_ia && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-green-900">Resposta Automática da IA (SOP)</h3>
          </div>
          <p className="text-green-800">{ticket.resposta_ia}</p>
          <p className="text-xs text-green-600 mt-3">Ticket resolvido automaticamente com base nos procedimentos da empresa.</p>
        </div>
      )}

      {sev === "medio" && ticket.resposta_ia && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <h3 className="font-semibold text-yellow-900">Resposta Sugerida pela IA</h3>
          </div>
          <p className="text-yellow-800">{ticket.resposta_ia}</p>
          <p className="text-xs text-yellow-700 mt-3 font-medium">Agente notificado — acompanhe este ticket.</p>
        </div>
      )}

      {sev === "critico" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <h3 className="font-semibold text-red-900">Ticket Crítico — Resolução Humana Necessária</h3>
          </div>
          <p className="text-sm text-red-700">O resumo e as soluções acima são apoio para o agente responsável.</p>
        </div>
      )}

      {/* Ações */}
      {(ticket.status === "novo" || ticket.status === "em_andamento") && (
        <div className="flex items-center gap-3">
          <button onClick={() => atualizarStatus("resolvido")} className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center gap-2">
            <CheckCircle className="w-4 h-4" /> Marcar como Resolvido
          </button>
          <button onClick={() => atualizarStatus("escalado")} className="btn-secondary flex items-center gap-2">
            <ArrowUpRight className="w-4 h-4" /> Escalar
          </button>
          {ticket.status === "em_andamento" && (
            <button onClick={() => atualizarStatus("novo")} className="btn-secondary flex items-center gap-2">
              <RotateCcw className="w-4 h-4" /> Devolver à Fila
            </button>
          )}
        </div>
      )}
    </div>
  );
}
