export type Estado = "foco_urgente" | "acompanhar" | "engajar" | "qualificar" | "desistir";

export const ESTADOS: Estado[] = ["foco_urgente", "acompanhar", "engajar", "qualificar", "desistir"];

export const ESTADO_LABELS: Record<Estado, string> = {
  foco_urgente: "Foco urgente",
  acompanhar: "Acompanhar",
  engajar: "Engajar",
  qualificar: "Qualificar",
  desistir: "Desistir",
};

export type Confianca = "A" | "B" | "C" | "D";

export type SortKey = "score" | "prioridade" | "age_days" | "estado";
export type SortOrder = "asc" | "desc";

export interface Oportunidade {
  opportunity_id: string;
  sales_agent: string;
  manager: string | null;
  regional_office: string | null;
  product: string;
  account: string | null;
  sector: string | null;
  porte: string | null;
  deal_stage: "Prospecting" | "Engaging";
  age_days: number | null;
  p_hat: number;
  valor: number;
  urgencia: number;
  prioridade: number;
  score: number;
  confianca: Confianca;
  confianca_label: string;
  razao_confianca: string;
  estado: Estado;
  estado_label: string;
  plano_de_acao: string;
}

export interface DealsEnvelope {
  items: Oportunidade[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  contagem_por_estado: Record<Estado, number>;
  excluidas_idade_desconhecida: number;
}

export interface Conta {
  vinculada: boolean;
  sector: string | null;
  porte: string | null;
  revenue: number | null;
  employees: number | null;
  year_established: number | null;
  office_location: string | null;
}

export interface DealDetail extends Oportunidade {
  conta: Conta;
  plano_de_acao_passos: string[];
}

export interface FiltroVendedor {
  nome: string;
  manager: string | null;
  regional_office: string | null;
}

export interface FiltroGerente {
  nome: string;
  regional_office: string | null;
}

export interface FilterOptions {
  vendedores: FiltroVendedor[];
  gerentes: FiltroGerente[];
  escritorios: string[];
  produtos: string[];
  idade_min: number | null;
  idade_max: number | null;
}

export interface Kpis {
  total_oportunidades: number;
  receita_ganha: number;
  valor_esperado_aberto: number;
  total_desistir: number;
  maior_negocio_fechado: number;
  data_inicio: string;
  data_fim: string;
  idade_maxima_aberta: number | null;
  indicadores_historicos: string[];
}

export interface RollupLinha {
  chave: string;
  nivel: "sales_agent" | "manager" | "regional_office";
  n_abertas: number;
  valor_esperado: number;
  por_estado: Record<Estado, number>;
}

export interface ProdutoEsforco {
  product: string;
  n_oportunidades: number;
  participacao_receita_historica: number;
}

export interface Rollup {
  linhas: RollupLinha[];
  esforco_por_produto: ProdutoEsforco[];
}

export interface ScoreAvulsaResult {
  product: string;
  porte: string | null;
  age_days: number | null;
  p_hat: number;
  valor: number;
  urgencia: number;
  prioridade: number;
  score: number;
  confianca: Confianca;
  confianca_label: string;
  razao_confianca: string;
  estado: Estado;
  estado_label: string;
  plano_de_acao: string;
  plano_de_acao_passos: string[];
}

export interface Filtros {
  sales_agent?: string;
  manager?: string;
  regional_office?: string;
  product?: string;
  confianca?: Confianca;
  idade_min?: string;
  idade_max?: string;
}
