export type Tier = "hot" | "warm" | "cold" | "at_risk";
export type Role = "gestor" | "manager" | "seller";
export type DealStage = "Engaging" | "Prospecting";

export interface ScoreBreakdown {
  stage: number;
  agentFit: number;
  dealValue: number;
  productWr: number;
  accountQuality: number;
  seasonality: number;
}

export interface ScoredDeal {
  id: string;
  account: string;
  sector: string;
  product: string;
  price: number;
  stage: DealStage;
  currentAgent: string;
  optimalAgent: string;
  manager: string;
  region: string;
  score: number;
  tier: Tier;
  breakdown: ScoreBreakdown;
  currentAgentWr: number;
  optimalAgentWr: number;
  isReallocated: boolean;
  bestSector: string;
  bestSectorWr: number;
  engageDate: string | null;
  daysSinceEngage: number | null;
}

export interface SectorPerformance {
  sector: string;
  wr: number;
  deals: number;
}

export interface AgentProfile {
  name: string;
  manager: string;
  region: string;
  overallWr: number;
  totalClosed: number;
  openDeals: number;
  hotDeals: number;
  warmDeals: number;
  coldDeals: number;
  atRiskDeals: number;
  pipelineValue: number;
  sectors: SectorPerformance[];
  bestSector: string;
  bestSectorWr: number;
  reallocatedIn: number;
  reallocatedOut: number;
}

export interface ManagerSummary {
  manager: string;
  agents: number;
  totalDeals: number;
  hotDeals: number;
  reallocations: number;
  pipelineValue: number;
}

export interface TierThresholds {
  p85: number;
  p50: number;
  p15: number;
}

export interface DatasetMeta {
  totalOpenDeals: number;
  totalClosedDeals: number;
  overallWinRate: number;
  maxProductPrice: number;
  tierThresholds: TierThresholds;
  totalPipelineValue: number;
  reallocatedCount: number;
  stageCounts: { Prospecting: number; Engaging: number; Won: number; Lost: number };
  generatedAt: string;
}

export type ClosedStage = "Won" | "Lost";

export interface ClosedDeal {
  id: string;
  account: string;
  sector: string;
  product: string;
  price: number;
  stage: ClosedStage;
  agent: string;
  manager: string;
  region: string;
  closeValue: number;
  engageDate: string | null;
  closeDate: string | null;
  daysToClose: number | null;
}

export interface RevenueBucket {
  key: string;
  revenue: number;
  deals: number;
  avgTicket: number;
}

export interface SectorLossPattern {
  sector: string;
  product: string;
  lostDeals: number;
  lostValue: number;
  shareOfSectorLosses: number;
}

export interface SectorLossRate {
  sector: string;
  lossRate: number;
  totalClosed: number;
  lostDeals: number;
  lostValue: number;
}

export interface WorstAgentBySector {
  sector: string;
  worstAgent: string;
  worstWr: number;
  worstDeals: number;
  bestAgent: string;
  bestWr: number;
  bestDeals: number;
  deltaPP: number;
}

export interface Analytics {
  conversion: {
    topSectorsByRevenue: RevenueBucket[];
    topProductsByRevenue: RevenueBucket[];
    topAgentsByRevenue: RevenueBucket[];
    avgTicketBySector: { sector: string; avgTicket: number }[];
    avgTicketByProduct: { product: string; avgTicket: number }[];
    totalWonRevenue: number;
    wonDealCount: number;
  };
  losses: {
    sectorsByLossRate: SectorLossRate[];
    sectorProductPatterns: SectorLossPattern[];
    worstAgentBySector: WorstAgentBySector[];
    actionableInsights: string[];
    totalLostRevenue: number;
    lostDealCount: number;
  };
}
