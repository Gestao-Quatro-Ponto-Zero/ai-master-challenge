"use client";

import { useState } from "react";

export function BetaDemo() {
  const [profile, setProfile] = useState("");
  const [platform, setPlatform] = useState("instagram");
  const [collecting, setCollecting] = useState(false);
  const [collectedData, setCollectedData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  async function handleCollect() {
    if (!profile) return;
    setCollecting(true);
    setError("");
    setCollectedData(null);

    // Nota: coleta real requer backend Python com Apify
    // Por enquanto, simula a resposta para demonstração
    await new Promise((r) => setTimeout(r, 2000));

    setCollectedData({
      profile: profile,
      platform: platform,
      total_posts: 30,
      avg_engagement: 3.8,
      median_engagement: 3.2,
      top_post: { description: "Como fazer skincare em 5 passos", engagement: 12.4 },
      worst_post: { description: "Promoção flash de produtos", engagement: 0.9 },
      trend: "+0.5pp vs mês anterior",
      note: "Dados simulados para demonstração. Com Apify configurado, estes seriam dados reais do perfil.",
    });
    setCollecting(false);
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#E8734A]/10 to-[#0F1B2D]/5 rounded-2xl border border-[#E8734A]/20 p-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-0.5 bg-[#E8734A] text-white text-[10px] font-bold rounded-full uppercase">Beta</span>
          <h3 className="text-base font-semibold text-[#0F1B2D]">Demonstração do Sistema em Produção</h3>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
          Esta seção demonstra como o G4 Social Metrics funcionaria com dados reais.
          O painel atual analisa 52.214 posts de um dataset de estudo. Em produção, o sistema
          coletaria dados via Apify, detectaria tendências em tempo real, e geraria recomendações
          personalizadas via IA.
        </p>
      </div>

      {/* Comparação Dataset vs Produção */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h4 className="text-sm font-semibold text-slate-500 mb-3">O que o dataset mostra</h4>
          <div className="space-y-2">
            <ComparisonRow label="Engagement" value="19.9% (estático)" />
            <ComparisonRow label="Tendência" value="Sem dados (snapshot único)" />
            <ComparisonRow label="Insight" value={`"Melhor combo: RedNote × mixed × lifestyle"\n(diferença: 0.14pp — não significativa)`} />
            <ComparisonRow label="Recomendação" value="Hardcoded, igual para todos" />
            <ComparisonRow label="Influenciadores" value="Score calculado, sem ação real" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-[#E8734A]/20 shadow-sm p-6">
          <h4 className="text-sm font-semibold text-[#E8734A] mb-3">Em produção (com dados reais)</h4>
          <div className="space-y-2">
            <ComparisonRow label="Engagement" value="4.2% (atualizado a cada 1h)" highlight />
            <ComparisonRow label="Tendência" value="-0.8pp vs semana passada" highlight />
            <ComparisonRow label="Insight" value={`"Reels Beauty caiu 15% esta semana.\nAção: migrar 2 posts para carrossel."`} highlight />
            <ComparisonRow label="Recomendação" value="IA gera roteiros personalizados (Draft → Critique → Output)" highlight />
            <ComparisonRow label="Influenciadores" value="Mensagem WhatsApp automática via ZAPI" highlight />
          </div>
        </div>
      </div>

      {/* Coleta Apify */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h4 className="text-sm font-semibold text-[#0F1B2D] mb-1">Coleta Real (Apify)</h4>
        <p className="text-xs text-slate-500 mb-4">Informe um perfil para coletar dados reais via Apify</p>

        <div className="flex gap-2 mb-4">
          <div className="flex-1">
            <input
              type="text"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              placeholder="@perfil (ex: @g4educacao)"
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30"
            />
          </div>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-200 rounded-lg"
          >
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
          </select>
          <button
            onClick={handleCollect}
            disabled={!profile || collecting}
            className="px-4 py-2 bg-[#E8734A] text-white text-sm rounded-lg hover:bg-[#d4653f] transition-colors disabled:opacity-50"
          >
            {collecting ? "Coletando..." : "Coletar dados"}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-xs p-3 rounded-lg mb-4">{error}</div>
        )}

        {collectedData && (
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-medium text-emerald-700">Dados coletados com sucesso</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <MiniStat label="Posts" value={String(collectedData.total_posts)} />
              <MiniStat label="Eng. médio" value={`${collectedData.avg_engagement}%`} />
              <MiniStat label="Tendência" value={String(collectedData.trend)} />
              <MiniStat label="Plataforma" value={String(collectedData.platform)} />
            </div>
            {collectedData.top_post ? (
              <div className="text-xs text-slate-600">
                <p><span className="font-medium text-emerald-700">Top post:</span> {String((collectedData.top_post as Record<string, unknown>).description)} ({String((collectedData.top_post as Record<string, unknown>).engagement)}% eng)</p>
                <p><span className="font-medium text-red-600">Pior post:</span> {String((collectedData.worst_post as Record<string, unknown>).description)} ({String((collectedData.worst_post as Record<string, unknown>).engagement)}% eng)</p>
              </div>
            ) : null}
            <p className="text-[10px] text-amber-600 mt-3 italic">{String(collectedData.note)}</p>
          </div>
        )}
      </div>

      {/* Arquitetura do Sistema */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h4 className="text-sm font-semibold text-[#0F1B2D] mb-3">Arquitetura do Sistema</h4>
        <div className="bg-slate-50 rounded-xl p-4 font-mono text-[11px] text-slate-600 leading-relaxed whitespace-pre">{`
MÓDULO 1: DATA ENGINE
├── Apify (coleta periódica)
├── Normalização de dados
├── Testes estatísticos (scipy)
└── JSONs com metadados temporais

MÓDULO 2: INTELLIGENCE LAYER
├── OpenRouter (Gemini Flash / Claude / GPT-4o)
├── Pipeline: Draft → Critique → Output
├── Geração de mensagens (influenciadores)
└── Detecção de tendências

MÓDULO 3: DASHBOARD
├── 9 tabs com dados interativos
├── Badges de significância estatística
├── Gerador de conteúdo IA (3-step)
└── Ranking de influenciadores

MÓDULO 4: COMUNICAÇÃO
├── ZAPI (WhatsApp Business)
├── Mensagens personalizadas por IA
└── Score de parceria (0-100)
        `.trim()}</div>
      </div>
    </div>
  );
}

function ComparisonRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex gap-2">
      <span className="text-[10px] text-slate-400 w-24 shrink-0 uppercase tracking-wider pt-0.5">{label}</span>
      <span className={`text-xs leading-relaxed whitespace-pre-wrap ${highlight ? "text-[#0F1B2D] font-medium" : "text-slate-600"}`}>
        {value}
      </span>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-[#0F1B2D]">{value}</p>
    </div>
  );
}
