"use client";

import { PendingApproval } from "./pending-approval";

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  stats: any;
  topCombinations: any[];
  bottomCombinations: any[];
  sponsoredData: any;
  paidTrafficSummary: any;
  temporalDow: any[];
  temporalHour: any[];
}

export function ExecutiveSummary({ stats, topCombinations, bottomCombinations, sponsoredData, paidTrafficSummary, temporalDow, temporalHour }: Props) {
  const top3 = (topCombinations || []).slice(0, 3);
  const bottom3 = (bottomCombinations || []).slice(-3).reverse();
  const significance = stats?.significance_tests || {};
  const kpis = paidTrafficSummary?.kpis;

  // Melhores dias e horários do dataset
  const bestDays = [...(temporalDow || [])].sort((a, b) => (b.avg_engagement_rate || 0) - (a.avg_engagement_rate || 0)).slice(0, 3);
  const bestHours = [...(temporalHour || [])].sort((a, b) => (b.avg_engagement_rate || 0) - (a.avg_engagement_rate || 0)).slice(0, 4);

  const dayLabels: Record<string, string> = {
    Monday: "Segunda", Tuesday: "Terça", Wednesday: "Quarta",
    Thursday: "Quinta", Friday: "Sexta", Saturday: "Sábado", Sunday: "Domingo",
  };
  const typeLabels: Record<string, string> = { video: "Vídeo", image: "Imagem", mixed: "Carrossel", text: "Texto" };
  const catLabels: Record<string, string> = { beauty: "Beleza", lifestyle: "Estilo de vida", tech: "Tecnologia" };

  return (
    <div className="space-y-4">
      {/* 3 Respostas para o Gestor */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Card 1: O que gera engajamento */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-8 h-8 bg-[#E8734A]/10 rounded-lg flex items-center justify-center text-[#E8734A] font-bold text-sm">1</span>
            <h3 className="text-sm font-semibold text-[#0F1B2D]">O que gera engajamento?</h3>
          </div>

          {top3.length > 0 ? (
            <div className="space-y-2">
              {top3.map((combo: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                  <div className="text-xs">
                    <span className="font-medium text-[#0F1B2D]">{combo.platform}</span>
                    <span className="text-slate-400 mx-1">·</span>
                    <span className="text-slate-600">{combo.content_type}</span>
                    <span className="text-slate-400 mx-1">·</span>
                    <span className="text-slate-600">{combo.content_category}</span>
                  </div>
                  <span className="text-xs font-bold text-[#E8734A]">{combo.avg_engagement_rate?.toFixed(2)}%</span>
                </div>
              ))}
              <SignificanceBadge test={significance.h3_platforms} />
            </div>
          ) : (
            <p className="text-xs text-slate-400">Dados não carregados</p>
          )}
        </div>

        {/* Card 2: Vale patrocinar? */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-8 h-8 bg-[#E8734A]/10 rounded-lg flex items-center justify-center text-[#E8734A] font-bold text-sm">2</span>
            <h3 className="text-sm font-semibold text-[#0F1B2D]">Vale patrocinar?</h3>
          </div>

          <div className="space-y-2">
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-xs text-slate-600 leading-relaxed">
                {kpis ? (
                  <>
                    Lift geral do patrocinio:{" "}
                    <span className={`font-bold ${kpis.lift_geral_pp >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                      {kpis.lift_geral_pp >= 0 ? "+" : ""}{kpis.lift_geral_pp?.toFixed(2)}%
                    </span>
                  </>
                ) : (
                  <>
                    Organico: <span className="font-medium">{sponsoredData?.[0]?.avg_engagement_rate?.toFixed(2) || "—"}%</span>{" "}
                    vs Patrocinado: <span className="font-medium">{sponsoredData?.[1]?.avg_engagement_rate?.toFixed(2) || "—"}%</span>
                  </>
                )}
              </p>
            </div>

            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
              <p className="text-[10px] font-medium text-emerald-800">Tendência positiva:</p>
              <p className="text-xs text-emerald-700">Micro/Nano no Bilibili e YouTube mostram lift com patrocinio</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg border border-red-100">
              <p className="text-[10px] font-medium text-red-800">Tendência negativa:</p>
              <p className="text-xs text-red-700">Mega no TikTok e YouTube — organico tende a performar melhor</p>
            </div>

            <SignificanceBadge test={significance.h1_sponsored_vs_organic} />
            <p className="text-[9px] text-slate-400 mt-1">Diferenças pequenas no dataset (~0.1-0.2%). Validar com dados reais na aba Analise de Perfil.</p>
          </div>
        </div>

        {/* Card 3: Estratégia de conteúdo */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-8 h-8 bg-[#E8734A]/10 rounded-lg flex items-center justify-center text-[#E8734A] font-bold text-sm">3</span>
            <h3 className="text-sm font-semibold text-[#0F1B2D]">Estratégia de conteúdo</h3>
          </div>

          <div className="space-y-2 text-xs text-slate-600">
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="font-medium text-[#0F1B2D] mb-1">Tendências identificadas no dataset:</p>
              <ul className="space-y-1 text-slate-600">
                <li>• Carrossel/video para 19-25 anos (maior volume + engagement relativo)</li>
                <li>• Horários com mais interação: 7h, 11h, 18h, 21h</li>
                <li>• Posts com 2 hashtags mostram melhor performance relativa</li>
                <li>• Sextas e domingos tendem a ter mais interação</li>
              </ul>
            </div>
            <p className="text-[10px] text-slate-400">
              Baseado em tendencias do dataset. Conteúdos personalizados são gerados pela IA no Calendário.
            </p>
          </div>
        </div>
      </div>

      {/* Recomendações baseadas no dataset */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Recomendações baseadas nos dados</h3>
        <p className="text-xs text-slate-500 mb-4">Ações concretas derivadas da análise de 52.214 publicações</p>

        <div className="grid md:grid-cols-2 gap-4">
          {/* Onde investir */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Onde concentrar esforço</h4>
            {top3.map((combo: any, i: number) => (
              <div key={i} className="p-3 bg-emerald-50 border border-emerald-100 rounded-lg">
                <p className="text-xs font-medium text-emerald-900">
                  {combo.platform} + {typeLabels[combo.content_type] || combo.content_type} + {catLabels[combo.content_category] || combo.content_category}
                </p>
                <p className="text-[10px] text-emerald-700 mt-0.5">
                  Público {combo.audience_age_distribution} · Engagement: {combo.avg_engagement_rate?.toFixed(2)}%
                </p>
              </div>
            ))}
          </div>

          {/* O que evitar */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-red-800 uppercase tracking-wider">O que evitar</h4>
            {bottom3.map((combo: any, i: number) => (
              <div key={i} className="p-3 bg-red-50 border border-red-100 rounded-lg">
                <p className="text-xs font-medium text-red-900">
                  {combo.platform} + {typeLabels[combo.content_type] || combo.content_type} + {catLabels[combo.content_category] || combo.content_category}
                </p>
                <p className="text-[10px] text-red-700 mt-0.5">
                  Público {combo.audience_age_distribution} · Engagement: {combo.avg_engagement_rate?.toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Timing */}
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          <div className="p-3 bg-slate-50 rounded-lg">
            <h4 className="text-xs font-semibold text-[#0F1B2D] mb-2">Melhores dias para publicar</h4>
            <div className="flex gap-2">
              {bestDays.map((d: any, i: number) => (
                <span key={i} className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-xs text-[#0F1B2D] font-medium">
                  {dayLabels[d.day_of_week] || d.day_of_week}
                </span>
              ))}
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <h4 className="text-xs font-semibold text-[#0F1B2D] mb-2">Melhores horários</h4>
            <div className="flex gap-2">
              {bestHours.map((h: any, i: number) => (
                <span key={i} className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-xs text-[#0F1B2D] font-medium">
                  {h.hour}h
                </span>
              ))}
            </div>
          </div>
        </div>

        <p className="text-[9px] text-amber-600 mt-3">
          Tendências identificadas no dataset. Diferenças pequenas (~0.1-0.2%). Validar com dados reais na aba Análise de Perfil.
        </p>
      </div>

      {/* Aprovação Pendente */}
      <PendingApproval />
    </div>
  );
}

function SignificanceBadge({ test }: { test?: { is_significant?: boolean; p_value?: number } }) {
  if (!test) return null;
  return (
    <span className={`text-[9px] px-2 py-0.5 rounded-full font-medium ${
      test.is_significant
        ? "bg-emerald-100 text-emerald-700"
        : "bg-amber-100 text-amber-700"
    }`}>
      {test.is_significant ? "Estatisticamente significativo" : "Não significativo"} (p={test.p_value?.toFixed(3)})
    </span>
  );
}
