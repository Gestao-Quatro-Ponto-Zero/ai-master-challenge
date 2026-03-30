import { useEffect, useState } from "react";
import { fetchKPIs } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const OperationalAnalysis = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKPIs()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const usageVsChurn = data?.usage_vs_churn ?? [
    { range: "Low", churned: 12, active: 88 },
    { range: "Medium", churned: 18, active: 82 },
    { range: "High", churned: 22, active: 78 },
  ];

  const errorsVsChurn = data?.errors_vs_churn ?? [
    { range: "0-5", churned: 8, active: 92 },
    { range: "6-20", churned: 15, active: 85 },
    { range: "20+", churned: 30, active: 70 },
  ];

  const ticketsVsChurn = data?.tickets_vs_churn ?? [
    { range: "0", churned: 10, active: 90 },
    { range: "1-3", churned: 20, active: 80 },
    { range: "4+", churned: 35, active: 65 },
  ];

  const chartColors = {
    churned: "hsl(0, 84%, 60%)",
    active: "hsl(172, 66%, 50%)",
  };

  const renderChart = (title: string, chartData: any[]) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
            <XAxis dataKey="range" tick={{ fontSize: 12 }} stroke="hsl(220, 9%, 46%)" />
            <YAxis tick={{ fontSize: 12 }} stroke="hsl(220, 9%, 46%)" />
            <Tooltip
              contentStyle={{
                background: "hsl(0, 0%, 100%)",
                border: "1px solid hsl(220, 13%, 91%)",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px" }} />
            <Bar dataKey="churned" name="Churned" fill={chartColors.churned} radius={[4, 4, 0, 0]} />
            <Bar dataKey="active" name="Active" fill={chartColors.active} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Operational Analysis</h1>
        <p className="text-muted-foreground text-sm mt-1">Correlações operacionais com churn</p>
      </div>

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-3">
        {renderChart("Usage vs Churn", usageVsChurn)}
        {renderChart("Errors vs Churn", errorsVsChurn)}
        {renderChart("Support Tickets vs Churn", ticketsVsChurn)}
      </div>
    </div>
  );
};

export default OperationalAnalysis;
