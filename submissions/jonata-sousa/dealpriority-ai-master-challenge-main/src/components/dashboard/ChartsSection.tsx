import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LabelList,
} from "recharts";
import type { Deal } from "@/types/deal";

interface Props {
  deals: Deal[];
}

const PRIORITY_COLORS: Record<string, string> = {
  "Foco Agora": "hsl(220, 72%, 50%)",
  "Nutrir": "hsl(35, 92%, 50%)",
  "Baixa Prioridade": "hsl(220, 10%, 55%)",
};

const STAGE_COLORS = [
  "hsl(220, 72%, 50%)",
  "hsl(220, 72%, 65%)",
  "hsl(35, 92%, 50%)",
  "hsl(152, 60%, 38%)",
  "hsl(220, 10%, 55%)",
];

const BAR_COLOR = "hsl(220, 72%, 50%)";

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-card rounded-xl border shadow-sm p-4 flex flex-col">
      <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest mb-3">
        {title}
      </h3>
      <div className="flex-1 min-h-[200px]">{children}</div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover border rounded-lg shadow-lg px-3 py-2 text-xs">
      <p className="font-semibold text-foreground mb-0.5">{label || payload[0]?.name}</p>
      <p className="text-muted-foreground">
        {payload[0].value} oportunidade{payload[0].value !== 1 ? "s" : ""}
      </p>
    </div>
  );
}

function PieTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="bg-popover border rounded-lg shadow-lg px-3 py-2 text-xs">
      <p className="font-semibold text-foreground mb-0.5">{d.name}</p>
      <p className="text-muted-foreground">
        {d.value} ({((d.value / (d.payload?.total || 1)) * 100).toFixed(0)}%)
      </p>
    </div>
  );
}

function truncate(str: string, max: number) {
  return str.length > max ? str.slice(0, max - 1) + "…" : str;
}

export function ChartsSection({ deals }: Props) {
  const priorityData = useMemo(() => {
    const total = deals.length;
    const counts: Record<string, number> = { "Foco Agora": 0, "Nutrir": 0, "Baixa Prioridade": 0 };
    deals.forEach((d) => {
      if (counts[d.priority_label] !== undefined) counts[d.priority_label]++;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value, total }));
  }, [deals]);

  const stageData = useMemo(() => {
    const counts: Record<string, number> = {};
    deals.forEach((d) => {
      if (d.deal_stage) counts[d.deal_stage] = (counts[d.deal_stage] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name: truncate(name, 16), value }));
  }, [deals]);

  const topSellers = useMemo(() => {
    const counts: Record<string, number> = {};
    deals.forEach((d) => {
      if (d.sales_agent) counts[d.sales_agent] = (counts[d.sales_agent] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name: truncate(name, 14), value }));
  }, [deals]);

  const topManagersFocus = useMemo(() => {
    const counts: Record<string, number> = {};
    deals
      .filter((d) => d.priority_label === "Foco Agora")
      .forEach((d) => {
        if (d.manager) counts[d.manager] = (counts[d.manager] || 0) + 1;
      });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name: truncate(name, 14), value }));
  }, [deals]);

  const renderLegend = (props: any) => {
    const { payload } = props;
    return (
      <div className="flex flex-wrap justify-center gap-3 mt-1">
        {payload?.map((entry: any, i: number) => (
          <div key={i} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
            {entry.value}
          </div>
        ))}
      </div>
    );
  };

  const yAxisProps = {
    type: "category" as const,
    dataKey: "name",
    width: 90,
    tick: { fontSize: 11, fill: "hsl(220,10%,50%)" },
    axisLine: false,
    tickLine: false,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {/* 1 — Priority distribution (donut) */}
      <ChartCard title="Distribuição por Prioridade">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 0, bottom: 0 }}>
            <Pie
              data={priorityData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="44%"
              innerRadius={40}
              outerRadius={68}
              paddingAngle={3}
              strokeWidth={0}
            >
              {priorityData.map((entry) => (
                <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] || "#888"} />
              ))}
            </Pie>
            <Tooltip content={<PieTooltip />} />
            <Legend content={renderLegend} />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* 2 — Deal stage (horizontal bar) */}
      <ChartCard title="Top 5 Estágios">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={stageData} layout="vertical" margin={{ left: 0, right: 32, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(220,14%,96%)" }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={14}>
              {stageData.map((_, i) => (
                <Cell key={i} fill={STAGE_COLORS[i % STAGE_COLORS.length]} />
              ))}
              <LabelList dataKey="value" position="right" style={{ fontSize: 11, fontWeight: 600, fill: "hsl(220,10%,50%)" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* 3 — Top sellers */}
      <ChartCard title="Top 5 Vendedores">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topSellers} layout="vertical" margin={{ left: 0, right: 32, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(220,14%,96%)" }} />
            <Bar dataKey="value" fill={BAR_COLOR} radius={[0, 4, 4, 0]} barSize={14}>
              <LabelList dataKey="value" position="right" style={{ fontSize: 11, fontWeight: 600, fill: "hsl(220,10%,50%)" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* 4 — Top managers Foco Agora */}
      <ChartCard title="Top 5 Gestores — Foco Agora">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topManagersFocus} layout="vertical" margin={{ left: 0, right: 32, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(220,14%,96%)" }} />
            <Bar dataKey="value" fill="hsl(152,60%,38%)" radius={[0, 4, 4, 0]} barSize={14}>
              <LabelList dataKey="value" position="right" style={{ fontSize: 11, fontWeight: 600, fill: "hsl(220,10%,50%)" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
