"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { IconTarget } from "@/components/icons";

interface Props {
  locationData: Record<string, unknown>[];
  brazilPlatform: Record<string, unknown>[];
  brazilContentType: Record<string, unknown>[];
  brazilAge: Record<string, unknown>[];
}

const typeLabel: Record<string, string> = { video: "Vídeo", image: "Imagem", mixed: "Carrossel", text: "Texto" };
const ageLabel: Record<string, string> = { "13-18": "13-18", "19-25": "19-25", "26-35": "26-35", "36-50": "36-50", "50+": "50+" };

export function MarketAnalysis({ locationData, brazilPlatform, brazilContentType, brazilAge }: Props) {
  // Location chart data
  const locChart = locationData.map(d => ({
    location: d.audience_location as string,
    rate: Number((d.avg_engagement_rate as number).toFixed(3)),
    posts: d.posts as number,
  })).sort((a, b) => b.rate - a.rate);

  // Brazil data
  const brPlatform = brazilPlatform.map(d => ({
    name: d.platform as string,
    rate: Number((d.avg_engagement_rate as number).toFixed(3)),
  })).sort((a, b) => b.rate - a.rate);

  const brContent = brazilContentType.map(d => ({
    name: typeLabel[d.content_type as string] || d.content_type as string,
    rate: Number((d.avg_engagement_rate as number).toFixed(3)),
    posts: d.posts as number,
  })).sort((a, b) => b.rate - a.rate);

  const brAge = brazilAge.map(d => ({
    name: ageLabel[d.audience_age_distribution as string] || d.audience_age_distribution as string,
    rate: Number((d.avg_engagement_rate as number).toFixed(3)),
    posts: d.posts as number,
  })).sort((a, b) => b.rate - a.rate);

  // Brazil rank
  const brazilRank = locChart.findIndex(d => d.location === "Brazil") + 1;
  const brazilRate = locChart.find(d => d.location === "Brazil")?.rate || 0;
  const globalAvg = locChart.reduce((acc, d) => acc + d.rate, 0) / locChart.length;
  const brazilDiff = (brazilRate - globalAvg).toFixed(3);

  return (
    <div className="space-y-4">
      {/* ========= H4 — Brasil vs Mercados ========= */}
      <div className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] rounded-2xl p-6 text-white">
        <div className="flex items-center gap-2 mb-2">
          <IconTarget className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold">H4: A audiência brasileira se comporta diferente?</h3>
        </div>
        <p className="text-sm text-white/80 leading-relaxed">
          O Brasil ocupa a <strong className="text-[#E8734A]">{brazilRank}a posição</strong> entre 8 mercados com taxa de {brazilRate}%
          ({Number(brazilDiff) >= 0 ? "+" : ""}{brazilDiff}% vs media global).
          A diferenca entre mercados e <strong className="text-white">muito pequena</strong> neste dataset (dados simulados com distribuição uniforme).
          Os dados <strong className="text-[#F4A261]">não permitem concluir</strong> se o Brasil precisa de estratégia localizada —
          seria necessario validar com dados reais de cada mercado.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Engagement por mercado */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Interação por Mercado</h3>
          <p className="text-xs text-slate-500 mb-4">Taxa média de interação por localização da audiência</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={locChart} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" domain={[19.88, 19.92]} fontSize={10} tick={{ fill: "#64748b" }} tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="location" fontSize={11} tick={{ fill: "#64748b" }} width={60} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                formatter={(v: number) => [`${v}%`, "Taxa de Interação"]}
              />
              <Bar dataKey="rate" radius={[0, 6, 6, 0]}>
                {locChart.map((d, i) => (
                  <Cell key={i} fill={d.location === "Brazil" ? "#E8734A" : "#0F1B2D"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Brasil em detalhe */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Brasil em Detalhe</h3>
          <p className="text-xs text-slate-500 mb-4">Melhores estratégias para a audiência brasileira</p>

          <div className="space-y-4">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wide">Melhor plataforma no Brasil</span>
              <div className="mt-1.5 space-y-1.5">
                {brPlatform.map((d, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-slate-700">{d.name}</span>
                    <span className="font-mono text-xs text-[#0F1B2D] font-medium">{d.rate}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <span className="text-[10px] text-slate-400 uppercase tracking-wide">Melhor formato no Brasil</span>
              <div className="mt-1.5 space-y-1.5">
                {brContent.map((d, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-700">{d.name}</span>
                      <span className="text-[10px] text-slate-400">({d.posts} posts)</span>
                    </div>
                    <span className="font-mono text-xs text-[#0F1B2D] font-medium">{d.rate}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <span className="text-[10px] text-slate-400 uppercase tracking-wide">Faixa etária mais engajada no Brasil</span>
              <div className="mt-1.5 space-y-1.5">
                {brAge.map((d, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-700">{d.name} anos</span>
                      <span className="text-[10px] text-slate-400">({d.posts} posts)</span>
                    </div>
                    <span className="font-mono text-xs text-[#0F1B2D] font-medium">{d.rate}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
