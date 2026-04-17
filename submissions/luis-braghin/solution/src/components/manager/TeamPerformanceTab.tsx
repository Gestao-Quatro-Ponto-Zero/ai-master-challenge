import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LeaderboardTable } from "@/components/dashboard/LeaderboardTable";
import { tooltipStyle } from "./types";
import type { Agent } from "@/types/deals";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface TeamPerformanceTabProps {
  agentChartData: Array<{ name: string; winRate: number; deals: number }>;
  filteredAgents: Agent[];
}

export function TeamPerformanceTab({ agentChartData, filteredAgents }: TeamPerformanceTabProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Win Rate por Vendedor (Top 15)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={agentChartData}>
              <defs>
                <linearGradient id="barGreen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0.4} />
                </linearGradient>
                <linearGradient id="barWarning" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--warning))" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="hsl(var(--warning))" stopOpacity={0.4} />
                </linearGradient>
                <linearGradient id="barPrimary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="name" className="text-xs" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="winRate" radius={[4, 4, 0, 0]} name="Win Rate %">
                {agentChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.winRate >= 70 ? "url(#barGreen)" : entry.winRate >= 66 ? "url(#barPrimary)" : "url(#barWarning)"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Ranking Completo</CardTitle>
        </CardHeader>
        <CardContent>
          <LeaderboardTable agents={filteredAgents} limit={35} />
        </CardContent>
      </Card>
    </div>
  );
}
