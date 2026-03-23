"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

interface SLAGaugeProps {
  complianceRate: number;
}

export function SLAGauge({ complianceRate }: SLAGaugeProps) {
  const value = Math.min(100, Math.max(0, complianceRate));
  const remaining = 100 - value;

  const data = [
    { name: "Dentro do SLA", value },
    { name: "Fora do SLA", value: remaining },
  ];

  // Color based on compliance level
  const fillColor =
    value >= 90 ? "#10b981" : value >= 75 ? "#f59e0b" : "#ef4444";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">SLA Compliance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center">
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="75%"
                startAngle={180}
                endAngle={0}
                innerRadius={60}
                outerRadius={85}
                dataKey="value"
                stroke="none"
              >
                <Cell fill={fillColor} />
                <Cell fill="#e5e7eb" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="-mt-12 text-center">
            <p className="text-3xl font-bold" style={{ color: fillColor }}>
              {value.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground">
              dos tickets dentro do prazo
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
