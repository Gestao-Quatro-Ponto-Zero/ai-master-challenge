"use client";

import { IconCheck, IconBan } from "@/components/icons";

interface Persona {
  age_group: string;
  total_posts: number;
  pct_dataset: number;
  avg_engagement_rate: number;
  recommendations: {
    best_platform: string;
    best_content_type: string;
    best_category: string;
    best_creator_tier: string;
    best_post_hour: number;
    best_post_day: string;
    top_locations: string[];
  };
  engagement_organic_vs_sponsored: { organic: number; sponsored: number };
  top_combination: {
    platform: string;
    content_type: string;
    category: string;
    engagement_rate: number;
  };
}

interface Props {
  personas: Record<string, unknown>[];
}

const personaNames: Record<string, string> = {
  "13-18": "Gen Z Jovem",
  "19-25": "Gen Z",
  "26-35": "Millennial",
  "36-50": "Gen X",
  "50+": "Boomers",
};

const personaGradient: Record<string, string> = {
  "13-18": "from-[#E8734A] to-[#d4613b]",
  "19-25": "from-[#0F1B2D] to-[#1A2D47]",
  "26-35": "from-[#1A2D47] to-[#2D4A6F]",
  "36-50": "from-[#F4A261] to-[#E8734A]",
  "50+": "from-[#2D4A6F] to-[#0F1B2D]",
};

const typeLabel: Record<string, string> = { video: "Vídeo", image: "Imagem", mixed: "Carrossel", text: "Texto" };
const catLabel: Record<string, string> = { beauty: "Beleza", lifestyle: "Estilo de vida", tech: "Tecnologia" };
const dayLabel: Record<string, string> = {
  Monday: "Segunda", Tuesday: "Terça", Wednesday: "Quarta",
  Thursday: "Quinta", Friday: "Sexta", Saturday: "Sábado", Sunday: "Domingo",
};
const tierLabel: Record<string, string> = {
  "Nano (< 10K)": "Nano (até 10mil)",
  "Micro (10K-50K)": "Micro (10-50mil)",
  "Mid (50K-100K)": "Médio (50-100mil)",
  "Macro (100K-500K)": "Grande (100-500mil)",
  "Mega (500K+)": "Mega (500mil+)",
};

export function PersonaCards({ personas }: Props) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] rounded-2xl p-6 text-white">
        <h3 className="text-base font-semibold mb-2">Perfis de Público-Alvo</h3>
        <p className="text-sm text-white/70 leading-relaxed">
          Cada cartão representa uma <strong className="text-white">faixa etária da audiência</strong> com as melhores
          estratégias para alcançá-la. Use esses perfis para direcionar campanhas e conteúdo.
        </p>
      </div>

      {/* Cards grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {(personas as unknown as Persona[]).map((persona) => {
          const orgRate = persona.engagement_organic_vs_sponsored.organic;
          const sponRate = persona.engagement_organic_vs_sponsored.sponsored;
          const sponsorWins = sponRate > orgRate;
          const diffPp = Math.abs(sponRate - orgRate).toFixed(3);

          return (
            <div key={persona.age_group} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
              {/* Card header with gradient */}
              <div className={`bg-gradient-to-r ${personaGradient[persona.age_group] || "from-[#0F1B2D] to-[#1A2D47]"} p-4 text-white`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-base">{personaNames[persona.age_group] || persona.age_group}</h4>
                    <span className="text-white/70 text-xs">{persona.age_group} anos</span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{persona.avg_engagement_rate.toFixed(2)}%</div>
                    <div className="text-white/60 text-[10px]">taxa de interação</div>
                  </div>
                </div>
                <div className="mt-2 text-xs text-white/60">
                  {persona.total_posts.toLocaleString("pt-BR")} publicações ({persona.pct_dataset}% do total)
                </div>
              </div>

              {/* Card body */}
              <div className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <InfoItem label="Melhor Plataforma" value={persona.recommendations.best_platform} />
                  <InfoItem label="Melhor Formato" value={typeLabel[persona.recommendations.best_content_type] || persona.recommendations.best_content_type} />
                  <InfoItem label="Melhor Categoria" value={catLabel[persona.recommendations.best_category] || persona.recommendations.best_category} />
                  <InfoItem label="Tamanho do Influenciador" value={tierLabel[persona.recommendations.best_creator_tier] || persona.recommendations.best_creator_tier} />
                  <InfoItem label="Melhor Horário" value={`${persona.recommendations.best_post_hour}h`} />
                  <InfoItem label="Melhor Dia" value={dayLabel[persona.recommendations.best_post_day] || persona.recommendations.best_post_day} />
                </div>

                {/* Melhor combinação */}
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wide">Melhor Combinação</span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[11px] font-medium text-slate-700">{persona.top_combination.platform}</span>
                    <span className="text-slate-300 text-[10px] self-center">+</span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[11px] text-slate-600">{typeLabel[persona.top_combination.content_type] || persona.top_combination.content_type}</span>
                    <span className="text-slate-300 text-[10px] self-center">+</span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[11px] text-slate-600">{catLabel[persona.top_combination.category] || persona.top_combination.category}</span>
                    <span className="text-[#E8734A] font-mono text-xs font-semibold self-center ml-1">({persona.top_combination.engagement_rate}%)</span>
                  </div>
                </div>

                {/* Mercados */}
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wide">Principais Mercados</span>
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    {persona.recommendations.top_locations.map(loc => (
                      <span key={loc} className="px-2 py-0.5 bg-slate-50 border border-slate-200 rounded-full text-[10px] text-slate-600">{loc}</span>
                    ))}
                  </div>
                </div>

                {/* Patrocínio — com dados e contexto */}
                <div className="pt-2 border-t border-slate-100">
                  <div className={`p-2.5 rounded-lg ${sponsorWins ? "bg-emerald-50 border border-emerald-100" : "bg-red-50 border border-red-100"}`}>
                    <div className="flex items-center gap-2 mb-1">
                      {sponsorWins
                        ? <IconCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                        : <IconBan className="w-4 h-4 text-red-500 shrink-0" />
                      }
                      <span className={`text-xs font-semibold ${sponsorWins ? "text-emerald-700" : "text-red-700"}`}>
                        {sponsorWins ? "Patrocínio vale a pena" : "Orgânico funciona melhor"}
                      </span>
                    </div>
                    <p className={`text-[10px] leading-relaxed ${sponsorWins ? "text-emerald-600" : "text-red-600"}`}>
                      Orgânico: {orgRate.toFixed(3)}% vs Patrocinado: {sponRate.toFixed(3)}%
                      {sponsorWins
                        ? ` — patrocínio supera o orgânico em ${diffPp}pp nesta faixa etária`
                        : ` — orgânico supera o patrocinado em ${diffPp}pp, investir em conteúdo próprio`
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[10px] text-slate-400 uppercase tracking-wide">{label}</span>
      <div className="text-sm font-medium text-[#0F1B2D] mt-0.5">{value}</div>
    </div>
  );
}
