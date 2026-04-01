/**
 * Account data from accounts.csv
 */
export interface Account {
  account: string;
  sector: string;
  year_established?: number;
  revenue: number;
  employees: number;
  office_location: string;
  subsidiary_of?: string;
}

/**
 * Product data from products.csv
 */
export interface Product {
  product: string;
  series: string;
  sales_price: number;
}

/**
 * Sales team member from sales_teams.csv
 */
export interface SalesTeam {
  sales_agent: string;
  manager: string;
  regional_office: string;
}

/**
 * Sales opportunity from sales_pipeline.csv
 */
export interface PipelineOpportunity {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account?: string; // Can be null for active deals
  deal_stage: 'Won' | 'Lost' | 'Engaging' | 'Prospecting';
  engage_date: Date;
  close_date?: Date; // Null for active deals
  close_value: number;
}

/**
 * Single factor contribution to a score
 */
export interface ScoreFactor {
  name: string; // e.g., "Win Rate da Conta"
  weight: number; // Percentage (0-100)
  raw_value: number | string; // Original value
  normalized_value: number; // 0-1
  contribution: number; // Points contributed to final score
  explanation: string; // Human-readable explanation in Portuguese
}

/**
 * Deal-level score (for active opportunities)
 */
export interface DealScore {
  opportunity_id: string;
  deal_stage: string;
  score: number; // 0-100
  tier: 'HOT' | 'WARM' | 'COOL' | 'COLD';
  factors: ScoreFactor[];
  recommendation: string;
  account?: string;
  product: string;
  sales_agent: string;
  engage_date: Date;
  region?: string; // regional_office do vendedor
  manager?: string; // manager do vendedor
  series?: string; // série do produto
}

/**
 * Account-level aggregated score
 */
export interface AccountScore {
  account: string;
  score: number; // 0-100
  tier: 'HOT' | 'WARM' | 'COOL' | 'COLD';
  factors: ScoreFactor[];
  deals_summary: {
    total: number;
    won: number;
    lost: number;
    engaging: number;
    prospecting: number;
  };
  win_rate: number; // 0-1
  avg_ticket: number;
  revenue_total: number;
  last_deal_date: Date | null;
  insufficient_data?: boolean;
}

/**
 * Context for SPIN Selling script generation
 */
export interface SPINContext {
  // Account data
  accountName?: string;
  sector?: string;
  employees?: number;
  revenue?: number;
  location?: string;

  // Metrics
  winRate?: number;
  avgTicket?: number;
  totalDeals?: number;
  wonDeals?: number;
  lostDeals?: number;
  activeDeals?: number;

  // Pattern analysis
  topProduct?: string;
  failedProducts?: string[];
  missingProducts?: string[];
  bestAgent?: string;
  avgCycleTime?: number;
  lostRevenue?: number;

  // Current deal (if applicable)
  currentProduct?: string;
  currentStage?: string;
  daysInPipeline?: number;
}

/**
 * SPIN Selling script (4 sections)
 */
export interface SPINScript {
  situation: string;
  problem: string;
  implication: string;
  need_payoff: string;
}

/**
 * Complete lead report with score breakdown and script
 */
export interface LeadReport {
  account_score?: AccountScore;
  deal_score: DealScore;
  spin_script: SPINScript;
  context: SPINContext;
  generated_at: Date;
}

/**
 * Data loading state
 */
export interface DataLoadingState {
  isLoading: boolean;
  isLoaded: boolean;
  errors: string[];
}

/**
 * Global application data context
 */
export interface AppData {
  accounts: Account[];
  products: Product[];
  salesTeams: SalesTeam[];
  pipeline: PipelineOpportunity[];
  dealScores: DealScore[];
  accountScores: AccountScore[];
}

/**
 * Filter options for the application
 */
export interface FilterOptions {
  region?: string;
  manager?: string;
  sales_agent?: string;
  product?: string;
  series?: string;
  tier?: 'HOT' | 'WARM' | 'COOL' | 'COLD';
}

/**
 * Tier type for scoring
 */
export type TierType = 'HOT' | 'WARM' | 'COOL' | 'COLD';
