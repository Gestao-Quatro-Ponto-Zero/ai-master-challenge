"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface Props {
  data: Record<string, unknown>[];
}

const formatLabels: Record<string, string> = {
  video: "Vídeo",
  image: "Imagem",
  mixed: "Carrossel/Mix",
  text: "Texto",
};

const COLORS = { video: "#0F1B2D", image: "#1A2D47", mixed: "#E8734A", text: "#F4A261" };

export function PlatformChart({ data }: Props) {
  const platforms = [...new Set(data.map(d => d.platform as string))];
  const chartData = platforms.map(platform => {
    const rows = data.filter(d => d.platform === platform);
    const types: Record<string, number> = {};
    rows.forEach(r => {
      types[r.content_type as string] = Number((r.avg_engagement_rate as number).toFixed(2));
    });
    return { platform, ...types };
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-[#0F1B2D]">Interação por Plataforma e Formato</h3>
        <p className="text-xs text-slate-500 mt-1">
          Qual formato de conteúdo gera mais interação em cada rede social
        </p>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barGap={2}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="platform" fontSize={11} tick={{ fill: "#64748b" }} />
          <YAxis domain={[19.85, 19.95]} fontSize={10} tick={{ fill: "#64748b" }} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
            formatter={(value: number, name: string) => [`${value}%`, formatLabels[name] || name]}
          />
          <Legend formatter={(value) => formatLabels[value] || value} wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="video" fill={COLORS.video} radius={[4,4,0,0]} name="video" />
          <Bar dataKey="image" fill={COLORS.image} radius={[4,4,0,0]} name="image" />
          <Bar dataKey="mixed" fill={COLORS.mixed} radius={[4,4,0,0]} name="mixed" />
          <Bar dataKey="text" fill={COLORS.text} radius={[4,4,0,0]} name="text" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
