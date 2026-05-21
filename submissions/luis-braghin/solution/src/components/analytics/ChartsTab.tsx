import { useMemo } from "react";
import { useDeals, useAnalytics, useClosedDeals, useProducts } from "@/hooks/useG4Data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis,
} from "recharts";

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

const tooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "8px",
};

export default function ChartsTab() {
  const { data: deals = [] } = useDeals();
  const { data: closedDeals = [] } = useClosedDeals();
  const { data: products = [] } = useProducts();

  const productData = useMemo(() =>
    products.map(p => ({
      name: p.name,
      winRate: +(p.winRate * 100).toFixed(1),
      deals: p.totalDeals,
    })),
    [products]
  );

  const sectorData = useMemo(() => {
    const sectors: Record<string, { won: number; total: number }> = {};
    closedDeals.forEach(d => {
      if (!sectors[d.sector]) sectors[d.sector] = { won: 0, total: 0 };
      sectors[d.sector].total++;
      if (d.stage === "Won") sectors[d.sector].won++;
    });
    return Object.entries(sectors)
      .map(([sector, s]) => ({ sector, winRate: +((s.won / s.total) * 100).toFixed(1), deals: s.total }))
      .sort((a, b) => b.winRate - a.winRate);
  }, [closedDeals]);

  const regionData = useMemo(() => {
    const regions: Record<string, { won: number; total: number }> = {};
    closedDeals.forEach(d => {
      if (!regions[d.regionalOffice]) regions[d.regionalOffice] = { won: 0, total: 0 };
      regions[d.regionalOffice].total++;
      if (d.stage === "Won") regions[d.regionalOffice].won++;
    });
    return Object.entries(regions).map(([region, s]) => ({
      region, winRate: +((s.won / s.total) * 100).toFixed(1),
    }));
  }, [closedDeals]);

  const closeTimeData = useMemo(() => {
    const buckets: Record<string, number> = {
      "< 30d": 0, "30-60d": 0, "60-90d": 0, "90-120d": 0, "120d+": 0,
    };
    closedDeals.filter(d => d.stage === "Won").forEach(d => {
      if (d.daysToClose < 30) buckets["< 30d"]++;
      else if (d.daysToClose < 60) buckets["30-60d"]++;
      else if (d.daysToClose < 90) buckets["60-90d"]++;
      else if (d.daysToClose < 120) buckets["90-120d"]++;
      else buckets["120d+"]++;
    });
    return Object.entries(buckets).map(([range, count]) => ({ range, count }));
  }, [closedDeals]);

  const scatterData = useMemo(() =>
    deals.slice(0, 200).map(d => ({
      score: d.score,
      ev: d.expectedValue,
      account: d.account,
    })),
    [deals]
  );

  const funnelData = useMemo(() => {
    const prospecting = deals.filter(d => d.stage === "Prospecting").length;
    const engaging = deals.filter(d => d.stage === "Engaging").length;
    const wonCount = closedDeals.filter(d => d.stage === "Won").length;
    const lostCount = closedDeals.filter(d => d.stage === "Lost").length;
    return [
      { stage: "Prospecting", count: prospecting },
      { stage: "Engaging", count: engaging },
      { stage: "Won", count: wonCount },
      { stage: "Lost", count: lostCount },
    ];
  }, [deals, closedDeals]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Win Rate por Produto</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={productData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="winRate" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Win Rate por Setor</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sectorData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <YAxis dataKey="sector" type="category" width={100} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="winRate" fill="hsl(var(--chart-2))" radius={[0, 4, 4, 0]} name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Win Rate por Região</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={regionData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="winRate" nameKey="region" label={({ region, winRate }) => `${region}: ${winRate}%`}>
                {regionData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Tempo de Fechamento (Deals Won)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={closeTimeData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="range" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} name="Deals" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Score × Expected Value</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="score" name="Score" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <YAxis dataKey="ev" name="EV" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <ZAxis range={[30, 30]} />
              <Tooltip contentStyle={tooltipStyle} />
              <Scatter data={scatterData} fill="hsl(var(--chart-4))" />
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Funil de Conversão</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={funnelData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="stage" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Deals">
                {funnelData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
