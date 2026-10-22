/**
 * Tipos dos dados retornados pela API.
 * Espelham os modelos de backend/app/esquemas.py — se mudar lá, mude aqui.
 */

export type Prioridade = "Alta" | "Média" | "Baixa";
export type Etapa = "Prospecting" | "Engaging";
/** ativo = em negociação dentro do prazo histórico; parado = passou do prazo. */
export type Situacao = "ativo" | "prospeccao" | "parado";

export interface DealResumo {
  id: string;
  etapa: Etapa;
  situacao: Situacao;
  vendedor: string;
  manager: string;
  escritorio: string;
  conta: string;
  conta_informada: boolean;
  setor: string | null;
  produto: string;
  valor: number;
  chance: number;
  valor_esperado: number;
  dias_aberto: number | null;
  score: number;
  prioridade: Prioridade;
  /** Aberto há mais tempo que qualquer negócio do histórico. */
  parado: boolean;
  /** Frase curta com o que mais explica a nota (ex.: "Parado há 129 dias"). */
  motivo_principal: string;
}

export interface Motivo {
  texto: string;
  tipo: "positivo" | "negativo" | "neutro";
}

/** Pontos que uma parte deu ao negócio. A soma dos pontos das partes é o score. */
export interface ParteScore {
  chave: "situacao" | "valor" | "reta_final";
  nome: string;
  pontos: number;
  maximo: number;
  explicacao: string;
}

export interface DealDetalhe extends DealResumo {
  partes: ParteScore[];
  motivos: Motivo[];
  sugestao: string;
}

export interface ListaDeals {
  total: number;
  deals: DealResumo[];
}

export interface Resumo {
  total_abertos: number;
  qtd_prioridade_alta: number;
  qtd_ativos: number;
  qtd_parados: number;
  valor_esperado_total: number;
}

/** Regras atuais da pontuação (definidas em backend/app/config.py). */
export interface RegrasPontuacao {
  pontos_maximos: { situacao: number; valor: number; reta_final: number };
  pontos_prospeccao: number;
  limite_alta: number;
  limite_media: number;
  taxa_vitoria_geral: number;
  ciclo_mediano_dias: number;
  limite_dias: number;
  preco_minimo: number;
  preco_maximo: number;
}

/** Resultado do backtest com o histórico (backend/app/servicos/validacao.py). */
export interface Validacao {
  datas_corte: string[];
  parados: number;
  parados_fechados_depois: number;
  por_prioridade: { prioridade: Prioridade; negocios: number; taxa_vitoria: number; receita_media: number }[];
  atributos: { atributo: string; auc_medio: number }[];
}

export interface OpcoesFiltro {
  vendedores: string[];
  managers: string[];
  escritorios: string[];
  produtos: string[];
  prioridades: Prioridade[];
}

/** Filtros escolhidos na tela. Campo vazio ("") significa "todos". */
export interface Filtros {
  vendedor: string;
  manager: string;
  escritorio: string;
  produto: string;
  prioridade: string;
  busca: string;
}

export const FILTROS_VAZIOS: Filtros = {
  vendedor: "",
  manager: "",
  escritorio: "",
  produto: "",
  prioridade: "",
  busca: "",
};
