"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { Ticket, TriagemResponse, Severidade } from "@/types";
import { Plus, Send, Loader2, Filter, ArrowRight, UserCheck, Inbox } from "lucide-react";

const SEV_STYLE: Record<Severidade, string> = {
  baixo: "badge-baixo",
  medio: "badge-medio",
  critico: "badge-critico",
};

const SEV_LABEL: Record<Severidade, string> = { baixo: "Baixo", medio: "Médio", critico: "Crítico" };
const STATUS_LABEL: Record<string, string> = { novo: "Novo", em_andamento: "Em Andamento", resolvido: "Resolvido", escalado: "Escalado" };

export default function FilaTickets() {
  const { user } = useAuth();
  const router = useRouter();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState<string>("todos");
  const [showForm, setShowForm] = useState(false);
  const [texto, setTexto] = useState("");
  const [nomeCliente, setNomeCliente] = useState("Cliente");
  const [canal, setCanal] = useState("chat");
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<TriagemResponse | null>(null);

  const carregar = useCallback(async () => {
    try {
      const params: Record<string, string> = { limite: "100" };
      if (filtro !== "todos") params.severidade = filtro;
      const data = await api.listarTickets(params);
      setTickets(data.filter((t) => t.status === "novo" || t.status === "em_andamento"));
    } catch { /* ignore */ }
    setLoading(false);
  }, [filtro]);

  useEffect(() => { carregar(); }, [carregar]);

  const enviarTriagem = async () => {
    if (!texto.trim()) return;
    setEnviando(true);
    setResultado(null);
    try {
      const res = await api.triagem(texto, nomeCliente, canal);
      setResultado(res);
      setTexto("");
      carregar();
    } catch { /* ignore */ }
    setEnviando(false);
  };

  const assumir = async (id: string) => {
    await api.atualizarStatus(id, "em_andamento", user?.nome);
    carregar();
  };

  const resolver = async (id: string) => {
    await api.atualizarStatus(id, "resolvido", user?.nome);
    carregar();
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fila de Tickets</h1>
          <p className="text-sm text-gray-500 mt-1">{tickets.length} ticket(s) em aberto</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Novo Ticket
        </button>
      </div>

      {showForm && (
        <div className="card space-y-4">
          <h3 className="font-semibold text-gray-900">Submeter novo ticket para triagem</h3>
          <textarea
            className="input min-h-[100px] resize-y"
            placeholder="Descreva o problema do cliente..."
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
          />
          <div className="grid grid-cols-3 gap-4">
            <input className="input" placeholder="Nome do cliente" value={nomeCliente} onChange={(e) => setNomeCliente(e.target.value)} />
            <select className="input" value={canal} onChange={(e) => setCanal(e.target.value)}>
              <option value="chat">Chat</option>
              <option value="email">Email</option>
              <option value="telefone">Telefone</option>
              <option value="redes_sociais">Redes Sociais</option>
            </select>
            <button onClick={enviarTriagem} disabled={enviando || !texto.trim()} className="btn-primary flex items-center justify-center gap-2">
              {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {enviando ? "Classificando..." : "Enviar para Triagem"}
            </button>
          </div>

          {resultado && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-3">
                <span className={SEV_STYLE[resultado.severidade]}>{SEV_LABEL[resultado.severidade]}</span>
                <span className="text-sm font-medium text-gray-700">#{resultado.ticket_id} — {resultado.categoria}</span>
                <span className="text-xs text-gray-500">Confiança: {(resultado.confianca * 100).toFixed(0)}%</span>
              </div>
              <p className="text-sm text-gray-700"><strong>Resumo IA:</strong> {resultado.resumo_ia}</p>
              {resultado.solucoes_sugeridas && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Soluções sugeridas pela IA:</p>
                  <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                    {resultado.solucoes_sugeridas.map((s, i) => <li key={i}>{s}</li>)}
                  </ol>
                </div>
              )}
              {resultado.resposta_ia && <p className="text-sm text-green-700 bg-green-50 p-3 rounded"><strong>Resposta IA:</strong> {resultado.resposta_ia}</p>}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-400" />
        {["todos", "critico", "medio", "baixo"].map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filtro === f ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {f === "todos" ? "Todos" : SEV_LABEL[f as Severidade]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
      ) : tickets.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">
          <Inbox className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Nenhum ticket em aberto. Submeta um ticket acima para testar.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tickets.map((t) => (
            <div key={t.id} className="card-hover flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={SEV_STYLE[t.severidade]}>{SEV_LABEL[t.severidade]}</span>
                  <span className="font-mono text-xs text-gray-400">#{t.id}</span>
                  <span className="text-sm font-semibold text-gray-800">{t.categoria}</span>
                  <span className="text-xs text-gray-400">{(t.confianca * 100).toFixed(0)}%</span>
                </div>
                <p className="text-sm text-gray-600 truncate">{t.texto}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                  <span>{t.nome_cliente}</span>
                  <span>•</span>
                  <span>{t.canal}</span>
                  <span>•</span>
                  <span>{STATUS_LABEL[t.status]}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {t.status === "novo" && (
                  <button onClick={() => assumir(t.id)} className="btn-primary text-xs py-1.5 flex items-center gap-1">
                    <UserCheck className="w-3.5 h-3.5" /> Assumir
                  </button>
                )}
                {t.status === "em_andamento" && (
                  <button onClick={() => resolver(t.id)} className="bg-green-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-green-700 transition-colors">
                    Resolver
                  </button>
                )}
                <button onClick={() => router.push(`/agente/ticket/${t.id}`)} className="btn-secondary text-xs py-1.5 flex items-center gap-1">
                  Detalhe <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
