"use client";

import { IconCheck, IconBan, IconLightbulb } from "@/components/icons";

interface Props {
  generalData: Record<string, unknown>[];
  roiData: Record<string, unknown>[];
}

const tierLabel: Record<string, string> = {
  "Nano (< 10K)": "Nano (até 10mil seg.)",
  "Micro (10K-50K)": "Micro (10-50mil seg.)",
  "Mid (50K-100K)": "Médio (50-100mil seg.)",
  "Macro (100K-500K)": "Grande (100-500mil seg.)",
  "Mega (500K+)": "Mega (500mil+ seg.)",
};

export function SponsorshipAnalysis({ generalData, roiData }: Props) {
  const organic = generalData.find(d => d.is_sponsored === false);
  const sponsored = generalData.find(d => d.is_sponsored === true);
  const positiveRoi = roiData.filter(d => (d.diff as number) > 0).sort((a, b) => (b.diff as number) - (a.diff as number)).slice(0, 8);
  const negativeRoi = roiData.filter(d => (d.diff as number) < 0).sort((a, b) => (a.diff as number) - (b.diff as number)).slice(0, 8);

  const rows = [
    { label: "Taxa de Interação", org: (organic?.avg_engagement_rate as number)?.toFixed(4), spon: (sponsored?.avg_engagement_rate as number)?.toFixed(4), unit: "%" },
    { label: "Média de Curtidas", org: Math.round(organic?.avg_likes as number), spon: Math.round(sponsored?.avg_likes as number), unit: "" },
    { label: "Média de Compartilhamentos", org: Math.round(organic?.avg_shares as number), spon: Math.round(sponsored?.avg_shares as number), unit: "" },
    { label: "Média de Comentários", org: Math.round(organic?.avg_comments as number), spon: Math.round(sponsored?.avg_comments as number), unit: "" },
  ];

  return (
    <div className="space-y-4">
      {/* Resumo executivo */}
      <div className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] rounded-2xl p-6 text-white">
        <div className="flex items-center gap-2 mb-2">
          <IconLightbulb className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold">Resumo: Patrocinar funciona?</h3>
        </div>
        <p className="text-sm text-white/80 leading-relaxed">
          No geral, <strong className="text-white">a diferença entre publicações orgânicas e pagas é mínima</strong> (menos de 0,01%).
          Porém, o contexto muda tudo: patrocínio com <strong className="text-[#E8734A]">influenciadores menores (até 50mil seguidores)</strong> gera
          resultados melhores que orgânico. Já com <strong className="text-[#F4A261]">mega-influenciadores</strong>, o patrocínio não se justifica.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Comparação */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Orgânico vs Patrocinado</h3>
          <p className="text-xs text-slate-500 mb-4">Comparação geral de todas as publicações</p>
          <div className="space-y-3">
            {rows.map(row => (
              <div key={row.label} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                <span className="text-sm text-slate-600">{row.label}</span>
                <div className="flex gap-3 text-sm">
                  <span className="font-mono text-emerald-600 font-medium">{row.org}{row.unit}</span>
                  <span className="text-slate-300">vs</span>
                  <span className="font-mono text-[#E8734A] font-medium">{row.spon}{row.unit}</span>
                </div>
              </div>
            ))}
            <div className="flex gap-4 justify-end text-[10px] text-slate-400 pt-1">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Orgânico</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#E8734A]" /> Patrocinado</span>
            </div>
          </div>
        </div>

        {/* Onde vale */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-1">
            <IconCheck className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-semibold text-[#0F1B2D]">Onde Patrocinar VALE a Pena</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">Tamanho do influenciador + plataforma com retorno positivo</p>
          <div className="space-y-2">
            {positiveRoi.map((row, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-emerald-50 rounded-xl border border-emerald-100">
                <div className="text-xs">
                  <span className="font-medium text-slate-700">{tierLabel[row.creator_tier as string] || row.creator_tier as string}</span>
                  <span className="text-slate-400 mx-1.5">no</span>
                  <span className="font-medium text-slate-700">{row.platform as string}</span>
                </div>
                <span className="text-emerald-700 font-mono text-xs font-semibold">+{(row.diff as number).toFixed(3)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Onde NÃO vale */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-1">
          <IconBan className="w-5 h-5 text-red-500" />
          <h3 className="text-base font-semibold text-[#0F1B2D]">Onde NÃO Patrocinar</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">Nestas combinações, a publicação orgânica gera mais interação do que a patrocinada</p>
        <div className="grid gap-2 md:grid-cols-2">
          {negativeRoi.map((row, i) => (
            <div key={i} className="flex items-center justify-between p-2.5 bg-red-50 rounded-xl border border-red-100">
              <div className="text-xs">
                <span className="font-medium text-slate-700">{tierLabel[row.creator_tier as string] || row.creator_tier as string}</span>
                <span className="text-slate-400 mx-1.5">no</span>
                <span className="font-medium text-slate-700">{row.platform as string}</span>
              </div>
              <span className="text-red-600 font-mono text-xs font-semibold">{(row.diff as number).toFixed(3)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
