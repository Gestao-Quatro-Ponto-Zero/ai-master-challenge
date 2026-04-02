export interface PipelineDeal {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: string;
  engage_date: string;
  close_date: string;
  close_value: string;
}

export interface SalesTeam {
  sales_agent: string;
  manager: string;
  regional_office: string;
}

export interface Product {
  product: string;
  series: string;
  sales_price: string;
}

export interface Account {
  account: string;
  sector: string;
  year_established: string;
  revenue: string;
  employees: string;
  office_location: string;
  subsidiary_of: string;
}

export interface Metadata {
  Table: string;
  Field: string;
  Description: string;
}

export interface ScoreResult {
  score: number;
  label: 'Crítico' | 'Alto' | 'Médio' | 'Baixo';
  context_reason: string;
  breakdown: {
    d1: number;
    d2: number;
    d3: number;
    d4: number;
    d5: number;
  };
}

export interface ScoredDeal extends PipelineDeal {
  est_value: number;
  scoreResult: ScoreResult;
}

export type FileStatus = 'waiting' | 'processing' | 'loaded' | 'error';

export interface FileUploadState {
  status: FileStatus;
  rowCount: number;
  error?: string;
}

export interface ActionRecord {
  dealId: string;
  actionType: 'call' | 'email' | 'meeting' | 'followup';
  result: 'advanced' | 'waiting' | 'rescheduled' | 'lost';
}
