import { useQuery } from "@tanstack/react-query";
import type { DashboardMetricsResponse } from "@shared/schema";

export function useDashboardMetrics() {
  return useQuery<DashboardMetricsResponse>({
    queryKey: ["/api/dashboard/metrics"],
    queryFn: () => fetch("/api/dashboard/metrics", { credentials: "include" }).then(r => r.json()),
  });
}
