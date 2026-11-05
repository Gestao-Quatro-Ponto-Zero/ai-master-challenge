import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Deal } from "@/hooks/useDeals";
import { dealsPorFila, distScoreFoco, valorFocoPorManager, valorFocoPorRegiao } from "@/lib/homeStats";
import { formatUSDCompact } from "@/lib/format";

const tooltipStyle = {
  background: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 12,
};

export function FilasChart({ deals }: { deals: Deal[] }) {
  const dados = useMemo(() => dealsPorFila(deals), [deals]);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={dados} margin={{ top: 16, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" width={44} />
        <Tooltip formatter={(v) => [`${v} deals`, "Total"]} contentStyle={tooltipStyle} />
        <Bar dataKey="total" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {dados.map((d) => (
            <Cell key={d.fila} fill={d.fila === "requalificar" ? "var(--warning)" : "var(--primary)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function RegiaoChart({ deals }: { deals: Deal[] }) {
  const dados = useMemo(() => valorFocoPorRegiao(deals), [deals]);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={dados} layout="vertical" margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke="var(--border)" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)"
          tickFormatter={(v) => formatUSDCompact(Number(v))} />
        <YAxis type="category" dataKey="regiao" width={110} tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" />
        <Tooltip
          formatter={(v, _n, item) => [`${formatUSDCompact(Number(v))} em ${(item.payload as { deals: number }).deals} deals`, "Valor esperado"]}
          contentStyle={tooltipStyle}
        />
        <Bar dataKey="valor" fill="var(--primary)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ManagerChart({ deals }: { deals: Deal[] }) {
  const dados = useMemo(() => valorFocoPorManager(deals), [deals]);
  const altura = Math.max(200, dados.length * 34 + 40);
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={dados} layout="vertical" margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke="var(--border)" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)"
          tickFormatter={(v) => formatUSDCompact(Number(v))} />
        <YAxis type="category" dataKey="manager" width={140} tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" />
        <Tooltip
          formatter={(v, _n, item) => [`${formatUSDCompact(Number(v))} em ${(item.payload as { deals: number }).deals} deals`, "Valor esperado"]}
          contentStyle={tooltipStyle}
        />
        <Bar dataKey="valor" fill="var(--primary)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ScoreChart({ deals }: { deals: Deal[] }) {
  const dados = useMemo(() => distScoreFoco(deals), [deals]);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={dados} margin={{ top: 16, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="faixa" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" width={44} />
        <Tooltip formatter={(v) => [`${v} deals`, "Deals em foco"]} labelFormatter={(l) => `Score ${l}`} contentStyle={tooltipStyle} />
        <Bar dataKey="total" fill="var(--chart-2)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
