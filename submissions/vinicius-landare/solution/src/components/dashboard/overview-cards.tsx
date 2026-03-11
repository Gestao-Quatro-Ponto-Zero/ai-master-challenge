"use client";

import { IconChart, IconUsers, IconHeart, IconDollar } from "@/components/icons";

interface Props {
  summary: {
    total_posts: number;
    total_creators: number;
    avg_engagement_rate: number;
    sponsored_pct: number;
  };
}

export function OverviewCards({ summary }: Props) {
  const data = [
    { label: "Publicações Analisadas", value: summary.total_posts.toLocaleString("pt-BR"), sub: "posts de 5 plataformas", icon: IconChart, color: "bg-[#0F1B2D]" },
    { label: "Criadores de Conteúdo", value: summary.total_creators.toLocaleString("pt-BR"), sub: "influenciadores ativos", icon: IconUsers, color: "bg-[#1A2D47]" },
    { label: "Taxa de Interação Média", value: `${summary.avg_engagement_rate.toFixed(2)}%`, sub: "curtidas + compartilhamentos + comentários / visualizações", icon: IconHeart, color: "bg-[#E8734A]" },
    { label: "Publicações Pagas", value: `${summary.sponsored_pct}%`, sub: "do total são patrocinadas", icon: IconDollar, color: "bg-[#F4A261]" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {data.map((d) => {
        const Icon = d.icon;
        return (
          <div key={d.label} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-xl ${d.color} flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{d.label}</span>
            </div>
            <div className="text-2xl font-bold text-[#0F1B2D]">{d.value}</div>
            <p className="text-[11px] text-slate-400 mt-1">{d.sub}</p>
          </div>
        );
      })}
    </div>
  );
}
