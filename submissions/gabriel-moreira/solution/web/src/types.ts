export type Estado = "prioritize" | "acompanhar" | "qualificar" | "revisao_lote";

export const ESTADOS: Estado[] = ["prioritize", "acompanhar", "qualificar", "revisao_lote"];

/** Os três estados trabalháveis, exibidos como filtro na aba Oportunidades
 * — `revisao_lote` não é um filtro dessa fila, é alcançado por uma visão
 * própria (Requirement "Filtro de estado"). */
export const ESTADOS_TRABALHAVEIS: Estado[] = ["prioritize", "acompanhar", "qualificar"];

export const ESTADO_LABELS: Record<Estado, string> = {
  prioritize: "Priorizar",
  acompanhar: "Acompanhar",
  qualificar: "Qualificar",
  revisao_lote: "Revisão em lote",
};

export type SortKey = "score" | "confianca" | "age_days" | "estado";
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
  preco_tabela: number;
  valor: number;
  urgencia: number;
  score: number;
  /** 0-100 — min(completude, suporte). A escala por letra (A-D) não existe mais. */
  confianca: number;
  completude: number;
  suporte: number;
  sem_precedente: boolean;
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
  /** PRIORIDADE em dólares — valor intermediário auditável, exposto só no
   * detalhe (nunca na listagem nem como critério de ordenação). */
  prioridade: number;
  plano_de_acao_passos: string[];
  /** Por que este SCORE — decomposição de p̂/VALOR/URGÊNCIA e do porte da
   * conta em frases de negócio, sem jargão técnico. Só no detalhe. */
  score_fatores: string[];
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
  total_revisao_lote: number;
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
  /** CONFIANÇA mediana do grupo — indicador de qualidade de cadastro, não
   * de desempenho de vendas (Requirement "Rollup de gestão"). */
  confianca_mediana: number;
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
  confianca: number;
  completude: number;
  suporte: number;
  sem_precedente: boolean;
  razao_confianca: string;
  estado: Estado;
  estado_label: string;
  plano_de_acao: string;
  plano_de_acao_passos: string[];
  score_fatores: string[];
}

export interface Filtros {
  sales_agent?: string;
  manager?: string;
  regional_office?: string;
  product?: string;
  confianca_min?: string;
  confianca_max?: string;
  idade_min?: string;
  idade_max?: string;
}
