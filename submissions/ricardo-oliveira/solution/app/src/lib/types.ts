// Formas de dado que o app usa. Vêm da planilha, pela API (Apps Script) ou pelo snapshot.
export type Papel = "vendedor" | "manager";

export type User = {
  nome: string;
  manager: string;
  regiao: string;
  email: string;
  papel: Papel;
};

export type Config = {
  fimDosDados: string;
  diasPassados: number;
  hoje: string;
  cicloNormal: number;
  cicloMaisLongo: number;
  janelaEntrando: number;
  janelaPoucoFora: number;
  modoDono: string;
  prazoFilaDiasUteis: number;
  requalificacaoDias: number;
  dealsPorSemana: number;
  ordemDentroDoPasso: string;
  filaPorDia?: number;
  totais: {
    comConta: number; passo1: number; passo2: number; passo3: number; passo4: number;
    semConta: number; filaForaDoPrazo: number; confirmar?: number;
  };
  triggerLigado?: boolean;
};

// Linhas da planilha chegam como objetos com as colunas como chave (cabeçalhos em PT-BR).
export type Row = Record<string, string | number | boolean | null | undefined>;

export type RepData = {
  user: User;
  config: Config;
  kpi: Row | null;
  kpisTime: Row[];
  lista: Row[];
  fila: Row[];
  recompra: Row[];
  contas: string[];
  modo: "live" | "snapshot";
};

export type ManagerData = {
  user: User;
  config: Config;
  time: Row[];
  resumo: Row | null;
  kpisTime: Row[];
  lista: Row[];
  fila: Row[];
  recompra: Row[];
  modo: "live" | "snapshot";
};

export type RevopsData = {
  config: Config;
  reps: Row[];
  managers: Row[];
  recompra: Row[];
  kpis: Row[];
  modo: "live" | "snapshot";
};

// Nomes das colunas, exatamente como estão na planilha.
export const L = {
  id: "Oportunidade",
  vendedorAtual: "Vendedor atual",
  produto: "Produto",
  conta: "Conta",
  estagio: "Estágio",
  engajou: "Engajou em",
  diasAberto: "Dias aberto",
  vivo: "Vivo?",
  dono: "Dono da conta",
  trabalha: "Trabalha hoje",
  manager: "Manager",
  regiao: "Região",
  icp: "ICP",
  preco: "Preço de tabela",
  recompra: "Recompra",
  diasRecompra: "Dias até a recompra",
  compras: "Compras na base da estimativa",
  passo: "Passo",
  ordem: "Ordem do dia",
  porque: "Por quê",
  acao: "Próxima ação",
  ultimoContato: "Último contato (app)",
  estado: "Estado (app)",
  feitoHoje: "Feito hoje?",
  receita: "Receita da conta (US$ mi)",
  funcionarios: "Funcionários",
  setor: "Setor",
  motivoIcp: "Motivo do ICP",
  intervalo: "Intervalo médio de recompra (dias)",
  ultimaCompra: "Última compra do produto (dias atrás)",
  comprasDepois: "Compras depois de abrir o deal",
  ultimoComprador: "Último comprador",
  ultimaCompraOutro: "Última compra de outro vendedor (dias atrás)",
  separado: "Demanda separada confirmada?",
} as const;

export const F = {
  id: "Oportunidade",
  vendedor: "Vendedor",
  produto: "Produto",
  estagio: "Estágio",
  engajou: "Engajou em",
  diasAberto: "Dias aberto",
  preco: "Preço de tabela",
  vivo: "Vivo?",
  manager: "Manager",
  prazo: "Prazo pra identificar",
  status: "Status (vendedor)",
  conta: "Conta identificada (vendedor)",
  dono: "Dono da conta (se identificada)",
  escalada: "Escalada",
  ordem: "Ordem na fila",
} as const;

export const K = {
  vendedor: "Vendedor",
  abertos: "Deals abertos na lista",
  ganhos: "Ganhos",
  perdidos: "Perdidos",
  fechados: "Fechados",
  taxa: "Taxa de fechamento",
  vendido: "Vendido ($)",
  contas: "Contas que você é dono",
  produtosPorConta: "Média de produtos por conta",
  gastoTotal: "Gasto total das suas contas ($)",
  gastoMedio: "Gasto médio por conta ($)",
  fila: "Fila sem conta",
  p1: "Passo 1", p2: "Passo 2", p3: "Passo 3", p4: "Passo 4",
  semana: "Pra tocar até sexta",
  confirmar: "Confirmar",
} as const;

export const M = {
  vendedor: "Vendedor",
  manager: "Manager",
  regiao: "Região",
  hojeComoEsta: "Deals com conta hoje (como está)",
  carteiras: "Deals com conta (carteiras)",
  naLista: "Na Lista do Dia (modo atual)",
  p1: "Passo 1", p2: "Passo 2", p3: "Passo 3", p4: "Passo 4",
  semana: "Pra tocar até sexta (1 a 3)",
  fila: "Fila sem conta",
  filaFora: "Fila fora do prazo",
  vivosOutroDono: "Deals vivos em conta de outro dono",
  carteiraVsPassado: "Carteira vs passado",
  faixa: "Checagem da faixa",
  alerta: "Alerta",
  confirmar: "Confirmar",
} as const;

export const R = {
  conta: "Conta",
  produto: "Produto",
  intervalo: "Intervalo médio (dias)",
  compras: "Compras (14 meses)",
  diasAte: "Dias até a recompra",
  situacao: "Situação",
  dono: "Dono (Books)",
  icp: "ICP",
  preco: "Preço de tabela",
  ultimaCompra: "Última compra (dias atrás)",
  entra: "Entra na lista?",
  ordem: "Ordem (por dono)",
  porque: "Por quê",
  acao: "Próxima ação",
  abertos: "Deals abertos (todos)",
  feito: "Feito hoje?",
  dealConfirmar: "Deal a confirmar",
} as const;
