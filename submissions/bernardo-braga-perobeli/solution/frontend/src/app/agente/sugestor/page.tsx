"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { TicketSimilar } from "@/types";
import { Search, Loader2, Lightbulb, Copy, CheckCircle } from "lucide-react";

export default function Sugestor() {
  const [texto, setTexto] = useState("");
  const [qtd, setQtd] = useState(3);
  const [resultados, setResultados] = useState<TicketSimilar[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [buscou, setBuscou] = useState(false);
  const [copiado, setCopiado] = useState<number | null>(null);

  const buscar = async () => {
    if (!texto.trim()) return;
    setBuscando(true);
    setBuscou(false);
    try {
      const res = await api.sugerirResposta(texto, qtd);
      setResultados(res.tickets_similares);
    } catch {
      setResultados([]);
    }
    setBuscando(false);
    setBuscou(true);
  };

  const copiar = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiado(index);
    setTimeout(() => setCopiado(null), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Base RAG — Soluções</h1>
        <p className="text-sm text-gray-500 mt-1">Busca semântica na base de ~56.500 tickets para encontrar soluções já aplicadas</p>
      </div>

      <div className="card space-y-4">
        <textarea
          className="input min-h-[120px] resize-y"
          placeholder="Descreva o problema do cliente para encontrar resoluções similares..."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Resultados:</label>
            <select className="input w-20" value={qtd} onChange={(e) => setQtd(+e.target.value)}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <button onClick={buscar} disabled={buscando || !texto.trim()} className="btn-primary flex items-center gap-2">
            {buscando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {buscando ? "Buscando..." : "Buscar na Base RAG"}
          </button>
        </div>
      </div>

      {buscou && resultados.length === 0 && (
        <div className="card text-center py-12 text-gray-400">
          <Search className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p>Nenhum ticket similar encontrado.</p>
        </div>
      )}

      {resultados.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Top {resultados.length} Tickets Similares</h2>
          {resultados.map((r, i) => {
            const score = r.pontuacao_similaridade;
            const pct = score <= 1 ? `${(score * 100).toFixed(0)}%` : score.toFixed(2);
            return (
              <div key={i} className="card space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-semibold text-gray-700">Ticket Similar #{i + 1}</span>
                  </div>
                  <span className="text-xs font-medium bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    Similaridade: {pct}
                  </span>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Descrição original:</p>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{r.texto.length > 300 ? r.texto.slice(0, 300) + "..." : r.texto}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Resolução aplicada:</p>
                  <div className="bg-green-50 border border-green-200 p-3 rounded-lg flex items-start justify-between gap-3">
                    <p className="text-sm text-green-800">{r.resolucao}</p>
                    <button
                      onClick={() => copiar(r.resolucao, i)}
                      className="shrink-0 p-1.5 rounded hover:bg-green-100 transition-colors"
                      title="Copiar resolução"
                    >
                      {copiado === i ? <CheckCircle className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4 text-green-600" />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
