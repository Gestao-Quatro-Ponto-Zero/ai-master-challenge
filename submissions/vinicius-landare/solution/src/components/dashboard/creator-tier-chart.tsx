"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  data: Record<string, unknown>[];
}

const tierLabels: Record<string, string> = {
  "Nano (< 10K)": "Nano\n(até 10mil)",
  "Micro (10K-50K)": "Micro\n(10-50mil)",
  "Mid (50K-100K)": "Médio\n(50-100mil)",
  "Macro (100K-500K)": "Grande\n(100-500mil)",
  "Mega (500K+)": "Mega\n(500mil+)",
};

const COLORS = ["#E8734A", "#F4A261", "#0F1B2D", "#1A2D47", "#2D4A6F"];

export function CreatorTierChart({ data }: Props) {
  const chartData = data.map(d => ({
    tier: (d.creator_tier as string).replace(/\s*\(.*\)/, ""),
    fullLabel: tierLabels[d.creator_tier as string] || d.creator_tier,
    taxa: Number((d.avg_engagement_rate as number).toFixed(4)),
    posts: d.posts as number,
    creators: d.creators as number,
  }));

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-[#0F1B2D]">Interação por Tamanho do Influenciador</h3>
        <p className="text-xs text-slate-500 mt-1">
          Como o número de seguidores do criador impacta o resultado das publicações
        </p>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="tier" fontSize={11} tick={{ fill: "#64748b" }} />
          <YAxis domain={[19.85, 19.95]} fontSize={10} tick={{ fill: "#64748b" }} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
            formatter={(v: number) => [`${v}%`, "Taxa de Interação"]}
          />
          <Bar dataKey="taxa" name="Taxa de Interação" radius={[6,6,0,0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-5 gap-2 text-center">
        {chartData.map((d, i) => (
          <div key={i} className="text-[11px] text-slate-500">
            <div className="font-semibold text-[#0F1B2D]">{d.posts.toLocaleString("pt-BR")}</div>
            publicações
          </div>
        ))}
      </div>
    </div>
  );
}
