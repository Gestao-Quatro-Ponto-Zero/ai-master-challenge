// Pipeline Focus Console — data model for the CRM source tables.
// Central table: sales_pipeline. Joined to accounts, products, sales_teams.

export interface AccountRow {
  account: string;
  sector?: string;
  year_established?: number;
  revenue?: number; // millions
  employees?: number;
  office_location?: string;
  subsidiary_of?: string;
}

export interface ProductRow {
  product: string;
  series?: string;
  sales_price?: number;
}

export interface SalesTeamRow {
  sales_agent: string;
  manager?: string;
  regional_office?: string;
}

export interface PipelineRow {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: string; // Prospecting | Engaging | Won | Lost
  engage_date?: string;
  close_date?: string;
  close_value?: number;
}

export interface Dataset {
  accounts: AccountRow[];
  products: ProductRow[];
  salesTeams: SalesTeamRow[];
  pipeline: PipelineRow[];
}

export type DealStage = "Prospecting" | "Engaging" | "Won" | "Lost";
export const OPEN_STAGES = ["Prospecting", "Engaging"];

export type Priority = "High" | "Priority" | "Watch" | "Low";

export interface ScoreFactor {
  // stable identity for logic checks, independent of the translated label
  code: string;
  label: string;
  detail: string;
  // signed weighted points this factor contributed to the 0-100 total
  points: number;
  tone: "positive" | "risk" | "neutral";
}

export interface ScoredDeal {
  opportunity_id: string;
  account: string;
  sector?: string;
  product: string;
  series?: string;
  salesAgent: string;
  manager?: string;
  region?: string;
  stage: string;
  expectedValue: number; // close_value or product list price
  valueIsEstimated: boolean;
  ageDays: number | null;
  score: number; // 0-100
  priority: Priority;
  confidence: Confidence;
  positives: ScoreFactor[];
  risks: ScoreFactor[];
  breakdown: { name: string; weight: number; score0to1: number; weighted: number }[];
  whyThisScore: string;
  risk: string;
  nextBestAction: string;
  nextActionCode: NextActionCode;
  dataUsed: string[];
  limitations: string[];
}

export type Confidence = "High" | "Medium" | "Low";

export type NextActionCode =
  | "revive"
  | "callToday"
  | "engageBuyer"
  | "followUp"
  | "qualify"
  | "managerReview"
  | "monitor"
  | "deprioritize";
