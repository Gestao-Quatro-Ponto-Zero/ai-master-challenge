"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { DiagnosticPanel } from "./diagnostic-panel";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis,
  ReferenceLine,
  ReferenceArea,
  Label,
} from "recharts";

interface GroupStats {
  name: string;
  totalTickets: number;
  closedTickets: number;
  avgResolutionHours: number;
  medianResolutionHours: number;
  avgCsat: number;
  medianCsat: number;
  satisfied: number;
  neutral: number;
  unsatisfied: number;
  dissatisfactionRate: number;
  avgPriorityWeight: number;
  riscoOperacional: number;
  riscoPrioridade: number;
}

interface Stats {
  totals: {
    tickets: number;
    closed: number;
    open: number;
    pending: number;
    avgResolutionHours: number;
    medianResolutionHours: number;
    avgCsat: number;
    satisfied: number;
    neutral: number;
    unsatisfied: number;
  };
  byChannel: GroupStats[];
  bySubject: GroupStats[];
  byPriority: GroupStats[];
  byType: GroupStats[];
  byChannelSubject: GroupStats[];
  byChannelPriority: GroupStats[];
  byPrioritySubject: GroupStats[];
  correlationBySubject: {
    subject: string;
    totalTickets: number;
    closedWithCsat: number;
    avgCsat: number | null;
    avgDuration: number | null;
    correlation: number | null;
    impact: number;
  }[];
  correlationDurationCsat: {
    channels: string[];
    subjects: string[];
    matrix: Record<string, Record<string, number | null>>;
  };
  durationVsCsat: {
    buckets: string[];
    csatValues: number[];
    matrix: Record<string, Record<number, number>>;
  };
  filterOptions: {
    channels: string[];
    priorities: string[];
    types: string[];
    subjects: string[];
    statuses: string[];
    csatSegments: string[];
    dates: string[];
  };
}

const COLORS = [
  "#2563eb", "#dc2626", "#f59e0b", "#16a34a", "#8b5cf6",
  "#ec4899", "#06b6d4", "#f97316", "#6366f1", "#84cc16",
  "#14b8a6", "#e11d48", "#a855f7", "#eab308", "#3b82f6", "#ef4444",
];

const CSAT_COLORS = {
  satisfied: "#16a34a",
  neutral: "#f59e0b",
  unsatisfied: "#dc2626",
};

