// Tipos do domínio. Os nomes seguem a ESPEC-TELAS e as views do banco (core_deals_visao etc.),
// para a troca da fonte (arquivo → banco) não mexer nas telas.

export type Papel = "vendedor" | "manager" | "admin";
export type Estagio = "Prospecting" | "Engaging" | "Won" | "Lost";
export type Icone = "super_hot" | "em_risco" | "esfriou";
export type FaixaNota = "alta" | "media" | "baixa";
export type AcaoSugerida = "focar" | "requalificar" | "desistir";
export type TipoAcao = "liguei" | "requalifiquei" | "desisti" | "prioridade_feita" | "prioridade_pulada";
export type MotivoPerda = "preco" | "concorrente" | "sem_orcamento" | "sem_resposta" | "outro" | "cadastro_desfeito";
export type Porte = "pequena" | "media" | "grande";
export type CorTag = "tag-1" | "tag-2" | "tag-3" | "tag-4" | "tag-5" | "tag-6";

export interface Usuario {
  id: number;
  papel: Papel;
  nome: string;
  vendedor?: string;
  manager?: string;
  regiao?: string;
}

export interface Tag {
  id: number;
  nome: string;
  cor: CorTag;
  ativa: boolean;
}

export interface Contato {
  id: number;
  conta: string | null;
  nome: string;
  cargo: string | null;
  email: string | null;
  telefone: string | null;
}

/** Uma linha de core_deals_visao: o deal com tudo o que as telas mostram. */
export interface DealVisao {
  id: string;
  nome: string;
  estagio: Estagio;
  vendedor: string;
  manager: string;
  regiao: string;
  produto: string;
  serie: string;
  preco: number;
  conta: string | null;
  setor: string | null;
  porte: Porte | null;
  contato: Pick<Contato, "id" | "nome" | "cargo"> | null;
  dataAbertura: string | null;
  diasDesdeAbertura: number | null;
  ultimoContato: string | null;
  closeDate: string | null;
  closeValue: number | null;
  motivoPerda: MotivoPerda | null;
  fit: number | null;
  heat: number | null;
  bonus: number | null;
  score: number | null;
  faixaNota: FaixaNota | null;
  acaoSugerida: AcaoSugerida | null;
  marcadores: string[];
  valorEsperado: number | null;
  valorPeloPrecoDeTabela: boolean;
  icone: Icone | null;
  tags: Tag[];
  qtdComentarios: number;
  atualizadoDepoisDaNota: boolean;
  criadoEm: string | null;
  atualizadoEm: string;
}

export interface Componente {
  grupo: "fit" | "heat" | "bonus";
  nome: string;
  pontos: number;
  maximo: number | null;
}

export interface EventoLinhaDoTempo {
  data: string | null;
  momento: string | null;
  tipo: "aberto" | "fechado" | "criado" | "estagio" | "dados" | "acao" | "comentario" | "tag" | "repasse";
  descricao: string;
  autor: string | null;
  desfeito: boolean;
}

export interface Comentario {
  id: number;
  autorId: number;
  autor: string;
  texto: string;
  data: string;
  criadoEm: string;
  editado: boolean;
}

export interface DealDetalhe {
  deal: DealVisao;
  componentes: Componente[];
  motivos: string[];
  linhaDoTempo: EventoLinhaDoTempo[];
  comentarios: Comentario[];
  contatoCompleto: Contato | null;
  transicoes: Estagio[];
}

export interface ContaVisao {
  nome: string;
  setor: string | null;
  porte: Porte | null;
  funcionarios: number | null;
  receitaMilhoes: number | null;
  anoFundacao: number | null;
  sede: string | null;
  empresaMae: string | null;
  dealsAbertos: number;
  compras: number;
  perdas: number;
  receitaGanha: number;
  padrao: "na_janela" | "fora_da_janela" | "sem_padrao" | null;
  bonus: number | null;
}

export interface ContaDetalhe {
  conta: ContaVisao;
  porMes: { mes: string; ganhos: number; perdidos: number }[];
  produtos: { produto: string; compras: number; receita: number }[];
  ticketMedio: number | null;
  primeiraCompra: string | null;
  ultimaCompra: string | null;
  padrao: {
    intervaloTipicoDias: number | null;
    mesHabitual: string | null;
    proximaCompra: string | null;
    explicacao: string | null;
  } | null;
  abertos: DealVisao[];
}

export interface Prioridade {
  posicao: number;
  deal: DealVisao;
  marcada: "feita" | "pulada" | "contato" | null;
  puladoDiasSeguidos: number;
}

export interface Escopo {
  papel: Papel;
  vendedor?: string;
  manager?: string;
  regiao?: string;
}

export interface Pagina<T> {
  total: number;
  linhas: T[];
}
