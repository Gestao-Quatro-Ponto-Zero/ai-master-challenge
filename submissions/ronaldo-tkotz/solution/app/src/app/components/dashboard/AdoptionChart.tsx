"use client";

import type { TrendResult } from "@/engine/dashboard";
import { LineChart } from "../charts/LineChart";

/** Client wrapper so the formatter function stays on the client side of the boundary. */
export function AdoptionChart({ trend, bare = false, height = 240 }: { trend: TrendResult; bare?: boolean; height?: number }) {
  return (
    <LineChart
      categories={trend.categories}
      series={trend.series}
      markLastPartial={trend.lastPartial}
      yFormat={(n) => n.toLocaleString("pt-BR")}
      height={height}
      bare={bare}
    />
  );
}
