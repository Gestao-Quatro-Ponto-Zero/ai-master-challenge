export interface RawRow {
  opportunity_id: string;
  sales_agent: string;
  manager: string;
  account: string;
  employees: any;
  sector: any;
  product: string;
  deal_stage: string;
  engage_date: any;
  close_date: any;
  close_value: any;
}

export type DealStage = "Prospecting" | "Engaging" | "Lost" | "Won";
export type ScoreGrade = "A" | "B" | "C" | "D";
export type EmployeeBucket = "0-250" | "251-1000" | "1001-5000" | "5001+";
export type ActionStatus = "Corrigir cadastro" | "Foco agora" | "Foco depois" | "Baixa prioridade" | "Ganho" | "Perdido";

export interface Lead {
  opportunity_id: string;
  sales_agent: string;
  manager: string;
  account: string;
  employees: number | null;
  sector: string | null;
  product: string;
  deal_stage: DealStage;
  engage_date: Date | null;
  close_date: Date | null;
  close_value: number;
  employeeBucket: EmployeeBucket | null;
  isIncomplete: boolean;
  missingFields: string[];
  scoreNumeric: number | null;
  scoreGrade: ScoreGrade | null;
  actionStatus: ActionStatus;
  scoreExplanation: string;
}
