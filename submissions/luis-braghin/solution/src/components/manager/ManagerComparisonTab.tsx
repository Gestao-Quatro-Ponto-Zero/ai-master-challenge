import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { Crown } from "lucide-react";
import { formatUSD, formatCompact } from "@/lib/formatters";
import { ManagerComparisonTable } from "./ManagerComparisonTable";
import { tooltipStyle } from "./types";
import type { ManagerStats } from "./types";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from "recharts";

interface ManagerComparisonTabProps {
  managerStats: ManagerStats[];
  managerInsights: string[];
  categoryBarData: Array<Record<string, string | number>>;
}

export function ManagerComparisonTab({ managerStats, managerInsights, categoryBarData }: ManagerComparisonTabProps) {
  return (
    <div className="space-y-6">
      <InsightsPanel title="Comparativo entre Managers" insights={managerInsights.length > 0 ? managerInsights : ["Selecione 'Todos os Managers' para ver o comparativo."]} />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Crown className="h-4 w-4 text-primary" />
            Ranking de Managers
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ManagerComparisonTable stats={managerStats} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Win Rate Média por Manager</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={managerStats.map(m => ({ name: m.name.split(" ")[0], winRate: +(m.avgWinRate * 100).toFixed(1), ev: m.ev }))}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="winRate" radius={[4, 4, 0, 0]} name="Win Rate %">
                  {managerStats.map((m, i) => (
                    <Cell key={i} fill={m.avgWinRate >= 0.65 ? "hsl(var(--success))" : m.avgWinRate >= 0.58 ? "hsl(var(--primary))" : "hsl(var(--warning))"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Composição do Pipeline por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categoryBarData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend />
                <Bar dataKey="HOT" stackId="a" fill="hsl(var(--success))" name="HOT" />
                <Bar dataKey="WARM" stackId="a" fill="hsl(var(--chart-2))" name="WARM" />
                <Bar dataKey="COOL" stackId="a" fill="hsl(var(--chart-3))" name="COOL" />
                <Bar dataKey="COLD" stackId="a" fill="hsl(var(--warning))" name="COLD" />
                <Bar dataKey="DEAD" stackId="a" fill="hsl(var(--destructive))" name="DEAD" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Expected Value por Vendedor (Eficiência do Time)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={managerStats.map(m => ({ name: m.name.split(" ")[0], evPerAgent: m.evPerAgent, pipelinePerAgent: m.pipelinePerAgent }))}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => formatCompact(v)} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatUSD(v)} />
              <Legend />
              <Bar dataKey="evPerAgent" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} name="EV / Vendedor" />
              <Bar dataKey="pipelinePerAgent" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} name="Pipeline / Vendedor" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
