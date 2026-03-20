export interface Account {
  account: string;
  sector: string;
  year_established: number;
  revenue: number;
  employees: number;
  office_location: string;
  subsidiary_of: string;
}

export interface SalesTeam {
  sales_agent: string;
  manager: string;
  regional_office: string;
}

export interface Product {
  product: string;
  series: string;
  sales_price: number;
}

export interface Deal {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: 'Prospecting' | 'Engaging' | 'Won' | 'Lost';
  engage_date: string;
  close_date: string;
  close_value: number;
}

export interface ScoreExplanation {
  score: number;
  maturity: { score: number; explanation: string; weight: string };
  agent: { score: number; explanation: string; weight: string };
  product: { score: number; explanation: string; weight: string };
  firmographics: { score: number; explanation: string; weight: string };
  days_in_deal: number;
  zone: string;
}

export interface ScoredDeal extends Deal {
  score: number;
  explanation: ScoreExplanation;
}
