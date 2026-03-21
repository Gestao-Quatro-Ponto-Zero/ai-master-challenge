"use client";

import { useState, useEffect, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

/* eslint-disable @typescript-eslint/no-explicit-any */

interface DimensionResult {
  dimension: string;
  value: string;
  organic_engagement: number;
  sponsored_engagement: number;
  lift: number;
  organic_reach: number;
  sponsored_reach: number;
  organic_cpe: number;
  sponsored_cpe: number;
  organic_posts: number;
  sponsored_posts: number;
  organic_avg_likes: number;
  sponsored_avg_likes: number;
  organic_avg_shares: number;
  sponsored_avg_shares: number;
  organic_avg_comments: number;
  sponsored_avg_comments: number;
  organic_avg_views: number;
  sponsored_avg_views: number;
}

interface PairResult {
  dim1: string;
  val1: string;
  dim2: string;
  val2: string;
  organic_engagement: number;
  sponsored_engagement: number;
  lift: number;
  organic_reach: number;
  sponsored_reach: number;
  organic_cpe: number;
  sponsored_cpe: number;
  organic_posts: number;
  sponsored_posts: number;
}

interface ExplorerData {
  dimensions: Record<string, string[]>;
  by_dimension: DimensionResult[];
  by_pair: PairResult[];
  totals: {
    organic_engagement: number;
    sponsored_engagement: number;
    organic_reach: number;
    sponsored_reach: number;
    organic_cpe: number;
    sponsored_cpe: number;
    total_organic: number;
    total_sponsored: number;
  };
}

interface Props {
  generalData: any[];
  roiData: any[];
  paidTrafficSummary: any;
  campaignRoi: any;
  budgetAllocation: any;
}

const DIM_LABELS: Record<string, string> = {
  platform: "Plataforma",
  content_category: "Categoria",
  content_type: "Formato",
  creator_tier: "Tier do Creator",
  audience_age: "Faixa Etária",
  audience_location: "Mercado",
};

const TIER_SHORT: Record<string, string> = {
  "Nano (< 10K)": "Nano",
  "Micro (10K-50K)": "Micro",
  "Mid (50K-100K)": "Médio",
  "Macro (100K-500K)": "Grande",
  "Mega (500K+)": "Mega",
};

type MetricKey = "engagement" | "reach" | "cpe";

const METRIC_CONFIG: Record<MetricKey, { label: string; orgKey: string; sponKey: string; format: (v: number) => string; description: string }> = {
  engagement: {
    label: "Engagement Rate",
    orgKey: "organic_engagement",
    sponKey: "sponsored_engagement",
    format: (v) => `${v.toFixed(2)}%`,
    description: "Taxa de interação (likes + shares + comments / views)",
  },
  reach: {
    label: "Alcance Relativo",
    orgKey: "organic_reach",
    sponKey: "sponsored_reach",
    format: (v) => v.toFixed(3),
    description: "Views / seguidores (quanto do público o post alcança)",
  },
  cpe: {
    label: "Custo por Engajamento",
    orgKey: "organic_cpe",
    sponKey: "sponsored_cpe",
    format: (v) => v.toFixed(2),
    description: "Views necessárias para 1 interação (menor = mais eficiente)",
  },
};

export function SponsorshipVerdict({ generalData, roiData }: Props) {
  const [explorer, setExplorer] = useState<ExplorerData | null>(null);
  const [dim1, setDim1] = useState<string>("platform");
  const [dim2, setDim2] = useState<string>("none");
  const [val2, setVal2] = useState<string>("all");
  const [metric, setMetric] = useState<MetricKey>("engagement");

  useEffect(() => {
    fetch("/data/sponsorship_explorer.json")
      .then((r) => r.json())
      .then((d) => setExplorer(d))
      .catch(() => null);
  }, []);

  // Dados filtrados para o grafico
  const chartData = useMemo(() => {
    if (!explorer) return [];
    const cfg = METRIC_CONFIG[metric];

    if (dim2 === "none") {
      // Filtrar por dimensao unica
      return explorer.by_dimension
        .filter((d) => d.dimension === dim1)
        .map((d) => ({
          name: TIER_SHORT[d.value] || d.value,
          Organico: d[cfg.orgKey as keyof DimensionResult] as number,
          Patrocinado: d[cfg.sponKey as keyof DimensionResult] as number,
          lift: d.lift,
          organic_posts: d.organic_posts,
          sponsored_posts: d.sponsored_posts,
        }))
        .sort((a, b) => b.lift - a.lift);
    }

    // Cruzamento: dim1 fixo, filtrar por dim2
    let pairs = explorer.by_pair.filter((p) => p.dim1 === dim1 && p.dim2 === dim2);
    if (val2 !== "all") {
      pairs = pairs.filter((p) => p.val2 === val2);
    }

    // Agrupar por val1
    const grouped: Record<string, { org: number[]; spon: number[]; orgR: number[]; sponR: number[]; orgC: number[]; sponC: number[]; orgP: number; sponP: number }> = {};
    for (const p of pairs) {
      if (!grouped[p.val1]) grouped[p.val1] = { org: [], spon: [], orgR: [], sponR: [], orgC: [], sponC: [], orgP: 0, sponP: 0 };
      grouped[p.val1].org.push(p.organic_engagement);
      grouped[p.val1].spon.push(p.sponsored_engagement);
      grouped[p.val1].orgR.push(p.organic_reach);
      grouped[p.val1].sponR.push(p.sponsored_reach);
      grouped[p.val1].orgC.push(p.organic_cpe);
      grouped[p.val1].sponC.push(p.sponsored_cpe);
      grouped[p.val1].orgP += p.organic_posts;
      grouped[p.val1].sponP += p.sponsored_posts;
    }

    return Object.entries(grouped).map(([key, g]) => {
      const avgOrg = metric === "engagement" ? avg(g.org) : metric === "reach" ? avg(g.orgR) : avg(g.orgC);
      const avgSpon = metric === "engagement" ? avg(g.spon) : metric === "reach" ? avg(g.sponR) : avg(g.sponC);
      return {
        name: TIER_SHORT[key] || key,
        Organico: avgOrg,
        Patrocinado: avgSpon,
        lift: avgSpon - avgOrg,
        organic_posts: g.orgP,
        sponsored_posts: g.sponP,
      };
    }).sort((a, b) => b.lift - a.lift);
  }, [explorer, dim1, dim2, val2, metric]);

  const dim2Values = useMemo(() => {
    if (!explorer || dim2 === "none") return [];
    return explorer.dimensions[dim2 === "audience_age" ? "audience_age" : dim2] || [];
  }, [explorer, dim2]);

  if (!explorer) {
    return <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-xs text-slate-400">Carregando dados de patrocinio...</div>;
  }

  const cfg = METRIC_CONFIG[metric];
  const totals = explorer.totals;

  return (
    <div className="space-y-4">
      {/* KPIs totais */}
      <div className="grid grid-cols-3 gap-3">
        <TotalCard
          label="Engagement Rate"
          organic={`${totals.organic_engagement.toFixed(2)}%`}
          sponsored={`${totals.sponsored_engagement.toFixed(2)}%`}
          lift={totals.sponsored_engagement - totals.organic_engagement}
          active={metric === "engagement"}
          onClick={() => setMetric("engagement")}
        />
        <TotalCard
          label="Alcance Relativo"
          organic={totals.organic_reach.toFixed(3)}
          sponsored={totals.sponsored_reach.toFixed(3)}
          lift={totals.sponsored_reach - totals.organic_reach}
          active={metric === "reach"}
          onClick={() => setMetric("reach")}
        />
        <TotalCard
          label="Custo / Engajamento"
          organic={totals.organic_cpe.toFixed(2)}
          sponsored={totals.sponsored_cpe.toFixed(2)}
          lift={totals.organic_cpe - totals.sponsored_cpe}
          invertColor
          active={metric === "cpe"}
          onClick={() => setMetric("cpe")}
        />
      </div>

      {/* Filtros interativos */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Explorador de Patrocínio</h3>
        <p className="text-xs text-slate-500 mb-4">{cfg.description}. Selecione as dimensões para cruzar os dados.</p>

        <div className="flex flex-wrap gap-3 mb-4">
          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">Agrupar por</label>
            <select
              value={dim1}
              onChange={(e) => { setDim1(e.target.value); setVal2("all"); }}
              className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
            >
              {Object.entries(DIM_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">Cruzar com</label>
            <select
              value={dim2}
              onChange={(e) => { setDim2(e.target.value); setVal2("all"); }}
              className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
            >
              <option value="none">Sem cruzamento</option>
              {Object.entries(DIM_LABELS)
                .filter(([k]) => k !== dim1)
                .map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>

          {dim2 !== "none" && dim2Values.length > 0 && (
            <div>
              <label className="text-[10px] text-slate-400 uppercase block mb-1">Filtrar {DIM_LABELS[dim2]}</label>
              <select
                value={val2}
                onChange={(e) => setVal2(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
              >
                <option value="all">Todos</option>
                {dim2Values.map((v) => (
                  <option key={v} value={v}>{TIER_SHORT[v] || v}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="text-[10px] text-slate-400 uppercase block mb-1">Metrica</label>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value as MetricKey)}
              className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
            >
              <option value="engagement">Engagement Rate</option>
              <option value="reach">Alcance Relativo</option>
              <option value="cpe">Custo / Engajamento</option>
            </select>
          </div>
        </div>

        {/* Grafico comparativo */}
        {chartData.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ left: 10, right: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" fontSize={11} angle={-20} textAnchor="end" height={50} />
                <YAxis fontSize={11} tickFormatter={(v) => cfg.format(v)} />
                <Tooltip
                  formatter={(value: number, name: string) => [cfg.format(value), name]}
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                  labelStyle={{ fontWeight: "bold" }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="Organico" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Patrocinado" fill="#E8734A" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-40 flex items-center justify-center text-xs text-slate-400">
            Sem dados suficientes para esta combinação de filtros
          </div>
        )}

        {/* Tabela detalhada */}
        {chartData.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                  <th className="px-3 py-2 text-left">{DIM_LABELS[dim1]}</th>
                  <th className="px-3 py-2 text-center">Organico</th>
                  <th className="px-3 py-2 text-center">Patrocinado</th>
                  <th className="px-3 py-2 text-center">Lift</th>
                  <th className="px-3 py-2 text-center">Posts Org.</th>
                  <th className="px-3 py-2 text-center">Posts Pat.</th>
                  <th className="px-3 py-2 text-center">Veredicto</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((row, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-2 font-medium text-[#0F1B2D]">{row.name}</td>
                    <td className="px-3 py-2 text-center font-mono text-emerald-600">{cfg.format(row.Organico)}</td>
                    <td className="px-3 py-2 text-center font-mono text-[#E8734A]">{cfg.format(row.Patrocinado)}</td>
                    <td className={`px-3 py-2 text-center font-mono font-semibold ${
                      metric === "cpe"
                        ? (row.Organico - row.Patrocinado > 0 ? "text-emerald-600" : "text-red-600")
                        : (row.lift > 0 ? "text-emerald-600" : "text-red-600")
                    }`}>
                      {row.lift > 0 ? "+" : ""}{cfg.format(row.lift)}
                    </td>
                    <td className="px-3 py-2 text-center text-slate-400">{row.organic_posts}</td>
                    <td className="px-3 py-2 text-center text-slate-400">{row.sponsored_posts}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        Math.abs(row.lift) < 0.05
                          ? "bg-slate-100 text-slate-500"
                          : row.lift > 0
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-red-100 text-red-700"
                      }`}>
                        {Math.abs(row.lift) < 0.05 ? "Neutro" : row.lift > 0 ? "Patrocinar" : "Organico"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 rounded-xl border border-amber-100 p-4">
        <p className="text-xs text-amber-700">
          <strong>Contexto:</strong> As diferencas no dataset sao pequenas (~0.1-0.2%). Os veredictos indicam
          <strong> tendências</strong>, não certezas. Em produção com dados reais, os deltas seriam maiores.
          Use a aba &quot;Análise de Perfil&quot; para validar com dados reais via Apify antes de tomar decisoes de investimento.
        </p>
      </div>
    </div>
  );
}

function avg(arr: number[]): number {
  return arr.length === 0 ? 0 : arr.reduce((a, b) => a + b, 0) / arr.length;
}

function TotalCard({ label, organic, sponsored, lift, invertColor, active, onClick }: {
  label: string; organic: string; sponsored: string; lift: number; invertColor?: boolean; active: boolean; onClick: () => void;
}) {
  const isPositive = invertColor ? lift > 0 : lift > 0;
  return (
    <button
      onClick={onClick}
      className={`rounded-xl border p-4 text-left transition-all ${
        active ? "border-[#E8734A] ring-1 ring-[#E8734A]/30 bg-white" : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-xs text-emerald-600 font-mono">{organic}</span>
        <span className="text-[10px] text-slate-300">vs</span>
        <span className="text-xs text-[#E8734A] font-mono">{sponsored}</span>
      </div>
      <div className="flex items-center gap-1 mt-1">
        <span className="text-[10px] text-slate-400">Lift:</span>
        <span className={`text-xs font-semibold ${isPositive ? "text-emerald-600" : "text-red-500"}`}>
          {lift > 0 ? "+" : ""}{lift.toFixed(3)}
        </span>
      </div>
      <div className="flex gap-2 mt-1 text-[9px] text-slate-400">
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />Organico</span>
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#E8734A]" />Patrocinado</span>
      </div>
    </button>
  );
}
