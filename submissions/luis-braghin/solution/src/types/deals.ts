export interface DealBreakdown {
  velocity?: number;
  opportunityWindow?: number;
  agentProductAffinity: number;
  productSectorFit: number;
  dealValue: number;
  seasonality?: number;
  accountQuality: number;
}

export type DealCategory = "HOT" | "WARM" | "COOL" | "COLD" | "DEAD";
export type DealStage = "Engaging" | "Prospecting";
export type ClosedStage = "Won" | "Lost";

export interface ScoredDeal {
  id: string;
  agent: string;
  product: string;
  account: string;
  stage: DealStage;
  engageDate: string;
  daysInPipeline: number;
  salesPrice: number;
  score: number;
  category: DealCategory;
  breakdown: DealBreakdown;
  expectedValue: number;
  manager: string;
  regionalOffice: string;
  sector: string;
  accountRevenue: number;
  accountEmployees: number;
  aiSummary: string;
  aiButton: string;
}

export interface ClosedDeal {
  id: string;
  agent: string;
  product: string;
  account: string;
  stage: ClosedStage;
  engageDate: string;
  closeDate: string;
  closeValue: number;
  daysToClose: number;
  manager: string;
  regionalOffice: string;
  sector: string;
}

export interface ProductWinRate {
  won: number;
  total: number;
  winRate: number;
}

export interface Agent {
  name: string;
  manager: string;
  regionalOffice: string;
  totalDeals: number;
  wonDeals: number;
  lostDeals: number;
  activeDeals: number;
  winRate: number;
  totalRevenue: number;
  avgDealSize: number;
  productWinRates: Record<string, ProductWinRate>;
}

export interface Product {
  name: string;
  series: string;
  price: number;
  totalDeals: number;
  wonDeals: number;
  winRate: number;
  avgCloseTime: number;
  medianCloseTime: number;
}

export interface Account {
  account: string;
  sector: string;
  year_established: number;
  revenue: number;
  employees: number;
  office_location: string;
  subsidiary_of: string;
}

export interface EnrichmentContact {
  name: string;
  role: string;
  linkedin: string;
}

export interface Enrichment {
  description: string;
  risk: string;
  riskDetail: string;
  contacts: EnrichmentContact[];
  news: string;
}

export interface VelocityCurvePoint {
  range: string;
  winRate: number;
  deals: number;
  score: number;
}

export interface Seasonality {
  pushMonths: { months: number[]; avgWinRate: number; label: string };
  nonPushMonths: { avgWinRate: number; label: string };
  difference: number;
}

export interface PipelineHealth {
  totalActive: number;
  engaging: number;
  prospecting: number;
  over90Days: number;
  over130Days: number;
  pctInflated: number;
}

export interface TopAgent {
  name: string;
  winRate: number;
  deals: number;
  revenue: number;
}

export interface ProductPerformance {
  product: string;
  price: number;
  winRate: number;
  deals: number;
  medianDays: number;
}

export interface Analytics {
  overallWinRate: number;
  totalRevenue: number;
  avgDealSize: number;
  medianCloseTime: number;
  seasonality: Seasonality;
  productPerformance: ProductPerformance[];
  velocityCurve: VelocityCurvePoint[];
  pipelineHealth: PipelineHealth;
  topAgents: TopAgent[];
  bottomAgents: TopAgent[];
}

export interface ManagerInfo {
  name: string;
  office: string;
  agents: number;
}

export interface OfficeInfo {
  name: string;
  agents: number;
}

export interface TeamStructure {
  managers: ManagerInfo[];
  offices: OfficeInfo[];
}

export interface ScoringCategory {
  label: string;
  min: number;
  max: number;
}

export interface ScoringMethodology {
  version: string;
  referenceDate: string;
  engagingWeights: Record<string, number>;
  prospectingWeights: Record<string, number>;
  categories: Record<string, ScoringCategory>;
}

export interface G4Data {
  scoredDeals: ScoredDeal[];
  closedDeals: ClosedDeal[];
  agents: Agent[];
  products: Product[];
  accounts: Account[];
  referenceDate: string;
  enrichment: Record<string, Enrichment>;
  analytics: Analytics;
  scoringMethodology: ScoringMethodology;
  teamStructure: TeamStructure;
}
