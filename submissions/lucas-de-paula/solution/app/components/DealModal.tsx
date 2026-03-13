"use client";

import { useState } from "react";
import { type ScoredDeal, scoreColor } from "@/lib/scoring";
import { getActionTag, getUrgencyNote } from "@/lib/actions";
import { ScoreBreakdown } from "./ScoreBreakdown";

interface DealModalProps {
  deal: ScoredDeal;
  onClose: () => void;
  onUpdate?: () => void; // called after a successful stage change / close
}

const NOTES_KEY = "lead-scorer-notes";

function loadNotes(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try { return JSON.parse(localStorage.getItem(NOTES_KEY) ?? "{}"); }
  catch { return {}; }
}
function saveNote(id: string, text: string) {
  const notes = loadNotes();
  notes[id] = text;
  localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
}

const stageColor: Record<string, string> = {
  Engaging:    "text-blue-400 bg-blue-500/15 border-blue-500/30",
  Prospecting: "text-gray-400 bg-gray-500/15 border-gray-500/30",
  Won:         "text-emerald-400 bg-emerald-500/15 border-emerald-500/30",
  Lost:        "text-red-400 bg-red-500/15 border-red-500/30",
};

// ── Close deal form ─────────────────────────────────────────────────────────
interface CloseFormProps {
  onConfirm: (data: { outcome: "Won" | "Lost"; closeValue: string; closeDate: string; obs: string }) => void;
  onCancel: () => void;
  saving: boolean;
}
function CloseForm({ onConfirm, onCancel, saving }: CloseFormProps) {
  const [outcome, setOutcome]       = useState<"Won" | "Lost">("Won");
  const [closeValue, setCloseValue] = useState("");
  const [closeDate, setCloseDate]   = useState(new Date().toISOString().split("T")[0]);
  const [obs, setObs]               = useState("");

  return (
    <div className="bg-gray-800/60 border border-gray-700 rounded-2xl p-5 space-y-4">
      <p className="text-white text-sm font-semibold">🔒 Encerrar este deal</p>

      {/* Win / Lost toggle */}
      <div className="flex gap-2">
        {(["Won", "Lost"] as const).map((o) => (
          <button
            key={o}
            onClick={() => setOutcome(o)}
            className={`flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-colors ${
              outcome === o
                ? o === "Won"
                  ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                  : "bg-red-500/20 border-red-500 text-red-400"
                : "border-gray-700 text-gray-500 hover:border-gray-600"
            }`}
          >
            {o === "Won" ? "🏆 Ganho (Won)" : "❌ Perdido (Lost)"}
          </button>
        ))}
      </div>

      {/* Valor fechado */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 uppercase tracking-wider">
          Valor fechado {outcome === "Won" ? "(obrigatório)" : "(opcional)"}
        </label>
        <input
          type="number"
          value={closeValue}
          onChange={(e) => setCloseValue(e.target.value)}
          placeholder={outcome === "Won" ? "Ex: 5482" : "Deixe em branco se não houve valor"}
          className="bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Data de fechamento */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 uppercase tracking-wider">Data de fechamento</label>
        <input
          type="date"
          value={closeDate}
          onChange={(e) => setCloseDate(e.target.value)}
          className="bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Observações */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 uppercase tracking-wider">Observações (opcional)</label>
        <textarea
          value={obs}
          onChange={(e) => setObs(e.target.value)}
          placeholder="Motivo do resultado, próximos passos, contexto para o time..."
          rows={3}
          className="bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-blue-500 focus:outline-none resize-none placeholder-gray-600"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={onCancel}
          className="flex-1 py-2.5 rounded-xl border border-gray-700 text-gray-400 hover:border-gray-600 text-sm transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={() => onConfirm({ outcome, closeValue, closeDate, obs })}
          disabled={saving || (outcome === "Won" && !closeValue)}
          className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors disabled:opacity-40 ${
            outcome === "Won"
              ? "bg-emerald-600 hover:bg-emerald-500 text-white"
              : "bg-red-700 hover:bg-red-600 text-white"
          }`}
        >
          {saving ? "Salvando..." : `Confirmar como ${outcome}`}
        </button>
      </div>
    </div>
  );
}

// ── Main modal ──────────────────────────────────────────────────────────────
interface AiAnalysis {
  urgencia: "alta" | "media" | "baixa";
  resumo: string;
  acao: string;
  raciocinio: string;
}

export function DealModal({ deal, onClose, onUpdate }: DealModalProps) {
  const [note, setNote]               = useState(() => loadNotes()[deal.opportunity_id] ?? "");
  const [saved, setSaved]             = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showCloseForm, setShowCloseForm] = useState(false);
  const [saving, setSaving]           = useState(false);
  const [actionResult, setActionResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [currentStage, setCurrentStage] = useState(deal.deal_stage);
  const [aiLoading, setAiLoading]     = useState(false);
  const [aiResult, setAiResult]       = useState<AiAnalysis | null>(null);
  const [aiError, setAiError]         = useState<string | null>(null);

  async function handleAnalyze() {
    setAiLoading(true);
    setAiResult(null);
    setAiError(null);
    try {
      const res = await fetch("/api/ai/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(deal),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Erro desconhecido");
      setAiResult(data);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Erro ao analisar.");
    } finally {
      setAiLoading(false);
    }
  }

  const color = scoreColor(deal.score);
  const badgeColor = {
    green:  "text-emerald-400 bg-emerald-500/20 border-emerald-500/40",
    yellow: "text-amber-400 bg-amber-500/20 border-amber-500/40",
    red:    "text-red-400 bg-red-500/20 border-red-500/40",
  }[color];

  // Action tag reflects the current (possibly updated) stage
  const dealForTag = { ...deal, deal_stage: currentStage };
  const actionTag  = getActionTag(dealForTag);
  const urgency    = getUrgencyNote(dealForTag);

  function handleSaveNote() {
    saveNote(deal.opportunity_id, note);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const parseDate = (d: unknown) => (d ? new Date(d as string) : null);
  const engageStr = deal.engage_date ? parseDate(deal.engage_date)!.toLocaleDateString("pt-BR") : "—";
  const closeStr  = deal.close_date  ? parseDate(deal.close_date)!.toLocaleDateString("pt-BR")  : "Em aberto";

  async function handleAdvanceStage() {
    setSaving(true);
    const today = new Date().toISOString().split("T")[0];
    const res = await fetch("/api/admin/deal", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: deal.opportunity_id, deal_stage: "Engaging", engage_date: today }),
    });
    setSaving(false);
    if (res.ok) {
      setCurrentStage("Engaging");
      setActionResult({ ok: true, msg: "Deal movido para Engaging com sucesso." });
      onUpdate?.();
    } else {
      setActionResult({ ok: false, msg: "Erro ao mover o deal. Tente novamente." });
    }
  }

  async function handleClose(data: { outcome: "Won" | "Lost"; closeValue: string; closeDate: string; obs: string }) {
    setSaving(true);
    if (data.obs.trim()) {
      const combined = note ? `${note}\n\n[${data.outcome} em ${data.closeDate}] ${data.obs}` : `[${data.outcome} em ${data.closeDate}] ${data.obs}`;
      saveNote(deal.opportunity_id, combined);
      setNote(combined);
    }
    const res = await fetch("/api/admin/deal", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: deal.opportunity_id,
        deal_stage:  data.outcome,
        close_date:  data.closeDate,
        close_value: data.closeValue || "0",
      }),
    });
    setSaving(false);
    if (res.ok) {
      setCurrentStage(data.outcome);
      setShowCloseForm(false);
      setActionResult({
        ok:  true,
        msg: data.outcome === "Won"
          ? `🏆 Deal encerrado como Ganho em ${new Date(data.closeDate).toLocaleDateString("pt-BR")}!`
          : `❌ Deal encerrado como Perdido em ${new Date(data.closeDate).toLocaleDateString("pt-BR")}.`,
      });
      onUpdate?.();
    } else {
      setActionResult({ ok: false, msg: "Erro ao encerrar o deal. Tente novamente." });
    }
  }

  return (
    <>
      {showBreakdown && (
        <ScoreBreakdown
          score={deal.score}
          components={deal.components}
          dealName={deal.account || deal.opportunity_id}
          onClose={() => setShowBreakdown(false)}
        />
      )}

      {/* ── Outer: full-screen scrollable overlay ── */}
      <div
        className="fixed inset-0 z-50 overflow-y-auto"
        onClick={onClose}
      >
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        {/* ── Center wrapper (allows scroll when content > viewport) ── */}
        <div className="relative min-h-full flex items-center justify-center p-4">
          <div
            className="relative bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl my-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-800">
              <div className="flex-1 min-w-0">
                {/* Stage badge + action tag + urgency */}
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${stageColor[currentStage] ?? stageColor.Prospecting}`}>
                    {currentStage}
                  </span>
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${actionTag.style}`}>
                    {actionTag.label}
                  </span>
                  {urgency && (
                    <span className={`text-[10px] font-medium ${
                      deal.score >= 70 && deal.days_in_stage <= 30
                        ? "text-emerald-500/70"
                        : "text-amber-500/70"
                    }`}>
                      {urgency}
                    </span>
                  )}
                  <span className="text-gray-600 text-xs font-mono">#{deal.opportunity_id}</span>
                </div>
                <h2 className="text-white font-bold text-xl leading-tight truncate">
                  {deal.account || "Sem conta identificada"}
                </h2>
                <p className="text-gray-500 text-sm mt-0.5">{deal.product}</p>
              </div>

              <div className="flex items-center gap-3 ml-4 shrink-0">
                <button
                  onClick={() => setShowBreakdown(true)}
                  className={`flex flex-col items-center px-4 py-2 rounded-xl border cursor-pointer hover:opacity-80 transition-opacity ${badgeColor}`}
                  title="Ver breakdown do score"
                >
                  <span className="text-3xl font-black tabular-nums">{deal.score}</span>
                  <span className="text-[10px] opacity-70">ver breakdown</span>
                </button>
                <button onClick={onClose} className="text-gray-500 hover:text-gray-300 p-1">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Details grid */}
            <div className="p-6 grid grid-cols-2 gap-4">
              {[
                { label: "Vendedor",           value: deal.sales_agent },
                { label: "Manager",            value: deal.manager },
                { label: "Região",             value: deal.regional_office },
                { label: "Setor",              value: deal.account_sector || "—" },
                { label: "País",               value: deal.account_country || "—" },
                { label: "Produto",            value: deal.product },
                { label: "Ticket",             value: deal.product_price ? `$${deal.product_price.toLocaleString()}` : "—" },
                { label: "Valor fechado",      value: deal.close_value ? `$${deal.close_value.toLocaleString()}` : "—" },
                { label: "Revenue da conta",   value: deal.account_revenue ? `$${deal.account_revenue.toFixed(0)}M` : "—" },
                { label: "Funcionários",       value: deal.account_employees || "—" },
                { label: "Início do Engaging", value: engageStr },
                { label: "Data de fechamento", value: closeStr },
                {
                  label: "Dias no stage",
                  value: (
                    <span className={
                      deal.days_in_stage > 90 ? "text-red-400 font-semibold" :
                      deal.days_in_stage > 30 ? "text-amber-400" : "text-gray-300"
                    }>
                      {deal.days_in_stage} dias
                      {deal.days_in_stage > 90  && " 💀 Zumbi"}
                      {deal.days_in_stage > 30 && deal.days_in_stage <= 90 && " ⚠️ Em risco"}
                    </span>
                  ),
                },
                { label: "Subsidiária de", value: deal.account_has_parent ? "Sim" : "Não" },
              ].map(({ label, value }) => (
                <div key={label} className="bg-gray-800/40 rounded-xl p-3">
                  <p className="text-gray-500 text-xs mb-1">{label}</p>
                  <div className="text-gray-200 text-sm font-medium">{value as React.ReactNode}</div>
                </div>
              ))}
            </div>

            {/* Notes */}
            <div className="px-6 pb-4">
              <div className="border-t border-gray-800 pt-4">
                <label className="text-gray-400 text-xs uppercase tracking-wider block mb-2">Anotações</label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Adicione notas sobre este deal... próximos passos, objeções, contexto."
                  rows={3}
                  className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-xl px-4 py-3 focus:border-gray-500 focus:outline-none resize-none placeholder-gray-600"
                />
                <div className="flex items-center justify-between mt-2">
                  <p className="text-gray-600 text-xs">Salvo localmente no seu navegador</p>
                  <button
                    onClick={handleSaveNote}
                    className={`text-sm px-4 py-1.5 rounded-lg transition-colors font-medium ${
                      saved ? "bg-emerald-600 text-white" : "bg-blue-600 hover:bg-blue-500 text-white"
                    }`}
                  >
                    {saved ? "Salvo ✓" : "Salvar nota"}
                  </button>
                </div>
              </div>
            </div>

            {/* ── AI Coach ── */}
            <div className="px-6 pb-4">
              <div className="border-t border-gray-800 pt-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-gray-400 text-xs uppercase tracking-wider">Coach de IA</p>
                  <button
                    onClick={handleAnalyze}
                    disabled={aiLoading}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-semibold transition-colors disabled:opacity-50"
                  >
                    {aiLoading ? (
                      <><span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analisando...</>
                    ) : (
                      <>✨ Analisar deal</>
                    )}
                  </button>
                </div>

                {aiError && (
                  <div className="rounded-xl p-3 text-xs bg-red-500/10 border border-red-500/25 text-red-400">
                    {aiError}
                  </div>
                )}

                {aiResult && (
                  <div className="rounded-xl border border-violet-500/25 bg-violet-500/5 p-4 space-y-3">
                    {/* Urgência badge */}
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                        aiResult.urgencia === "alta"
                          ? "bg-red-500/15 text-red-400 border-red-500/30"
                          : aiResult.urgencia === "media"
                          ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
                          : "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                      }`}>
                        {aiResult.urgencia === "alta" ? "🔴 Urgência alta" : aiResult.urgencia === "media" ? "🟡 Urgência média" : "🟢 Urgência baixa"}
                      </span>
                    </div>

                    {/* Resumo */}
                    <p className="text-white text-sm font-semibold leading-snug">{aiResult.resumo}</p>

                    {/* Ação recomendada */}
                    <div className="bg-violet-500/10 rounded-lg p-3">
                      <p className="text-violet-300 text-[10px] uppercase tracking-wider font-semibold mb-1">Ação recomendada</p>
                      <p className="text-gray-200 text-sm leading-relaxed">{aiResult.acao}</p>
                    </div>

                    {/* Raciocínio */}
                    <div>
                      <p className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold mb-1">Raciocínio</p>
                      <p className="text-gray-400 text-xs leading-relaxed">{aiResult.raciocinio}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ── Deal Actions ── */}
            {(currentStage === "Prospecting" || currentStage === "Engaging") && (
              <div className="px-6 pb-6">
                <div className="border-t border-gray-800 pt-4 space-y-3">
                  <p className="text-gray-400 text-xs uppercase tracking-wider">Ações do Deal</p>

                  {actionResult && (
                    <div className={`rounded-xl p-3 text-sm ${
                      actionResult.ok
                        ? "bg-emerald-500/10 border border-emerald-500/25 text-emerald-400"
                        : "bg-red-500/10 border border-red-500/25 text-red-400"
                    }`}>
                      {actionResult.msg}
                    </div>
                  )}

                  {currentStage === "Prospecting" && !actionResult?.ok && (
                    <button
                      onClick={handleAdvanceStage}
                      disabled={saving}
                      className="w-full py-3 rounded-xl border border-blue-500/40 text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 text-sm font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
                    >
                      {saving ? (
                        <><span className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" /> Movendo...</>
                      ) : (
                        <>➡️ Mover para Engaging</>
                      )}
                    </button>
                  )}

                  {currentStage === "Engaging" && !actionResult?.ok && (
                    showCloseForm ? (
                      <CloseForm
                        onConfirm={handleClose}
                        onCancel={() => setShowCloseForm(false)}
                        saving={saving}
                      />
                    ) : (
                      <button
                        onClick={() => setShowCloseForm(true)}
                        className="w-full py-3 rounded-xl border border-gray-600 text-gray-300 hover:border-gray-500 hover:bg-gray-800/40 text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                      >
                        🔒 Encerrar Deal
                      </button>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Already closed */}
            {(currentStage === "Won" || currentStage === "Lost") && (
              <div className="px-6 pb-6">
                <div className={`rounded-xl p-4 text-sm border ${
                  currentStage === "Won"
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                    : "bg-red-500/10 border-red-500/20 text-red-400"
                }`}>
                  {currentStage === "Won" ? "🏆 Deal encerrado como Ganho." : "❌ Deal encerrado como Perdido."}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