function KPICard({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

function FilterBar({
  options,
  filters,
  onFilterChange,
}: {
  options: Stats["filterOptions"];
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}) {
  const filterConfig = [
    { key: "channel", label: "Canal", options: options.channels },
    { key: "priority", label: "Prioridade", options: options.priorities },
    { key: "type", label: "Tipo", options: options.types },
    { key: "subject", label: "Assunto", options: options.subjects },
    { key: "status", label: "Status", options: options.statuses },
    { key: "csatSegment", label: "CSAT", options: options.csatSegments },
  ];

  const hasActiveFilters = Object.values(filters).some((v) => v && v !== "all" && v !== "");

  return (
    <div className="flex flex-wrap gap-3 items-end">
      {filterConfig.map(({ key, label, options: opts }) => (
        <div key={key} className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
          <Select
            value={filters[key] || "all"}
            onValueChange={(v) => v && onFilterChange(key, v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={label} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {opts.map((opt) => (
                <SelectItem key={opt} value={opt}>
                  {opt}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ))}

      {/* Date range filters */}
      {options.dates.length > 0 && (
        <>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Data início</span>
            <input
              type="date"
              value={filters.dateFrom || ""}
              min={options.dates[0]}
              max={filters.dateTo || options.dates[options.dates.length - 1]}
              onChange={(e) => onFilterChange("dateFrom", e.target.value || "")}
              className="h-9 w-[160px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Data fim</span>
            <input
              type="date"
              value={filters.dateTo || ""}
              min={filters.dateFrom || options.dates[0]}
              max={options.dates[options.dates.length - 1]}
              onChange={(e) => onFilterChange("dateTo", e.target.value || "")}
              className="h-9 w-[160px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
        </>
      )}

      {hasActiveFilters && (
        <button
          onClick={() => {
            Object.keys(filters).forEach((k) => onFilterChange(k, k === "dateFrom" || k === "dateTo" ? "" : "all"));
          }}
          className="text-sm text-muted-foreground hover:text-foreground underline"
        >
          Limpar filtros
        </button>
      )}
    </div>
  );
}

interface ScatterPoint {
  name: string;
  dim1: string;
  dim2: string;
  avgDuration: number;
  avgCsat: number;
  riscoOperacional: number;
  totalTickets: number;
  dissatisfactionRate: number;
}

interface ScatterData {
  worst25pct: ScatterPoint[];
  rest: ScatterPoint[];
  regression: {
    slope: number;
    intercept: number;
    r2: number;
    lineStart: { x: number; y: number };
    lineEnd: { x: number; y: number };
  };
  goal: { maxDuration: number; minCsat: number };
  overall: { avgDuration: number; avgCsat: number };
}

function BubbleDot(color: string, strokeColor: string) {
  return function Dot(props: { cx?: number; cy?: number; payload?: ScatterPoint }) {
    const { cx, cy, payload } = props;
    if (!cx || !cy || !payload) return null;
    const r = Math.max(5, Math.min(22, Math.sqrt(payload.totalTickets) * 1.8));
    return (
      <circle cx={cx} cy={cy} r={r} fill={color} fillOpacity={0.6} stroke={strokeColor} strokeWidth={1.5} />
    );
  };
}

function RegressionChart({ scatterData, title, subtitle }: { scatterData: ScatterData; title: string; subtitle: string }) {
  const { worst25pct, rest, regression, goal, overall } = scatterData;

  // Build regression line points
  const allX = [...worst25pct, ...rest].map((p) => p.avgDuration);
  const minX = 0;
  const maxX = Math.max(...allX) * 1.1;
  const regLineData = [
    { x: minX, y: regression.slope * minX + regression.intercept },
    { x: maxX, y: regression.slope * maxX + regression.intercept },
  ];

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: ScatterPoint }> }) => {
    if (!active || !payload?.[0]) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-popover border rounded-md p-2 text-xs shadow-md">
        <p className="font-semibold">{d.dim1} × {d.dim2}</p>
        <p>Duração média: {d.avgDuration.toFixed(1)}h</p>
        <p>CSAT médio: {d.avgCsat.toFixed(2)}</p>
        <p>Risco Op.: {d.riscoOperacional.toFixed(0)}</p>
        <p>% Insatisf.: {d.dissatisfactionRate.toFixed(1)}%</p>
        <p>Tickets: {d.totalTickets}</p>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">
          {subtitle} Regressão sobre todos os pontos (R² = {regression.r2.toFixed(3)}). Zona verde = meta.
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="avgDuration"
              name="Duração Média"
              unit="h"
              domain={[0, maxX]}
            >
              <Label value="Duração Média (horas)" position="bottom" offset={0} />
            </XAxis>
            <YAxis
              type="number"
              dataKey="avgCsat"
              name="CSAT Médio"
              domain={[1, 5]}
            >
              <Label value="CSAT Médio" angle={-90} position="insideLeft" offset={10} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />

            {/* Goal zone: low duration, high CSAT */}
            <ReferenceArea
              x1={0}
              x2={goal.maxDuration}
              y1={goal.minCsat}
              y2={5}
              fill="#16a34a"
              fillOpacity={0.08}
              stroke="#16a34a"
              strokeDasharray="4 4"
              strokeOpacity={0.4}
            >
              <Label value="META" position="insideTopLeft" fill="#16a34a" fontSize={11} fontWeight="bold" />
            </ReferenceArea>

            {/* Danger zone: high duration, low CSAT */}
            <ReferenceArea
              x1={overall.avgDuration}
              x2={maxX}
              y1={1}
              y2={2.5}
              fill="#dc2626"
              fillOpacity={0.06}
              stroke="#dc2626"
              strokeDasharray="4 4"
              strokeOpacity={0.3}
            >
              <Label value="CRÍTICO" position="insideBottomRight" fill="#dc2626" fontSize={11} fontWeight="bold" />
            </ReferenceArea>

            {/* Average reference lines */}
            <ReferenceLine
              x={overall.avgDuration}
              stroke="#6b7280"
              strokeDasharray="6 3"
              label={{ value: `Média: ${overall.avgDuration.toFixed(1)}h`, position: "top", fill: "#6b7280", fontSize: 10 }}
            />
            <ReferenceLine
              y={overall.avgCsat}
              stroke="#6b7280"
              strokeDasharray="6 3"
              label={{ value: `CSAT médio: ${overall.avgCsat.toFixed(1)}`, position: "right", fill: "#6b7280", fontSize: 10 }}
            />

            {/* Regression line */}
            <Scatter
              name="Regressão"
              data={regLineData}
              fill="none"
              line={{ stroke: "#ef4444", strokeWidth: 2, strokeDasharray: "8 4" }}
              shape={() => <></>}
              legendType="line"
            />

            {/* Rest 75% points */}
            <Scatter
              name="Demais 75%"
              data={rest}
              shape={BubbleDot("#94a3b8", "#64748b")}
            />

            {/* Worst 25% points */}
            <Scatter
              name="Piores 25% (Risco Op.)"
              data={worst25pct}
              shape={BubbleDot("#dc2626", "#991b1b")}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function riskColor(value: number, max: number): string {
  if (max === 0) return "bg-gray-50 dark:bg-gray-900";
  const ratio = Math.min(value / max, 1);
  if (ratio < 0.15) return "bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-100";
  if (ratio < 0.3) return "bg-green-100 text-green-900 dark:bg-green-900 dark:text-green-100";
  if (ratio < 0.45) return "bg-yellow-100 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100";
  if (ratio < 0.6) return "bg-orange-100 text-orange-900 dark:bg-orange-900 dark:text-orange-100";
  if (ratio < 0.75) return "bg-orange-200 text-orange-900 dark:bg-orange-800 dark:text-orange-100";
  if (ratio < 0.9) return "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100";
  return "bg-red-300 text-red-900 font-semibold dark:bg-red-700 dark:text-red-100";
}

function correlationColor(r: number | null): string {
  if (r === null) return "bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500";
  const abs = Math.abs(r);
  if (abs < 0.1) return "bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300";
  if (r < -0.3) return "bg-red-200 text-red-900 font-semibold dark:bg-red-800 dark:text-red-100";
  if (r < -0.1) return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
  if (r > 0.3) return "bg-green-200 text-green-900 font-semibold dark:bg-green-800 dark:text-green-100";
  if (r > 0.1) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  return "bg-gray-50 text-gray-700 dark:bg-gray-900 dark:text-gray-300";
}

function CorrelationHeatmap({
  data,
}: {
  data: Stats["correlationDurationCsat"];
}) {
  const { channels, subjects, matrix } = data;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Correlação Duração × CSAT por Canal × Assunto (Pearson r)
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Coeficiente de Pearson entre duração de resolução e CSAT para cada par Canal × Assunto.
          Vermelho = correlação negativa (mais tempo → menor CSAT). Verde = positiva. Cinza = sem correlação significativa (|r| &lt; 0.1).
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left font-medium text-muted-foreground border-b">
                  Canal ↓ / Assunto →
                </th>
                {subjects.map((s) => (
                  <th
                    key={s}
                    className="p-2 text-center font-medium text-xs border-b min-w-[70px]"
                    style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
                  >
                    {s}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channels.map((ch) => (
                <tr key={ch}>
                  <td className="p-2 font-medium border-r whitespace-nowrap">{ch}</td>
                  {subjects.map((sub) => {
                    const val = matrix[ch]?.[sub];
                    return (
                      <td
                        key={sub}
                        className={`p-2 text-center text-xs border ${correlationColor(val)}`}
                        title={`${ch} × ${sub}: r = ${val !== null ? val.toFixed(3) : "n/a"}`}
                      >
                        {val !== null ? val.toFixed(2) : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function impactColor(value: number, minVal: number, maxVal: number): string {
  if (value === 0) return "bg-gray-50 dark:bg-gray-900 text-gray-400";
  const range = Math.max(Math.abs(minVal), Math.abs(maxVal));
  if (range === 0) return "bg-gray-50 dark:bg-gray-900 text-gray-400";
  if (value < 0) {
    const ratio = Math.min(Math.abs(value) / range, 1);
    if (ratio < 0.15) return "bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-200";
    if (ratio < 0.3) return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
    if (ratio < 0.5) return "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100";
    if (ratio < 0.7) return "bg-red-300 text-red-900 font-semibold dark:bg-red-700 dark:text-red-100";
    return "bg-red-400 text-red-950 font-semibold dark:bg-red-600 dark:text-red-50";
  }
  const ratio = Math.min(value / range, 1);
  if (ratio < 0.15) return "bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-200";
  if (ratio < 0.3) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  if (ratio < 0.5) return "bg-green-200 text-green-900 dark:bg-green-800 dark:text-green-100";
  return "bg-green-300 text-green-900 font-semibold dark:bg-green-700 dark:text-green-100";
}

function buildVolumeAndImpact(
  correlationData: Stats["correlationDurationCsat"],
  channelSubjectStats: GroupStats[],
) {
  const { channels, subjects, matrix: corrMatrix } = correlationData;

  const volumeMatrix: Record<string, Record<string, number>> = {};
  let maxVolume = 0;
  channelSubjectStats.forEach((d) => {
    const [ch, sub] = d.name.split(" | ");
    if (!volumeMatrix[ch]) volumeMatrix[ch] = {};
    volumeMatrix[ch][sub] = d.totalTickets;
    if (d.totalTickets > maxVolume) maxVolume = d.totalTickets;
  });

  const impactMatrix: Record<string, Record<string, number>> = {};
  let minImpact = 0;
  let maxImpact = 0;
  channels.forEach((ch) => {
    impactMatrix[ch] = {};
    subjects.forEach((sub) => {
      const r = corrMatrix[ch]?.[sub];
      const vol = volumeMatrix[ch]?.[sub] || 0;
      const impact = r !== null ? Math.round(r * vol * 10) / 10 : 0;
      impactMatrix[ch][sub] = impact;
      if (impact < minImpact) minImpact = impact;
      if (impact > maxImpact) maxImpact = impact;
    });
  });

  return { volumeMatrix, maxVolume, impactMatrix, minImpact, maxImpact, corrMatrix };
}

function VolumeHeatmap({
  correlationData,
  channelSubjectStats,
}: {
  correlationData: Stats["correlationDurationCsat"];
  channelSubjectStats: GroupStats[];
}) {
  const { channels, subjects } = correlationData;
  const { volumeMatrix, maxVolume } = buildVolumeAndImpact(correlationData, channelSubjectStats);

  const headerStyle = subjects.length > 6
    ? { writingMode: "vertical-rl" as const, textOrientation: "mixed" as const }
    : undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Volume de Tickets: Canal × Assunto</CardTitle>
        <p className="text-xs text-muted-foreground">
          Quantidade de tickets por par. Cor: verde (baixo) → vermelho (alto volume).
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left font-medium text-muted-foreground border-b">
                  Canal ↓ / Assunto →
                </th>
                {subjects.map((s) => (
                  <th key={s} className="p-2 text-center font-medium text-xs border-b min-w-[55px]" style={headerStyle}>
                    {s}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channels.map((ch) => (
                <tr key={ch}>
                  <td className="p-2 font-medium border-r whitespace-nowrap">{ch}</td>
                  {subjects.map((sub) => {
                    const val = volumeMatrix[ch]?.[sub] || 0;
                    return (
                      <td key={sub} className={`p-2 text-center text-xs border ${riskColor(val, maxVolume)}`}
                          title={`${ch} × ${sub}: ${val} tickets`}>
                        {val || "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function ImpactHeatmap({
  correlationData,
  channelSubjectStats,
}: {
  correlationData: Stats["correlationDurationCsat"];
  channelSubjectStats: GroupStats[];
}) {
  const { channels, subjects } = correlationData;
  const { impactMatrix, minImpact, maxImpact, corrMatrix, volumeMatrix } = buildVolumeAndImpact(correlationData, channelSubjectStats);

  const headerStyle = subjects.length > 6
    ? { writingMode: "vertical-rl" as const, textOrientation: "mixed" as const }
    : undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Score de Impacto: Correlação × Volume</CardTitle>
        <p className="text-xs text-muted-foreground">
          Score = r × tickets. Vermelho = onde atacar primeiro (correlação negativa × alto volume = mais tempo → menos CSAT em escala). Verde = pares saudáveis.
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left font-medium text-muted-foreground border-b">
                  Canal ↓ / Assunto →
                </th>
                {subjects.map((s) => (
                  <th key={s} className="p-2 text-center font-medium text-xs border-b min-w-[55px]" style={headerStyle}>
                    {s}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channels.map((ch) => (
                <tr key={ch}>
                  <td className="p-2 font-medium border-r whitespace-nowrap">{ch}</td>
                  {subjects.map((sub) => {
                    const val = impactMatrix[ch]?.[sub] || 0;
                    return (
                      <td key={sub} className={`p-2 text-center text-xs border ${impactColor(val, minImpact, maxImpact)}`}
                          title={`${ch} × ${sub}: impacto ${val.toFixed(1)} (r=${corrMatrix[ch]?.[sub]?.toFixed(2) ?? "n/a"} × ${volumeMatrix[ch]?.[sub] || 0} tickets)`}>
                        {val !== 0 ? val.toFixed(0) : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function HeatmapCard({
  data,
  title,
  dim1Label,
  dim2Label,
}: {
  data: GroupStats[];
  title: string;
  dim1Label: string;
  dim2Label: string;
}) {
  // Build matrix from "Dim1 | Dim2" data
  const dim1Values = [...new Set(data.map((d) => d.name.split(" | ")[0]))].sort();
  const dim2Values = [...new Set(data.map((d) => d.name.split(" | ")[1]))].sort();

  const matrix: Record<string, Record<string, number>> = {};
  let maxVal = 0;
  data.forEach((d) => {
    const [d1, d2] = d.name.split(" | ");
    if (!matrix[d1]) matrix[d1] = {};
    matrix[d1][d2] = d.riscoOperacional;
    if (d.riscoOperacional > maxVal) maxVal = d.riscoOperacional;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">
          Score = Volume × Taxa Insatisfação × Duração Média | Cor: verde (baixo risco) → vermelho (alto risco)
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left font-medium text-muted-foreground border-b">
                  {dim1Label} ↓ / {dim2Label} →
                </th>
                {dim2Values.map((d2) => (
                  <th
                    key={d2}
                    className="p-2 text-center font-medium text-xs border-b min-w-[80px]"
                    style={{ writingMode: dim2Values.length > 6 ? "vertical-rl" : undefined, textOrientation: "mixed" }}
                  >
                    {d2}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dim1Values.map((d1) => (
                <tr key={d1}>
                  <td className="p-2 font-medium border-r whitespace-nowrap">{d1}</td>
                  {dim2Values.map((d2) => {
                    const val = matrix[d1]?.[d2] ?? 0;
                    return (
                      <td
                        key={d2}
                        className={`p-2 text-center text-xs border ${riskColor(val, maxVal)}`}
                        title={`${d1} × ${d2}: Risco Op. ${val.toFixed(0)}`}
                      >
                        {val > 0 ? val.toFixed(0) : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

type SortKey = keyof GroupStats;
type SortDir = "asc" | "desc";

function SortableHeader({
  label,
  sortKey,
  currentSort,
  currentDir,
  onSort,
  align = "right",
}: {
  label: string;
  sortKey: SortKey;
  currentSort: SortKey;
  currentDir: SortDir;
  onSort: (key: SortKey) => void;
  align?: "left" | "right";
}) {
  const isActive = currentSort === sortKey;
  return (
    <th
      className={`pb-2 pr-4 font-medium cursor-pointer select-none hover:text-foreground transition-colors ${align === "right" ? "text-right" : "text-left"}`}
      onClick={() => onSort(sortKey)}
    >
      {label}
      {isActive && (
        <span className="ml-1 text-xs">{currentDir === "desc" ? "▼" : "▲"}</span>
      )}
    </th>
  );
}

function BottleneckTable({ data, title }: { data: GroupStats[]; title: string }) {
  const [sortKey, setSortKey] = useState<SortKey>("riscoOperacional");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filterDim1, setFilterDim1] = useState("all");
  const [filterDim2, setFilterDim2] = useState("all");

  // Extract dimensions from "Dim1 | Dim2" names
  const isCrossTab = data.length > 0 && data[0].name.includes(" | ");
  const dim1Values = isCrossTab
    ? [...new Set(data.map((d) => d.name.split(" | ")[0]))].sort()
    : [];
  const dim2Values = isCrossTab
    ? [...new Set(data.map((d) => d.name.split(" | ")[1]))].sort()
    : [];

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  // Filter cross-tab data by selected dimensions
  const filtered = isCrossTab
    ? data.filter((d) => {
        const [d1, d2] = d.name.split(" | ");
        if (filterDim1 !== "all" && d1 !== filterDim1) return false;
        if (filterDim2 !== "all" && d2 !== filterDim2) return false;
        return true;
      })
    : data;

  const sorted = [...filtered].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortDir === "desc" ? bVal - aVal : aVal - bVal;
    }
    return sortDir === "desc"
      ? String(bVal).localeCompare(String(aVal))
      : String(aVal).localeCompare(String(bVal));
  });

  const columns: { label: string; key: SortKey; align?: "left" | "right" }[] = [
    { label: "Nome", key: "name", align: "left" },
    { label: "Tickets", key: "totalTickets" },
    { label: "Resolvidos", key: "closedTickets" },
    { label: "Duração Média (h)", key: "avgResolutionHours" },
    { label: "% Insatisf.", key: "dissatisfactionRate" },
    { label: "CSAT Médio", key: "avgCsat" },
    { label: "CSAT Mediana", key: "medianCsat" },
    { label: "Risco Op.", key: "riscoOperacional" },
    { label: "Risco Prio.", key: "riscoPrioridade" },
  ];

  // Extract dimension labels from title (e.g. "Canal × Assunto" → ["Canal", "Assunto"])
  const dimLabels = title.match(/— (.+?) × (.+?)(?:\s|$)/);
  const dim1Label = dimLabels?.[1] || "Dim 1";
  const dim2Label = dimLabels?.[2] || "Dim 2";

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3">
          <CardTitle className="text-base">{title}</CardTitle>
          {isCrossTab && (
            <div className="flex gap-3 items-end">
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground">{dim1Label}</span>
                <Select value={filterDim1} onValueChange={(v) => v && setFilterDim1(v)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    {dim1Values.map((v) => (
                      <SelectItem key={v} value={v}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground">{dim2Label}</span>
                <Select value={filterDim2} onValueChange={(v) => v && setFilterDim2(v)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    {dim2Values.map((v) => (
                      <SelectItem key={v} value={v}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {(filterDim1 !== "all" || filterDim2 !== "all") && (
                <button
                  onClick={() => { setFilterDim1("all"); setFilterDim2("all"); }}
                  className="text-sm text-muted-foreground hover:text-foreground underline pb-1"
                >
                  Limpar
                </button>
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-2 pr-4 font-medium">#</th>
                {columns.map((col) => (
                  <SortableHeader
                    key={col.key}
                    label={col.label}
                    sortKey={col.key}
                    currentSort={sortKey}
                    currentDir={sortDir}
                    onSort={handleSort}
                    align={col.align || "right"}
                  />
                ))}
                <th className="pb-2 font-medium">Satisfação</th>
              </tr>
            </thead>
            <tbody>
              {sorted.slice(0, 30).map((row, i) => (
                <tr key={row.name} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="py-2 pr-4 text-muted-foreground">{i + 1}</td>
                  <td className="py-2 pr-4 font-medium">{row.name}</td>
                  <td className="py-2 pr-4 text-right">{row.totalTickets.toLocaleString()}</td>
                  <td className="py-2 pr-4 text-right">{row.closedTickets}</td>
                  <td className="py-2 pr-4 text-right">{row.avgResolutionHours.toFixed(1)}</td>
                  <td className="py-2 pr-4 text-right">
                    <span className={row.dissatisfactionRate > 50 ? "text-red-600 font-semibold" : row.dissatisfactionRate < 25 ? "text-green-600" : ""}>
                      {row.dissatisfactionRate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right">
                    <span className={row.avgCsat < 2.5 ? "text-red-600 font-semibold" : row.avgCsat >= 4 ? "text-green-600 font-semibold" : ""}>
                      {row.avgCsat.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right">
                    <span className={row.medianCsat <= 2 ? "text-red-600 font-semibold" : row.medianCsat >= 4 ? "text-green-600 font-semibold" : ""}>
                      {row.medianCsat.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right">
                    <Badge variant={row.riscoOperacional > 500 ? "destructive" : "secondary"}>
                      {row.riscoOperacional.toFixed(0)}
                    </Badge>
                  </td>
                  <td className="py-2 pr-4 text-right">
                    <Badge variant={row.riscoPrioridade > 1000 ? "destructive" : "secondary"}>
                      {row.riscoPrioridade.toFixed(0)}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <div className="flex gap-1 items-center">
                      {row.satisfied > 0 && (
                        <span className="text-xs text-green-600">{row.satisfied}</span>
                      )}
                      {row.neutral > 0 && (
                        <span className="text-xs text-yellow-600">{row.neutral}</span>
                      )}
                      {row.unsatisfied > 0 && (
                        <span className="text-xs text-red-600">{row.unsatisfied}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export function OverviewDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [scatterData, setScatterData] = useState<ScatterData | null>(null);
  const [scatterDataCP, setScatterDataCP] = useState<ScatterData | null>(null);
  const [scatterDataPS, setScatterDataPS] = useState<ScatterData | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v && v !== "all" && v !== "") params.set(k, v);
    });
    const [statsRes, scatterRes, scatterCPRes, scatterPSRes] = await Promise.all([
      fetch(`/api/tickets/stats?${params}`),
      fetch("/api/tickets/scatter?groupBy=channelSubject"),
      fetch("/api/tickets/scatter?groupBy=channelPriority"),
      fetch("/api/tickets/scatter?groupBy=prioritySubject"),
    ]);
    const [statsData, scatterJson, scatterCPJson, scatterPSJson] = await Promise.all([
      statsRes.json(),
      scatterRes.json(),
      scatterCPRes.json(),
      scatterPSRes.json(),
    ]);
    setStats(statsData);
    setScatterData(scatterJson);
    setScatterDataCP(scatterCPJson);
    setScatterDataPS(scatterPSJson);
    setLoading(false);
  }, [filters]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  if (loading || !stats) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Carregando dados...</p>
      </div>
    );
  }

  const { totals } = stats;

  const DurationCsatHeatmap = ({ title, subtitle }: { title: string; subtitle: string }) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-3 text-left font-medium text-muted-foreground border-b">
                  Duração ↓ / CSAT →
                </th>
                {stats.durationVsCsat.csatValues.map((c) => (
                  <th key={c} className="p-3 text-center font-medium border-b min-w-[70px]">
                    {c} {c <= 2 ? "😞" : c === 3 ? "😐" : "😊"}
                  </th>
                ))}
                <th className="p-3 text-center font-medium border-b border-l min-w-[70px]">Total</th>
              </tr>
            </thead>
            <tbody>
              {stats.durationVsCsat.buckets.map((bucket) => {
                const row = stats.durationVsCsat.matrix[bucket];
                const rowTotal = stats.durationVsCsat.csatValues.reduce((s, c) => s + (row[c] || 0), 0);
                const allValues = stats.durationVsCsat.buckets.flatMap((b) =>
                  stats.durationVsCsat.csatValues.map((c) => stats.durationVsCsat.matrix[b]?.[c] || 0)
                );
                const maxVal = Math.max(...allValues);
                return (
                  <tr key={bucket}>
                    <td className="p-3 font-medium border-r whitespace-nowrap">{bucket}</td>
                    {stats.durationVsCsat.csatValues.map((c) => {
                      const val = row[c] || 0;
                      return (
                        <td key={c} className={`p-3 text-center text-sm border ${riskColor(val, maxVal)}`}>
                          {val > 0 ? val : "—"}
                        </td>
                      );
                    })}
                    <td className="p-3 text-center font-semibold border-l">{rowTotal}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-10">
      {/* Filters */}
      <FilterBar
        options={stats.filterOptions}
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* ============================================================ */}
      {/* SECTION 1: Visão Geral */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">1. Visão Geral</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Panorama geral da operação de suporte. Duração e satisfação por canal e prioridade — as duas dimensões que a operação controla diretamente.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <KPICard title="Total Tickets" value={totals.tickets.toLocaleString()} />
          <KPICard
            title="Resolvidos"
            value={totals.closed.toLocaleString()}
            subtitle={`${((totals.closed / totals.tickets) * 100).toFixed(0)}% do total`}
          />
          <KPICard
            title="Duração Média"
            value={`${totals.avgResolutionHours.toFixed(1)}h`}
            subtitle={`Mediana: ${totals.medianResolutionHours.toFixed(1)}h`}
          />
          <KPICard title="CSAT Médio" value={totals.avgCsat.toFixed(1)} subtitle="de 5.0" />
          <KPICard
            title="Satisfeitos"
            value={totals.satisfied.toLocaleString()}
            subtitle={`${((totals.satisfied / (totals.satisfied + totals.neutral + totals.unsatisfied || 1)) * 100).toFixed(0)}%`}
          />
          <KPICard
            title="Insatisfeitos"
            value={totals.unsatisfied.toLocaleString()}
            subtitle={`${((totals.unsatisfied / (totals.satisfied + totals.neutral + totals.unsatisfied || 1)) * 100).toFixed(0)}%`}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Duração Média por Canal</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.byChannel} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit="h" />
                  <YAxis type="category" dataKey="name" width={100} />
                  <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}h`, "Duração média"]} />
                  <Bar dataKey="avgResolutionHours" fill="#2563eb" radius={[0, 4, 4, 0]}>
                    {stats.byChannel.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Duração Média por Prioridade</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.byPriority} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit="h" />
                  <YAxis type="category" dataKey="name" width={80} />
                  <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}h`, "Duração média"]} />
                  <Bar dataKey="avgResolutionHours" fill="#dc2626" radius={[0, 4, 4, 0]}>
                    {stats.byPriority.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Satisfação por Canal</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.byChannel}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="satisfied" name="Satisfeito (≥4)" stackId="csat" fill={CSAT_COLORS.satisfied} />
                  <Bar dataKey="neutral" name="Neutro (3)" stackId="csat" fill={CSAT_COLORS.neutral} />
                  <Bar dataKey="unsatisfied" name="Insatisfeito (≤2)" stackId="csat" fill={CSAT_COLORS.unsatisfied} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Satisfação por Prioridade</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.byPriority}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="satisfied" name="Satisfeito (≥4)" stackId="csat" fill={CSAT_COLORS.satisfied} />
                  <Bar dataKey="neutral" name="Neutro (3)" stackId="csat" fill={CSAT_COLORS.neutral} />
                  <Bar dataKey="unsatisfied" name="Insatisfeito (≤2)" stackId="csat" fill={CSAT_COLORS.unsatisfied} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 2: Drill-down Assunto × Satisfação */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">2. Drill-down: Assunto × Satisfação</h2>
          <p className="text-sm text-muted-foreground mt-2">
            O assunto do ticket não é algo que a operação controla — o cliente chega com o problema que tem.
            Mas precisamos entender quais assuntos têm relação entre tempo de resolução e satisfação.
            Isso revela onde resolver mais rápido realmente impacta o CSAT.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Duração Média por Assunto (16 categorias)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={450}>
              <BarChart data={stats.bySubject} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" unit="h" />
                <YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}h`, "Duração média"]} />
                <Bar dataKey="avgResolutionHours" fill="#8b5cf6" radius={[0, 4, 4, 0]}>
                  {stats.bySubject.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Correlação Duração × CSAT por Assunto</CardTitle>
            <p className="text-xs text-muted-foreground">
              Pearson r entre duração de resolução e CSAT para cada assunto (todos os canais agregados).
              Negativo = resolver mais rápido melhora satisfação. Positivo = tempo não prejudica (ou até ajuda — ex: resolução mais cuidadosa).
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 pr-4 font-medium">Assunto</th>
                    <th className="pb-2 pr-4 text-right font-medium">Tickets</th>
                    <th className="pb-2 pr-4 text-right font-medium">Com CSAT</th>
                    <th className="pb-2 pr-4 text-right font-medium">Duração Média</th>
                    <th className="pb-2 pr-4 text-right font-medium">CSAT Médio</th>
                    <th className="pb-2 pr-4 text-right font-medium">Correlação (r)</th>
                    <th className="pb-2 pr-4 text-right font-medium">Impacto (r × vol)</th>
                  </tr>
                </thead>
                <tbody>
                  {[...stats.correlationBySubject]
                    .sort((a, b) => a.impact - b.impact)
                    .map((row) => (
                    <tr key={row.subject} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-2 pr-4 font-medium">{row.subject}</td>
                      <td className="py-2 pr-4 text-right">{row.totalTickets}</td>
                      <td className="py-2 pr-4 text-right">{row.closedWithCsat}</td>
                      <td className="py-2 pr-4 text-right">{row.avgDuration !== null ? `${row.avgDuration.toFixed(1)}h` : "—"}</td>
                      <td className="py-2 pr-4 text-right">
                        <span className={row.avgCsat !== null && row.avgCsat < 2.5 ? "text-red-600 font-semibold" : row.avgCsat !== null && row.avgCsat >= 4 ? "text-green-600 font-semibold" : ""}>
                          {row.avgCsat !== null ? row.avgCsat.toFixed(2) : "—"}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-right">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          row.correlation === null ? "text-gray-400" :
                          row.correlation < -0.1 ? "bg-red-100 text-red-800 font-semibold" :
                          row.correlation > 0.1 ? "bg-green-100 text-green-800 font-semibold" :
                          "text-gray-500"
                        }`}>
                          {row.correlation !== null ? row.correlation.toFixed(3) : "n/a"}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-right">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          row.impact < -5 ? "bg-red-200 text-red-900 font-semibold" :
                          row.impact < 0 ? "bg-red-50 text-red-700" :
                          row.impact > 5 ? "bg-green-200 text-green-900 font-semibold" :
                          row.impact > 0 ? "bg-green-50 text-green-700" :
                          "text-gray-400"
                        }`}>
                          {row.impact !== 0 ? row.impact.toFixed(1) : "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ============================================================ */}
      {/* SECTION 3: Canal × Assunto */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">3. Análise: Canal × Assunto</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Canal é a dimensão acionável — podemos mudar como cada canal processa cada tipo de assunto.
            A análise cruza canal com assunto para encontrar os pares específicos onde a operação pode melhorar.
            A sequência é: risco operacional → correlação duração×CSAT → volume → score de impacto (onde atacar primeiro).
          </p>
        </div>

        <HeatmapCard
          data={stats.byChannelSubject}
          title="Mapa de Calor — Risco Operacional: Canal × Assunto"
          dim1Label="Canal"
          dim2Label="Assunto"
        />

        <DurationCsatHeatmap
          title="Duração vs CSAT — Todos os tickets (agregado)"
          subtitle="Quantidade de tickets por faixa de duração × rating CSAT. A distribuição uniforme confirma que no agregado não há correlação — precisamos descer ao nível do par."
        />

        <CorrelationHeatmap data={stats.correlationDurationCsat} />

        <VolumeHeatmap
          correlationData={stats.correlationDurationCsat}
          channelSubjectStats={stats.byChannelSubject}
        />

        <ImpactHeatmap
          correlationData={stats.correlationDurationCsat}
          channelSubjectStats={stats.byChannelSubject}
        />

        {scatterData && (
          <RegressionChart
            scatterData={scatterData}
            title="Regressão: Duração vs CSAT — Canal × Assunto"
            subtitle="Cada ponto = uma combinação Canal × Assunto. Vermelho = piores 25% por risco operacional. Cinza = restante."
          />
        )}

        <BottleneckTable
          data={stats.byChannelSubject}
          title="Ranking de Gargalos — Canal × Assunto"
        />
      </section>

      {/* ============================================================ */}
      {/* SECTIONS 5-6: Diagnóstico + Plano de Ação (componente separado) */}
      {/* ============================================================ */}
      <DiagnosticPanel />

      {/* ============================================================ */}
      {/* SECTION 7: Canal × Prioridade (referência) */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">7. Referência: Canal × Prioridade</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Cruzamento secundário: como cada canal performa por nível de prioridade.
            Útil para verificar se tickets críticos estão sendo tratados mais rápido independente do canal.
          </p>
        </div>

        <HeatmapCard
          data={stats.byChannelPriority}
          title="Mapa de Calor — Risco Operacional: Canal × Prioridade"
          dim1Label="Canal"
          dim2Label="Prioridade"
        />

        <DurationCsatHeatmap
          title="Duração vs CSAT — Canal × Prioridade (todos os tickets)"
          subtitle="Quantidade de tickets por faixa de duração × rating CSAT. Análise complementar para Canal × Prioridade."
        />

        {scatterDataCP && (
          <RegressionChart
            scatterData={scatterDataCP}
            title="Regressão: Duração vs CSAT — Canal × Prioridade"
            subtitle="Cada ponto = uma combinação Canal × Prioridade. Vermelho = piores 25% por risco operacional. Cinza = restante."
          />
        )}

        <BottleneckTable
          data={stats.byChannelPriority}
          title="Ranking de Gargalos — Canal × Prioridade"
        />
      </section>

      {/* ============================================================ */}
      {/* SECTION 8: Prioridade × Assunto (referência) */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">8. Referência: Prioridade × Assunto</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Cruzamento de referência: quais assuntos são classificados como críticos e se a prioridade impacta o tratamento.
            Nem prioridade nem assunto são diretamente acionáveis pela operação, mas revelam padrões de classificação.
          </p>
        </div>

        <HeatmapCard
          data={stats.byPrioritySubject}
          title="Mapa de Calor — Risco Operacional: Prioridade × Assunto"
          dim1Label="Prioridade"
          dim2Label="Assunto"
        />

        <DurationCsatHeatmap
          title="Duração vs CSAT — Prioridade × Assunto (todos os tickets)"
          subtitle="Quantidade de tickets por faixa de duração × rating CSAT. Análise complementar para Prioridade × Assunto."
        />

        {scatterDataPS && (
          <RegressionChart
            scatterData={scatterDataPS}
            title="Regressão: Duração vs CSAT — Prioridade × Assunto"
            subtitle="Cada ponto = uma combinação Prioridade × Assunto. Vermelho = piores 25% por risco operacional. Cinza = restante."
          />
        )}

        <BottleneckTable
          data={stats.byPrioritySubject}
          title="Ranking de Gargalos — Prioridade × Assunto"
        />
      </section>
    </div>
  );
}
