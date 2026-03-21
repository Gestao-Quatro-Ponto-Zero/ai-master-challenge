"use client";

import { useState, useEffect } from "react";
import type { CalendarEntry } from "@/lib/calendar-store";
import { MiniGame } from "./mini-game";

export function PendingApproval() {
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState("");
  const [showGame, setShowGame] = useState(false);
  const [genDone, setGenDone] = useState(false);
  const [weekStatus, setWeekStatus] = useState<{ occupied: number; empty: number; total: number; filled: number; accumulated: number; fullWeek: boolean } | null>(null);
  const [genMessage, setGenMessage] = useState("");

  async function loadPending() {
    try {
      const res = await fetch("/api/calendar/list?status=pendente");
      const data = await res.json();
      setEntries(data.entries || []);
    } catch {
      setEntries([]);
    }
  }

  useEffect(() => { loadPending(); }, []);

  async function handleAction(id: string, action: "approve" | "discard") {
    setLoading(true);
    await fetch(`/api/calendar/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    await loadPending();
    setLoading(false);
  }

  async function handleGenerate() {
    setGenerating(true);
    setGenError("");
    setGenDone(false);
    setWeekStatus(null);
    setGenMessage("");
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 240000);
      const res = await fetch("/api/cron/daily-recommendations", { method: "POST", signal: controller.signal });
      clearTimeout(timeout);
      const data = await res.json();
      if (!data.success) {
        setGenError(data.message || "Erro ao gerar recomendações. Tente novamente.");
      } else {
        if (data.weekStatus) setWeekStatus(data.weekStatus);
        if (data.message) setGenMessage(data.message);
      }
      await loadPending();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setGenError("A geração demorou mais que o esperado. Tente novamente.");
      } else {
        setGenError(err instanceof Error ? err.message : "Erro ao gerar. Verifique a OPENROUTER_API_KEY no .env");
      }
    }
    setGenerating(false);
    setGenDone(true);
    setTimeout(() => { setShowGame(false); setGenDone(false); }, 3000);
  }

  // Overlay de loading fullscreen com mini-game
  const overlay = (generating || genDone) ? (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl p-4 text-center max-w-md mx-4 relative">
        {genDone && (
          <div className="absolute inset-x-0 top-0 z-10 rounded-t-2xl overflow-hidden">
            {weekStatus?.fullWeek ? (
              <div className="bg-amber-500 text-white text-xs font-semibold py-2 px-3 text-center">
                📅 Semana já completa — conteúdos gerados para a próxima semana
              </div>
            ) : genMessage ? (
              <div className="bg-amber-500 text-white text-xs font-semibold py-2 px-3 text-center">
                📅 {genMessage}
              </div>
            ) : weekStatus ? (
              <div className="bg-green-500 text-white text-xs font-semibold py-2 px-3 text-center">
                ✓ {weekStatus.filled} conteúdo{weekStatus.filled !== 1 ? "s" : ""} gerado{weekStatus.filled !== 1 ? "s" : ""}
                {weekStatus.empty === 0 ? " · Semana completa!" : ` · ${weekStatus.empty} dia${weekStatus.empty !== 1 ? "s" : ""} vazios preenchidos`}
                {weekStatus.accumulated > 0 ? ` · +${weekStatus.accumulated} acumulado${weekStatus.accumulated !== 1 ? "s" : ""}` : ""}
              </div>
            ) : (
              <div className="bg-green-500 text-white text-xs font-semibold py-2 px-3 text-center">
                ✓ Recomendações geradas! Fechando...
              </div>
            )}
          </div>
        )}
        {showGame ? (
          <div className={genDone ? "mt-8" : ""}>
            <MiniGame onClose={() => setShowGame(false)} />
          </div>
        ) : (
          <>
            <div className="w-10 h-10 border-3 border-[#E8734A] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-sm font-semibold text-[#0F1B2D] mb-1">Gerando recomendações...</h3>
            <p className="text-xs text-slate-500">A IA está analisando o dataset e criando conteúdos otimizados</p>
            <p className="text-[10px] text-slate-400 mt-3">Isso pode levar 1-3 minutos</p>
            <button onClick={() => setShowGame(true)} className="mt-4 px-4 py-2 text-xs bg-[#0F1B2D] text-white rounded-lg hover:bg-[#1a2d47] transition-colors">
              Jogar enquanto aguarda
            </button>
          </>
        )}
      </div>
    </div>
  ) : null;

  if (entries.length === 0) {
    return (
      <>
        {overlay}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#0F1B2D] mb-1">Conteúdos Pendentes</h3>
              <p className="text-xs text-slate-400">Nenhum conteúdo aguardando aprovação.</p>
            </div>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-2 bg-[#E8734A] text-white text-xs font-medium rounded-lg hover:bg-[#d4653f] transition-colors disabled:opacity-50"
            >
              Gerar recomendações
            </button>
          </div>
          {genError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">{genError}</div>
          )}
        </div>
      </>
    );
  }

  return (
    <>
    {overlay}
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-[#0F1B2D]">Conteúdos Pendentes ({entries.length})</h3>
          <p className="text-xs text-slate-400">Gerados pela IA — aguardando sua aprovação</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-[#E8734A] text-white text-xs font-medium rounded-lg hover:bg-[#d4653f] transition-colors disabled:opacity-50"
        >
          {generating ? "Gerando..." : "Gerar mais"}
        </button>
      </div>

      <div className="space-y-2">
        {entries.slice(0, 5).map((entry) => (
          <div key={entry.id} className="border border-amber-100 bg-amber-50/50 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-[#0F1B2D]">{entry.script.title}</h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  {entry.platform} · {entry.niche} · {new Date(entry.scheduled_date).toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" })} {entry.scheduled_time}
                </p>
                {expandedId === entry.id && (
                  <div className="mt-3 space-y-2">
                    <div className="bg-white rounded-lg p-3 text-xs text-slate-600 whitespace-pre-wrap">
                      <p className="text-[10px] text-slate-400 uppercase mb-1">Copy</p>
                      {entry.script.copy}
                    </div>
                    <div className="bg-white rounded-lg p-3 text-xs text-slate-600">
                      <p className="text-[10px] text-slate-400 uppercase mb-1">Visual</p>
                      {entry.script.visual_spec}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {entry.script.hashtags.map((h, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px]">{h}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                {expandedId === entry.id ? "Fechar" : "Ver roteiro"}
              </button>
              <button
                onClick={() => handleAction(entry.id, "approve")}
                disabled={loading}
                className="px-3 py-1.5 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                Aprovar
              </button>
              <button
                onClick={() => handleAction(entry.id, "discard")}
                disabled={loading}
                className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
              >
                Descartar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
    </>
  );
}
