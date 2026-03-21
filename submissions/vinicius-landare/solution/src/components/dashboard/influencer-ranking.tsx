"use client";

import { useState } from "react";

interface Influencer {
  rank: number;
  creator_id: string;
  creator_name: string;
  score: number;
  action: "incentivar" | "manter" | "alinhar" | "reavaliar";
  avg_engagement: number;
  total_posts: number;
  follower_count: number;
  creator_tier: string;
  primary_platform: string;
  primary_category: string;
  sponsorship_lift: number | null;
  sponsored_rate: number;
}

interface RankingData {
  total_creators: number;
  action_summary: Record<string, number>;
  data: Influencer[];
}

interface Props {
  rankingData: RankingData;
  onGenerateMessage?: (influencer: Influencer) => void;
  onSendZAPI?: (influencer: Influencer, message: string) => void;
}

const ACTION_CONFIG = {
  incentivar: { label: "Incentivar", icon: "\u2605", color: "emerald", bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  manter: { label: "Manter", icon: "\u25CF", color: "blue", bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  alinhar: { label: "Alinhar", icon: "\u25B2", color: "amber", bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  reavaliar: { label: "Reavaliar", icon: "\u25BC", color: "red", bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
};

const TIER_LABELS: Record<string, string> = {
  "Nano (< 10K)": "Nano",
  "Micro (10K-50K)": "Micro",
  "Mid (50K-100K)": "M\u00e9dio",
  "Macro (100K-500K)": "Grande",
  "Mega (500K+)": "Mega",
};

const PER_PAGE = 20;

export function InfluencerRanking({ rankingData, onGenerateMessage, onSendZAPI }: Props) {
  const [filterPlatform, setFilterPlatform] = useState<string>("all");
  const [filterTier, setFilterTier] = useState<string>("all");
  const [filterAction, setFilterAction] = useState<string>("all");
  const [selectedInfluencer, setSelectedInfluencer] = useState<Influencer | null>(null);
  const [generatedMessage, setGeneratedMessage] = useState<string>("");
  const [editableMessage, setEditableMessage] = useState<string>("");
  const [loadingMessage, setLoadingMessage] = useState(false);
  const [phone, setPhone] = useState<string>("");
  const [sendStatus, setSendStatus] = useState<string>("");
  const [page, setPage] = useState(1);

  const allData = rankingData?.data || [];
  const platforms = [...new Set(allData.map((d) => d.primary_platform))].sort();
  const tiers = [...new Set(allData.map((d) => d.creator_tier))];

  const filtered = allData.filter((d) => {
    if (filterPlatform !== "all" && d.primary_platform !== filterPlatform) return false;
    if (filterTier !== "all" && d.creator_tier !== filterTier) return false;
    if (filterAction !== "all" && d.action !== filterAction) return false;
    return true;
  });

  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const safePage = Math.min(page, totalPages || 1);
  const displayed = filtered.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE);

  async function handleGenerateMessage(inf: Influencer) {
    setLoadingMessage(true);
    setGeneratedMessage("");
    try {
      const res = await fetch("/api/influencer-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          creator_name: inf.creator_name,
          score: inf.score,
          action: inf.action,
          avg_engagement: inf.avg_engagement,
          total_posts: inf.total_posts,
          trend: "est\u00e1vel",
          sponsorship_lift: inf.sponsorship_lift,
        }),
      });
      const data = await res.json();
      const msg = data.message || data.error || "Erro ao gerar mensagem";
      setGeneratedMessage(msg);
      setEditableMessage(msg);
    } catch {
      setGeneratedMessage("Erro de conexao com a API");
      setEditableMessage("Erro de conexao com a API");
    }
    setLoadingMessage(false);
    onGenerateMessage?.(inf);
  }

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(["incentivar", "manter", "alinhar", "reavaliar"] as const).map((action) => {
          const config = ACTION_CONFIG[action];
          const count = rankingData?.action_summary?.[action] || 0;
          return (
            <button
              key={action}
              onClick={() => { setFilterAction(filterAction === action ? "all" : action); setPage(1); }}
              className={`rounded-xl border p-4 text-left transition-all ${
                filterAction === action ? `${config.bg} ${config.border} ring-1 ring-${config.color}-300` : "bg-white border-slate-200"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`text-lg ${config.text}`}>{config.icon}</span>
                <span className="text-xs font-medium text-slate-500">{config.label}</span>
              </div>
              <p className="text-2xl font-bold text-[#0F1B2D] mt-1">{count}</p>
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <select
          value={filterPlatform}
          onChange={(e) => { setFilterPlatform(e.target.value); setPage(1); }}
          className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
        >
          <option value="all">Todas plataformas</option>
          {platforms.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select
          value={filterTier}
          onChange={(e) => { setFilterTier(e.target.value); setPage(1); }}
          className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
        >
          <option value="all">Todos tiers</option>
          {tiers.map((t) => <option key={t} value={t}>{TIER_LABELS[t] || t}</option>)}
        </select>
        <span className="text-xs text-slate-400 self-center ml-2">{filtered.length} creators</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">Creator</th>
                <th className="px-4 py-3 text-center">Score</th>
                <th className="px-4 py-3 text-center">Eng%</th>
                <th className="px-4 py-3 text-center">Posts</th>
                <th className="px-4 py-3 text-center">Tier</th>
                <th className="px-4 py-3 text-center">Plataforma</th>
                <th className="px-4 py-3 text-center">A\u00e7\u00e3o</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map((inf) => {
                const config = ACTION_CONFIG[inf.action];
                return (
                  <tr
                    key={inf.creator_id}
                    onClick={() => setSelectedInfluencer(selectedInfluencer?.creator_id === inf.creator_id ? null : inf)}
                    className={`border-t border-slate-100 cursor-pointer hover:bg-slate-50 transition-colors ${
                      selectedInfluencer?.creator_id === inf.creator_id ? "bg-[#E8734A]/5" : ""
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-400">{inf.rank}</td>
                    <td className="px-4 py-3 font-medium text-[#0F1B2D]">@{inf.creator_name}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-bold text-[#0F1B2D]">{inf.score}</span>
                    </td>
                    <td className="px-4 py-3 text-center">{inf.avg_engagement?.toFixed(2)}%</td>
                    <td className="px-4 py-3 text-center">{inf.total_posts}</td>
                    <td className="px-4 py-3 text-center">{TIER_LABELS[inf.creator_tier] || inf.creator_tier}</td>
                    <td className="px-4 py-3 text-center">{inf.primary_platform}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${config.bg} ${config.text} font-medium`}>
                        {config.icon} {config.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Paginacao */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Mostrando {(safePage - 1) * PER_PAGE + 1}–{Math.min(safePage * PER_PAGE, filtered.length)} de {filtered.length}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-30"
            >
              Anterior
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 7) {
                pageNum = i + 1;
              } else if (safePage <= 4) {
                pageNum = i + 1;
              } else if (safePage >= totalPages - 3) {
                pageNum = totalPages - 6 + i;
              } else {
                pageNum = safePage - 3 + i;
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-8 h-8 text-xs rounded-lg transition-colors ${
                    pageNum === safePage
                      ? "bg-[#0F1B2D] text-white"
                      : "border border-slate-200 hover:bg-slate-50 text-slate-600"
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-30"
            >
              Proxima
            </button>
          </div>
        </div>
      )}

      {/* Detail Popup (modal) */}
      {selectedInfluencer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => { setSelectedInfluencer(null); setGeneratedMessage(""); setEditableMessage(""); setPhone(""); setSendStatus(""); }}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-[#0F1B2D]">@{selectedInfluencer.creator_name}</h3>
                <p className="text-xs text-slate-500">Score: {selectedInfluencer.score}/100 · {ACTION_CONFIG[selectedInfluencer.action].label}</p>
              </div>
              <button
                onClick={() => { setSelectedInfluencer(null); setGeneratedMessage(""); setEditableMessage(""); setPhone(""); setSendStatus(""); }}
                className="text-slate-400 hover:text-slate-600 text-xl"
              >
                &times;
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <DetailItem label="Engagement" value={`${selectedInfluencer.avg_engagement?.toFixed(2)}%`} />
              <DetailItem label="Posts" value={String(selectedInfluencer.total_posts)} />
              <DetailItem label="Seguidores" value={selectedInfluencer.follower_count?.toLocaleString("pt-BR")} />
              <DetailItem label="Lift Patrocínio" value={
                selectedInfluencer.sponsorship_lift != null
                  ? `${selectedInfluencer.sponsorship_lift > 0 ? "+" : ""}${selectedInfluencer.sponsorship_lift.toFixed(2)}%`
                  : "N/A"
              } />
            </div>

            {/* Disclaimer dataset */}
            <div className="p-2.5 bg-amber-50 border border-amber-100 rounded-lg mb-4">
              <p className="text-[10px] text-amber-700">
                Dados baseados no dataset de estudo. As diferenças são pequenas (~0.1-0.2%).
                Use a aba Análise de Perfil para validar com dados reais antes de tomar decisões.
              </p>
            </div>

            <button
              onClick={() => handleGenerateMessage(selectedInfluencer)}
              disabled={loadingMessage}
              className="w-full px-4 py-2 bg-[#0F1B2D] text-white text-xs rounded-lg hover:bg-[#1A2D47] transition-colors disabled:opacity-50 mb-4"
            >
              {loadingMessage ? "Gerando mensagem com IA..." : generatedMessage ? "Regerar mensagem" : "Gerar mensagem WhatsApp"}
            </button>

            {generatedMessage && (
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Mensagem (edite antes de enviar)</label>
                  <textarea
                    value={editableMessage}
                    onChange={(e) => setEditableMessage(e.target.value)}
                    rows={6}
                    maxLength={500}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30 resize-none"
                  />
                  <p className="text-[9px] text-slate-400 text-right">{editableMessage.length}/500</p>
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">Telefone do influenciador (com DDD, ex: 5511999999999)</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="5511999999999"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30"
                  />
                </div>

                <div className="flex gap-2">
                  <a
                    href={`https://wa.me/${phone.replace(/\D/g, "")}?text=${encodeURIComponent(editableMessage)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex-1 px-4 py-2 bg-emerald-600 text-white text-xs text-center rounded-lg hover:bg-emerald-700 transition-colors ${!phone ? "opacity-50 pointer-events-none" : ""}`}
                  >
                    Abrir no WhatsApp (wa.me)
                  </a>
                  <button
                    onClick={async () => {
                      if (!phone) return;
                      setSendStatus("enviando...");
                      try {
                        // Verificar status ZAPI antes de enviar
                        const statusRes = await fetch("/api/zapi/status");
                        const statusData = await statusRes.json();

                        if (!statusData.configured) {
                          setSendStatus("Z-API não configurado. Configure no botão WhatsApp do header.");
                          return;
                        }
                        if (statusData.needsClientToken) {
                          setSendStatus("Falta o Token de Segurança (ZAPI_CLIENT_TOKEN) no .env");
                          return;
                        }
                        if (!statusData.connected) {
                          setSendStatus("WhatsApp não conectado. Escaneie o QR Code no botão WhatsApp do header.");
                          return;
                        }

                        const res = await fetch("/api/zapi/send", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ phone, message: editableMessage }),
                        });
                        const data = await res.json();

                        if (data.success) {
                          setSendStatus("Mensagem enviada com sucesso!");
                        } else {
                          const errorMsg = data.error || "Erro desconhecido";
                          if (errorMsg.includes("not connected") || errorMsg.includes("disconnected")) {
                            setSendStatus("WhatsApp desconectado. Escaneie o QR Code no botão WhatsApp do header.");
                          } else if (errorMsg.includes("invalid phone") || errorMsg.includes("phone")) {
                            setSendStatus("Número inválido. Use o formato: 5511999999999 (país + DDD + número)");
                          } else {
                            setSendStatus(`Erro: ${errorMsg}`);
                          }
                        }
                      } catch {
                        setSendStatus("Falha na conexão com o servidor");
                      }
                    }}
                    disabled={!phone}
                    className="flex-1 px-4 py-2 bg-[#0F1B2D] text-white text-xs rounded-lg hover:bg-[#1A2D47] transition-colors disabled:opacity-50"
                  >
                    Enviar via ZAPI
                  </button>
                </div>

                {sendStatus && (
                  <div className={`p-3 rounded-lg text-xs ${
                    sendStatus.includes("sucesso")
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : sendStatus === "enviando..."
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-red-50 text-red-700 border border-red-200"
                  }`}>
                    {sendStatus}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-400 uppercase">{label}</p>
      <p className="text-sm font-semibold text-[#0F1B2D]">{value}</p>
    </div>
  );
}
