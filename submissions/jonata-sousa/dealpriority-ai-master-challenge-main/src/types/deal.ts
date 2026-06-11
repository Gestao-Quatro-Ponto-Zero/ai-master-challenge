export interface Deal {
  id?: string;
  opportunity_id: string;
  account: string;
  sales_agent: string;
  manager: string;
  regional_office: string;
  product: string;
  deal_stage: string;
  priority_score: number;
  priority_label: string;
  positive_factor_1: string;
  positive_factor_2: string;
  risk_factor_1: string;
  risk_factor_2: string;
  recommended_action: string;
}
