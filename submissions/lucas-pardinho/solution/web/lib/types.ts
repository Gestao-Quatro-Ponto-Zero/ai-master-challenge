export const QUEUES = [
  "Foco agora",
  "Acelerar",
  "Nutrir",
  "Resgatar ou desqualificar",
  "Qualificar",
] as const;

export type Queue = (typeof QUEUES)[number];
export type Confidence = "high" | "medium" | "low";

export interface ScoreBreakdown {
  conversion?: number | null;
  actionability?: number | null;
  valuePotential?: number | null;
  accountCompleteness?: number | null;
  weightedContribution?: {
    conversion?: number | null;
    actionability?: number | null;
    value?: number | null;
    account?: number | null;
  };
}

export interface AccountDetails {
  sector?: string | null;
  revenue?: number | null;
  employees?: number | null;
  officeLocation?: string | null;
  [key: string]: string | number | boolean | null | undefined;
}

export interface Opportunity {
  opportunityId: string;
  salesAgent: string;
  manager: string;
  regionalOffice: string;
  product: string;
  productRaw: string;
  productSeries?: string | null;
  account: string | null;
  accountDetails?: AccountDetails | null;
  dealStage: string;
  engageDate: string | null;
  ageDays: number | null;
  estimatedValue: number;
  probability: number | null;
  priorityScore: number | null;
  qualificationScore: number | null;
  scoreBreakdown?: ScoreBreakdown | null;
  queue: Queue;
  confidence: Confidence;
  reasons: string[];
  dataQualityFlags: string[];
  nextAction: string;
  rankGlobal: number | null;
  rankByAgent: number | null;
}

export interface DashboardFile {
  [key: string]: unknown;
}

export interface ModelReport {
  [key: string]: unknown;
}

export interface DataQualityReport {
  [key: string]: unknown;
}

export interface QueueSummary {
  queue: Queue;
  count: number;
  estimatedValue: number;
  weightedValue: number;
}

export interface ExecutiveMetrics {
  openDeals: number;
  estimatedPipeline: number;
  weightedPipeline: number;
  focusNow: number;
  staleDeals: number;
  averageScore: number | null;
  queues: QueueSummary[];
  confidence: Record<Confidence, number>;
  regions: Array<{ name: string; count: number; estimatedValue: number }>;
  topOpportunities: Opportunity[];
  dataIssueDeals: number;
}

export interface DataStatus {
  source: "generated" | "sample" | "unavailable";
  directory: string;
  availableFiles: string[];
  missingFiles: string[];
  sampleAllowed: boolean;
}
