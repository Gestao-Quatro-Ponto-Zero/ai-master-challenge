"use client";

import { useState, useEffect, useCallback } from "react";
import type { CalendarEntry } from "@/lib/calendar-store";
import { MiniGame } from "./mini-game";

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; text: string; border: string }> = {
  pendente: { label: "Pendente", color: "bg-amber-400", bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  aprovado: { label: "Aprovado", color: "bg-emerald-400", bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  publicado: { label: "Publicado", color: "bg-blue-400", bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
};

function getWeekDates(offset: number): { start: Date; dates: Date[] } {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const monday = new Date(today);
  monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1) + offset * 7);
  monday.setHours(0, 0, 0, 0);

  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    dates.push(d);
  }
  return { start: monday, dates };
}

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

const DAY_NAMES = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];

export function ContentCalendar() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<CalendarEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterPlatform, setFilterPlatform] = useState("");
  const [filterNiche, setFilterNiche] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showBadge, setShowBadge] = useState(false);
  // WhatsApp
  const [phone, setPhone] = useState("");
  const [editableMsg, setEditableMsg] = useState("");
  const [sendStatus, setSendStatus] = useState("");
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [showWA, setShowWA] = useState(false);

  const { dates } = getWeekDates(weekOffset);
  const weekStart = formatDate(dates[0]);
  const weekEnd = formatDate(dates[6]);

  const loadEntries = useCallback(async () => {
    try {
      const res = await fetch(`/api/calendar/list?from=${weekStart}&to=${weekEnd}`);
      const data = await res.json();
      setEntries(data.entries || []);
    } catch {
      setEntries([]);
    }
  }, [weekStart, weekEnd]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  async function handleAction(id: string, action: "approve" | "discard") {
    setLoading(true);
    await fetch(`/api/calendar/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    await loadEntries();
    setSelectedEntry(null);
    setLoading(false);
  }

  const [generating, setGenerating] = useState(false);
  const [showGame, setShowGame] = useState(false);

  // Extrair valores únicos para os filtros
  const platforms = [...new Set(entries.map((e) => e.platform).filter(Boolean))];
  const niches = [...new Set(entries.map((e) => e.niche).filter(Boolean))];

  const filteredEntries = entries.filter((e) => {
    if (filterPlatform && e.platform !== filterPlatform) return false;
    if (filterNiche && e.niche !== filterNiche) return false;
    if (filterStatus && e.status !== filterStatus) return false;
    return true;
  });

  async function handleGenerateWAMessage() {
    if (!selectedEntry) return;
    setLoadingMsg(true);
    try {
      const roteiro = [
        `Título: ${selectedEntry.script.title}`,
        `Plataforma: ${selectedEntry.platform} | Mercado: ${selectedEntry.niche} | Público: ${selectedEntry.audience}`,
        `Data sugerida: ${selectedEntry.scheduled_date} às ${selectedEntry.scheduled_time}`,
        ``,
        `Copy: ${selectedEntry.script.copy}`,
        `CTA: ${selectedEntry.script.cta}`,
        `Hashtags: ${selectedEntry.script.hashtags?.join(" ")}`,
        `Especificação visual: ${selectedEntry.script.visual_spec}`,
      ].join("\n");

      const res = await fetch("/api/ai/generate-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context: "calendar_content",
          data: { roteiro, platform: selectedEntry.platform, niche: selectedEntry.niche },
        }),
      });
      const data = await res.json();
      setEditableMsg(data.message || roteiro);
      setShowWA(true);
    } catch {
      setEditableMsg(`Olá! Tenho um roteiro de conteúdo para ${selectedEntry.platform} no segmento de ${selectedEntry.niche} que gostaria de compartilhar com você.`);
      setShowWA(true);
    }
    setLoadingMsg(false);
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 240000);
      // Passa a segunda-feira da semana visualizada
      const res = await fetch("/api/cron/daily-recommendations", {
        method: "POST",
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ targetMonday: formatDate(dates[0]) }),
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Erro desconhecido" }));
        console.error("[cron] Erro:", err);
      }
    } catch (e) {
      console.error("[cron] Fetch falhou:", e);
    }
    await loadEntries();
    setGenerating(false);
    setShowGame(false);
  }

  return (
    <div className="space-y-4">
      {/* Overlay de geração */}
      {generating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-md mx-4">
            {showGame ? (
              <MiniGame onClose={() => setShowGame(false)} />
            ) : (
              <>
                <div className="w-10 h-10 border-3 border-[#E8734A] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <h3 className="text-sm font-semibold text-[#0F1B2D] mb-1">Gerando recomendações...</h3>
                <p className="text-xs text-slate-500">A IA está analisando o dataset e criando conteúdos otimizados</p>
                <p className="text-[10px] text-slate-400 mt-3">Isso pode levar 1-3 minutos. Não saia da tela.</p>
                <button onClick={() => setShowGame(true)} className="mt-4 px-4 py-2 text-xs bg-[#0F1B2D] text-white rounded-lg hover:bg-[#1a2d47] transition-colors">
                  Jogar enquanto aguarda
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Badge explicativo */}
      <div className="bg-[#0F1B2D]/3 border border-[#0F1B2D]/8 rounded-xl p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#0F1B2D]">Como os conteúdos são gerados</span>
            <button onClick={() => setShowBadge((v) => !v)} className="text-[10px] text-slate-400 underline">{showBadge ? "fechar" : "saiba mais"}</button>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />Dataset (52k posts)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#E8734A] inline-block" />IA (3 etapas)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />Mercado + Público</span>
          </div>
        </div>
        {showBadge && (
          <div className="mt-3 grid grid-cols-3 gap-3 text-[10px] text-slate-600">
            <div className="bg-white rounded-lg p-2.5 border border-slate-100">
              <p className="font-semibold text-[#0F1B2D] mb-1">1. Cruzamento de dados</p>
              <p>O sistema analisa 52.214 posts reais e identifica quais combinações de <strong>plataforma × formato × mercado × faixa etária</strong> tiveram maior engajamento histórico.</p>
            </div>
            <div className="bg-white rounded-lg p-2.5 border border-slate-100">
              <p className="font-semibold text-[#0F1B2D] mb-1">2. Geração em 3 etapas</p>
              <p><strong>Rascunho</strong> (criativo) → <strong>Crítica</strong> (avalia viabilidade e alinhamento) → <strong>Roteiro final</strong> (formatado para produção). Cada etapa usa um modelo diferente.</p>
            </div>
            <div className="bg-white rounded-lg p-2.5 border border-slate-100">
              <p className="font-semibold text-[#0F1B2D] mb-1">3. Distribuição semanal</p>
              <p>Conteúdos são distribuídos nos <strong>dias com maior engajamento histórico</strong> da semana. Dias vazios são preenchidos primeiro. Dias preenchidos acumulam conteúdo adicional.</p>
            </div>
          </div>
        )}
      </div>

      {/* Header + Filtros */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button onClick={() => setWeekOffset((w) => w - 1)} className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg hover:bg-slate-50">Anterior</button>
          <h3 className="text-sm font-semibold text-[#0F1B2D]">
            {dates[0].toLocaleDateString("pt-BR", { day: "numeric", month: "short" })} — {dates[6].toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" })}
          </h3>
          <button onClick={() => setWeekOffset((w) => w + 1)} className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg hover:bg-slate-50">Próxima</button>
        </div>
        <button onClick={handleGenerate} disabled={generating} className="px-4 py-2 bg-[#E8734A] text-white text-xs font-medium rounded-lg hover:bg-[#d4653f] disabled:opacity-50">
          Gerar conteúdos para a semana
        </button>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] text-slate-400 uppercase tracking-wider">Filtrar:</span>
        <select value={filterPlatform} onChange={(e) => setFilterPlatform(e.target.value)} className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-[#0F1B2D]">
          <option value="">Todas as plataformas</option>
          {platforms.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select value={filterNiche} onChange={(e) => setFilterNiche(e.target.value)} className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-[#0F1B2D]">
          <option value="">Todos os mercados</option>
          {niches.map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-[#0F1B2D]">
          <option value="">Todos os status</option>
          {Object.entries(STATUS_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        {(filterPlatform || filterNiche || filterStatus) && (
          <button onClick={() => { setFilterPlatform(""); setFilterNiche(""); setFilterStatus(""); }} className="text-[10px] text-[#E8734A] underline">Limpar filtros</button>
        )}
        <span className="text-[10px] text-slate-400 ml-auto">{filteredEntries.length} conteúdo{filteredEntries.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Legenda */}
      <div className="flex gap-4">
        {(Object.entries(STATUS_CONFIG) as [string, typeof STATUS_CONFIG.pendente][]).map(([key, cfg]) => (
          <div key={key} className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <span className={`w-2.5 h-2.5 rounded-full ${cfg.color}`} />
            {cfg.label}
          </div>
        ))}
      </div>

      {/* Grid semanal */}
      <div className="grid grid-cols-7 gap-2">
        {dates.map((date, i) => {
          const dateStr = formatDate(date);
          const dayEntries = filteredEntries.filter((e) => e.scheduled_date === dateStr);
          const isToday = formatDate(new Date()) === dateStr;

          return (
            <div
              key={dateStr}
              className={`min-h-[140px] rounded-xl border p-2 ${isToday ? "border-[#E8734A]/40 bg-[#E8734A]/5" : "border-slate-200 bg-white"}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] font-medium ${isToday ? "text-[#E8734A]" : "text-slate-400"}`}>{DAY_NAMES[i]}</span>
                <span className={`text-xs font-semibold ${isToday ? "text-[#E8734A]" : "text-[#0F1B2D]"}`}>{date.getDate()}</span>
              </div>
              <div className="space-y-1.5">
                {dayEntries.map((entry) => {
                  const cfg = STATUS_CONFIG[entry.status] || STATUS_CONFIG.pendente;
                  return (
                    <button
                      key={entry.id}
                      onClick={() => setSelectedEntry(entry)}
                      className={`w-full text-left p-1.5 rounded-lg border ${cfg.border} ${cfg.bg} transition-all hover:shadow-sm`}
                    >
                      <div className="flex items-center gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full ${cfg.color}`} />
                        <span className="text-[9px] text-slate-400">{entry.scheduled_time}</span>
                      </div>
                      <p className={`text-[10px] font-medium ${cfg.text} truncate mt-0.5`}>{entry.script.title}</p>
                      <p className="text-[9px] text-slate-400">{entry.platform}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Detalhe do conteudo selecionado */}
      {selectedEntry && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-semibold text-[#0F1B2D]">{selectedEntry.script.title}</h4>
              <p className="text-xs text-slate-500">
                {selectedEntry.platform} · {selectedEntry.niche} · Público: {selectedEntry.audience}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${(STATUS_CONFIG[selectedEntry.status] || STATUS_CONFIG.pendente).bg} ${(STATUS_CONFIG[selectedEntry.status] || STATUS_CONFIG.pendente).text}`}>
                {(STATUS_CONFIG[selectedEntry.status] || STATUS_CONFIG.pendente).label}
              </span>
              <button onClick={() => setSelectedEntry(null)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
          </div>

          <div className="space-y-3">
            <DetailSection label="Copy (legenda)" content={selectedEntry.script.copy} />
            <DetailSection label="Especificação Visual" content={selectedEntry.script.visual_spec} />
            <DetailSection label="CTA" content={selectedEntry.script.cta} />
            <DetailSection label="Thumbnail" content={selectedEntry.script.thumbnail_description} />

            <div className="flex flex-wrap gap-1.5">
              {selectedEntry.script.hashtags.map((tag, j) => (
                <span key={j} className="px-2 py-0.5 bg-[#0F1B2D]/5 text-[#0F1B2D] rounded-full text-[10px] font-medium">{tag}</span>
              ))}
            </div>

            <p className="text-[10px] text-slate-400">Horário sugerido: {selectedEntry.scheduled_time}</p>
          </div>

          <div className="flex gap-2 mt-4 pt-4 border-t border-slate-100 flex-wrap">
            {selectedEntry.status === "pendente" && (<>
              <button onClick={() => handleAction(selectedEntry.id, "approve")} disabled={loading} className="px-4 py-2 bg-emerald-600 text-white text-xs rounded-lg hover:bg-emerald-700 disabled:opacity-50">Aprovar</button>
              <button onClick={() => handleAction(selectedEntry.id, "discard")} disabled={loading} className="px-4 py-2 bg-red-500 text-white text-xs rounded-lg hover:bg-red-600 disabled:opacity-50">Descartar</button>
            </>)}
            <button
              onClick={handleGenerateWAMessage}
              disabled={loadingMsg}
              className="px-4 py-2 bg-[#25D366] text-white text-xs rounded-lg hover:bg-[#1ebe5a] disabled:opacity-50 flex items-center gap-1.5 ml-auto"
            >
              <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
              {loadingMsg ? "Gerando..." : "Enviar roteiro via WhatsApp"}
            </button>
          </div>
        </div>
      )}

      {/* Modal WhatsApp */}
      {showWA && selectedEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => { setShowWA(false); setSendStatus(""); }}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-[#0F1B2D]">Enviar roteiro via WhatsApp</h3>
                <p className="text-xs text-slate-500">{selectedEntry.platform} · {selectedEntry.niche} · {selectedEntry.scheduled_date}</p>
              </div>
              <button onClick={() => { setShowWA(false); setSendStatus(""); }} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>

            <div className="p-2.5 bg-amber-50 border border-amber-100 rounded-lg mb-4">
              <p className="text-[10px] text-amber-700">Roteiro gerado com base no dataset. Edite a mensagem antes de enviar ao influenciador ou equipe de produção.</p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Mensagem (edite antes de enviar)</label>
                <textarea value={editableMsg} onChange={(e) => setEditableMsg(e.target.value)} rows={8} className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30 resize-none" />
                <p className="text-[9px] text-slate-400 text-right">{editableMsg.length} caracteres</p>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Telefone (com DDI, ex: 5511999999999)</label>
                <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="5511999999999" className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30" />
              </div>
              <div className="flex gap-2">
                <a
                  href={`https://wa.me/${phone.replace(/\D/g, "")}?text=${encodeURIComponent(editableMsg)}`}
                  target="_blank" rel="noopener noreferrer"
                  className={`flex-1 px-4 py-2 bg-[#25D366] text-white text-xs text-center rounded-lg hover:bg-[#1ebe5a] transition-colors ${!phone ? "opacity-50 pointer-events-none" : ""}`}
                >
                  Abrir no WhatsApp
                </a>
                <button
                  onClick={async () => {
                    if (!phone) return;
                    setSendStatus("enviando...");
                    try {
                      const statusRes = await fetch("/api/zapi/status");
                      const statusData = await statusRes.json();
                      if (!statusData.configured) { setSendStatus("Z-API não configurado. Configure no header."); return; }
                      if (!statusData.connected) { setSendStatus("WhatsApp desconectado. Escaneie o QR Code no header."); return; }
                      const res = await fetch("/api/zapi/send", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ phone, message: editableMsg }),
                      });
                      const data = await res.json();
                      setSendStatus(data.success ? "Mensagem enviada com sucesso!" : `Erro: ${data.error || "Falha ao enviar"}`);
                    } catch { setSendStatus("Erro de conexão."); }
                  }}
                  disabled={!phone || sendStatus === "enviando..."}
                  className="flex-1 px-4 py-2 bg-[#0F1B2D] text-white text-xs rounded-lg hover:bg-[#1A2D47] disabled:opacity-50"
                >
                  Enviar via Z-API
                </button>
              </div>
              {sendStatus && (
                <p className={`text-xs text-center font-medium ${sendStatus.includes("sucesso") ? "text-emerald-600" : "text-red-500"}`}>{sendStatus}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailSection({ label, content }: { label: string; content: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xs text-[#0F1B2D] whitespace-pre-wrap leading-relaxed">{content}</p>
    </div>
  );
}

