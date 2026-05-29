"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useHydrated } from "@/lib/use-hydrated";

type Bottleneck = {
  segment: string;
  avg_resolution_hours: number;
};

type HeatmapChartProps = {
  data: Bottleneck[];
};

export function HeatmapChart({ data }: HeatmapChartProps) {
  const isHydrated = useHydrated();

  return (
    <div className="card p-4">
      <h3 className="text-base font-semibold">Onde o fluxo trava</h3>
      <p className="mt-1 text-xs text-slate-500">Canal x Tipo x Prioridade com maior tempo médio</p>

      <div className="mt-4 h-72 w-full">
        {isHydrated ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 10, right: 20, left: 60, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#64748b" />
              <YAxis dataKey="segment" type="category" stroke="#64748b" width={180} />
              <Tooltip
                contentStyle={{
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: 12,
                }}
              />
              <Bar dataKey="avg_resolution_hours" fill="#184962" radius={[6, 6, 6, 6]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full animate-pulse rounded-lg bg-slate-100" />
        )}
      </div>
    </div>
  );
}
