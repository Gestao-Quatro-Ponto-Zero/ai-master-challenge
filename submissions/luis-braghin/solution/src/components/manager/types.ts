export interface ManagerStats {
  name: string;
  agents: number;
  totalDeals: number;
  pipeline: number;
  ev: number;
  avgWinRate: number;
  avgScore: number;
  hotWarm: number;
  coldDead: number;
  over130d: number;
  avgDaysInPipeline: number;
  totalRevenue: number;
  evPerAgent: number;
  pipelinePerAgent: number;
  pctEngaging: number;
  topProduct: string;
  topProductWR: number;
}

export const tooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "8px",
};
