import { useQuery } from "@tanstack/react-query";
import { fetchKPIs } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const SEGMENT_COLORS = {
  A: "hsl(172, 66%, 50%)",
  B: "hsl(38, 92%, 50%)",
  C: "hsl(220, 9%, 46%)",
};

const Revenue = () => {
  const { data, isLoading } = useQuery({
    queryKey: ["kpis"],
    queryFn: fetchKPIs,
  });

  const abcData = data?.abc_curve ?? [
    { segment: "A", revenue_pct: 70, churn_pct: 3 },
    { segment: "B", revenue_pct: 20, churn_pct: 7 },
    { segment: "C", revenue_pct: 10, churn_pct: 15 },
  ];

  const mrrRanges = data?.mrr_ranges ?? [
    { range: "$95 – $500", accounts_pct: 45, revenue_pct: 12, churn_pct: 18 },
    { range: "$500 – $2.000", accounts_pct: 30, revenue_pct: 28, churn_pct: 8 },
    { range: "$2.000 – $5.000", accounts_pct: 18, revenue_pct: 35, churn_pct: 4 },
    { range: "$5.000+", accounts_pct: 7, revenue_pct: 25, churn_pct: 2 },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Receita</h1>
        <p className="text-muted-foreground text-sm mt-1">Análise de receita por segmento e faixa de MRR</p>
      </div>

      {/* Curva ABC */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold mb-6">Curva ABC</h2>
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={abcData} barCategoryGap="30%">
                <XAxis dataKey="segment" axisLine={false} tickLine={false} className="text-xs" />
                <YAxis axisLine={false} tickLine={false} className="text-xs" tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{
                    borderRadius: "0.5rem",
                    border: "1px solid hsl(220, 13%, 91%)",
                    fontSize: "0.75rem",
                  }}
                />
                <Bar dataKey="revenue_pct" name="Receita (%)" radius={[6, 6, 0, 0]}>
                  {abcData.map((entry: { segment: string }) => (
                    <Cell
                      key={entry.segment}
                      fill={SEGMENT_COLORS[entry.segment as keyof typeof SEGMENT_COLORS] || SEGMENT_COLORS.C}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-2 font-medium text-muted-foreground">Segmento</th>
                  <th className="text-right py-3 px-2 font-medium text-muted-foreground">Receita (%)</th>
                  <th className="text-right py-3 px-2 font-medium text-muted-foreground">Churn (%)</th>
                </tr>
              </thead>
              <tbody>
                {abcData.map((row: { segment: string; revenue_pct: number; churn_pct: number }) => (
                  <tr key={row.segment} className="border-b border-border/50">
                    <td className="py-3 px-2 font-semibold">
                      <span
                        className="inline-block w-2 h-2 rounded-full mr-2"
                        style={{ backgroundColor: SEGMENT_COLORS[row.segment as keyof typeof SEGMENT_COLORS] }}
                      />
                      {row.segment}
                    </td>
                    <td className="text-right py-3 px-2">{row.revenue_pct}%</td>
                    <td className="text-right py-3 px-2">
                      <span className={row.churn_pct > 10 ? "text-destructive font-medium" : ""}>
                        {row.churn_pct}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Faixas de MRR */}
      <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: "150ms" }}>
        <h2 className="text-lg font-semibold mb-6">Faixas de MRR</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 font-medium text-muted-foreground">Faixa</th>
                <th className="text-right py-3 px-2 font-medium text-muted-foreground">% Contas</th>
                <th className="text-right py-3 px-2 font-medium text-muted-foreground">% Receita</th>
                <th className="text-right py-3 px-2 font-medium text-muted-foreground">Churn</th>
              </tr>
            </thead>
            <tbody>
              {mrrRanges.map((row: { range: string; accounts_pct: number; revenue_pct: number; churn_pct: number }) => (
                <tr key={row.range} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-2 font-medium">{row.range}</td>
                  <td className="text-right py-3 px-2">{row.accounts_pct}%</td>
                  <td className="text-right py-3 px-2">{row.revenue_pct}%</td>
                  <td className="text-right py-3 px-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      row.churn_pct > 10 ? "bg-destructive/10 text-destructive" :
                      row.churn_pct > 5 ? "bg-chart-warning/10 text-chart-warning" :
                      "bg-chart-up/10 text-chart-up"
                    }`}>
                      {row.churn_pct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Revenue;
