"use client";

import { IconZap, IconDollar, IconStop, IconTarget, IconCheck, IconBan, IconLightbulb } from "@/components/icons";

interface Props {
  personas: Record<string, unknown>[];
}

interface Persona {
  age_group: string;
  pct_dataset: number;
  recommendations: {
    best_platform: string;
    best_content_type: string;
    best_category: string;
    best_creator_tier: string;
    best_post_hour: number;
    best_post_day: string;
    top_locations: string[];
  };
}

const dayLabel: Record<string, string> = {
  Monday: "Segunda", Tuesday: "Terça", Wednesday: "Quarta",
  Thursday: "Quinta", Friday: "Sexta", Saturday: "Sábado", Sunday: "Domingo",
};
const typeLabel: Record<string, string> = { video: "Vídeo", image: "Imagem", mixed: "Carrossel", text: "Texto" };
const catLabel: Record<string, string> = { beauty: "Beleza", lifestyle: "Estilo de vida", tech: "Tecnologia" };
const tierLabel: Record<string, string> = {
  "Nano (< 10K)": "Nano (até 10mil seg.)",
  "Micro (10K-50K)": "Micro (10-50mil seg.)",
  "Mid (50K-100K)": "Médio (50-100mil seg.)",
  "Macro (100K-500K)": "Grande (100-500mil seg.)",
  "Mega (500K+)": "Mega (500mil+ seg.)",
};

export function Recommendations({ personas }: Props) {
  return (
    <div className="space-y-4">
      {/* Ações Rápidas */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-1">
          <IconZap className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold text-[#0F1B2D]">Ações Rápidas — Implementar Esta Semana</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">Mudanças simples com impacto imediato nos resultados</p>
        <div className="grid gap-3 md:grid-cols-2">
          <ActionCard
            number={1}
            title="Priorizar carrossel e texto para jovens adultos (19-25)"
            description="Conteúdo misto (carrossel) tem a maior interação na faixa 19-25, que representa 35% do total. Criar 3-4 carrosseis por semana no RedNote e Bilibili."
          />
          <ActionCard
            number={2}
            title="Publicar nos horários de pico: 7h, 11h, 18h e 21h"
            description="Os dados mostram picos claros de interação nesses horários. Agendar as publicações mais importantes para esses slots."
          />
          <ActionCard
            number={3}
            title="Usar exatamente 2 hashtags por publicação"
            description="Publicações com 2 hashtags têm a melhor taxa de interação. Mais que 2 não agrega valor — menos é mais."
          />
          <ActionCard
            number={4}
            title="Concentrar conteúdo de valor nas sextas e domingos"
            description="Esses dois dias mostram as maiores taxas de interação da semana. Reserve o melhor conteúdo para eles."
          />
        </div>
      </div>

      {/* Política de Patrocínio */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-1">
          <IconDollar className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold text-[#0F1B2D]">Política de Patrocínio</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">Quando investir e quando economizar com base nos dados</p>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-4 bg-emerald-50 rounded-xl border border-emerald-100">
            <IconCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm text-emerald-800">PATROCINAR: Influenciadores pequenos (até 50mil seg.)</h4>
              <p className="text-xs text-emerald-700 mt-1 leading-relaxed">
                Nano (até 10mil) no Bilibili e YouTube mostram o maior retorno de patrocínio
                (+0,17pp e +0,11pp). Micro (10-50mil) no Instagram também tem retorno positivo (+0,08pp).
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl border border-red-100">
            <IconBan className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm text-red-800">NÃO PATROCINAR: Mega influenciadores no TikTok e YouTube</h4>
              <p className="text-xs text-red-700 mt-1 leading-relaxed">
                Influenciadores com mais de 500mil seguidores no TikTok e micro no TikTok mostram queda
                de interação quando patrocinados. Manter orgânico para esses perfis.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-[#0F1B2D]/5 rounded-xl border border-[#0F1B2D]/10">
            <IconLightbulb className="w-5 h-5 text-[#E8734A] shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm text-[#0F1B2D]">Transparência funciona melhor</h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Divulgação explícita de patrocínio tem interação levemente superior à implícita (19,909% vs 19,900%).
                Além de ser eticamente correto, ser transparente não penaliza — na verdade, melhora o resultado. Use hashtags para sinalizar.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* O que PARAR */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-1">
          <IconStop className="w-5 h-5 text-red-500" />
          <h3 className="text-base font-semibold text-[#0F1B2D]">Parar de Fazer</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">Investimentos com baixo retorno que devem ser cortados</p>
        <div className="grid gap-3 md:grid-cols-3">
          <StopCard
            title="Carrossel de estilo de vida para 36-50 no TikTok"
            detail="Pior combinação do dataset (19,74% de interação). Redirecionar orçamento."
          />
          <StopCard
            title="Moda no Instagram com mega-influenciadores"
            detail="Pior combinação de patrocínio x plataforma (19,86%). Trocar para beleza no Bilibili (19,95%)."
          />
          <StopCard
            title="Publicações às 15h-16h e 22h-23h"
            detail="Menores taxas de interação do dia. Evitar agendar conteúdo importante nesses horários."
          />
        </div>
      </div>

      {/* Plano por audiência */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-1">
          <IconTarget className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold text-[#0F1B2D]">Plano por Audiência — Próximo Trimestre</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">Estratégia personalizada para cada faixa etária</p>
        <div className="grid gap-3 md:grid-cols-2">
          {(personas as unknown as Persona[]).map((persona) => (
            <div key={persona.age_group} className="p-4 bg-[#0F1B2D]/[0.03] rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-[#0F1B2D]">
                  Audiência {persona.age_group} anos
                </h4>
                <span className="text-[10px] bg-[#E8734A]/10 text-[#E8734A] px-2 py-0.5 rounded-full font-medium">
                  {persona.pct_dataset}% do volume
                </span>
              </div>
              <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <PlanItem label="Plataforma" value={persona.recommendations.best_platform} />
                <PlanItem label="Formato" value={typeLabel[persona.recommendations.best_content_type] || persona.recommendations.best_content_type} />
                <PlanItem label="Categoria" value={catLabel[persona.recommendations.best_category] || persona.recommendations.best_category} />
                <PlanItem label="Influenciador" value={tierLabel[persona.recommendations.best_creator_tier] || persona.recommendations.best_creator_tier} />
                <PlanItem label="Horário" value={`${persona.recommendations.best_post_hour}h`} />
                <PlanItem label="Dia" value={dayLabel[persona.recommendations.best_post_day] || persona.recommendations.best_post_day} />
              </div>
              <div className="mt-2 pt-2 border-t border-slate-200">
                <span className="text-[10px] text-slate-400">Mercados: </span>
                <span className="text-[10px] text-[#0F1B2D] font-medium">{persona.recommendations.top_locations.join(", ")}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ActionCard({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="p-4 rounded-xl border border-[#E8734A]/20 bg-[#E8734A]/5">
      <div className="flex items-start gap-3">
        <span className="bg-[#E8734A] text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">{number}</span>
        <div>
          <h4 className="font-medium text-sm text-[#0F1B2D]">{title}</h4>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  );
}

function StopCard({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="p-3.5 bg-red-50 rounded-xl border border-red-100">
      <h4 className="font-medium text-sm text-red-800">{title}</h4>
      <p className="text-xs text-red-600 mt-1.5 leading-relaxed">{detail}</p>
    </div>
  );
}

function PlanItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-slate-400">{label}:</span>
      <span className="text-[#0F1B2D] font-medium ml-1">{value}</span>
    </div>
  );
}
