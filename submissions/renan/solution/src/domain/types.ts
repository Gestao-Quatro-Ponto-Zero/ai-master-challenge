export type DealStage = "Prospecting" | "Engaging" | "Won" | "Lost";

export interface Account {
  name: string;
  sector: string;
  yearEstablished: number;
  /** Receita anual em milhões de US$. */
  revenue: number;
  employees: number;
  officeLocation: string;
  subsidiaryOf: string | null;
}

export interface Product {
  name: string;
  series: string;
  salesPrice: number;
}

export interface SalesAgent {
  name: string;
  manager: string;
  regionalOffice: string;
}

/** Deal já ligado a conta, produto e vendedor. Datas em ISO (YYYY-MM-DD). */
export interface Deal {
  id: string;
  stage: DealStage;
  agent: string;
  manager: string;
  regionalOffice: string;
  product: string;
  productSeries: string;
  listPrice: number;
  account: string | null;
  sector: string | null;
  accountEmployees: number | null;
  engageDate: string | null;
  closeDate: string | null;
  closeValue: number | null;
}

export interface QualityIssue {
  code: string;
  description: string;
  affected: number;
  treatment: string;
}

export interface Dataset {
  referenceDate: string;
  deals: Deal[];
  accounts: Account[];
  products: Product[];
  agents: SalesAgent[];
  quality: QualityIssue[];
}
