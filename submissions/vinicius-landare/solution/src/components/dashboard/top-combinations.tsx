"use client";

import { IconTrophy, IconWarning } from "@/components/icons";

interface Props {
  topData: Record<string, unknown>[];
  bottomData: Record<string, unknown>[];
}

const typeLabel: Record<string, string> = { video: "Vídeo", image: "Imagem", mixed: "Carrossel", text: "Texto" };
const catLabel: Record<string, string> = { beauty: "Beleza", lifestyle: "Estilo de vida", tech: "Tecnologia" };
const ageLabel: Record<string, string> = { "13-18": "13-18 anos", "19-25": "19-25 anos", "26-35": "26-35 anos", "36-50": "36-50 anos", "50+": "50+ anos" };

function Row({ row, variant }: { row: Record<string, unknown>; variant: "top" | "bottom" }) {
  const bg = variant === "top" ? "bg-emerald-50 border-emerald-100" : "bg-red-50 border-red-100";
  const textColor = variant === "top" ? "text-emerald-700" : "text-red-700";
  return (
    <div className={`flex items-center justify-between p-3 rounded-xl border ${bg}`}>
      <div className="flex flex-wrap gap-1.5 items-center">
        <span className="px-2 py-0.5 bg-white rounded-md text-[11px] font-medium text-slate-700 border">{row.platform as string}</span>
        <span className="text-slate-400 text-[10px]">+</span>
        <span className="px-2 py-0.5 bg-white rounded-md text-[11px] text-slate-600 border">{typeLabel[row.content_type as string] || row.content_type as string}</span>
        <span className="text-slate-400 text-[10px]">+</span>
        <span className="px-2 py-0.5 bg-white rounded-md text-[11px] text-slate-600 border">{catLabel[row.content_category as string] || row.content_category as string}</span>
        <span className="text-slate-400 text-[10px]">para</span>
        <span className="px-2 py-0.5 bg-white rounded-md text-[11px] text-slate-600 border">{ageLabel[row.audience_age_distribution as string] || row.audience_age_distribution as string}</span>
      </div>
      <span className={`font-mono text-xs font-semibold ${textColor} ml-2 whitespace-nowrap`}>
        {(row.avg_engagement_rate as number).toFixed(2)}%
      </span>
    </div>
  );
}

export function TopCombinations({ topData, bottomData }: Props) {
  const best = topData[0] ? (topData[0].avg_engagement_rate as number) : 0;
  const worst = bottomData.length ? (bottomData[bottomData.length - 1].avg_engagement_rate as number) : 0;
  const diff = Math.abs(best - worst);

  return (
    <div className="space-y-4">
      {/* Nota sobre dados simulados */}
      <div className="bg-[#0F1B2D]/[0.03] rounded-xl border border-slate-200 px-5 py-3 flex items-start gap-3">
        <svg className="w-4 h-4 text-[#E8734A] shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/></svg>
        <p className="text-xs text-slate-600 leading-relaxed">
          <strong className="text-[#0F1B2D]">Nota sobre os dados:</strong> Este dataset é simulado e possui distribuições muito uniformes.
          A diferença entre a melhor e a pior combinação é de apenas <strong className="text-[#E8734A]">{diff.toFixed(2)}pp</strong>.
          Em dados reais de redes sociais, essas variações costumam ser muito maiores (5-20pp).
          Ainda assim, os <strong>rankings relativos</strong> e as <strong>direções das tendências</strong> são válidos para tomada de decisão.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <IconTrophy className="w-5 h-5 text-[#E8734A]" />
              <h3 className="text-base font-semibold text-[#0F1B2D]">O que Funciona Melhor</h3>
            </div>
            <p className="text-xs text-slate-500">
              As 10 combinações de plataforma + formato + categoria + idade que geram mais interação
            </p>
          </div>
          <div className="space-y-2">
            {topData.slice(0, 10).map((row, i) => <Row key={i} row={row} variant="top" />)}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <IconWarning className="w-5 h-5 text-red-500" />
              <h3 className="text-base font-semibold text-[#0F1B2D]">Menor Performance Relativa</h3>
            </div>
            <p className="text-xs text-slate-500">
              As 10 combinacoes com menor engagement no dataset — monitorar antes de cortar (diferencas pequenas)
            </p>
          </div>
          <div className="space-y-2">
            {bottomData.slice(-10).reverse().map((row, i) => <Row key={i} row={row} variant="bottom" />)}
          </div>
        </div>
      </div>
    </div>
  );
}
